"""Turn a raw overnight PSG into a small derived file.

One CAP recording is ~370 MB; what RWA quantification needs is the EMG
amplitude envelope and the hypnogram, a few MB. Extracting and discarding the
raw signal is what makes the project runnable on hosted notebooks, where disk
is ephemeral and sessions end without warning.

Per recording we keep:
    chin  (4, n_bins) float16 - chin EMG amplitude per 20 ms bin:
              rows = RMS and mean-rectified in the native band (10-100 Hz or
              as high as the sampling rate allows), then the same two in the
              common 10-45 Hz band shared by every recording
    legs  (n_legs, n_bins) float16 - leg EMG RMS, native band
    hypnogram (n_epochs,) int8   - 30 s sleep stages on the EDF timeline
    meta  json - channels, native rates, bands, units, alignment

TIMING. Bins are exactly 1/ENV_FS seconds long whatever the source rate, so a
bin index converts to time without drift. (An earlier version used a whole
number of samples per bin; at 512 Hz that made 51.2 bins per second instead
of 50 and shifted the hypnogram by ~11 minutes by the end of a night.)
"""
import json
from pathlib import Path

import numpy as np

from .config import ENV_FS, EMG_BAND, HARMONIZED_BAND, DERIVED
from .cap import build_hypnogram, EPOCH_SEC
from .edf import read_header, read_channel

CHIN_ROWS = ("rms", "mav", "rms_h", "mav_h")

# How chin and leg EMG are labelled across CAP's recording systems. Bipolar
# labels win over split electrodes, which win over a lone referential name.
CHIN_BIPOLAR = ("EMG1-EMG2", "EMG-EMG", "CHIN1-CHIN2")
CHIN_PAIRS = (("EMG1", "EMG2"), ("CHIN1", "CHIN2"))
CHIN_SINGLE = ("CHIN", "MILO", "EMG", "MENT", "SUBM")   # MILO = mylohyoid
LEG_BIPOLAR = ("DX1-DX2", "SX1-SX2")                    # DX/SX = right/left
LEG_CONTAINS = ("TIB",)
LEG_PAIRS = (("DX1", "DX2"), ("SX1", "SX2"))


def _norm(label):
    return label.upper().replace(" ", "")


def _pair(chans, a, b):
    lab = {_norm(c.label): c for c in chans}
    if a in lab and b in lab and lab[a].fs == lab[b].fs:
        return (lab[a], lab[b])
    return None


def find_emg(hdr):
    """
    Locate chin and leg EMG. Each source is either a single channel or a
    (positive, negative) pair to be subtracted. Returns (chin, legs).
    """
    chans = hdr.channels
    chin = next((c for c in chans if _norm(c.label) in CHIN_BIPOLAR
                 or any(p in _norm(c.label) for p in CHIN_BIPOLAR)), None)
    if chin is None:
        chin = next((p for a, b in CHIN_PAIRS if (p := _pair(chans, a, b))), None)
    if chin is None:
        chin = next((c for name in CHIN_SINGLE for c in chans
                     if _norm(c.label) == name), None)

    legs = [c for c in chans if any(p in _norm(c.label) for p in LEG_BIPOLAR)]
    legs += [c for c in chans if any(p in _norm(c.label) for p in LEG_CONTAINS)
             and c not in legs]
    if not legs:
        legs = [p for a, b in LEG_PAIRS if (p := _pair(chans, a, b))]
    return chin, legs


def read_source(hdr, src):
    """Signal for a channel or a (positive, negative) pair of channels."""
    if isinstance(src, tuple):
        a, fs, ka = read_channel(hdr, src[0])
        b, _, kb = read_channel(hdr, src[1])
        return a - b, fs, ka and kb, f"{src[0].label}-{src[1].label}", src[0]
    x, fs, k = read_channel(hdr, src)
    return x, fs, k, src.label, src


def emg_band(fs, band=EMG_BAND):
    """The EMG pass-band actually usable at this sampling rate."""
    lo, hi = band
    hi = min(hi, fs / 2.0 - 5.0)
    if hi <= lo:
        raise ValueError(f"sampling rate {fs} Hz too low for EMG band {band}")
    return lo, hi


def envelope(sig, fs, env_fs=ENV_FS, band=EMG_BAND, mains=None):
    """
    Band-pass (and optionally notch) the EMG, then reduce it to amplitude per
    bin of exactly 1/env_fs seconds. Returns (rms, mav, (lo, hi)).
    """
    from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt

    lo, hi = emg_band(fs, band)
    sos = butter(4, [lo, hi], btype="band", fs=fs, output="sos")
    x = sosfiltfilt(sos, np.asarray(sig, dtype=np.float64))
    if mains:
        # Mains and its harmonics that fall inside the pass-band
        for f0 in np.arange(mains, hi, mains):
            b, a = iirnotch(f0, Q=30.0, fs=fs)
            x = filtfilt(b, a, x)

    n_bins = int(np.floor(len(x) * env_fs / fs))
    if n_bins == 0:
        raise ValueError("signal shorter than one envelope bin")
    edges = np.floor(np.arange(n_bins + 1) * fs / env_fs).astype(np.int64)
    counts = np.diff(edges)
    rms = np.sqrt(np.add.reduceat(x * x, edges[:-1]) / counts)
    mav = np.add.reduceat(np.abs(x), edges[:-1]) / counts
    return rms.astype(np.float32), mav.astype(np.float32), (lo, hi)


def _describe(label, ch, fs, unit_known, band, x):
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    return {"label": label, "fs": fs, "band": list(band),
            "unit": ch.dim, "unit_known": bool(unit_known),
            "transducer": ch.transducer, "prefilter": ch.prefilter,
            # share of samples sitting at the recording's largest magnitude:
            # well above ~1e-4 means the recorder was clipping
            "clipped_frac": float(np.mean(np.abs(x) >= 0.999 * peak)) if peak > 0 else 0.0}


def extract_recording(edf_path: Path, txt_path: Path, record: str,
                      out_dir: Path = None, overwrite=False, mains=50.0):
    """Extract one CAP recording to a compact .npz. Returns the output path."""
    out_dir = Path(out_dir or DERIVED)
    out = out_dir / f"{record}.npz"
    if out.exists() and not overwrite:
        return out

    hdr = read_header(edf_path)
    chin_src, leg_srcs = find_emg(hdr)
    if chin_src is None:
        raise ValueError(f"{record}: no chin EMG channel among "
                         f"{[c.label for c in hdr.channels]}")

    x, fs, unit_known, label, ch = read_source(hdr, chin_src)
    rms, mav, band = envelope(x, fs, mains=mains)
    rms_h, mav_h, band_h = envelope(x, fs, band=HARMONIZED_BAND, mains=mains)
    chin_meta = _describe(label, ch, fs, unit_known, band, x)
    chin_meta["band_harmonized"] = list(band_h)
    chin_rows = [rms, mav, rms_h, mav_h]
    del x

    leg_rows, leg_meta = [], []
    for src in leg_srcs:
        x, fs, k, label, ch = read_source(hdr, src)
        r, _, b = envelope(x, fs, mains=mains)
        leg_rows.append(r)
        leg_meta.append(_describe(label, ch, fs, k, b, x))
        del x

    n = min(len(r) for r in chin_rows + leg_rows)   # sources can differ by a bin
    chin = np.stack([r[:n] for r in chin_rows])
    legs = np.stack([r[:n] for r in leg_rows]) if leg_rows \
        else np.zeros((0, n), np.float32)

    n_seconds = n / ENV_FS
    hyp, align = build_hypnogram(edf_path, txt_path, n_seconds)

    meta = {
        "record": record,
        "chin_channel": chin_meta["label"],
        "leg_channels": [m["label"] for m in leg_meta],
        "chin_info": chin_meta,
        "leg_info": leg_meta,
        "chin_rows": list(CHIN_ROWS),
        "env_fs": ENV_FS,
        "mains_notch": mains,
        "duration_s": float(n_seconds),
        "epoch_sec": EPOCH_SEC,
        "alignment": align,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp.npz")
    np.savez_compressed(tmp, chin=chin.astype(np.float16), legs=legs.astype(np.float16),
                        hypnogram=hyp, meta=json.dumps(meta))
    tmp.replace(out)                             # never leave a half-written file
    return out


def load_derived(path):
    """
    Read a derived file back. Returns a dict with float32 arrays:
    chin_rms, chin_mav, chin_rms_h, chin_mav_h, legs (n_legs, n) and
    hypnogram, plus meta.
    """
    z = np.load(path, allow_pickle=False)
    meta = json.loads(str(z["meta"]))
    chin = z["chin"].astype(np.float32)
    d = {f"chin_{name}": chin[i] for i, name in enumerate(meta["chin_rows"])}
    d["legs"] = z["legs"].astype(np.float32)
    d["hypnogram"] = z["hypnogram"]
    d["meta"] = meta
    return d


def summarise(path):
    d = load_derived(path)
    meta, hyp = d["meta"], d["hypnogram"]
    rem = int((hyp == 4).sum())
    ci = meta["chin_info"]
    legs = "/".join(f"{m['fs']:g}" for m in meta["leg_info"]) or "-"
    unit = "" if ci["unit_known"] else "  NO-UNITS"
    return (f"{meta['record']:<8} {meta['duration_s']/3600:>5.1f} h  "
            f"chin {ci['label']} @ {ci['fs']:g} Hz{unit}  legs {legs} Hz  "
            f"REM {rem} epochs ({rem*0.5:.0f} min)")
