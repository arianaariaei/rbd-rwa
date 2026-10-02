"""Remove the heartbeat from chin EMG.

The chin electrodes pick up the ECG. Each QRS complex adds a ~50-100 ms
deflection to the chin signal, so in quiet REM sleep - exactly where RWA is
measured - every heartbeat can look like a small muscle burst. In CAP's
healthy controls the chin amplitude at the R-peak is up to 2.5x the
surrounding level, enough to cross the 2x-background threshold of SINBAR.
Automated RWA tools remove it (RBDtector uses template subtraction), and so
do we:

  1. find R-peaks on the ECG channel
  2. average the filtered chin EMG around them, in 5-minute blocks, into a
     heartbeat template (a median, so genuine muscle bursts do not leak in)
  3. subtract the template at every beat
"""
import numpy as np

ECG_BIPOLAR = ("ECG1-ECG2", "EKG1-EKG2")
ECG_PAIRS = (("ECG1", "ECG2"), ("EKG1", "EKG2"))
ECG_PREFIX = ("ECG", "EKG")


def _norm(label):
    return label.upper().replace(" ", "")


def find_ecg(hdr):
    """The ECG source: a channel, a (positive, negative) pair, or None."""
    chans = hdr.channels
    for c in chans:
        if any(p in _norm(c.label) for p in ECG_BIPOLAR):
            return c
    lab = {_norm(c.label): c for c in chans}
    for a, b in ECG_PAIRS:
        if a in lab and b in lab and lab[a].fs == lab[b].fs:
            return (lab[a], lab[b])
    return next((c for c in chans if _norm(c.label).startswith(ECG_PREFIX)), None)


def r_peaks(ecg, fs, window_s=30.0):
    """
    R-peak times in seconds. Band-pass 5-20 Hz, orient so the QRS points up,
    then keep peaks >= 0.3 s apart (<= 200 bpm) that exceed 35% of the local
    99th percentile, computed in `window_s` windows so that slow changes in
    ECG amplitude through the night do not break detection.
    """
    from scipy.signal import butter, sosfiltfilt, find_peaks
    if fs < 50 or len(ecg) < fs * 60:
        return np.empty(0)
    sos = butter(3, [5.0, min(20.0, fs / 2 - 1)], btype="band", fs=fs, output="sos")
    y = sosfiltfilt(sos, np.asarray(ecg, dtype=np.float64))
    if abs(np.percentile(y, 0.1)) > abs(np.percentile(y, 99.9)):
        y = -y
    w = int(window_s * fs)
    n = int(np.ceil(len(y) / w))
    level = np.array([np.percentile(y[i * w:(i + 1) * w], 99) for i in range(n)])
    height = np.repeat(0.35 * level, w)[: len(y)]
    peaks, _ = find_peaks(y, height=height, distance=int(0.3 * fs))
    return peaks / fs


def plausible(peaks_s, duration_s):
    """True when the detected beats look like a heart rate, not noise."""
    if len(peaks_s) < 100:
        return False
    rate = 60.0 * len(peaks_s) / duration_s
    rr = np.diff(peaks_s)
    return 35.0 <= rate <= 130.0 and np.mean((rr > 0.33) & (rr < 2.0)) > 0.9


def subtract_heartbeat(x, fs, peaks_s, pre_s=0.10, post_s=0.15, block_s=300.0):
    """
    Subtract a local heartbeat template from a FILTERED signal. Returns the
    cleaned copy. Segments never overlap because beats are >= 0.3 s apart.
    """
    from scipy.signal.windows import tukey
    x = np.array(x, dtype=np.float64, copy=True)
    a, b = int(round(pre_s * fs)), int(round(post_s * fs))
    idx = np.round(np.asarray(peaks_s) * fs).astype(np.int64)
    idx = idx[(idx - a >= 0) & (idx + b <= len(x))]
    if len(idx) < 20:
        return x
    seg = idx[:, None] + np.arange(-a, b)[None, :]
    beats = x[seg]
    taper = tukey(a + b, alpha=0.3)
    overall = np.median(beats, axis=0)
    block = (idx / fs // block_s).astype(np.int64)
    for k in np.unique(block):
        m = block == k
        tmpl = np.median(beats[m], axis=0) if m.sum() >= 20 else overall
        x[seg[m]] -= tmpl * taper
    return x


def artifact_ratio(env, env_fs, peaks_s):
    """
    Heartbeat-locked envelope profile: the median at each lag around the
    R-peak, peak (-40..+80 ms) over baseline (-500..-300 ms). ~1 means no
    heartbeat artifact; 2.5 means the beat dominates quiet EMG. Medians at
    each lag (not a maximum over noisy single beats) keep this unbiased.
    """
    i = np.round(np.asarray(peaks_s) * env_fs).astype(np.int64)
    lags = np.arange(-int(0.5 * env_fs), int(0.1 * env_fs) + 1)
    i = i[(i + lags[0] >= 0) & (i + lags[-1] < len(env))]
    if len(i) < 50:
        return float("nan")
    prof = np.array([np.median(env[i + k]) for k in lags])
    t = lags / env_fs
    base = np.median(prof[(t >= -0.5) & (t <= -0.3)])
    peak = prof[(t >= -0.04) & (t <= 0.08)].max()
    return float(peak / base) if base > 0 else float("nan")
