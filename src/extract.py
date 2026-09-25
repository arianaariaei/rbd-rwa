"""Turn a raw overnight PSG into a small derived file.

One CAP recording is ~370 MB; what RWA quantification needs is the EMG
amplitude envelope and the hypnogram, which is a few MB. Extracting and
discarding the raw signal is what makes the project runnable on hosted
notebooks, where disk is ephemeral and sessions end without warning.

Per recording we keep, for chin EMG first and then each leg EMG channel:
    rms   (n_channels, n_bins) float16 - RMS amplitude per 20 ms bin
    mav   (n_channels, n_bins) float16 - mean absolute (rectified) amplitude
    hypnogram (n_epochs,) int8         - 30 s sleep stages on the EDF timeline
    meta  json - channels, native rates, filter bands, units, alignment

TIMING. Bins are exactly 1/ENV_FS seconds long whatever the source rate, so a
bin index converts to time without drift. (An earlier version used a fixed
integer number of samples per bin; at 512 Hz that made 51.2 bins per second
instead of 50 and shifted the hypnogram by ~11 minutes by the end of a night.)
"""
import json
from pathlib import Path

import numpy as np

from .config import ENV_FS, EMG_BAND, DERIVED
from .cap import build_hypnogram, EPOCH_SEC
from .edf import read_header, read_channel

# Channel roles. CAP uses Italian labels: DX = destra (right), SX = sinistra (left).
CHIN_PATTERNS = ("EMG1-EMG2", "EMG1", "CHIN", "MENT")
LEG_PATTERNS = ("DX1-DX2", "SX1-SX2", "TIB", "LEG")


def _match(channels, patterns):
    out = []
    for c in channels:
        u = c.label.upper().replace(" ", "")
        if c.uv_scale is not None and any(p.replace(" ", "") in u for p in patterns):
            out.append(c)
    return out


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


def extract_recording(edf_path: Path, txt_path: Path, record: str,
                      out_dir: Path = None, overwrite=False, mains=50.0):
    """Extract one CAP recording to a compact .npz. Returns the output path."""
    out_dir = Path(out_dir or DERIVED)
    out = out_dir / f"{record}.npz"
    if out.exists() and not overwrite:
        return out

    hdr = read_header(edf_path)
    chin = _match(hdr.channels, CHIN_PATTERNS)
    legs = _match(hdr.channels, LEG_PATTERNS)
    if not chin:
        raise ValueError(f"{record}: no chin EMG channel among "
                         f"{[c.label for c in hdr.channels]}")
    picks = chin[:1] + legs                      # chin first, by convention

    rms, mav, chan_meta = [], [], []
    for c in picks:
        x, fs = read_channel(hdr, c.label)
        r, m, (lo, hi) = envelope(x, fs, mains=mains)
        rms.append(r)
        mav.append(m)
        peak = float(np.max(np.abs(x))) if len(x) else float("nan")
        chan_meta.append({
            "label": c.label, "fs": fs, "band": [lo, hi], "unit": c.dim,
            "prefilter": c.prefilter,
            # share of samples sitting at the recorder's clipping level
            "clipped_frac": float(np.mean(np.abs(x) >= 0.999 * peak)) if peak > 0 else 0.0,
        })
        del x
    n = min(len(r) for r in rms)                 # channels can differ by a bin
    rms = np.stack([r[:n] for r in rms])
    mav = np.stack([m[:n] for m in mav])

    n_seconds = n / ENV_FS
    hyp, align = build_hypnogram(edf_path, txt_path, n_seconds)

    meta = {
        "record": record,
        "channels": [c.label for c in picks],
        "chin_channel": chin[0].label,
        "leg_channels": [c.label for c in legs],
        "channel_info": chan_meta,
        "env_fs": ENV_FS,
        "mains_notch": mains,
        "duration_s": float(n_seconds),
        "epoch_sec": EPOCH_SEC,
        "alignment": align,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp.npz")
    np.savez_compressed(tmp, rms=rms.astype(np.float16), mav=mav.astype(np.float16),
                        hypnogram=hyp, meta=json.dumps(meta))
    tmp.replace(out)                             # never leave a half-written file
    return out


def load_derived(path, kind="rms"):
    """Read a derived file back as (env, hypnogram, meta); env is float32."""
    z = np.load(path, allow_pickle=False)
    meta = json.loads(str(z["meta"]))
    key = kind if kind in z.files else "env"     # files from the first version
    return z[key].astype(np.float32), z["hypnogram"], meta


def summarise(path):
    env, hyp, meta = load_derived(path)
    rem = int((hyp == 4).sum())
    rates = "/".join(f"{c['fs']:g}" for c in meta.get("channel_info", []))
    return (f"{meta['record']:<8} {meta['duration_s']/3600:>5.1f} h  "
            f"fs {rates} Hz  chin={meta['chin_channel']:<10} "
            f"legs={len(meta['leg_channels'])}  "
            f"REM {rem} epochs ({rem*0.5:.0f} min)")
