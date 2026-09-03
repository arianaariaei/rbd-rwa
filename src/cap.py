"""Parse CAP Sleep Database annotations and align them to the EDF clock.

The annotation file is a RemLogic export whose epochs are stamped with WALL
CLOCK times ("23:07:19"), while the signal array starts at whatever time the
EDF header declares. Aligning them is the step most likely to go silently
wrong: an unnoticed offset shifts every sleep stage relative to the signal and
quietly corrupts every downstream measurement, so the offset is computed
explicitly here and reported.
"""
import datetime as dt
import re
from pathlib import Path

import numpy as np

# W / S1 / S2 / S3 / S4 / R / MT  ->  compact codes
STAGE_CODE = {"W": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 3, "R": 4}
STAGE_NAME = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM", -1: "excluded"}
EPOCH_SEC = 30


def edf_start_datetime(edf_path: Path) -> dt.datetime:
    """Recording start from the EDF header (bytes 168-183)."""
    with open(edf_path, "rb") as f:
        head = f.read(184)
    d = head[168:176].decode("ascii", "ignore").strip()   # dd.mm.yy
    t = head[176:184].decode("ascii", "ignore").strip()   # hh.mm.ss
    day, mon, yr = (int(x) for x in re.split(r"[.\-/]", d))
    hh, mm, ss = (int(x) for x in re.split(r"[.\-:]", t))
    # EDF year is two digits: 85-99 -> 19xx, 00-84 -> 20xx (EDF spec clipping rule)
    yr += 1900 if yr >= 85 else 2000
    return dt.datetime(yr, mon, day, hh, mm, ss)


def parse_annotations(txt_path: Path):
    """Return (times, stages) for every scored 30 s epoch, in file order."""
    raw = Path(txt_path).read_bytes().decode("latin-1")
    lines = [l.rstrip("\r") for l in raw.split("\n")]

    # The table begins at the header row; column order varies between files.
    hdr_i = next(i for i, l in enumerate(lines) if l.startswith("Sleep Stage"))
    cols = [c.strip() for c in lines[hdr_i].split("\t")]
    i_stage = cols.index("Sleep Stage")
    i_time = next(i for i, c in enumerate(cols) if c.startswith("Time"))
    i_event = cols.index("Event") if "Event" in cols else None

    times, stages = [], []
    for line in lines[hdr_i + 1:]:
        parts = line.split("\t")
        if len(parts) <= max(i_stage, i_time):
            continue
        # Only sleep-stage rows; CAP files also carry MCAP-A1/A2/A3 arousal events
        if i_event is not None and i_event < len(parts):
            if not parts[i_event].strip().upper().startswith("SLEEP"):
                continue
        stage = parts[i_stage].strip().upper()
        tm = parts[i_time].strip()
        m = re.match(r"(\d{1,2})[:.](\d{2})[:.](\d{2})", tm)
        if not m:
            continue
        times.append(tuple(int(g) for g in m.groups()))
        stages.append(STAGE_CODE.get(stage, -1))
    return times, np.array(stages, dtype=np.int8)


def build_hypnogram(edf_path: Path, txt_path: Path, n_seconds: float):
    """
    Hypnogram on the EDF's own timeline: one code per 30 s epoch from recording
    start. Returns (hypnogram, info).
    """
    start = edf_start_datetime(edf_path)
    times, stages = parse_annotations(txt_path)
    if len(times) == 0:
        raise ValueError(f"{Path(txt_path).name}: no scored epochs found")

    # Walk the clock forward, adding a day whenever it wraps past midnight.
    day = 0
    prev = None
    offsets = []
    for hh, mm, ss in times:
        cur = hh * 3600 + mm * 60 + ss
        if prev is not None and cur < prev - 3600:   # wrapped midnight
            day += 1
        prev = cur
        stamp = dt.datetime(start.year, start.month, start.day, hh, mm, ss) \
            + dt.timedelta(days=day)
        offsets.append((stamp - start).total_seconds())

    offsets = np.array(offsets)
    # The first annotation may precede the EDF start by a day if the recording
    # itself began before midnight and the header date is the following day.
    if offsets[0] < -12 * 3600:
        offsets += 24 * 3600

    n_epochs = int(np.floor(n_seconds / EPOCH_SEC))
    hyp = np.full(n_epochs, -1, dtype=np.int8)
    idx = np.round(offsets / EPOCH_SEC).astype(int)
    keep = (idx >= 0) & (idx < n_epochs)
    hyp[idx[keep]] = stages[keep]

    info = {
        "edf_start": start.isoformat(),
        "first_annotation_offset_s": float(offsets[0]),
        "n_annotated": int(len(stages)),
        "n_placed": int(keep.sum()),
        "n_dropped_outside_signal": int((~keep).sum()),
        "n_epochs": int(n_epochs),
        "counts": {STAGE_NAME[k]: int((hyp == k).sum())
                   for k in sorted(STAGE_NAME) if (hyp == k).sum()},
    }
    return hyp, info
