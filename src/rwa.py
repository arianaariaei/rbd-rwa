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

Five COMPUTERIZED indices (RAI among them) were compared on the same 146
recordings by Cesari et al., Sleep 2018;41(10):zsy133. This module puts the
visual-criteria methods and the RAI on one code path so they can be applied
unchanged to large clinical cohorts.

OPERATIONALIZING "BACKGROUND". The visual methods judge background by eye.
Here it is an explicit, named choice (`baseline_amplitude`), because it
changes every downstream percentage. Values still listed in a method's
`verify` tuple are secondary-source readings not yet checked against the
original paper.
"""
from dataclasses import dataclass, field

import numpy as np

REM_CODE = 4
NREM_CODES = (2, 3)
# The 5th percentile of 1 s RMS values of band-limited white noise, relative to
# its RMS (0.910-0.913 for 10-95/100 Hz at 200, 256 and 512 Hz, simulated).
NOISE_P5_RATIO = 0.91


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED MACHINERY
# ══════════════════════════════════════════════════════════════════════════════

def mini_epoch_rms(env, env_fs, seconds, how="rms"):
    """
    Split an envelope into consecutive mini-epochs and summarize each: "rms"
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
    if not above.any():
        return np.zeros(len(env), dtype=bool)
    edges = np.diff(np.r_[0, above.astype(np.int8), 0])
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    dur = (stops - starts) / env_fs
    keep = dur >= min_s
    if max_s is not None:
        keep &= dur <= max_s
    # runs never touch (a stop is always followed by a sample below threshold),
    # so +1 at each kept start and -1 at its stop, summed, marks the runs
    step = np.zeros(len(env) + 1, dtype=np.int32)
    step[starts[keep]] += 1
    step[stops[keep]] -= 1
    return np.cumsum(step[:-1]) > 0


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
    # How "k x background" becomes an amplitude threshold (see `threshold`):
    # "relative" as published, "floor" corrected for the noise floor, "clamp"
    # with the background never taken below ref_floor_uv.
    mode: str = "relative"
    ref_floor_uv: float = None
    guard_mult: float = 1.5


def threshold(method, k, b):
    """
    The amplitude (uV RMS) that "activity above k x background" means for a
    night whose background is b.

    relative  k b, as published. Because b is mostly the recording's own noise
              floor, the muscle activity this requires, sqrt(k^2 - 1) b, rises
              and falls with the noise of the recording system.
    floor     max(sqrt(n^2 + (k^2 - 1) B^2), g b) with B = ref_floor_uv and
              n = b / NOISE_P5_RATIO the noise RMS that b implies: the muscle
              activity required is fixed at what the published rule requires
              on a system whose background is B, and the night's noise is
              subtracted (in power) instead of multiplied. The guard g b keeps
              noise alone from being counted: with g = 1.5, white noise puts a
              0.1 s run above threshold in < 1% of mini-epochs (0 for tonic).
    clamp     k max(b, B): the published rule with the background never taken
              to be lower than B (an absolute floor, no subtraction).
    """
    if method.mode == "floor":
        B, n = method.ref_floor_uv, b / NOISE_P5_RATIO
        return max(float(np.sqrt(n * n + (k * k - 1.0) * B * B)), method.guard_mult * b)
    if method.mode == "clamp":
        return k * max(b, method.ref_floor_uv)
    return k * b


def floor_corrected(method, ref_uv, mode="floor", guard=1.5):
    """A method's floor-corrected (or clamped) version, same name and cut-offs."""
    import dataclasses
    return dataclasses.replace(method, mode=mode, ref_floor_uv=float(ref_uv),
                               guard_mult=guard)


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


# ══════════════════════════════════════════════════════════════════════════════
#  SCORING A NIGHT (from a pack: REM epochs at full resolution, see pack.py)
# ══════════════════════════════════════════════════════════════════════════════

# band -> (RMS row, mean-rectified row) of the pack. Any other name X selects
# the rows "rms_X" and "mav_X" (the noise-ladder copies, see cohorts.py).
BANDS = {"native": ("rms", "mav"), "harmonized": ("rms_h", "mav_h"),
         "native_with_ecg": ("rms_with_ecg", None)}


def _select(pack, band, exclude=()):
    """REM epoch numbers and (n_epochs, bins) arrays for a band, minus any
    REM epoch carrying one of the `exclude` flags."""
    rows = pack["meta"]["rows"]
    rk, mk = BANDS.get(band, (f"rms_{band}", f"mav_{band}"))
    ep = pack["rem_epochs"]
    keep = np.ones(len(ep), bool)
    for name in exclude or ():
        flag = pack["epoch_flags"].get(name)
        if flag is not None and len(ep):
            keep &= flag[ep] == 0
    rms = pack["rem"][rows.index(rk)][keep] if rk in rows else None
    mav = pack["rem"][rows.index(mk)][keep] if mk in rows else None
    nrem = pack["nrem_1s"][rows.index(rk)] if (rk in rows and pack["nrem_1s"].size) \
        else np.empty(0)
    return ep[keep], rms, mav, nrem


def _segments(ep):
    """(start, stop) positions of runs of consecutive epoch numbers."""
    if len(ep) == 0:
        return []
    brk = np.flatnonzero(np.diff(ep) != 1) + 1
    return list(zip(np.r_[0, brk], np.r_[brk, len(ep)]))


def _runs(rem2d, ep, env_fs, thr, min_s, max_s):
    """runs_above within each stretch of consecutive REM epochs, so that a
    burst never bridges the gap between two separate REM periods."""
    out = np.zeros(rem2d.shape, bool)
    for a, b in _segments(ep):
        out[a:b] = runs_above(rem2d[a:b].reshape(-1), env_fs, thr, min_s,
                              max_s).reshape(b - a, -1)
    return out


def _background(rem2d, nrem_1s, env_fs, how):
    """
    Background from 1 s RMS values of REM or of N2/N3 (see baseline_amplitude).
    how = "<stat>_<stage>" with stat "min" or "pNN" (NN-th percentile) and stage
    "rem" or "nrem", e.g. "p5_rem" (the default), "p25_rem", "min_nrem".
    """
    stat, stage = how.split("_", 1)
    if stage == "nrem":
        vals = nrem_1s
    else:
        vals, _ = mini_epoch_rms(rem2d.reshape(-1), env_fs, 1.0)
    if len(vals) < 10:
        return np.nan
    if stat == "min":
        return float(vals.min())
    return float(np.percentile(vals, float(stat[1:])))


def _mini(mask2d, env_fs, seconds):
    """Split concatenated REM into mini-epochs; True where any sample is."""
    flat = mask2d.reshape(-1)
    w = int(round(env_fs * seconds))
    n = len(flat) // w
    return flat[: n * w].reshape(n, w)


def score_night(pack, method: Method, band="native", exclude=(), masks=None):
    """Apply one method to one night. Returns a dict of its measures. If a dict
    is passed as `masks`, it receives the per-unit decisions behind them:
    "tonic" (one per tonic epoch), "phasic" (per phasic mini-epoch) and "any"
    (per SINBAR mini-epoch), on consecutive units of the night's REM."""
    meta = pack["meta"]
    env_fs, epoch_sec = meta["env_fs"], meta["epoch_sec"]
    ep, env, _, nrem = _select(pack, band, exclude)
    out = {"method": method.name,
           "rem_minutes": round(len(ep) * epoch_sec / 60.0, 1)}
    if env is None:
        out["error"] = f"band {band} not stored"
        return out
    if len(ep) < 2:
        out["error"] = "less than one minute of REM"
        return out
    if method.mode != "relative" and not meta.get("unit_known", True):
        out["error"] = "floor correction needs the EMG in physical units"
        return out

    bt = _background(env, nrem, env_fs, method.tonic_baseline)
    bp = _background(env, nrem, env_fs, method.phasic_baseline)
    if not (np.isfinite(bt) and bt > 0 and np.isfinite(bp) and bp > 0):
        out["error"] = "background could not be estimated"
        return out

    # ── tonic ────────────────────────────────────────────────────────────────
    thr_t = threshold(method, method.tonic_mult, bt)
    if method.tonic_abs_uv is not None and meta.get("unit_known", True):
        thr_t = min(thr_t, method.tonic_abs_uv)      # "2x background OR > 10 uV"
    above = _mini(env > thr_t, env_fs, method.tonic_epoch_s)
    tonic = above.mean(axis=1) > 0.5

    # ── phasic ───────────────────────────────────────────────────────────────
    thr_p = threshold(method, method.phasic_mult, bp)
    burst = _runs(env, ep, env_fs, thr_p, 0.1, method.phasic_max_s)
    phasic = _mini(burst, env_fs, method.phasic_mini_s).any(axis=1)

    out.update(background_tonic_uV=round(bt, 3), background_phasic_uV=round(bp, 3),
               tonic_threshold_uV=round(thr_t, 3), phasic_threshold_uV=round(thr_p, 3),
               tonic_pct=round(100.0 * tonic.mean(), 2) if len(tonic) else np.nan,
               phasic_pct=round(100.0 * phasic.mean(), 2) if len(phasic) else np.nan)

    # ── AASM: an epoch is phasic when >= 5 of its ten 3 s mini-epochs are ──
    if method.phasic_epoch_rule:
        w = int(round(env_fs * method.phasic_mini_s))
        per = burst.shape[1]
        minis = burst[:, : (per // w) * w].reshape(len(burst), -1, w).any(axis=2)
        hits = minis.sum(axis=1) >= method.phasic_epoch_rule
        out["phasic_epoch_pct"] = round(100.0 * hits.mean(), 2)

    # ── SINBAR "any": tonic, phasic or both, above the same amplitude ──────
    any_ = None
    if method.any_mini_s:
        active = _runs(env, ep, env_fs, threshold(method, method.any_mult, bp), 0.1, None)
        any_ = _mini(active, env_fs, method.any_mini_s).any(axis=1)
        out["any_pct"] = round(100.0 * any_.mean(), 2)

    if masks is not None:
        masks.update(tonic=tonic, phasic=phasic, any=any_)
    hits = [out.get(k, np.nan) >= v for k, v in method.cutoffs.items()
            if np.isfinite(out.get(k, np.nan))]
    out["positive"] = bool(any(hits)) if hits else None
    return out


def rem_atonia_index(pack, band="native", exclude=(), bin_width=1.0,
                     n_bins=20, noise="moving_min", window_s=60):
    """
    REM Atonia Index. Average rectified amplitude per 1 s mini-epoch of REM,
    noise-corrected, then binned by amplitude:

        RAI = A0 / (1 - A1)

    with A0 the fraction of mini-epochs <= 1 uV and A1 the fraction in
    (1, 2] uV. Runs from 0 (no atonia) to 1 (complete atonia). Uses the
    MEAN-RECTIFIED rows, which must be in microvolts: the bins are absolute.

    noise = "moving_min": subtract the minimum of the `window_s` mini-epochs
            surrounding each one (Ferri et al. 2010, "improved" RAI);
            "global_min": subtract the night's single minimum (2008 version).
    """
    meta = pack["meta"]
    ep, _, env_mav, _ = _select(pack, band, exclude)
    if env_mav is None:
        return {"method": "RAI", "error": f"no mean-rectified row for band {band}"}
    if not meta.get("unit_known", True):
        return {"method": "RAI", "error": "chin EMG has no physical units"}
    if len(ep) < 2:
        return {"method": "RAI", "error": "less than one minute of REM"}
    amp, _ = mini_epoch_rms(env_mav.reshape(-1), meta["env_fs"], 1.0, how="mean")
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
        "rem_minutes": round(len(ep) * meta["epoch_sec"] / 60.0, 1),
        "positive": bool(rai < 0.8) if np.isfinite(rai) else None,
    }


def score_all(pack, band="native", exclude=()):
    """
    Run every method on one night (a pack; see pack.py).
    band = "native" uses each recording's own EMG band; "harmonized" uses the
    common 10-45 Hz band, the fair choice when comparing ACROSS recordings made
    on different equipment; "native_with_ecg" leaves the heartbeat in.
    exclude = epoch-flag names (e.g. "resp", "arousal") whose REM epochs are
    dropped before scoring.
    """
    rows = [score_night(pack, m, band, exclude) for m in METHODS.values()]
    rows.append(rem_atonia_index(pack, band, exclude))
    for r in rows:
        r["band"] = band
        r["excluded"] = "+".join(exclude) if exclude else ""
    return rows
