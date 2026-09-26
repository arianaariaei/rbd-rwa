"""Open polysomnography cohorts, each reduced to the same compact pack.

Every cohort here is downloadable with no application and no credential:

  cap     CAP Sleep Database (PhysioNet, ODC-By). 22 RBD patients plus
          healthy sleepers and other sleep disorders. Italy, 50 Hz mains.
  chal18  PhysioNet/CinC Challenge 2018 training set (PhysioNet, ODC-By).
          994 clinical PSGs from Massachusetts General Hospital with sleep
          stages, respiratory events and arousals, age and sex. USA, 60 Hz.
  hmc     Haaglanden Medisch Centrum sleep staging database (PhysioNet,
          CC BY 4.0). 148 clinical PSGs. The Netherlands, 50 Hz.

A cohort adapter knows how to list records, fetch one record's files into
scratch, and read from them: chin EMG, ECG, leg EMG (if any), the hypnogram in
30 s epochs from the start of the signal, per-epoch event flags and any
demographics. `extract_pack` turns that into a pack (see pack.py).
"""
import csv
import io
import urllib.request
from pathlib import Path

import numpy as np

from .config import ENV_FS, HARMONIZED_BAND
from .ecg import r_peaks, plausible, artifact_ratio
from .extract import envelope
from .fetch import download_any
from .pack import build_pack

EPOCH_SEC = 30
PHYSIONET = ("https://physionet-open.s3.amazonaws.com/{db}/",
             "https://physionet.org/files/{db}/")


def _mirrors(db):
    return tuple(m.format(db=db) for m in PHYSIONET)


def _read_text(db, name):
    for base in _mirrors(db):
        try:
            return urllib.request.urlopen(base + name, timeout=60).read().decode("latin-1")
        except Exception:
            continue
    raise IOError(f"cannot fetch {db}/{name}")


# ══════════════════════════════════════════════════════════════════════════════
#  CHALLENGE 2018 (MGH)
# ══════════════════════════════════════════════════════════════════════════════

class Chal18:
    name, db, mains = "chal18", "challenge-2018/1.0.0", 60.0
    STAGES = {"W": 0, "N1": 1, "N2": 2, "N3": 3, "R": 4}

    def records(self):
        return [r.strip("/").split("/")[-1]
                for r in _read_text(self.db, "training/RECORDS").split()]

    def demographics(self):
        rows = csv.DictReader(io.StringIO(_read_text(self.db, "age-sex.csv")))
        return {r["Record"]: {"age": float(r["Age"]), "sex": r["Sex"]} for r in rows}

    def fetch(self, rec, scratch):
        out = {}
        for ext in ("hea", "mat", "arousal"):
            out[ext] = download_any(f"training/{rec}/{rec}.{ext}",
                                    Path(scratch) / f"{rec}.{ext}", _mirrors(self.db))
        return out

    def read(self, rec, files):
        import wfdb
        base = str(files["hea"])[:-4]
        sig = wfdb.rdrecord(base, channel_names=["Chin1-Chin2", "ECG"])
        units = [u.lower() for u in sig.units]
        chin = sig.p_signal[:, 0] * (1e3 if units[0] == "mv" else 1.0)
        ecg = sig.p_signal[:, 1] * (1e3 if units[1] == "mv" else 1.0)
        fs = float(sig.fs)
        n_ep = int(len(chin) / fs // EPOCH_SEC)

        ann = wfdb.rdann(base, "arousal")
        hyp = np.full(n_ep, -1, np.int8)
        stage_marks = [(s, self.STAGES[n]) for s, n in zip(ann.sample, ann.aux_note)
                       if n in self.STAGES]
        for (s0, code), nxt in zip(stage_marks, stage_marks[1:] + [(len(chin), None)]):
            a = int(round(s0 / fs / EPOCH_SEC))
            b = int(round(nxt[0] / fs / EPOCH_SEC))
            hyp[a:min(b, n_ep)] = code

        flags = {"resp": np.zeros(n_ep, np.int8), "arousal": np.zeros(n_ep, np.int8)}
        open_ev = {}
        for s, note in zip(ann.sample, ann.aux_note):
            if note.startswith("("):
                open_ev[note[1:]] = s
            elif note.endswith(")") and note[:-1] in open_ev:
                label, s0 = note[:-1], open_ev.pop(note[:-1])
                kind = "resp" if label.startswith("resp_") else \
                    "arousal" if label.startswith("arousal_") else None
                if kind:
                    a = int(s0 / fs // EPOCH_SEC)
                    b = int(s / fs // EPOCH_SEC)
                    flags[kind][a:min(b + 1, n_ep)] = 1
        n_resp = sum(1 for n in ann.aux_note if n.startswith("(resp_"))
        sleep_h = np.isin(hyp, (1, 2, 3, 4)).sum() * EPOCH_SEC / 3600.0
        extra = {"ahi": round(n_resp / sleep_h, 1) if sleep_h > 0 else None}
        return dict(chin=chin, fs=fs, unit_known=units[0] in ("uv", "mv"),
                    chin_label="Chin1-Chin2", ecg=ecg, fs_ecg=fs, legs=[],
                    hypnogram=hyp, flags=flags, extra=extra)


# ══════════════════════════════════════════════════════════════════════════════
#  HAAGLANDEN MEDISCH CENTRUM
# ══════════════════════════════════════════════════════════════════════════════

class HMC:
    name, db, mains = "hmc", "hmc-sleep-staging/1.1", 50.0
    STAGES = {"W": 0, "N1": 1, "N2": 2, "N3": 3, "R": 4}
    # v1.1 lists 151 recordings: SN001-SN154 minus SN014, SN064 and SN135,
    # which the release notes withdrew for erroneous, unfixable signal data.

    def records(self):
        return [Path(x).stem for x in _read_text(self.db, "RECORDS").split()]

    def demographics(self):
        return {}                       # only group-level age/sex are published

    def fetch(self, rec, scratch):
        return {"edf": download_any(f"recordings/{rec}.edf", Path(scratch) / f"{rec}.edf",
                                    _mirrors(self.db)),
                "txt": download_any(f"recordings/{rec}_sleepscoring.txt",
                                    Path(scratch) / f"{rec}_sleepscoring.txt",
                                    _mirrors(self.db))}

    def read(self, rec, files):
        from .edf import read_header, read_channel
        hdr = read_header(files["edf"])
        chin_ch = next(c for c in hdr.channels if "CHIN" in c.label.upper())
        ecg_ch = next((c for c in hdr.channels if "ECG" in c.label.upper()), None)
        chin, fs, unit_known = read_channel(hdr, chin_ch)
        ecg, fs_e = (read_channel(hdr, ecg_ch)[:2]) if ecg_ch else (None, None)
        n_ep = int(len(chin) / fs // EPOCH_SEC)
        hyp = np.full(n_ep, -1, np.int8)
        text = Path(files["txt"]).read_text(encoding="latin-1").splitlines()
        for line in text[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 5 or not parts[4].startswith("Sleep stage"):
                continue
            code = self.STAGES.get(parts[4].split()[-1])
            e = int(round(float(parts[2]) / EPOCH_SEC))
            if code is not None and 0 <= e < n_ep:
                hyp[e] = code
        return dict(chin=chin, fs=fs, unit_known=unit_known, chin_label=chin_ch.label,
                    ecg=ecg, fs_ecg=fs_e, legs=[], hypnogram=hyp, flags={}, extra={})


COHORTS = {"chal18": Chal18(), "hmc": HMC()}


# ══════════════════════════════════════════════════════════════════════════════
#  COMMON: raw signals -> pack
# ══════════════════════════════════════════════════════════════════════════════

def extract_pack(cohort, rec, d, demo=None):
    """Envelopes, heartbeat removal and packing for one record's signals."""
    beats = np.empty(0)
    if d.get("ecg") is not None:
        beats = r_peaks(d["ecg"], d["fs_ecg"])
        if not plausible(beats, len(d["ecg"]) / d["fs_ecg"]):
            beats = np.empty(0)
    x, fs, mains = d["chin"], d["fs"], cohort.mains
    rms, mav, band = envelope(x, fs, mains=mains, beats_s=beats)
    rms_h, mav_h, band_h = envelope(x, fs, band=HARMONIZED_BAND, mains=mains, beats_s=beats)
    rms_raw, _, _ = envelope(x, fs, mains=mains)
    legs = [envelope(l, fs_l, mains=mains)[0] for l, fs_l in d.get("legs", [])]
    meta = {
        "record": rec, "cohort": cohort.name, "chin_channel": d["chin_label"],
        "chin_fs": fs, "band": list(band), "band_harmonized": list(band_h),
        "unit_known": bool(d["unit_known"]), "mains_notch": mains,
        "ecg": {"beats": int(len(beats)),
                "artifact_ratio_before": round(artifact_ratio(rms_raw, ENV_FS, beats), 3),
                "artifact_ratio_after": round(artifact_ratio(rms, ENV_FS, beats), 3)},
        "duration_s": round(len(x) / fs, 1),
        **(demo or {}), **d.get("extra", {}),
    }
    chin = {"rms": rms, "mav": mav, "rms_h": rms_h, "mav_h": mav_h, "rms_with_ecg": rms_raw}
    return build_pack(chin, legs, d["hypnogram"], ENV_FS, EPOCH_SEC, meta, d.get("flags"))
