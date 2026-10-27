"""Noise that is not white: the ladder's harmonized steps with other kinds of noise.

The noise ladder (cohorts.extract_ladder_pack) added band-limited white noise,
which is stationary and spectrally flat; real recording noise is neither. Here
the same nights are raised to the same quiet-REM levels (1.5 and 2.0 uV, the
ladder's steps h150 and h200) with four kinds of noise (review M6;
paper/preregistration_revision.md, R1):

  white   the ladder's own seeded white noise (reproduces the ladder's copies)
  pink    1/f noise, passed through the same EMG filter
  drift   white noise whose level wanders slowly through the night: a log-normal
          random walk with a 10-min correlation time and SD 0.3 of the log
          level, as electrode impedance does
  hmc     recorded noise: the quietest REM seconds of 30 HMC nights (every fifth
          record), runs of at least 3 s below each night's 20th percentile of
          1-s REM RMS, filtered and heartbeat-cleaned as in the main pipeline,
          spliced with 20-ms cross-fades; resampled to the night's rate and
          passed through its filter. It carries HMC's real spectrum, mains
          residue and electrode artifacts.

Every kind is added after the night's own filtering and heartbeat removal, in the
whole night (REM and N2/N3), as the ladder's noise was.
"""
import json
import zlib
from fractions import Fraction

import numpy as np

from .config import ENV_FS
from .extract import bandpass, bin_envelope

KINDS = ("white", "pink", "drift", "hmc")
TARGETS_UV = (1.5, 2.0)
LIB_FS = 256.0
EPOCH_SEC = 30


def _unit(x, fs):
    """Scale to unit RMS, ignoring 5 s at each end (filter edges)."""
    e = int(5 * fs)
    core = x[e:-e] if len(x) > 4 * e else x
    return x / np.sqrt(np.mean(core * core))


def white(n, fs, mains, rec):
    """Exactly the ladder's track (same seed, same filter)."""
    rng = np.random.default_rng(zlib.crc32(rec.encode()))
    return _unit(bandpass(rng.normal(0.0, 1.0, n), fs, mains=mains)[0], fs)


def pink(n, fs, mains, rec):
    rng = np.random.default_rng(zlib.crc32(("pink/" + rec).encode()))
    spec = np.fft.rfft(rng.normal(0.0, 1.0, n))
    f = np.fft.rfftfreq(n, 1.0 / fs)
    spec[1:] /= np.sqrt(f[1:])
    spec[0] = 0.0
    return _unit(bandpass(np.fft.irfft(spec, n), fs, mains=mains)[0], fs)


def drift(n, fs, mains, rec, tau_s=600.0, sd=0.3):
    rng = np.random.default_rng(zlib.crc32(("drift/" + rec).encode()))
    w = bandpass(rng.normal(0.0, 1.0, n), fs, mains=mains)[0]
    secs = int(np.ceil(n / fs)) + 1
    a = np.exp(-1.0 / tau_s)
    z = np.empty(secs)
    z[0] = rng.normal(0.0, sd)
    steps = rng.normal(0.0, sd * np.sqrt(1 - a * a), secs)
    for i in range(1, secs):                       # Ornstein-Uhlenbeck in the log level
        z[i] = a * z[i - 1] + steps[i]
    level = np.exp(np.interp(np.arange(n) / fs, np.arange(secs), z))
    return _unit(w * level, fs)


def build_library(pieces_by_night, fs=LIB_FS, fade_s=0.02):
    """Splice the quiet runs of several nights into one unit-RMS track."""
    r = int(round(fade_s * fs))
    up = 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r)
    out = np.zeros(0)
    for pieces in pieces_by_night:
        for p in pieces:
            p = np.asarray(p, float)
            if len(p) <= 2 * r:
                continue
            if len(out) >= r:
                out[-r:] = out[-r:] * up[::-1] + p[:r] * up
                out = np.r_[out, p[r:]]
            else:
                out = np.r_[out, p]
    return (out / np.sqrt(np.mean(out * out))).astype(np.float32)


def quiet_runs(xf, fs, hyp, pct=20.0, min_s=3):
    """Runs of at least `min_s` consecutive REM seconds whose 1-s RMS is below the
    night's `pct` percentile: the night's recorded noise with little muscle."""
    per = int(round(fs * EPOCH_SEC))
    hyp = np.asarray(hyp)[: len(xf) // per]
    sec_rms, _ = bin_envelope(xf, fs, env_fs=1)
    rem = np.repeat(hyp == 4, EPOCH_SEC)[: len(sec_rms)]
    if rem.sum() < 60:
        return []
    quiet = rem & (sec_rms <= np.percentile(sec_rms[rem], pct))
    edges = np.diff(np.r_[0, quiet.astype(np.int8), 0])
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    out = []
    for a, b in zip(starts, stops):
        if b - a >= min_s:
            out.append(xf[int(a * fs): int(b * fs)].astype(np.float32))
    return out


def hmc(n, fs, mains, rec, library):
    """The recorded-noise library at this night's rate and filter, tiled from a
    seeded random offset to the night's length."""
    from scipy.signal import resample_poly
    rng = np.random.default_rng(zlib.crc32(("hmc/" + rec).encode()))
    lib = np.asarray(library, float)
    f = Fraction(int(round(fs)), int(LIB_FS)).limit_denominator(1000)
    if f != 1:
        lib = resample_poly(lib, f.numerator, f.denominator)
    start = int(rng.integers(0, len(lib)))
    reps = int(np.ceil((n + start) / len(lib)))
    x = np.tile(lib, reps)[start:start + n]
    return _unit(bandpass(x, fs, mains=mains)[0], fs)


def harmonized(xf, track, fs, hyp, target):
    """Envelopes of xf + s * track with s chosen so that the quiet-REM level is
    within 1% of `target` (the ladder's procedure). Returns (rms, mav, s, level)."""
    from .cohorts import quiet_level
    rms, mav = bin_envelope(xf, fs)
    level = quiet_level(rms, hyp)
    s, got = float(np.sqrt(max(target * target - level * level, 0.0))), level
    r, m = rms, mav
    for _ in range(5):
        if s <= 0:
            break
        r, m = bin_envelope(xf + s * track, fs)
        got = quiet_level(r, hyp)
        if abs(got - target) <= 0.01 * target:
            break
        s *= np.sqrt((target * target - level * level) / max(got * got - level * level, 1e-9))
    return r, m, s, got


def save_library(path, lib, meta):
    np.savez_compressed(path, lib=lib, meta=json.dumps(meta))


def load_library(path):
    z = np.load(path, allow_pickle=False)
    return z["lib"], json.loads(str(z["meta"]))
