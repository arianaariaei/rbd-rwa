"""Known muscle activity added to real nights: ground truth for RWA scoring.

The open RBD recordings are 21 nights from one center on one quiet recording
system, so what they show about detection could be a property of those
patients. Here the activity is known instead. It is added to the REM sleep of
nights recorded without RBD, on every system in the study
(paper/preregistration_injection.md):

  synthetic   tonic episodes (whole 30-s epochs) or phasic bursts (0.25-2 s):
              Gaussian noise shaped by an activity envelope and passed through
              the night's own EMG filter, at 49 amplitudes from 0.25 to 16 uV in
              steps of 9% (RMS in the night's band, during activity)
  transplant  the REM chin EMG of one of CAP's RBD patients, filtered and
              heartbeat-cleaned as in the main pipeline, resampled to the
              night's rate and passed through its filter, at full and half
              amplitude

Both are added after the night's own filtering and heartbeat removal, as the
noise ladder adds its noise (cohorts.extract_ladder_pack). What the added
activity has to be found in is therefore the night's real background: its
noise, colored and varying through the night, its artifacts and its own
twitches.

Every copy is scored with the published and floor-corrected rules unchanged
(rwa.py), and their per-unit decisions are compared with where activity was
added: a unit (tonic epoch, phasic or SINBAR mini-epoch) is "injected" when the
added activity covers most of it and "clean" when there is none in it (for
mini-epochs, none within 0.1 s of it either).

The amplitude steps are fine because detection of a 20- or 30-s tonic epoch is
nearly a step function of amplitude (each decision rests on 1,000-1,500 bins).
"""
import json
import zlib
from fractions import Fraction

import numpy as np

from .config import ENV_FS
from .extract import bandpass, bin_envelope
from .pack import build_pack
from .rwa import METHODS, _mini, floor_corrected, rem_atonia_index, score_night

EPOCH_SEC = 30
REM_CODE = 4
AMPLITUDES_UV = tuple(round(0.25 * 2 ** (i / 8), 4) for i in range(49))   # 0.25 ... 16
DONOR_SCALES = (1.0, 0.5)
BURST_S = (0.25, 0.5, 1.0, 2.0)  # phasic burst durations, used in turn
RAMP_S = 0.025                   # raised-cosine onset and offset of every episode
TONIC_COVER = 0.75               # tonic unit injected: activity covers >= 75% of it
INTERIOR_MIN_S = 0.1             # mini-epoch injected: >= 0.1 s of full activity
CLEAN_MARGIN_S = 0.1             # clean: no activity in the unit (mini-epochs: or within 0.1 s)
REF_UV = 1.0                     # floor-corrected reference background (primary)
COUNTS = ("ni", "ki", "nc", "kc")  # injected units, of them detected; clean, detected


def variants():
    """(method name, variant, Method) scored on every copy of a night."""
    out = []
    for key in ("montreal", "sinbar"):
        m = METHODS[key]
        out += [(m.name, "published", m), (m.name, "FC", floor_corrected(m, REF_UV))]
    out.append(("AASM", "published", METHODS["aasm"]))
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  WHERE ACTIVITY IS ADDED
# ══════════════════════════════════════════════════════════════════════════════

def rem_stretches(hyp):
    """(first, last + 1) epoch numbers of each run of consecutive REM epochs."""
    rem = np.flatnonzero(np.asarray(hyp) == REM_CODE)
    if len(rem) == 0:
        return []
    brk = np.flatnonzero(np.diff(rem) != 1) + 1
    starts = rem[np.r_[0, brk]]
    stops = rem[np.r_[brk - 1, len(rem) - 1]] + 1
    return list(zip(starts.tolist(), stops.tolist()))


def _episode(g, a, b, fs):
    """g[a:b] = 1 with raised-cosine onset and offset of RAMP_S."""
    g[a:b] = 1.0
    r = min(int(round(RAMP_S * fs)), (b - a) // 2)
    if r > 0:
        up = 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r)
        g[a:a + r] = up
        g[b - r:b] = up[::-1]


def tonic_envelope(hyp, fs, rng, n_samples):
    """Tonic episodes of 1-4 whole REM epochs separated by 2-6 epochs without,
    inside each run of REM epochs (never across two): about 40% of REM."""
    per = int(round(fs * EPOCH_SEC))
    g = np.zeros(n_samples, np.float32)
    for a, b in rem_stretches(hyp):
        e = a + int(rng.integers(0, 4))
        while e < b:
            stop = min(e + int(rng.integers(1, 5)), b)
            _episode(g, e * per, stop * per, fs)
            e = stop + int(rng.integers(2, 7))
    return g


def phasic_envelope(hyp, fs, rng, n_samples):
    """Phasic bursts of 0.25, 0.5, 1 and 2 s (in turn), 4-14 s apart, inside
    runs of REM epochs and at least 0.5 s from their ends."""
    g = np.zeros(n_samples, np.float32)
    k = 0
    for a, b in rem_stretches(hyp):
        t, end = a * EPOCH_SEC + rng.uniform(1.0, 6.0), b * EPOCH_SEC - 0.5
        while t + BURST_S[k % len(BURST_S)] <= end:
            d = BURST_S[k % len(BURST_S)]
            _episode(g, int(round(t * fs)), int(round((t + d) * fs)), fs)
            k += 1
            t += d + rng.uniform(4.0, 14.0)
    return g


def activity(g, fs, mains, rng):
    """Gaussian noise shaped by the envelope g and passed through the night's EMG
    filter, scaled to 1 uV RMS where g = 1: amplitude a then means a uV RMS in
    the night's band during activity."""
    s, _ = bandpass(rng.normal(0.0, 1.0, len(g)) * g, fs, mains=mains)
    full = g >= 0.999
    rms = float(np.sqrt(np.mean(s[full] ** 2))) if full.any() else 1.0
    return (s / rms).astype(np.float32)


def bin_mean(x, fs, env_fs=ENV_FS):
    """Mean of x in each envelope bin (the bins of extract.bin_envelope)."""
    n_bins = int(np.floor(len(x) * env_fs / fs))
    edges = np.floor(np.arange(n_bins + 1) * fs / env_fs).astype(np.int64)
    return (np.add.reduceat(np.asarray(x, np.float64), edges[:-1]) / np.diff(edges)) \
        .astype(np.float32)


def truth(gbins, seconds, kind, env_fs=ENV_FS):
    """
    Per unit of `seconds` over the night's concatenated REM (the units the
    methods score): 1 injected, 0 clean, -1 neither (left out). kind "tonic":
    injected when activity covers >= TONIC_COVER of the unit, clean when there
    is none in it; "burst": injected when the unit holds >= INTERIOR_MIN_S of
    full activity, clean when there is none in it or within CLEAN_MARGIN_S.
    """
    from scipy.ndimage import binary_dilation
    gbins = np.asarray(gbins, np.float32).reshape(-1)
    cover = _mini(gbins, env_fs, seconds).mean(axis=1)
    full = _mini(gbins >= 0.999, env_fs, seconds).sum(axis=1)
    m = int(round(CLEAN_MARGIN_S * env_fs)) if kind == "burst" else 0
    present = gbins > 0
    if m:
        present = binary_dilation(present, structure=np.ones(2 * m + 1, bool))
    near = _mini(present, env_fs, seconds).any(axis=1)
    inj = cover >= TONIC_COVER if kind == "tonic" \
        else full >= int(round(INTERIOR_MIN_S * env_fs))
    out = np.full(len(cover), -1, np.int8)
    out[inj] = 1
    out[~near] = 0
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  RBD DONORS (transplant)
# ══════════════════════════════════════════════════════════════════════════════

def make_donor(cohort, rec, d):
    """An RBD night's REM chin EMG as the main pipeline sees it (native band,
    mains notch, heartbeat removed), run of REM epochs by run, with its
    quiet-REM level."""
    from .cohorts import _beats, quiet_level
    from .ecg import subtract_heartbeat
    beats = _beats(d)
    fs = float(d["fs"])
    xf, band = bandpass(d["chin"], fs, mains=cohort.mains)
    if len(beats):
        xf = subtract_heartbeat(xf, fs, beats)
    per = int(round(fs * EPOCH_SEC))
    hyp = np.asarray(d["hypnogram"])[: len(xf) // per]
    rms, mav = bin_envelope(xf, fs)
    runs = [xf[a * per: b * per].astype(np.float32) for a, b in rem_stretches(hyp)]
    # the donor's own night scored as recorded: the reference on CAP's system
    pack = build_pack({"rms": rms, "mav": mav}, [], hyp, ENV_FS, EPOCH_SEC,
                      {"record": rec, "unit_known": bool(d["unit_known"])})
    own = {f"{r['method']}/{r['variant']}": {k: r.get(k) for k in
                                             ("tonic_pct", "phasic_pct", "any_pct", "rai",
                                              "positive", "background_phasic_uV")}
           for r in score_copy(pack, pack["rem"][0], pack["rem"][1])}
    return {"record": rec, "fs": fs, "band": list(band), "unit_known": bool(d["unit_known"]),
            "level_uv": round(float(quiet_level(rms, hyp)), 4),
            "rem_epochs": int(sum(len(r) for r in runs) // per),
            "lengths": [len(r) for r in runs], "own": own,
            "sig": np.concatenate(runs) if runs else np.zeros(0, np.float32)}


def save_donor(path, donor):
    meta = {k: v for k, v in donor.items() if k != "sig"}
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, sig=donor["sig"], meta=json.dumps(meta))
    tmp.replace(path)
    return path


def load_donor(path):
    z = np.load(path, allow_pickle=False)
    return dict(json.loads(str(z["meta"])), sig=z["sig"])


def donor_track(donor, hyp, fs, mains):
    """
    The donor's REM chin EMG laid over this night's REM, as one track over the
    night's concatenated REM samples. Recipient REM epoch j receives donor REM
    epoch floor(j n_d / n_r), i.e. the donor's night sampled evenly whatever the
    two REM durations; the donor's runs of REM are resampled to this night's
    rate first, and each run of this night's REM is then passed through its
    EMG filter (band and mains notch), as everything it records would be.
    """
    from scipy.signal import resample_poly
    per = int(round(fs * EPOCH_SEC))
    f = Fraction(int(round(fs)), int(round(donor["fs"]))).limit_denominator(1000)
    epochs, pos = [], 0
    for n in donor["lengths"]:
        y = donor["sig"][pos:pos + n].astype(np.float64)
        pos += n
        if f != 1:
            y = resample_poly(y, f.numerator, f.denominator)
        k = len(y) // per
        if k:
            epochs.append(y[: k * per].reshape(k, per))
    epochs = np.concatenate(epochs) if epochs else np.zeros((0, per))
    stretches = rem_stretches(hyp)
    n_r = sum(b - a for a, b in stretches)
    if n_r == 0 or len(epochs) == 0:
        return np.zeros(n_r * per, np.float32)
    track = epochs[(np.arange(n_r) * len(epochs)) // n_r].reshape(-1)
    out, i = np.empty(len(track), np.float32), 0
    for a, b in stretches:
        n = (b - a) * per
        out[i:i + n] = bandpass(track[i:i + n], fs, mains=mains)[0]
        i += n
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  SCORING THE COPIES OF ONE NIGHT
# ══════════════════════════════════════════════════════════════════════════════

def score_copy(pack, rms, mav, gbins=None, cache=None):
    """Score one copy of the night's REM (rms, mav: (n_rem_epochs, bins)) with
    every variant and the RAI. With gbins (the added activity's envelope per
    bin), also count detections on injected and clean units."""
    p = dict(pack, rem=np.stack([rms, mav]))
    rows = []
    cache = {} if cache is None else cache
    for name, variant, m in variants():
        masks = {}
        r = score_night(p, m, "native", masks=masks)
        r["variant"] = variant
        if gbins is not None and "error" not in r:
            for key, seconds, kind in (("tonic", m.tonic_epoch_s, "tonic"),
                                       ("phasic", m.phasic_mini_s, "burst"),
                                       ("any", m.any_mini_s, "burst")):
                dec = masks.get(key)
                if dec is None or not seconds:
                    continue
                if (seconds, kind) not in cache:
                    cache[seconds, kind] = truth(gbins, seconds, kind)
                t = cache[seconds, kind][: len(dec)]
                r.update({f"{key}_ni": int((t == 1).sum()), f"{key}_ki": int((dec & (t == 1)).sum()),
                          f"{key}_nc": int((t == 0).sum()), f"{key}_kc": int((dec & (t == 0)).sum())})
        rows.append(r)
    r = rem_atonia_index(p, "native")
    r["variant"] = "published"
    rows.append(r)
    return rows


def run_night(cohort, rec, d, donor=None, info=None):
    """
    Every copy of one night: as recorded; with synthetic tonic, then phasic,
    activity at each of AMPLITUDES_UV (the same placement and noise at every
    amplitude, seeded by cohort and record); and, given a donor, with the
    donor's RBD activity at each of DONOR_SCALES. Returns one row per copy and
    method variant.
    """
    from .cohorts import _beats, quiet_level
    from .ecg import subtract_heartbeat
    beats = _beats(d)
    fs, mains = float(d["fs"]), cohort.mains
    xf, band = bandpass(d["chin"], fs, mains=mains)
    if len(beats):
        xf = subtract_heartbeat(xf, fs, beats)
    rms, mav = bin_envelope(xf, fs)
    per_bins = int(round(ENV_FS * EPOCH_SEC))
    hyp = np.asarray(d["hypnogram"])[: len(rms) // per_bins]
    meta = {"record": rec, "cohort": cohort.name, "chin_fs": fs, "band": list(band),
            "unit_known": bool(d["unit_known"])}
    pack = build_pack({"rms": rms, "mav": mav}, [], hyp, ENV_FS, EPOCH_SEC, meta)
    rem_ep = pack["rem_epochs"]
    info = dict(info or {}, cohort=cohort.name, record=rec, chin_fs=fs,
                unit_known=bool(d["unit_known"]), beats=int(len(beats)),
                rem_minutes=round(len(rem_ep) * EPOCH_SEC / 60.0, 1),
                level_uv=round(float(quiet_level(rms, hyp)), 4))
    rows = []

    def add(pattern, amp, r_rms, r_mav, gbins=None, cache=None, extra=None):
        for r in score_copy(pack, r_rms, r_mav, gbins, cache):
            rows.append({**info, **(extra or {}), "pattern": pattern, "amp_uv": amp, **r})

    add("none", 0.0, pack["rem"][0], pack["rem"][1])
    if len(rem_ep) < 2 or not d["unit_known"]:
        return rows
    per = int(round(fs * EPOCH_SEC))
    idx = (rem_ep[:, None] * per + np.arange(per)[None, :]).reshape(-1)
    x_rem = xf[idx]
    shape = (len(rem_ep), per_bins)
    rng = np.random.default_rng(zlib.crc32(f"{cohort.name}/{rec}".encode()))
    for pattern, make in (("tonic", tonic_envelope), ("phasic", phasic_envelope)):
        g = make(hyp, fs, rng, len(xf))
        s = activity(g, fs, mains, rng)[idx]
        gbins, cache = bin_mean(g[idx], fs).reshape(shape), {}
        del g
        for a in AMPLITUDES_UV:
            r_rms, r_mav = bin_envelope(x_rem + a * s, fs)
            add(pattern, a, r_rms.reshape(shape), r_mav.reshape(shape), gbins, cache)
    if donor is not None:
        track = donor_track(donor, hyp, fs, mains)
        extra = {"donor": donor["record"], "donor_level_uv": donor.get("level_uv"),
                 "donor_rem_epochs": donor.get("rem_epochs")}
        for c in DONOR_SCALES:
            r_rms, r_mav = bin_envelope(x_rem + c * track, fs)
            add("transplant", c, r_rms.reshape(shape), r_mav.reshape(shape), extra=extra)
    return rows


# ══════════════════════════════════════════════════════════════════════════════
#  DETECTION THRESHOLD OF ONE NIGHT
# ══════════════════════════════════════════════════════════════════════════════

def corrected_rate(ki, ni, kc, nc):
    """Share of injected units detected, corrected for the share of clean units
    detected in the same copy: (h - p0) / (1 - p0)."""
    h = ki / ni if ni else np.nan
    p0 = kc / nc if nc else np.nan
    if not (np.isfinite(h) and np.isfinite(p0)) or p0 >= 1.0:
        return np.nan
    return (h - p0) / (1.0 - p0)


def isotonic(y):
    """Non-decreasing least-squares fit (pool adjacent violators)."""
    vals, wts = [], []
    for v in np.asarray(y, float):
        vals.append(v)
        wts.append(1.0)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            w = wts[-2] + wts[-1]
            vals[-2:] = [(vals[-2] * wts[-2] + vals[-1] * wts[-1]) / w]
            wts[-2:] = [w]
    return np.repeat(vals, np.asarray(wts, int))


def a50(amps, rates, level=0.5):
    """
    The amplitude at which the corrected detection rate, made non-decreasing in
    amplitude (isotonic fit), first reaches `level`, interpolated in log
    amplitude between grid points. Returns (amplitude, censored): censored -1 =
    reached at the smallest amplitude (value is the grid's lower end), +1 = never
    reached (value is the upper end), 0 = within.
    """
    amps, rates = np.asarray(amps, float), np.asarray(rates, float)
    ok = np.isfinite(rates)
    amps, rates = amps[ok], rates[ok]
    if len(amps) < 3:
        return np.nan, 0
    order = np.argsort(amps)
    amps, rates = amps[order], isotonic(rates[order])
    hit = np.flatnonzero(rates >= level)
    if len(hit) == 0:
        return float(amps[-1]), 1
    i = int(hit[0])
    if i == 0:
        return float(amps[0]), -1
    x0, x1 = np.log(amps[i - 1]), np.log(amps[i])
    y0, y1 = rates[i - 1], rates[i]
    x = x0 + (level - y0) * (x1 - x0) / (y1 - y0) if y1 > y0 else x1
    return float(np.exp(x)), 0


# The measures whose detection thresholds are analyzed: (method, measure, the
# pattern it is read on). The first three are the primary ones.
MEASURES = (("Montreal", "tonic", "tonic"), ("Montreal", "phasic", "phasic"),
            ("SINBAR", "any", "phasic"), ("SINBAR", "any", "tonic"),
            ("SINBAR", "tonic", "tonic"), ("SINBAR", "phasic", "phasic"),
            ("AASM", "tonic", "tonic"), ("AASM", "phasic", "phasic"))
PRIMARY = MEASURES[:3]


def a50_table(df):
    """One row per night, measure and variant: the detection threshold (A50,
    uV), its censoring, the corrected detection rate at each amplitude and the
    clean units' detection rate as recorded (p0 of the smallest amplitude)."""
    import pandas as pd
    out = []
    syn = df[df.pattern.isin(["tonic", "phasic"])]
    for (cohort, record), g in syn.groupby(["cohort", "record"], sort=False):
        for meth, measure, pattern in MEASURES:
            cols = [f"{measure}_{c}" for c in ("ki", "ni", "kc", "nc")]
            if not set(cols) <= set(g.columns):
                continue
            for variant in ("published", "FC"):
                s = g[(g.method == meth) & (g.variant == variant) & (g.pattern == pattern)]
                s = s.dropna(subset=cols).sort_values("amp_uv")
                if len(s) < 3:
                    continue
                rates = [corrected_rate(*r) for r in s[cols].to_numpy(float)]
                a, cens = a50(s.amp_uv.to_numpy(float), rates)
                first = s.iloc[0]
                out.append({"cohort": cohort, "record": record, "method": meth,
                            "variant": variant, "measure": measure, "pattern": pattern,
                            "a50": a, "censored": cens,
                            "p0": first[cols[2]] / first[cols[3]] if first[cols[3]] else np.nan,
                            "n_injected": int(first[cols[1]]),
                            **{f"r{a_:g}": r for a_, r in zip(s.amp_uv, rates)}})
    return pd.DataFrame(out)
