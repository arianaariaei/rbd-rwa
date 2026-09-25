"""The published methods for quantifying REM sleep without atonia.

Each method reduces one night to a percentage (or an index) which is compared
against a diagnostic cut-off. They differ along four axes:

    mini-epoch length   1 s (RAI), 2 s (Montreal phasic), 3 s (SINBAR, AASM
                        phasic), 20 s (Montreal tonic), 30 s (AASM tonic)
    muscles             submentalis alone, or submentalis + bilateral flexor
                        digitorum superficialis (SINBAR)
    baseline            "minimum amplitude" during REM or NREM, variously
                        defined; here parameterised explicitly
    threshold           2x or 4x that baseline

Five COMPUTERISED indices (RAI among them) were compared on the same 146
recordings by Cesari et al., Sleep 2018;41(10):zsy133, which reported
discrimination between groups. This module puts the visual-criteria methods
and the RAI on one code path so that all of them can be applied unchanged to
large clinical cohorts.

PARAMETER PROVENANCE. The structure of each method follows its original
description, but several numeric details - notably the exact baseline
definition and the RAI binning - are stated ambiguously or inconsistently
across the primary papers and secondary reviews. Every such value is a named
field on Method so it can be checked against the source and changed in one
place. Anything listed in a method's `verify` tuple has NOT been confirmed
against the original publication and must be before any result is reported.
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
    Background EMG level against which activity is judged.

    how = "min_nrem" : lowest mini-epoch amplitude in NREM. This is the classic
                       wording, but a literal minimum is set by a single
                       quietest window and is therefore unstable.
          "p5_nrem"  : 5th percentile in NREM - a robust reading of the same
                       intent, and this project's default.
          "min_rem"  : lowest mini-epoch amplitude within REM itself.
          "p5_rem"   : 5th percentile within REM.

    Which of these is used materially changes every downstream percentage, so
    it is treated as an explicit choice rather than an implementation detail.
    """
    codes = NREM_CODES if how.endswith("nrem") else (REM_CODE,)
    m = stage_mask_at(env_fs, hypnogram, epoch_sec, codes, len(env))
    if m.sum() < env_fs * seconds * 10:
        return np.nan
    r, _ = mini_epoch_rms(env[m], env_fs, seconds)
    if len(r) == 0:
        return np.nan
    return float(r.min() if how.startswith("min") else np.percentile(r, 5))


def phasic_bursts(env, env_fs, threshold, min_s=0.1, max_s=5.0):
    """
    Boolean array marking samples that fall inside a phasic burst.

    A burst is a run of consecutive samples above `threshold` whose duration
    lies in [min_s, max_s]. The upper bound is what distinguishes phasic bursts
    from sustained tonic activity, so longer runs are excluded here and counted
    by the tonic measure instead.
    """
    above = env > threshold
    out = np.zeros_like(above)
    if not above.any():
        return out
    edges = np.diff(np.r_[0, above.astype(np.int8), 0])
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    dur = (stops - starts) / env_fs
    keep = (dur >= min_s) & (dur <= max_s)
    for a, b in zip(starts[keep], stops[keep]):
        out[a:b] = True
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  METHOD DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Method:
    name: str
    mini_s: float                 # mini-epoch length for the phasic measure
    tonic_s: float                # epoch length for the tonic measure
    phasic_mult: float            # burst threshold, multiples of baseline
    tonic_mult: float             # tonic threshold, multiples of baseline
    tonic_fraction: float         # fraction of the epoch that must be active
    baseline: str = "p5_nrem"
    muscles: tuple = ("chin",)
    cutoff: float = float("nan")  # published cut-off, on the "any activity" %
    notes: str = ""
    verify: tuple = field(default_factory=tuple)


METHODS = {
    # Lapierre & Montplaisir 1992. Tonic scored on 20 s epochs, phasic on 2 s
    # mini-epochs containing bursts above 4x background.
    "montreal": Method(
        "Montreal", mini_s=2.0, tonic_s=20.0,
        phasic_mult=4.0, tonic_mult=2.0, tonic_fraction=0.50,
        notes="tonic = activity >2x background sustained over half a 20 s epoch",
        verify=("tonic_fraction", "cutoff"),
    ),
    # Frauscher et al. (SINBAR). 3 s mini-epochs. The published 31.9% cut-off
    # applies to the COMBINED submentalis + bilateral FDS montage, not to chin
    # alone, so scoring chin-only against it is not like-for-like.
    "sinbar": Method(
        "SINBAR", mini_s=3.0, tonic_s=30.0,
        phasic_mult=2.0, tonic_mult=2.0, tonic_fraction=0.50,
        muscles=("chin", "legs"), cutoff=31.9,
        notes="'any' activity = tonic or phasic, chin + bilateral FDS; CAP "
              "provides leg (tibialis) rather than FDS, an imperfect substitute",
        verify=("phasic_mult", "muscles"),
    ),
    # AASM scoring manual. Tonic on the full 30 s epoch; a phasic epoch is
    # positive when at least 5 of its ten 3 s mini-epochs contain bursts.
    "aasm": Method(
        "AASM", mini_s=3.0, tonic_s=30.0,
        phasic_mult=4.0, tonic_mult=1.0, tonic_fraction=0.50,
        notes="phasic epoch positive when >=5 of 10 mini-epochs contain bursts",
        verify=("tonic_mult", "cutoff"),
    ),
}


def score_night(env_chin, env_legs, env_fs, hypnogram, epoch_sec, method: Method):
    """Apply one method to one night. Returns a dict of its measures."""
    base = baseline_amplitude(env_chin, env_fs, hypnogram, epoch_sec,
                              method.baseline, seconds=method.mini_s)
    if not np.isfinite(base) or base <= 0:
        return {"method": method.name, "error": "baseline could not be estimated"}

    rem = stage_mask_at(env_fs, hypnogram, epoch_sec, (REM_CODE,), len(env_chin))
    if rem.sum() < env_fs * method.mini_s * 10:
        return {"method": method.name, "error": "insufficient REM"}

    # Phasic: fraction of REM mini-epochs containing a qualifying burst. Each
    # muscle is judged against ITS OWN background, not the chin's.
    burst = phasic_bursts(env_chin, env_fs, method.phasic_mult * base)
    if "legs" in method.muscles and env_legs is not None and len(env_legs):
        for row in env_legs:
            b_leg = baseline_amplitude(row, env_fs, hypnogram, epoch_sec,
                                       method.baseline, seconds=method.mini_s)
            if np.isfinite(b_leg) and b_leg > 0:
                burst |= phasic_bursts(row, env_fs, method.phasic_mult * b_leg)

    w = int(round(env_fs * method.mini_s))
    idx = np.flatnonzero(rem)
    idx = idx[: (len(idx) // w) * w].reshape(-1, w) if len(idx) >= w \
        else np.empty((0, w), dtype=int)
    tonic_over = (env_chin[idx] > method.tonic_mult * base).mean(axis=1) \
        if len(idx) else np.empty(0)
    phasic_hit = burst[idx].any(axis=1) if len(idx) else np.empty(0, bool)
    phasic_pct = 100.0 * phasic_hit.mean() if len(idx) else float("nan")

    # Tonic: fraction of REM epochs sustained above threshold, on the method's
    # own tonic epoch length rather than the phasic mini-epoch length.
    wt = int(round(env_fs * method.tonic_s))
    idt = np.flatnonzero(rem)
    idt = idt[: (len(idt) // wt) * wt].reshape(-1, wt) if len(idt) >= wt \
        else np.empty((0, wt), dtype=int)
    tonic_pct = (100.0 * ((env_chin[idt] > method.tonic_mult * base).mean(axis=1)
                          >= method.tonic_fraction).mean()) if len(idt) \
        else float("nan")

    # "Any" activity - the quantity the published cut-offs are stated against.
    any_pct = 100.0 * np.mean(phasic_hit | (tonic_over >= method.tonic_fraction)) \
        if len(idx) else float("nan")

    return {
        "method": method.name,
        "baseline_uV": round(base, 3),
        "rem_minutes": round(rem.sum() / env_fs / 60, 1),
        "tonic_pct": round(float(tonic_pct), 2),
        "phasic_pct": round(float(phasic_pct), 2),
        "any_pct": round(float(any_pct), 2),
        "cutoff": method.cutoff,
        "positive": (bool(any_pct >= method.cutoff)
                     if np.isfinite(method.cutoff) else None),
    }


def rem_atonia_index(env_mav, env_fs, hypnogram, epoch_sec, bin_width=1.0,
                     n_bins=20, noise="moving_min", window_s=60):
    """
    REM Atonia Index (Ferri et al.). Average rectified amplitude per 1 s
    mini-epoch of REM, noise-corrected, then binned by amplitude. The index
    contrasts the proportion of near-silent seconds against the proportion
    showing intermediate activity, running from 0 (no atonia) to 1 (complete
    atonia).

        RAI = A0 / (1 - A1)

    with A0 the fraction of mini-epochs at or below bin_width and A1 the
    fraction in the next bin. `env_mav` must be a MEAN-RECTIFIED envelope and
    in microvolts: the 1 uV bins are absolute.

    noise = "moving_min": subtract the minimum within a moving window of
            `window_s` mini-epochs centred on each one (the 2010 "improved"
            computation, as we understand it); "global_min": subtract the
            night's single minimum (the 2008 description).

    VERIFY: the noise-correction window and bin edges against the original
    papers before reporting absolute RAI values.
    """
    rem = stage_mask_at(env_fs, hypnogram, epoch_sec, (REM_CODE,), len(env_mav))
    if rem.sum() < env_fs * 30:
        return {"method": "RAI", "error": "insufficient REM"}
    amp, _ = mini_epoch_rms(env_mav[rem], env_fs, 1.0, how="mean")
    if len(amp) < 30:
        return {"method": "RAI", "error": "insufficient REM"}
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
        "rem_minutes": round(rem.sum() / env_fs / 60, 1),
        "cutoff": 0.8,          # RAI < 0.8 is commonly cited as abnormal
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
    sfx = "" if band == "native" else "_h"
    chin_rms, chin_mav = d[f"chin_rms{sfx}"], d[f"chin_mav{sfx}"]
    legs = d["legs"] if len(d["legs"]) else None
    rows = [score_night(chin_rms, legs, env_fs, hyp, epoch_sec, m)
            for m in METHODS.values()]
    if meta["chin_info"]["unit_known"]:
        rows.append(rem_atonia_index(chin_mav, env_fs, hyp, epoch_sec))
    else:
        rows.append({"method": "RAI", "error": "chin EMG has no physical units"})
    for r in rows:
        r["band"] = band
    return rows
