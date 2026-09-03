"""Turn a raw overnight PSG into a small derived file.

One CAP recording is ~430 MB; what RWA quantification actually needs is the
rectified EMG envelope and the hypnogram, which is a few MB. Extracting and
discarding the raw signal is what makes the project runnable on Colab, where
disk is ephemeral and sessions end without warning.

Per recording we keep:
    env        (n_channels, n_samples) float32 - rectified EMG envelope @ ENV_FS
    hypnogram  (n_epochs,) int8        - 30 s sleep stages on the EDF timeline
    meta       json - channels, sampling rates, alignment diagnostics
"""
import json
from pathlib import Path

import numpy as np

from .config import ENV_FS, EMG_BAND, DERIVED
from .cap import build_hypnogram, EPOCH_SEC, STAGE_NAME

# Channel roles. CAP uses Italian labels: DX = destra (right), SX = sinistra (left).
CHIN_PATTERNS = ("EMG1-EMG2", "EMG1", "CHIN", "MENT")
LEG_PATTERNS = ("DX1-DX2", "SX1-SX2", "TIB", "LEG")


def _match(ch_names, patterns):
    out = []
    for name in ch_names:
        u = name.upper().replace(" ", "")
        if any(p.replace(" ", "") in u for p in patterns):
            out.append(name)
    return out


def envelope(sig, fs, env_fs=ENV_FS, band=EMG_BAND):
    """Band-pass, rectify, and reduce to RMS in non-overlapping bins."""
    from scipy.signal import butter, filtfilt

    nyq = fs / 2.0
    lo, hi = band
    hi = min(hi, nyq - 5.0)
    if hi <= lo:
        raise ValueError(f"sampling rate {fs} Hz too low for EMG band {band}")
    b, a = butter(4, [lo / nyq, hi / nyq], btype="band")
    x = filtfilt(b, a, np.asarray(sig, dtype=np.float64))

    step = int(round(fs / env_fs))
    n = len(x) // step
    if n == 0:
        raise ValueError("signal shorter than one envelope bin")
    w = x[: n * step].reshape(n, step)
    return np.sqrt((w ** 2).mean(axis=1)).astype(np.float32)


def extract_recording(edf_path: Path, txt_path: Path, record: str,
                      out_dir: Path = None, overwrite=False):
    """Extract one recording to a compact .npz. Returns the output path."""
    import mne

    out_dir = Path(out_dir or DERIVED)
    out = out_dir / f"{record}.npz"
    if out.exists() and not overwrite:
        return out

    raw = mne.io.read_raw_edf(str(edf_path), preload=False, verbose=False)
    fs_all = raw.info["sfreq"]
    chin = _match(raw.ch_names, CHIN_PATTERNS)
    legs = _match(raw.ch_names, LEG_PATTERNS)
    if not chin:
        raise ValueError(f"{record}: no chin EMG channel among {raw.ch_names}")
    picks = chin[:1] + legs                      # chin first, by convention

    raw.pick(picks)
    raw.load_data(verbose=False)
    data = raw.get_data() * 1e6                  # MNE returns volts; use microvolts

    envs = np.stack([envelope(row, fs_all) for row in data])
    n_seconds = data.shape[1] / fs_all
    hyp, align = build_hypnogram(edf_path, txt_path, n_seconds)

    meta = {
        "record": record,
        "channels": picks,
        "chin_channel": chin[0],
        "leg_channels": legs,
        "source_fs": float(fs_all),
        "env_fs": ENV_FS,
        "emg_band": [EMG_BAND[0], min(EMG_BAND[1], fs_all / 2 - 5)],
        "duration_s": float(n_seconds),
        "epoch_sec": EPOCH_SEC,
        "alignment": align,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, env=envs, hypnogram=hyp,
                        meta=json.dumps(meta))
    return out


def load_derived(path):
    """Read a derived file back as (env, hypnogram, meta)."""
    z = np.load(path, allow_pickle=False)
    return z["env"], z["hypnogram"], json.loads(str(z["meta"]))


def summarise(path):
    env, hyp, meta = load_derived(path)
    rem = int((hyp == 4).sum())
    return (f"{meta['record']:<8} {meta['duration_s']/3600:>5.1f} h  "
            f"{meta['source_fs']:>5.0f} Hz -> {meta['env_fs']} Hz  "
            f"chin={meta['chin_channel']:<12} legs={len(meta['leg_channels'])}  "
            f"REM {rem} epochs ({rem*0.5:.0f} min)  "
            f"env {env.nbytes/1e6:.1f} MB")
