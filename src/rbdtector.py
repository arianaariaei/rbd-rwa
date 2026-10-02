"""RBDtector, run unchanged on our nights (paper/preregistration_parkinsons.md).

RBDtector (Röthenbacher et al., Sci Rep 2022; validated at a second center by
Joza et al., J Sleep Res 2025) is the open-source scorer of REM sleep without
atonia used in Parkinson's and RBD research; it was developed on patients with
Parkinson's disease with and without RBD, patients with isolated RBD and
controls. Its default rule counts chin activity where the RMS of a 30 ms chunk
exceeds twice a baseline, and the baseline is the lowest 30 s RMS window of
artifact-free REM in each REM period: on an atonic night, mostly the recording
system's own noise.

`write_inputs` puts one night in RBDtector's input format (an EDF with the chin
EMG as channel 'EMG', in microvolts, and the 'Sleep profile', 'Classification
Arousals' and 'Flow Events' text files of SOMNOmedics' software). `run` calls
RBDtector's own controller on it and returns the chin percentages it reports.
RBDtector does not filter: the signal is band-passed (10-100 Hz) and notched
as an acquisition system would, and the heartbeat is left in, as RBDtector
sees it in practice. No arousals are given (one dummy event in the first
second, which is wake), so no REM is excluded for arousals in any cohort.

The floor-corrected variant changes one thing: the baseline RBDtector computes
is replaced, before detection, by half the floor-corrected threshold
(src/rwa.py, `threshold`): with n = baseline / r the noise RMS that baseline
implies (r from `noise_ratio`, simulated), activity must exceed
max(sqrt(n^2 + 3 B^2), 1.5 n) instead of 2 x baseline, B = 1.0 uV.
"""
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = "https://github.com/aroethen/RBDtector"
COMMIT = "7c9c73d231a29d8ccf56d7eec69ae117ae781c0c"     # master, 19 May 2022
HOME = Path("/content/RBDtector")
# Röthenbacher et al. 2022, Table 5: chin alone, after removal of arousals,
# snoring and technical artifacts (cut-offs at ~100% specificity in their data)
CUTOFF = {"any_pct": 23.5, "phasic_pct": 19.0, "tonic_pct": 7.1}
B_REF, GUARD = 1.0, 1.5
START = dt.datetime(2020, 1, 1, 22, 0, 0)
STAGE = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}
PHYS_UV = 2000.0                      # EDF physical range +-2 mV: 0.06 uV steps

_state = {"variant": "published", "ratio": None, "baseline_uv": np.nan}


def install(home=HOME):
    """Clone RBDtector at the pinned commit (once) and make it importable."""
    home = Path(home)
    if not (home / "RBDtector" / "app_logic" / "PSG.py").exists():
        if home.exists():
            shutil.rmtree(home)
        subprocess.run(["git", "clone", "-q", REPO, str(home)], check=True)
        subprocess.run(["git", "-C", str(home), "checkout", "-q", COMMIT], check=True)
    pkg = str(home / "RBDtector")
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    _patch()
    return home


def noise_ratio(fs=256.0, minutes=10.0, n=20, seed=0):
    """RBDtector's baseline (lowest 30 s RMS of a REM period) over the RMS of
    band-limited white noise alone: median over `n` simulated REM periods."""
    from .extract import bandpass
    rng = np.random.default_rng(seed)
    w, out = int(30 * fs), []
    for _ in range(n):
        x, _ = bandpass(rng.normal(0.0, 1.0, int(minutes * 60 * fs) + int(10 * fs)), fs)
        x = x[int(5 * fs):-int(5 * fs)]
        c = np.r_[0.0, np.cumsum(x * x)]
        roll = np.sqrt((c[w:] - c[:-w]) / w)
        out.append(roll.min() / np.sqrt(np.mean(x * x)))
    return float(np.median(out))


def _find_rem_blocks(MIN_REM_BLOCK_LENGTH_IN_S, is_rem_series):
    """RBDtector's PSG.find_rem_blocks (commit 7c9c73d), copied with one change:
    the REM sample nearest to a short REM piece is found with numpy instead of
    Python's min(..., key=abs) over every REM sample at 256 Hz (about 35 s per
    night). Both return the first minimum, so the output is the same."""
    from util import settings
    continuuos_rem_ge_min_block_length = is_rem_series \
        .groupby(is_rem_series.diff().ne(0).cumsum()) \
        .transform('size') \
        .ge(settings.RATE * MIN_REM_BLOCK_LENGTH_IN_S)
    min_rem_block = continuuos_rem_ge_min_block_length & is_rem_series
    rem_block_counter = 0

    def transform_to_rem_group_name(x):
        if x.all():
            nonlocal rem_block_counter
            rem_block_counter += 1
            return rem_block_counter
        else:
            return 0

    numbered_rem_blocks = min_rem_block \
        .groupby(min_rem_block.diff().ne(0).cumsum()) \
        .transform(transform_to_rem_group_name)
    small_rem_pieces = is_rem_series & ~min_rem_block
    block_indices = numbered_rem_blocks[numbered_rem_blocks != 0].index   # loop-invariant

    def nearest(diff):                       # == min(diff, key=abs)
        return diff[int(np.argmin(np.abs(diff.asi8)))]

    def assign_small_piece_to_rem_block(x):
        if x.all():
            first_index_of_piece = x.index[0]
            last_index_of_piece = x.index[-1]
            closest_to_beginning_of_piece = nearest(first_index_of_piece - block_indices)
            closest_to_end_of_piece = nearest(last_index_of_piece - block_indices)
            if closest_to_beginning_of_piece < closest_to_end_of_piece:
                block_number = numbered_rem_blocks[first_index_of_piece - closest_to_beginning_of_piece]
            else:
                block_number = numbered_rem_blocks[last_index_of_piece - closest_to_end_of_piece]
            return block_number
        else:
            return 0

    small_rem_pieces_assigned_to_numbered_rem_blocks = small_rem_pieces \
        .groupby(small_rem_pieces.diff().ne(0).cumsum()) \
        .transform(assign_small_piece_to_rem_block)
    all_rem_sleep_numbered = numbered_rem_blocks + small_rem_pieces_assigned_to_numbered_rem_blocks
    return all_rem_sleep_numbered, min_rem_block, numbered_rem_blocks, small_rem_pieces


def _patch():
    """Wrap RBDtector's baseline finder: record the baseline, and replace it by
    half the floor-corrected threshold when the variant is 'FC'. Also give
    pyedflib's signal headers the key RBDtector (2022) reads: pyedflib has since
    renamed 'sample_rate' to 'sample_frequency' (an I/O shim; detection unchanged)."""
    from pyedflib import highlevel
    if not getattr(highlevel, "_rwa_patched", False):
        read_edf = highlevel.read_edf

        def read_edf_with_rate(*args, **kwargs):
            signals, headers, header = read_edf(*args, **kwargs)
            for h in headers:
                if "sample_rate" not in h and "sample_frequency" in h:
                    h["sample_rate"] = h["sample_frequency"]
            return signals, headers, header

        highlevel.read_edf = read_edf_with_rate
        highlevel._rwa_patched = True
    from app_logic.PSG import PSG
    if getattr(PSG, "_rwa_patched", False):
        return
    original = PSG.find_baselines
    PSG.find_rem_blocks = staticmethod(_find_rem_blocks)

    def find_baselines(*args, **kwargs):
        # The floor-corrected run of a night starts from the baseline its published
        # run computed from the same input files (identical, so reused, not redone)
        if _state["variant"] == "FC" and _state.get("cache_key") == _state.get("folder"):
            df_b, df_art = (d.copy() for d in _state["cache"])
        else:
            df_b, df_art = original(*args, **kwargs)
            _state["cache_key"], _state["cache"] = _state.get("folder"), (df_b.copy(), df_art.copy())
        cols = [c for c in df_b.columns if c.endswith("_baseline")]
        if cols:
            _state["baseline_uv"] = float(np.nanmedian(df_b[cols[0]].to_numpy(float)))
        if _state["variant"] == "FC":
            r = _state["ratio"] or noise_ratio()
            _state["ratio"] = r
            for c in cols:
                b = df_b[c].to_numpy(float)
                nz = b / r
                thr = np.maximum(np.sqrt(nz * nz + 3.0 * B_REF * B_REF), GUARD * nz)
                df_b[c] = thr / 2.0
        return df_b, df_art

    PSG.find_baselines = staticmethod(find_baselines)
    PSG._rwa_patched = True


def write_inputs(folder, x_uv, fs, hypnogram, epoch_s=30):
    """One night in RBDtector's input format; returns the folder."""
    import pyedflib
    from pyedflib import highlevel
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if not float(fs).is_integer():
        raise ValueError(f"EDF needs whole samples per second, got {fs} Hz")
    fs = int(fs)
    n_sec = len(x_uv) // fs
    n_ep = min(len(hypnogram), n_sec // epoch_s)
    x = np.clip(np.asarray(x_uv[: n_ep * epoch_s * fs], dtype=np.float64), -PHYS_UV, PHYS_UV)
    # pyEDFlib 0.1.22 calls the rate 'sample_rate', later versions 'sample_frequency'
    import inspect
    rate = "sample_frequency" if "sample_frequency" in \
        inspect.signature(highlevel.make_signal_header).parameters else "sample_rate"
    sh = highlevel.make_signal_header("EMG", dimension="uV", physical_min=-PHYS_UV,
                                      physical_max=PHYS_UV, digital_min=-32768,
                                      digital_max=32767, **{rate: fs})
    hdr = highlevel.make_header(startdate=START)
    highlevel.write_edf(str(folder / "night.edf"), [x], [sh], hdr,
                        file_type=pyedflib.FILETYPE_EDFPLUS)
    clock = lambda s: (START + dt.timedelta(seconds=s)).strftime("%H:%M:%S") + ",000"
    head = START.strftime("%d.%m.%Y %H:%M:%S")
    lines = ["Signal ID: SchlafProfil\\profil", f"Start Time: {head}", "Unit: ",
             "Signal Type: Discret", "Events list: N4,N3,N2,N1,REM,Wake,Movement",
             "Rate: 30 s", ""]
    lines += [f"{clock(i * epoch_s)}; {STAGE.get(int(c), 'A')}" for i, c in enumerate(hypnogram[:n_ep])]
    (folder / "Sleep profile - night.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, sid in (("Classification Arousals - night.txt", "KorrelationMA\\MAK"),
                      ("Flow Events - night.txt", "FlowEvents\\Events")):
        ev = [f"Signal ID: {sid}", f"Start Time: {head}", "Unit: s", "Signal Type: Impuls", "",
              f"{clock(0)}-{clock(1)}; 1;Dummy (first second, wake)"]
        (folder / name).write_text("\n".join(ev) + "\n", encoding="utf-8")
    return folder


def _flatten(df_out):
    """RBDtector's output frame -> {joined labels: value}."""
    import pandas as pd
    s = df_out
    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0] if s.shape[1] == 1 else s.stack()
    out = {}
    for key, val in s.items():
        parts = key if isinstance(key, tuple) else (key,)
        out["|".join(str(p) for p in parts if str(p))] = val
    return out


def run(folder, variant="published"):
    """RBDtector's controller on one input folder. Returns the chin percentages
    (tonic, phasic, any), the REM epochs it evaluated and its baseline (uV)."""
    import warnings
    warnings.filterwarnings("ignore")
    from app_logic.PSG_controller import PSGController
    _state["variant"] = variant
    _state["baseline_uv"] = np.nan
    _state["folder"] = str(folder)
    df_out, _ = PSGController.run_rbd_detection(str(folder), str(folder))
    if variant == "FC":
        _state["cache_key"] = _state["cache"] = None
    flat = _flatten(df_out)

    def pick(suffix, need="EMG"):
        hits = [v for k, v in flat.items() if k.endswith(suffix) and need in k
                and not k.startswith("Global")]
        return float(hits[0]) if hits else np.nan

    return {"tonic_pct": pick("tonic_%"), "phasic_pct": pick("phasic_%"),
            "any_pct": pick("any_%"),
            "rem_miniepochs": pick("REM_MiniEpochs_WO-Artifacts", need=""),
            "rem_macroepochs": pick("REM_MacroEpochs_WO-Artifacts", need=""),
            "baseline_uv": _state["baseline_uv"], "noise_ratio": _state["ratio"],
            "keys": ";".join(sorted(flat))[:2000]}
