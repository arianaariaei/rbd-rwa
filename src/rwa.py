"""The published methods for quantifying REM sleep without atonia (RWA).

Each method reduces one night to one or more percentages (or an index) that are
compared against a diagnostic cut-off. They differ in epoch length, amplitude
thresholds, what counts as "background", and which cut-off applies:

  Montreal  Montplaisir et al., Mov Disord 2010;25:2044 (after Lapierre &
            Montplaisir, Neurology 1992). Tonic: 20 s epochs, >50% of the
            epoch at >= 2x background or > 10 uV; positive at >= 30%.
            Phasic: 2 s mini-epochs containing bursts > 4x background;
            positive at >= 15%.
  SINBAR    Frauscher et al., Sleep 2012;35:835. Phasic bursts 0.1-5 s at
            > 2x background; tonic as Montreal but on 30 s epochs; "any"
            activity in 3 s mini-epochs. Mentalis-only "any" cut-off 18.2%
            (100% specificity). The better-known 32% needs bilateral flexor
            digitorum superficialis EMG, which most recordings lack.
  AASM      AASM scoring manual. Tonic epoch: >= 50% of a 30 s epoch above
            the minimum NREM amplitude. Phasic epoch: >= 5 of its ten 3 s
            mini-epochs contain 0.1-5 s bursts >= 4x background. The manual
            gives no numeric cut-off for "excessive".
  RAI       REM Atonia Index, Ferri et al., J Sleep Res 2008 and Sleep Med
            2010;11:947 ("improved" computation: subtract the minimum of the
            surrounding 60 one-second mini-epochs). RAI < 0.8 is the commonly
            used abnormal range.

Five COMPUTERISED indices (RAI among them) were compared on the same 146
recordings by Cesari et al., Sleep 2018;41(10):zsy133. This module puts the
visual-criteria methods and the RAI on one code path so they can be applied
unchanged to large clinical cohorts.

OPERATIONALISING "BACKGROUND". The visual methods judge background by eye.
Here it is an explicit, named choice (`baseline_amplitude`), because it
changes every downstream percentage. Values still listed in a method's
`verify` tuple are secondary-source readings not yet checked against the
original paper.
"""
from dataclasses import dataclass, field

import numpy as np

REM_CODE = 4
NREM_CODES = (2, 3)


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED MACHINERY
# ══════════════════════════════════════════════════════════════════════════════

def mini_epoch_rms(env, env_fs, seconds, how="rms"):
    """
    Split an envelope into consecutive mini-epochs and summarise each: "rms"
    for an RMS envelope (gives the RMS of the underlying signal), "mean" for a
    mean-rectified envelope (gives its average rectified amplitude).
    """
    w = int(round(env_fs * seconds))
    n = len(env) // w
    if n == 0:
        return np.empty(0), w
    blocks = env[: n * w].reshape(n, w)
    if how == "mean":
        return blocks.mean(axis=1), w
    return np.sqrt((blocks ** 2).mean(axis=1)), w


def stage_mask_at(env_fs, hypnogram, epoch_sec, codes, n_samples):
    """Boolean mask over envelope samples for the given sleep-stage codes."""
    per = int(round(env_fs * epoch_sec))
    mask = np.zeros(n_samples, dtype=bool)
    for i, code in enumerate(hypnogram):
        if code in codes:
            a = i * per
            if a >= n_samples:
                break
            mask[a: min(a + per, n_samples)] = True
    return mask


def baseline_amplitude(env, env_fs, hypnogram, epoch_sec, how, seconds=1.0):
    """
    Background EMG level against which activity is judged, from 1 s windows.

    how = "min_nrem" : lowest window in NREM (the AASM wording; a literal
                       minimum is set by one window, so unstable)
          "p5_nrem"  : 5th percentile in NREM (robust reading of the same)
          "min_rem" / "p5_rem" : the same within REM itself, i.e. the atonic
                       floor of REM - closer to what a visual scorer calls
                       "background" when judging a REM epoch
    """
    codes = NREM_CODES if how.endswith("nrem") else (REM_CODE,)
    m = stage_mask_at(env_fs, hypnogram, epoch_sec, codes, len(env))
    if m.sum() < env_fs * seconds * 10:
        return np.nan
    r, _ = mini_epoch_rms(env[m], env_fs, seconds)
    if len(r) == 0:
        return np.nan
    return float(r.min() if how.startswith("min") else np.percentile(r, 5))


def runs_above(env, env_fs, threshold, min_s=0.1, max_s=None):
    """
    Boolean array marking samples inside runs of consecutive supra-threshold
    samples lasting at least `min_s` (and at most `max_s`, if given). The upper
    bound separates phasic bursts from sustained tonic activity.
    """
    above = env > threshold
    out = np.zeros(len(env), dtype=bool)
    if not above.any():
        return out
    edges = np.diff(np.r_[0, above.astype(np.int8), 0])
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    dur = (stops - starts) / env_fs
    keep = dur >= min_s
    if max_s is not None:
        keep &= dur <= max_s
    for a, b in zip(starts[keep], stops[keep]):
        out[a:b] = True
    return out


def _blocks(mask_idx, width):
    """Consecutive, non-overlapping blocks of `width` indices from an index list."""
    n = len(mask_idx) // width
    return mask_idx[: n * width].reshape(n, width)


# ══════════════════════════════════════════════════════════════════════════════
#  METHOD DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Method:
    name: str
    tonic_epoch_s: float          # tonic scored on epochs of this length
    tonic_mult: float             # tonic threshold, multiples of background
    tonic_abs_uv: float = None    # "... or > X uV": an absolute alternative
    tonic_baseline: str = "p5_rem"
    phasic_mini_s: float = 3.0    # phasic scored on mini-epochs of this length
    phasic_mult: float = 4.0
    phasic_max_s: float = 5.0     # longest burst still counted as phasic
    phasic_baseline: str = "p5_rem"
    any_mini_s: float = None      # SINBAR "any" density on these mini-epochs
    any_mult: float = None
    phasic_epoch_rule: int = None # AASM: >= this many phasic mini-epochs / 30 s
    cutoffs: dict = field(default_factory=dict)   # metric -> % (positive if >=)
    verify: tuple = field(default_factory=tuple)


METHODS = {
    "montreal": Method(
        "Montreal", tonic_epoch_s=20.0, tonic_mult=2.0, tonic_abs_uv=10.0,
        phasic_mini_s=2.0, phasic_mult=4.0, phasic_max_s=15.0,
        cutoffs={"tonic_pct": 30.0, "phasic_pct": 15.0},
        verify=("phasic_max_s",),     # 10 s vs 15 s differs between sources
    ),
    "sinbar": Method(
        "SINBAR", tonic_epoch_s=30.0, tonic_mult=2.0, tonic_abs_uv=10.0,
        phasic_mini_s=3.0, phasic_mult=2.0, phasic_max_s=5.0,
        any_mini_s=3.0, any_mult=2.0,
        cutoffs={"any_pct": 18.2},    # mentalis only, 3 s mini-epochs
    ),
    "aasm": Method(
        "AASM", tonic_epoch_s=30.0, tonic_mult=1.0, tonic_baseline="p5_nrem",
        phasic_mini_s=3.0, phasic_mult=4.0, phasic_max_s=5.0,
        phasic_epoch_rule=5,
        cutoffs={},                   # the manual gives none
    ),
}


def score_night(env, env_fs, hypnogram, epoch_sec, method: Method, unit_known=True):
    """Apply one method to one night's chin RMS envelope."""
    out = {"method": method.name}
    rem = stage_mask_at(env_fs, hypnogram, epoch_sec, (REM_CODE,), len(env))
    out["rem_minutes"] = round(float(rem.sum()) / env_fs / 60, 1)
    if rem.sum() < env_fs * 60:
        out["error"] = "less than one minute of REM"
        return out

    # ── tonic ────────────────────────────────────────────────────────────────
    bt = baseline_amplitude(env, env_fs, hypnogram, epoch_sec, method.tonic_baseline)
    bp = baseline_amplitude(env, env_fs, hypnogram, epoch_sec, method.phasic_baseline)
    if not (np.isfinite(bt) and bt > 0 and np.isfinite(bp) and bp > 0):
        out["error"] = "background could not be estimated"
        return out
    thr_t = method.tonic_mult * bt
    if method.tonic_abs_uv is not None and unit_known:
        thr_t = min(thr_t, method.tonic_abs_uv)      # "2x background OR > 10 uV"
    idx = np.flatnonzero(rem)
    tb = _blocks(idx, int(round(env_fs * method.tonic_epoch_s)))
    tonic = (env[tb] > thr_t).mean(axis=1) > 0.5 if len(tb) else np.empty(0, bool)

    # ── phasic ───────────────────────────────────────────────────────────────
    thr_p = method.phasic_mult * bp
    burst = runs_above(env, env_fs, thr_p, 0.1, method.phasic_max_s)
    pb = _blocks(idx, int(round(env_fs * method.phasic_mini_s)))
    phasic = burst[pb].any(axis=1) if len(pb) else np.empty(0, bool)

    out.update(background_tonic_uV=round(bt, 3), background_phasic_uV=round(bp, 3),
               tonic_threshold_uV=round(thr_t, 3), phasic_threshold_uV=round(thr_p, 3),
               tonic_pct=round(100.0 * tonic.mean(), 2) if len(tonic) else np.nan,
               phasic_pct=round(100.0 * phasic.mean(), 2) if len(phasic) else np.nan)

    # ── AASM: an epoch is phasic when >= 5 of its ten 3 s mini-epochs are ──
    if method.phasic_epoch_rule:
        per = int(round(env_fs * epoch_sec))
        w = int(round(env_fs * method.phasic_mini_s))
        hits = []
        for i, code in enumerate(hypnogram):
            if code != REM_CODE or (i + 1) * per > len(env):
                continue
            seg = burst[i * per:(i + 1) * per]
            hits.append(seg[: (per // w) * w].reshape(-1, w).any(axis=1).sum()
                        >= method.phasic_epoch_rule)
        out["phasic_epoch_pct"] = round(100.0 * np.mean(hits), 2) if hits else np.nan

    # ── SINBAR "any": tonic, phasic or both, above the same amplitude ──────
    if method.any_mini_s:
        active = runs_above(env, env_fs, method.any_mult * bp, 0.1, None)
        ab = _blocks(idx, int(round(env_fs * method.any_mini_s)))
        out["any_pct"] = round(100.0 * active[ab].any(axis=1).mean(), 2) \
            if len(ab) else np.nan

    hits = [out.get(k, np.nan) >= v for k, v in method.cutoffs.items()
            if np.isfinite(out.get(k, np.nan))]
    out["positive"] = bool(any(hits)) if hits else None
    return out


def rem_atonia_index(env_mav, env_fs, hypnogram, epoch_sec, bin_width=1.0,
                     n_bins=20, noise="moving_min", window_s=60):
    """
    REM Atonia Index. Average rectified amplitude per 1 s mini-epoch of REM,
    noise-corrected, then binned by amplitude:

        RAI = A0 / (1 - A1)

    with A0 the fraction of mini-epochs <= 1 uV and A1 the fraction in
    (1, 2] uV. Runs from 0 (no atonia) to 1 (complete atonia). `env_mav` must
    be a MEAN-RECTIFIED envelope in microvolts, because the bins are absolute.

    noise = "moving_min": subtract the minimum of the `window_s` mini-epochs
            surrounding each one (Ferri et al. 2010, "improved" RAI);
            "global_min": subtract the night's single minimum (2008 version).
    """
    rem = stage_mask_at(env_fs, hypnogram, epoch_sec, (REM_CODE,), len(env_mav))
    if rem.sum() < env_fs * 60:
        return {"method": "RAI", "error": "less than one minute of REM"}
    amp, _ = mini_epoch_rms(env_mav[rem], env_fs, 1.0, how="mean")
    if noise == "moving_min":
        from scipy.ndimage import minimum_filter1d
        amp = amp - minimum_filter1d(amp, size=int(window_s), mode="nearest")
    else:
        amp = amp - amp.min()
    edges = np.arange(0, (n_bins + 1) * bin_width, bin_width)
    hist, _ = np.histogram(amp, bins=np.r_[edges, np.inf])
    frac = hist / hist.sum()
    a0, a1 = float(frac[0]), float(frac[1])
    rai = a0 / (1.0 - a1) if (1.0 - a1) > 1e-9 else float("nan")
    return {
        "method": "RAI",
        "rai": round(rai, 4),
        "frac_silent": round(a0, 4),
        "rem_minutes": round(float(rem.sum()) / env_fs / 60, 1),
        "positive": bool(rai < 0.8) if np.isfinite(rai) else None,
    }


def score_all(d, band="native"):
    """
    Run every method on one derived recording (the dict from load_derived).
    band = "native" uses each recording's own EMG band; "harmonized" uses the
    common 10-45 Hz band, the fair choice when comparing ACROSS recordings made
    on different equipment.
    """
    meta = d["meta"]
    env_fs, epoch_sec, hyp = meta["env_fs"], meta["epoch_sec"], d["hypnogram"]
    if band == "native_with_ecg":            # heartbeat left in: a sensitivity check
        chin_rms, chin_mav = d["chin_rms_with_ecg"], None
    else:
        sfx = "" if band == "native" else "_h"
        chin_rms, chin_mav = d[f"chin_rms{sfx}"], d[f"chin_mav{sfx}"]
    unit_known = meta["chin_info"]["unit_known"]
    rows = [score_night(chin_rms, env_fs, hyp, epoch_sec, m, unit_known)
            for m in METHODS.values()]
    if chin_mav is None:
        rows.append({"method": "RAI", "error": "not computed for this band"})
    elif unit_known:
        rows.append(rem_atonia_index(chin_mav, env_fs, hyp, epoch_sec))
    else:
        rows.append({"method": "RAI", "error": "chin EMG has no physical units"})
    for r in rows:
        r["band"] = band
    return rows
