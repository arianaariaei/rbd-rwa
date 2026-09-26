"""Floor-corrected RWA criteria: the published rules with the noise floor subtracted.

The relative criteria count activity above k x background, and background is
mostly the recording's own noise floor (run_ladder.py), so the muscle activity
a criterion requires scales with the noise of the recording system. The
floor-corrected (FC) rules fix that requirement in microvolts (src/rwa.py,
`threshold`): at a reference background B they are the published rules, below
it they become absolute, above it the noise is subtracted instead of
multiplied. A "clamp" variant (background never below B, no subtraction)
separates the two ingredients.

Scored on the ordinary packs (every night as recorded, and HMC scaled by 0.39
for gain) and on the noise-ladder packs (the same nights with noise added),
against the criteria fixed in paper/preregistration_floor_corrected.md:

  FC1  site comparison as recorded (criteria 3, 4, 5)
  FC2  noise invariance on the ladder (criteria 1, 2)
  FC3  the reference background B from 0.5 to 2.0 uV
  FC4  discrimination (AUC, RBD vs same-system CAP patients)
  FC5  cut-offs re-derived under FC (leave-one-out, bootstrap)
  FC6  gain: HMC scaled by 0.39, and the size of muscle activity per cohort
  FC7  Montreal phasic bursts up to 10 s instead of 15 s
  FC8  MGH: the floor by record batch, and the ladder's 300 against the rest
  FC9  age: RBD against same-system CAP patients under 50 and aged 50 or over
  FC10 CAP's healthy volunteers night by night (mixed recording systems)

CAP RBD and CAP patients are the nights recorded on CAP's main system (512 Hz,
microvolts): 21 RBD and 51 other patients.

    python run_floor.py -> results/floor_scores.csv, floor_ladder_scores.csv,
                           floor_report.md, figures/fig8_floor_corrected
"""
import dataclasses
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.pack import load_pack
from src.rwa import (METHODS, NOISE_P5_RATIO, _select, floor_corrected, mini_epoch_rms,
                     rem_atonia_index, score_night)
from run_ladder import STEPS, YES, pct, youden
from run_report import MIN_REM, WITHDRAWN, paired_change
from run_score import auc, group_of

REFS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)     # reference background B, uV
PRIMARY = 1.0
COHORTS = ("cap", "chal18", "hmc", "hmc_low")
PAIRED = "h150"                              # the ladder step the criteria use
WHO = ["CAP RBD", "CAP patients", "CAP healthy", "MGH", "HMC"]
KEY = {"Montreal": ["tonic_pct", "phasic_pct"], "SINBAR": ["any_pct"]}


def variants():
    """(variant, reference uV, Method) for every scoring of Montreal and SINBAR."""
    out = []
    for key in ("montreal", "sinbar"):
        m = METHODS[key]
        out.append(("published", np.nan, m))
        out += [("FC", ref, floor_corrected(m, ref)) for ref in REFS]
        out.append(("clamp", PRIMARY, floor_corrected(m, PRIMARY, mode="clamp")))
    out.append(("max10", np.nan, dataclasses.replace(METHODS["montreal"], phasic_max_s=10.0)))
    return out


def scale(pack):
    """The size of the night's chin EMG in 1 s RMS (uV): quiet-REM level b, REM
    median and 95th percentile, N2/N3 median, and each with the noise implied by
    b (b / 0.91) removed in power ("_net")."""
    ep, env, _, nrem = _select(pack, "native")
    if env is None or len(ep) < 2:
        return {}
    r, _ = mini_epoch_rms(env.reshape(-1), pack["meta"]["env_fs"], 1.0)
    if len(r) < 10:
        return {}
    b = float(np.percentile(r, 5))
    out = {"rem_p50": float(np.median(r)), "rem_p95": float(np.percentile(r, 95))}
    if len(nrem) >= 60:
        out["nrem_p50"] = float(np.median(nrem))
        out["nrem_p5"] = float(np.percentile(nrem, 5))
    n2 = (b / NOISE_P5_RATIO) ** 2
    out.update({f"{k}_net": float(np.sqrt(max(v * v - n2, 0.0))) for k, v in list(out.items())})
    return dict(out, level_1s=b)


def score_rows(pack, band, info):
    rows = []
    for variant, ref, m in variants():
        rows.append({**info, **score_night(pack, m, band), "variant": variant, "ref_uv": ref})
    rows.append({**info, **rem_atonia_index(pack, band), "variant": "published", "ref_uv": np.nan})
    return rows


def _info(m, cohort):
    ecg = m.get("ecg") or m.get("chin_info", {}).get("ecg") or {}
    return dict(cohort=cohort, record=m["record"], group=group_of(cohort, m["record"]),
                chin_fs=m.get("chin_fs", m.get("chin_info", {}).get("fs")),
                unit_known=m.get("unit_known", True), age=m.get("age"), pid=m.get("pid"),
                beats=int(ecg.get("beats") or 0))


def score_pack_file(path):
    pack = load_pack(path)
    m = pack["meta"]
    info = _info(m, m.get("cohort", path.parent.name))
    rows = score_rows(pack, "native", info)
    rows[0].update(scale(pack))                  # one row per night carries the scale
    return rows


def score_ladder_file(path):
    pack = load_pack(path)
    m = pack["meta"]
    info = _info(m, m["cohort"])
    rows = []
    for step in STEPS:
        if step == "native" or f"rms_{step}" in m["rows"]:
            rows += score_rows(pack, step, {**info, "step": step})
    return rows


def label(df):
    gone = {f"{c}/{r}" for c, r in WITHDRAWN}
    df = df[~(df.cohort + "/" + df.record).isin(gone)].copy()
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512) & df.unit_known.astype(bool)
    df["who"] = np.select(
        [same & (df.group == "RBD"), same & ~df.group.isin(["RBD", "healthy"]),
         cap & (df.group == "healthy"), df.cohort == "chal18", df.cohort == "hmc",
         df.cohort == "hmc_low"],
        ["CAP RBD", "CAP patients", "CAP healthy", "MGH", "HMC", "HMC x0.39"], default="")
    df["y"] = df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan)
    df["ref_key"] = df.ref_uv.fillna(0.0)
    return df


def score(files, fn):
    with ProcessPoolExecutor(max_workers=2) as ex:
        return pd.DataFrame([r for part in ex.map(fn, files, chunksize=4) for r in part])


def sel(df, method, variant="published", ref=PRIMARY):
    s = (df.method == method) & (df.variant == variant)
    if variant in ("FC", "clamp"):
        s &= np.isclose(df.ref_key, ref)
    return df[s]


def share(g):
    p, lo, hi, n = pct(g.y)
    return f"{100 * p:3.0f} [{100 * lo:.0f}-{100 * hi:.0f}]" if n else "   -"


def main():
    packs = [p for c in COHORTS for p in sorted((config.DURABLE / "packs" / c).glob("*.npz"))
             if ".tmp" not in p.name]
    ladder = sorted(p for p in (config.DURABLE / "ladder").glob("*/*.npz") if ".tmp" not in p.name)
    print(f"scoring {len(packs)} packs and {len(ladder)} ladder packs", flush=True)
    nat = label(score(packs, score_pack_file))
    nat.to_csv(config.RESULTS / "floor_scores.csv", index=False)
    lad = label(score(ladder, score_ladder_file))
    lad.to_csv(config.RESULTS / "floor_ladder_scores.csv", index=False)
    nat = nat[nat.rem_minutes >= MIN_REM]
    lad = lad[lad.rem_minutes >= MIN_REM]
    level = lad[(lad.method == "Montreal") & (lad.variant == "published")] \
        .set_index(["cohort", "record", "step"]).background_phasic_uV
    lad["level"] = level.reindex(pd.MultiIndex.from_frame(lad[["cohort", "record", "step"]])).to_numpy()

    lines = []
    say = lambda s="": (print(s), lines.append(s))
    verdict = {}

    # FC1 ────────────────────────────────────────────────────────────────────
    say(f"FC1 Share flagged positive as recorded (all nights, published % cut-offs), % [95% CI];")
    say(f"    FC and clamp with B = {PRIMARY} uV")
    say(f"    {'':<22}" + "".join(f"{w:<16}" for w in WHO) + "MGH-HMC")
    gaps = {}
    for meth in ("Montreal", "SINBAR", "RAI"):
        for variant in (("published",) if meth == "RAI" else ("published", "FC", "clamp")):
            g = sel(nat, meth, variant)
            cells = [share(g[g.who == w]) for w in WHO]
            gap = 100 * (g[g.who == "MGH"].y.mean() - g[g.who == "HMC"].y.mean())
            gaps[meth, variant] = gap
            say(f"    {meth + ' ' + variant:<22}" + "".join(f"{c:<16}" for c in cells) + f"{gap:+.1f}")
    for meth, limit in (("Montreal", 5), ("SINBAR", 10)):
        sens = sel(nat, meth, "FC")
        sens = 100 * sens[sens.who == "CAP RBD"].y.mean()
        pub_fp = sel(nat, meth)
        fc_fp = sel(nat, meth, "FC")
        verdict[f"3 {meth}"] = abs(gaps[meth, "FC"]) <= limit
        verdict[f"4 {meth}"] = sens >= 85
        verdict[f"5 {meth}"] = fc_fp[fc_fp.who == "CAP patients"].y.mean() <= \
            pub_fp[pub_fp.who == "CAP patients"].y.mean()
        say(f"  criterion 3 ({meth}-FC gap <= {limit}): {gaps[meth, 'FC']:+.1f} -> "
            f"{'met' if verdict[f'3 {meth}'] else 'not met'};  criterion 4 (RBD sensitivity >= 85%): "
            f"{sens:.0f}% -> {'met' if verdict[f'4 {meth}'] else 'not met'};  criterion 5 (CAP patients "
            f"not above published): {'met' if verdict[f'5 {meth}'] else 'not met'}")
    say()

    # FC2 ────────────────────────────────────────────────────────────────────
    say("FC2 The same nights as the noise floor rises: % positive per ladder step, published")
    say(f"    cut-offs; FC and clamp with B = {PRIMARY} uV; median quiet-REM level in the first line")
    steps = [s for s in STEPS if s in set(lad.step)]
    say(f"    {'':<30}" + "".join(f"{s:>7}" for s in steps))
    for who in ("CAP RBD", "CAP patients", "MGH", "HMC"):
        g = lad[lad.who == who]
        if g.empty:
            continue
        lv = [sel(g, "Montreal")[lambda d: d.step == s].level.median() for s in steps]
        say(f"  {who} (n={g[g.step == 'native'].record.nunique()})")
        say(f"    {'quiet-REM level, uV':<28}" + "".join(f"{v:7.2f}" for v in lv))
        for meth in ("Montreal", "SINBAR", "RAI"):
            for variant in (("published",) if meth == "RAI" else ("published", "FC", "clamp")):
                h = sel(g, meth, variant)
                say(f"    {meth + ' ' + variant:<28}" + "".join(
                    f"{100 * h[h.step == s].y.mean():7.1f}" for s in steps))
    say(f"  Paired change, as recorded -> {PAIRED} (same nights):")
    for who in ("MGH", "CAP RBD", "CAP patients", "HMC"):
        for meth in ("Montreal", "SINBAR", "RAI"):
            for variant in (("published",) if meth == "RAI" else ("published", "FC", "clamp")):
                h = sel(lad[lad.who == who], meth, variant)
                w = h.pivot_table(index="record", columns="step", values="y", aggfunc="first")
                if "native" not in w or PAIRED not in w:
                    continue
                w = w[["native", PAIRED]].dropna()
                d = 100 * (w[PAIRED].mean() - w["native"].mean())
                say(f"    {who:<13} {meth + ' ' + variant:<20} {100 * w['native'].mean():5.1f} -> "
                    f"{100 * w[PAIRED].mean():5.1f}   " + paired_change(w["native"], w[PAIRED]))
                if variant == "FC" and who == "MGH":
                    verdict[f"1 {meth}"] = abs(d) <= 5
                if variant == "FC" and who == "CAP RBD":
                    verdict[f"2 {meth}"] = abs(d) <= 10
    for meth in ("Montreal", "SINBAR"):
        say(f"  criterion 1 ({meth}-FC, MGH within 5 points): "
            f"{'met' if verdict.get(f'1 {meth}') else 'not met'};  criterion 2 ({meth}-FC, "
            f"CAP RBD within 10 points): {'met' if verdict.get(f'2 {meth}') else 'not met'}")
    say()

    # FC3 ────────────────────────────────────────────────────────────────────
    say("FC3 The reference background B: as recorded (sensitivity, CAP patients, MGH, HMC, gap)")
    say(f"    and on the ladder (change as recorded -> {PAIRED}, MGH and CAP RBD), points")
    for meth in ("Montreal", "SINBAR"):
        for variant, ref in [("published", np.nan)] + [("FC", r) for r in REFS] + [("clamp", PRIMARY)]:
            g = sel(nat, meth, variant, ref)
            v = {w: 100 * g[g.who == w].y.mean() for w in ("CAP RBD", "CAP patients", "MGH", "HMC")}
            h = sel(lad, meth, variant, ref)
            ch = {}
            for w in ("MGH", "CAP RBD"):
                p = h[h.who == w].pivot_table(index="record", columns="step", values="y", aggfunc="first")
                p = p[["native", PAIRED]].dropna() if {"native", PAIRED} <= set(p) else p.iloc[:0]
                ch[w] = 100 * (p[PAIRED].mean() - p["native"].mean()) if len(p) else np.nan
            name = meth + " " + variant + ("" if variant == "published" else f" {ref:g}")
            say(f"  {name:<20} RBD {v['CAP RBD']:3.0f}  CAP patients {v['CAP patients']:3.0f}  "
                f"MGH {v['MGH']:3.0f}  HMC {v['HMC']:3.0f}  gap {v['MGH'] - v['HMC']:+5.1f}   "
                f"ladder MGH {ch['MGH']:+5.1f}  RBD {ch['CAP RBD']:+5.1f}")
    say()

    # FC4 ────────────────────────────────────────────────────────────────────
    say("FC4 RBD vs same-system CAP patients (AUC), as recorded")
    for meth, metrics in KEY.items():
        for metric in metrics:
            cells = []
            for variant, ref in [("published", np.nan)] + [("FC", r) for r in REFS]:
                g = sel(nat, meth, variant, ref)
                cells.append(f"{'pub' if variant == 'published' else f'FC {ref:g}'} "
                             f"{auc(g[g.who == 'CAP RBD'][metric], g[g.who == 'CAP patients'][metric])[0]:.3f}")
            say(f"  {meth:<9} {metric:<11} " + "  ".join(cells))
    say()

    # FC5 ────────────────────────────────────────────────────────────────────
    say("FC5 Cut-offs re-derived on CAP (Youden, RBD vs same-system patients), leave-one-out")
    say("    and 2,000 bootstrap re-derivations; external shares flagged [95% interval]")
    rng = np.random.default_rng(0)
    for variant in ("published", "FC"):
        for meth, metrics in KEY.items():
            g = sel(nat, meth, variant)
            for metric in metrics:
                pos = g.loc[g.who == "CAP RBD", metric].dropna().to_numpy(float)
                neg = g.loc[g.who == "CAP patients", metric].dropna().to_numpy(float)
                ext = {k: g.loc[g.who == k, metric].dropna().to_numpy(float) for k in ("MGH", "HMC")}
                cut = youden(pos, neg)
                cv_s = np.mean([pos[i] >= youden(np.delete(pos, i), neg) for i in range(len(pos))])
                cv_f = np.mean([neg[i] >= youden(pos, np.delete(neg, i)) for i in range(len(neg))])
                boot = {k: [] for k in ext}
                for _ in range(2000):
                    c = youden(rng.choice(pos, len(pos)), rng.choice(neg, len(neg)))
                    for k, v in ext.items():
                        boot[k].append((v >= c).mean())
                fp = {k: 100 * (v >= cut).mean() for k, v in ext.items()}
                ci = {k: np.percentile(v, [2.5, 97.5]) * 100 for k, v in boot.items()}
                say(f"  {variant:<9} {meth:<9} {metric:<11} cut {cut:6.2f}  LOO sens {100 * cv_s:3.0f}%  "
                    f"LOO FP {100 * cv_f:3.0f}%  MGH {fp['MGH']:3.0f} [{ci['MGH'][0]:.0f}-{ci['MGH'][1]:.0f}]  "
                    f"HMC {fp['HMC']:3.0f} [{ci['HMC'][0]:.0f}-{ci['HMC'][1]:.0f}]  gap {fp['MGH'] - fp['HMC']:+.0f}")
    say()

    # FC6 ────────────────────────────────────────────────────────────────────
    say("FC6 Gain: HMC scaled by 0.39 against HMC, same nights")
    for meth in ("Montreal", "SINBAR", "RAI"):
        for variant in (("published",) if meth == "RAI" else ("published", "FC")):
            g = sel(nat, meth, variant)
            w = g[g.cohort.isin(["hmc", "hmc_low"])].pivot_table(index="record", columns="cohort",
                                                                  values="y", aggfunc="first").dropna()
            if {"hmc", "hmc_low"} <= set(w):
                say(f"  {meth + ' ' + variant:<20} {100 * w.hmc.mean():5.1f} -> {100 * w.hmc_low.mean():5.1f}   "
                    + paired_change(w.hmc, w.hmc_low))
    say("  Size of the chin EMG (1 s RMS, uV, median [IQR]); _net = noise (b / 0.91) removed")
    sc = nat[(nat.method == "Montreal") & (nat.variant == "published")]
    cols = [c for c in ("level_1s", "rem_p50_net", "rem_p95_net", "nrem_p50_net") if c in sc]
    for who in ("CAP RBD", "CAP patients", "MGH", "HMC", "HMC x0.39"):
        g = sc[sc.who == who]
        say(f"    {who:<13} n={len(g):<4} " + "  ".join(
            f"{c} {g[c].median():.2f} [{g[c].quantile(.25):.2f}-{g[c].quantile(.75):.2f}]" for c in cols))
    m, h = sc[sc.who == "MGH"], sc[sc.who == "HMC"]
    say("    MGH/HMC ratio of medians: " + "  ".join(f"{c} {m[c].median() / h[c].median():.2f}" for c in cols))
    say()

    # FC7 ────────────────────────────────────────────────────────────────────
    say("FC7 Montreal, phasic bursts up to 10 s instead of 15 s (published cut-offs), % positive")
    a, b = sel(nat, "Montreal"), sel(nat, "Montreal", "max10")
    for who in ("CAP RBD", "CAP patients", "MGH", "HMC"):
        w = pd.merge(a[a.who == who][["record", "y", "phasic_pct"]], b[b.who == who][["record", "y", "phasic_pct"]],
                     on="record", suffixes=("", "_10"))
        say(f"  {who:<13} {100 * w.y.mean():5.1f} -> {100 * w.y_10.mean():5.1f}   nights changed "
            f"{int((w.y != w.y_10).sum())}   phasic % median {w.phasic_pct.median():.1f} -> {w.phasic_pct_10.median():.1f}")
    say()

    # FC8 ────────────────────────────────────────────────────────────────────
    say("FC8 MGH: quiet-REM level and share positive (published) by record batch, and the")
    say("    noise-ladder subset against the rest")
    mg = sel(nat, "Montreal")
    sb = sel(nat, "SINBAR")
    mg = mg[mg.who == "MGH"].merge(sb[sb.who == "MGH"][["record", "y"]], on="record", suffixes=("", "_s"))
    mg["batch"] = mg.record.str[:4]
    for b_, g in mg.groupby("batch"):
        say(f"  {b_:<6} n={len(g):<4} level {g.background_phasic_uV.median():.2f}  Montreal "
            f"{100 * g.y.mean():3.0f}%  SINBAR {100 * g.y_s.mean():3.0f}%")
    sub = set(lad[lad.cohort == "chal18"].record)
    for name, g in (("ladder 300", mg[mg.record.isin(sub)]), ("the rest", mg[~mg.record.isin(sub)])):
        say(f"  {name:<10} n={len(g):<4} level {g.background_phasic_uV.median():.2f}  Montreal "
            f"{100 * g.y.mean():3.0f}%  SINBAR {100 * g.y_s.mean():3.0f}%  age {pd.to_numeric(g.age).mean():.0f}")
    from scipy.stats import spearmanr
    per = mg.groupby("batch").agg(level=("background_phasic_uV", "median"), m=("y", "mean"), s=("y_s", "mean"))
    if len(per) >= 4:
        say(f"  across batches, Spearman rho of median level with share positive: Montreal "
            f"{spearmanr(per.level, per.m)[0]:+.2f}, SINBAR {spearmanr(per.level, per.s)[0]:+.2f} "
            f"({len(per)} batches)")
    say()

    # FC9 ────────────────────────────────────────────────────────────────────
    from src.fetch import cap_demographics
    demo = cap_demographics()
    if demo:
        say("FC9 Age in CAP: RBD against same-system patients under 50 and aged 50 or over")
        cap = nat[nat.who.isin(["CAP RBD", "CAP patients"])].copy()
        cap["age"] = cap.record.map(lambda r: demo.get(r, {}).get("age"))
        parts = {"patients < 50": lambda d: d[(d.who == "CAP patients") & (d.age < 50)],
                 "patients >= 50": lambda d: d[(d.who == "CAP patients") & (d.age >= 50)],
                 "RBD": lambda d: d[d.who == "CAP RBD"]}
        one = cap[(cap.method == "Montreal") & (cap.variant == "published")]
        say("  " + "   ".join(f"{k}: n={len(f(one))}, age {f(one).age.mean():.0f}" for k, f in parts.items()))
        for meth in ("Montreal", "SINBAR"):
            for variant in ("published", "FC"):
                g = sel(cap, meth, variant)
                say(f"  {meth + ' ' + variant:<20} flagged: " + "   ".join(
                    f"{k} {100 * f(g).y.mean():3.0f}%" for k, f in parts.items()))
        for meth, metrics in KEY.items():
            for metric in metrics:
                for variant in ("published", "FC"):
                    g = sel(cap, meth, variant)
                    r_ = parts["RBD"](g)[metric]
                    say(f"  AUC {meth + ' ' + variant:<20} {metric:<11} vs all patients "
                        f"{auc(r_, g[g.who == 'CAP patients'][metric])[0]:.3f}   vs patients >= 50 "
                        f"{auc(r_, parts['patients >= 50'](g)[metric])[0]:.3f}")
        say()

    # FC10 ───────────────────────────────────────────────────────────────────
    say("FC10 CAP healthy volunteers, night by night (mixed recording systems): positive")
    say("     published / floor-corrected (- = not scored: no physical units)")
    h = nat[nat.who == "CAP healthy"]
    flag = lambda g: "-" if g.empty or pd.isna(g.y.iloc[0]) else str(int(g.y.iloc[0]))
    for rec, g in h.groupby("record"):
        mp = sel(g, "Montreal")
        say(f"  {rec:<4} fs {g.chin_fs.iloc[0]:>5g}  units {'yes' if bool(g.unit_known.iloc[0]) else 'no ':<3}  "
            f"level {mp.background_phasic_uV.iloc[0]:6.2f}   Montreal {flag(mp)}/{flag(sel(g, 'Montreal', 'FC'))}"
            f"   SINBAR {flag(sel(g, 'SINBAR'))}/{flag(sel(g, 'SINBAR', 'FC'))}")
    say()

    say("Pre-specified criteria: " + "  ".join(f"{k}: {'met' if v else 'not met'}" for k, v in sorted(verdict.items())))
    out = config.RESULTS / "floor_report.md"
    out.write_text("```\n" + "\n".join(lines) + "\n```\n", encoding="utf-8")
    print(f"\nwritten -> {out}")
    figure(nat, lad)


def figure(nat, lad):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from run_figures import COLOR, save

    colors = {"CAP RBD": "#d62728", "CAP patients": "#7f7f7f", "MGH": "#1f77b4", "HMC": "#9467bd"}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8), layout="constrained",
                             gridspec_kw={"width_ratios": [1, 1, 1.25]})
    ladder = [s for s in STEPS if s.startswith("n") or s == "native"]
    for ax, meth in zip(axes[:2], ("Montreal", "SINBAR")):
        for who, col in colors.items():
            for variant, ls in (("published", ":"), ("FC", "-")):
                g = sel(lad[lad.who == who], meth, variant)
                if g.empty:
                    continue
                lv = sel(lad[lad.who == who], "Montreal")
                x = [lv[lv.step == s].level.median() for s in ladder]
                y = [100 * g[g.step == s].y.mean() for s in ladder]
                ax.plot(x, y, ls, marker="o", ms=2.5, lw=1, color=col,
                        label=who if variant == "FC" else None)
        ax.set_xscale("log")
        ax.set_xticks([0.5, 1, 2, 4], ["0.5", "1", "2", "4"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_xlabel("quiet-REM level (µV)")
        ax.set_ylim(0, 100)
        ax.set_title(f"{'AB'[meth == 'SINBAR']}  {meth}")
    axes[0].set_ylabel("nights flagged positive (%)")
    axes[0].plot([], [], ":", color="k", lw=1, label="published")
    axes[0].plot([], [], "-", color="k", lw=1, label="floor-corrected")
    axes[0].legend(frameon=False, fontsize=6, loc="lower left", bbox_to_anchor=(0.0, 0.38))
    ax = axes[2]
    groups = ["CAP RBD", "CAP patients", "MGH", "HMC"]
    for j, (meth, variant, hatch) in enumerate([("Montreal", "published", ""), ("Montreal", "FC", "//"),
                                               ("SINBAR", "published", ""), ("SINBAR", "FC", "//")]):
        g = sel(nat, meth, variant)
        vals = [100 * g[g.who == w].y.mean() for w in groups]
        ax.bar(np.arange(4) + (j - 1.5) * 0.2, vals, width=0.19, color=COLOR[meth], hatch=hatch,
               edgecolor="white", label=f"{meth}, {'published' if variant == 'published' else 'floor-corrected'}")
    ax.set_xticks(range(4), ["CAP\nRBD", "CAP\npatients", "MGH", "HMC"])
    ax.set_ylim(0, 130)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("nights flagged positive (%)")
    ax.legend(frameon=False, fontsize=5.5, loc="upper center", ncol=2)
    ax.set_title("C  As recorded")
    save(fig, "fig8_floor_corrected")


if __name__ == "__main__":
    main()
