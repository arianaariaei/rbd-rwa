"""Floor check: can this recording system measure REM sleep without atonia?

The relative RWA criteria count chin activity above k x background, and the
background of an atonic night is mostly the recording system's own noise, so
every RWA threshold should be reported together with that floor. From one
night - the chin EMG and the 30 s sleep stages - this reports:

  floor b      quiet-REM level: 5th percentile of 1 s chin RMS in REM (uV), after
               band-pass (10-100 Hz, lower at low sampling rates), mains notch
               and, when an ECG is given, heartbeat removal
  noise n      the noise RMS that floor implies (b / 0.91, white noise)
  gain check   median 1 s N2/N3 chin RMS with that noise removed (uV); 1.0-1.7 uV
               in the seven cohorts of the paper - far outside suggests a gain or
               unit problem rather than a different population
  thresholds   what 'k x background' means in uV under the published rule and
               under the floor-corrected rule (B = 1.0 uV), and the muscle
               activity each requires on top of the noise
  verdict      whether the floor-corrected rule applies: sampling rate >= 200 Hz
               and b <= B / 0.59 (1.7 uV for B = 1.0)

    from src.floorcheck import floor_report, read_stages, format_report
    print(format_report(floor_report(chin_uv, fs, read_stages("night_stages.txt"))))
or, for an EDF, `python check_floor.py night.edf night_stages.txt`.
"""
import numpy as np

from .rwa import NOISE_P5_RATIO

B_REF = 1.0                    # reference background of the floor-corrected rule, uV
GUARD = 1.5
MIN_FS = 200.0
MAX_FLOOR = B_REF / 0.59       # above this, FC cannot hold the published requirement
EPOCH_S = 30
RULES = (("SINBAR any (2 x b)", 2.0), ("Montreal phasic (4 x b)", 4.0))
LABELS = {"W": 0, "WAKE": 0, "N1": 1, "S1": 1, "N2": 2, "S2": 2, "N3": 3, "S3": 3,
          "S4": 3, "N4": 3, "R": 4, "REM": 4}


def read_stages(path, rem_code=None, nrem_codes=(2, 3)):
    """30 s stages from a text file, one per line (extra columns ignored).
    Labels W/WAKE, N1, N2, N3 (N4/S4 -> N3), R/REM are read directly; for numeric
    files give the code used for REM (`rem_code`) and for N2/N3 (`nrem_codes`).
    Returns codes 0 W, 1 N1, 2 N2, 3 N3, 4 REM, -1 anything else."""
    number = lambda t: t.replace(".", "", 1).lstrip("-").isdigit()
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            tok = line.replace(",", " ").replace(";", " ").replace("\t", " ").split()
            if not tok:
                continue
            timed = tok[0][0].isdigit() and ":" in tok[0]          # 22:00:00 ...
            if not timed and any(t.endswith(":") for t in tok[:2]):
                continue                                         # header "Key: value"
            last = tok[-1].upper()
            if last in LABELS:
                out.append(LABELS[last])
            elif not timed and number(tok[0]):
                if rem_code is None:
                    raise ValueError("numeric stages: give rem_code (and nrem_codes)")
                v = int(float(tok[0]))
                out.append(4 if v == rem_code else 2 if v in nrem_codes else -1)
            else:
                out.append(-1)                                   # unknown stage keeps its slot
    return np.asarray(out, dtype=np.int8)


def thresholds(b):
    """Published and floor-corrected thresholds (uV RMS) for a floor b, and the
    muscle activity (uV RMS, added in power to the noise) each requires."""
    n = b / NOISE_P5_RATIO
    out = {}
    for name, k in RULES:
        pub = k * b
        fc = max(float(np.sqrt(n * n + (k * k - 1.0) * B_REF * B_REF)), GUARD * b)
        out[name] = {"k": k, "published_uv": pub, "fc_uv": fc,
                     "published_needs_uv": float(np.sqrt(max(pub * pub - n * n, 0.0))),
                     "fc_needs_uv": float(np.sqrt(max(fc * fc - n * n, 0.0)))}
    return out


def floor_report(chin_uv, fs, stages, ecg=None, fs_ecg=None, mains=None):
    """The floor check for one night (chin EMG in microvolts, 30 s stages)."""
    from .ecg import plausible, r_peaks, subtract_heartbeat
    from .extract import bandpass, bin_envelope
    x, band = bandpass(chin_uv, fs, mains=mains)
    beats = np.empty(0)
    if ecg is not None and fs_ecg:
        beats = r_peaks(ecg, fs_ecg)
        if plausible(beats, len(ecg) / fs_ecg):
            x = subtract_heartbeat(x, fs, beats)
        else:
            beats = np.empty(0)
    sec, _ = bin_envelope(x, fs, env_fs=1)            # 1 s RMS
    n = min(len(sec), len(stages) * EPOCH_S)
    stage = np.repeat(np.asarray(stages), EPOCH_S)[:n]
    rem, nrem = sec[:n][stage == 4], sec[:n][np.isin(stage, (2, 3))]
    if len(rem) < 600:
        raise ValueError(f"only {len(rem) / 60:.1f} min of REM: need at least 10")
    b = float(np.percentile(rem, 5))
    noise = b / NOISE_P5_RATIO
    net = float(np.sqrt(max(np.median(nrem) ** 2 - noise ** 2, 0.0))) if len(nrem) >= 60 else np.nan
    reasons = []
    if fs < MIN_FS:
        reasons.append(f"sampling rate {fs:g} Hz < {MIN_FS:g} Hz")
    if b > MAX_FLOOR:
        reasons.append(f"floor {b:.2f} uV > {MAX_FLOOR:.2f} uV")
    return {"fs": float(fs), "band_hz": [round(v, 1) for v in band],
            "heartbeat_removed": bool(len(beats)), "rem_min": round(len(rem) / 60, 1),
            "floor_uv": round(b, 3), "noise_uv": round(noise, 3),
            "net_n2n3_uv": round(net, 3) if np.isfinite(net) else None,
            "thresholds": thresholds(b), "fc_applies": not reasons, "reasons": reasons}


def format_report(r):
    """Plain-text version of `floor_report`."""
    lines = [f"Floor check  ({r['fs']:g} Hz, band {r['band_hz'][0]}-{r['band_hz'][1]} Hz, "
             f"{r['rem_min']} min REM, heartbeat {'removed' if r['heartbeat_removed'] else 'not removed'})",
             f"  quiet-REM floor b      {r['floor_uv']:.2f} uV   (noise RMS ~{r['noise_uv']:.2f} uV)",
             f"  net N2/N3 tone         {r['net_n2n3_uv'] if r['net_n2n3_uv'] is not None else '-'} uV"
             "   (1.0-1.7 uV in the paper's cohorts; far outside: check gain/units)"]
    for name, t in r["thresholds"].items():
        lines.append(f"  {name:<25} published {t['k']:g} x b = {t['published_uv']:.2f} uV "
                     f"(needs {t['published_needs_uv']:.2f} uV of muscle activity);  "
                     f"floor-corrected {t['fc_uv']:.2f} uV (needs {t['fc_needs_uv']:.2f} uV)")
    lines.append("  verdict: " + ("the floor-corrected rule applies (B = 1.0 uV)" if r["fc_applies"]
                                  else "outside the floor-corrected rule's range: " + "; ".join(r["reasons"])))
    lines.append("  report b with every RWA percentage from this system")
    return "\n".join(lines)
