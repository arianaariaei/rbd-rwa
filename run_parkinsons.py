"""What the noise floor means for Parkinson's disease research.

RBD is the strongest known prodromal marker of Parkinson's disease, dementia with
Lewy bodies and multiple system atrophy, and REM sleep without atonia is how it is
confirmed; how much RWA a patient has is also used to predict who develops
Parkinson's disease and to follow progression, and RWA without RBD is studied as
an earlier stage still. This puts the recording system's effect in those terms,
against the predictions fixed in paper/preregistration_parkinsons.md:

  PD1  the same RBD nights as recorded and at HMC's floor: change in tonic, phasic
       and 'any' RWA (points), against the baseline difference that separated later
       Parkinson's disease from no disease (Postuma 2010) and five years of
       progression (Iranzo 2009)
  PD2  RBDtector, the open scorer used in Parkinson's and RBD research, run
       unchanged: on the noise ladder, across recording systems, and with the
       floor-corrected baseline
  PD3  isolated RWA by system: DREAMER's RAI < 0.85 and the other rules, in people
       without RBD (descriptive)
  PD4  recruiting for prevention trials: per 1,000 sleep studies in people aged 50
       or over (descriptive)
  PD5  the floor check for each recording system (descriptive)

    python run_parkinsons.py -> results/parkinsons_report.md, figures/fig10_parkinsons
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.floorcheck import MAX_FLOOR, MIN_FS, thresholds
from src.rwa import NOISE_P5_RATIO
from run_floor import pct, sel
from run_report import MIN_REM, paired_change

PAIRED = "h150"                    # HMC's floor (1.5 uV), the ladder step used throughout
POSTUMA_PD = 72.9 - 41.0           # baseline tonic %: later Parkinson's vs disease-free
POSTUMA_ANY = 62.7 - 41.0          # ... any neurodegenerative disease vs disease-free
IRANZO_5Y = 54.0 - 30.0            # tonic %: rise over a mean 5 years of follow-up
IRANZO_YEAR = IRANZO_5Y / 5.0
CONVERT_12Y = 0.735                # isolated RBD -> synucleinopathy within 12 years
RBDT_CUT = 23.5                    # RBDtector chin 'any' cut-off (Rothenbacher 2022)
FC_CUT = 49.1                      # SINBAR-FC 'any' cut-off re-derived on CAP (FC5)
DREAMER_RAI = 0.85
PREVALENCE = (0.01, 0.02, 0.05)
WITHOUT_RBD = ["CAP patients", "MGH", "HMC", "DOD-O", "BOAS", "DOD-H"]


def boot_ci(x, n=2000, seed=0, stat=np.mean):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    b = [stat(rng.choice(x, len(x))) for _ in range(n)]
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def paired(df, metric, steps=("native", PAIRED)):
    """record x step table of a metric, complete pairs only."""
    w = df.pivot_table(index="record", columns="step", values=metric, aggfunc="first")
    if not set(steps) <= set(w):
        return w.iloc[:0]
    return w[list(steps)].dropna()


def load():
    R = config.RESULTS
    ext = pd.read_csv(R / "external_scores.csv", low_memory=False)
    ext = ext[(ext.rem_minutes >= MIN_REM) & (ext.who.fillna("") != "") & ext.primary.astype(bool)]
    lad = pd.read_csv(R / "floor_ladder_scores.csv", low_memory=False)
    lad = lad[lad.rem_minutes >= MIN_REM]
    rb = pd.read_csv(R / "rbdtector_scores.csv", dtype={"record": str}) \
        if (R / "rbdtector_scores.csv").exists() else pd.DataFrame()
    if len(rb):
        if rb.rem_miniepochs.notna().any():                     # 20 mini-epochs per minute
            rb = rb[rb.rem_miniepochs.fillna(0) >= MIN_REM * 20]
        floor = ext[(ext.method == "Montreal") & (ext.variant == "published")] \
            .drop_duplicates(["cohort", "record"]).set_index(["cohort", "record"])
        key = pd.MultiIndex.from_frame(rb[["cohort", "record"]].astype(str))
        floor.index = pd.MultiIndex.from_arrays([floor.index.get_level_values(0).astype(str),
                                                 floor.index.get_level_values(1).astype(str)])
        rb["level_1s"] = floor.level_1s.reindex(key).to_numpy()
        rb["age"] = pd.to_numeric(floor.age.reindex(key), errors="coerce").to_numpy()
        rb["who"] = floor.who.reindex(key).to_numpy()
        rb["y"] = (rb.any_pct >= RBDT_CUT).astype(float).where(rb.any_pct.notna())
    return ext, lad, rb


def main():
    ext, lad, rb = load()
    lines, verdict = [], {}
    say = lambda s="": (print(s), lines.append(s))
    sources = []                                          # (label, frame, method, metric, variant)
    for variant in ("published", "FC"):
        sources += [(f"Montreal tonic, {variant}", lambda d, v=variant: sel(d, "Montreal", v), "tonic_pct", variant),
                    (f"Montreal phasic, {variant}", lambda d, v=variant: sel(d, "Montreal", v), "phasic_pct", variant),
                    (f"SINBAR any, {variant}", lambda d, v=variant: sel(d, "SINBAR", v), "any_pct", variant)]
        if len(rb):
            sources += [(f"RBDtector {m.split('_')[0]}, {variant}", lambda d, v=variant: d[d.variant == v], m, variant)
                        for m in ("tonic_pct", "phasic_pct", "any_pct")]

    # PD1 ────────────────────────────────────────────────────────────────────
    say(f"PD1 The same nights as recorded and at HMC's floor ({PAIRED}): change in RWA, points")
    say(f"    benchmarks (tonic %): later Parkinson's vs disease-free at baseline {POSTUMA_PD:.1f}")
    say(f"    (Postuma 2010; any neurodegeneration {POSTUMA_ANY:.1f}); rise over 5 years {IRANZO_5Y:.0f}")
    say(f"    = {IRANZO_YEAR:.1f} per year (Iranzo 2009)")
    pd1 = {}
    for who in ("CAP RBD", "CAP patients"):
        say(f"  {who}")
        for label, pick, metric, variant in sources:
            src = rb if label.startswith("RBDtector") else lad
            w = paired(pick(src[src.who == who]), metric)
            if w.empty:
                continue
            d = w[PAIRED] - w["native"]
            lo, hi = boot_ci(d)
            pd1[who, label] = (d.mean(), lo, hi, len(d))
            extra = ""
            if "tonic" in label:
                extra = (f"   = {100 * abs(d.mean()) / POSTUMA_PD:3.0f}% of the Parkinson's difference,"
                         f" {abs(d.mean()) / IRANZO_YEAR:4.1f} years of progression")
            say(f"    {label:<26} n={len(d):<3} {w['native'].mean():5.1f} -> {w[PAIRED].mean():5.1f}   "
                f"change {d.mean():+6.1f} [{lo:+.1f} to {hi:+.1f}]  median {d.median():+5.1f} "
                f"[{d.quantile(.25):+.1f} to {d.quantile(.75):+.1f}]" + extra)
    get = lambda k: pd1.get(("CAP RBD", k), (np.nan,) * 4)[0]
    verdict["PD1a Montreal tonic published <= -10"] = get("Montreal tonic, published") <= -10
    verdict["PD1b Montreal tonic FC within 3"] = abs(get("Montreal tonic, FC")) <= 3
    if len(rb):
        verdict["PD1c RBDtector tonic published <= -10"] = get("RBDtector tonic, published") <= -10
        verdict["PD1d RBDtector tonic FC within 3"] = abs(get("RBDtector tonic, FC")) <= 3
    say("  Dose-response, CAP RBD, mean tonic % per ladder step (Montreal; RBDtector where scored):")
    steps = [s for s in ("native", "n050", "n100", "n150", "n200", "n300", "h150") if s in set(lad.step)]
    for label, pick, metric, variant in sources:
        if "tonic" not in label:
            continue
        src = rb if label.startswith("RBDtector") else lad
        g = pick(src[src.who == "CAP RBD"])
        say(f"    {label:<26} " + "  ".join(f"{s} {g[g.step == s][metric].mean():5.1f}"
                                            for s in steps if (g.step == s).any()))
    say()

    # PD2 ────────────────────────────────────────────────────────────────────
    if len(rb):
        say(f"PD2 RBDtector (run unchanged; chin 'any' >= {RBDT_CUT}% = positive), published baseline")
        say("    and floor-corrected baseline (B = 1.0 uV)")
        say("  a) The noise ladder, % flagged [95% CI], same nights")
        lv = sel(lad, "Montreal")
        for who in ("CAP RBD", "CAP patients"):
            g = rb[rb.who == who]
            st = [s for s in steps if (g.step == s).any()]
            level = [lv[(lv.who == who) & (lv.step == s)].background_phasic_uV.median() for s in st]
            say(f"    {who} (n={g[g.step == 'native'].record.nunique()})   quiet-REM level "
                + "  ".join(f"{s} {v:.2f}" for s, v in zip(st, level)))
            for variant in ("published", "FC"):
                h = g[g.variant == variant]
                say(f"      {variant:<10} " + "  ".join(f"{s} {100 * h[h.step == s].y.mean():5.1f}" for s in st))
                w = paired(h, "y")
                if len(w):
                    ch = 100 * (w[PAIRED].mean() - w["native"].mean())
                    say(f"      {'':<10} native -> {PAIRED}: " + paired_change(w["native"], w[PAIRED]))
                    if who == "CAP patients":
                        if variant == "published":
                            verdict["PD2a patients published fall >= 10"] = ch <= -10
                        else:
                            verdict["PD2b patients FC within 5"] = abs(ch) <= 5
                    elif variant == "FC":
                        verdict["PD2c RBD FC within 10"] = abs(ch) <= 10
        say("  b) As recorded, by system: % flagged [95% CI]; median floor")
        nat = rb[rb.step == "native"]
        share = {}
        for who in ["CAP RBD", "CAP patients", "MGH", "HMC", "BOAS"]:
            g = nat[nat.who == who]
            if g.empty:
                continue
            cells = []
            for variant in ("published", "FC"):
                p, lo, hi, n = pct(g[g.variant == variant].y)
                share[who, variant] = p
                cells.append(f"{variant} {100 * p:5.1f} [{100 * lo:.0f}-{100 * hi:.0f}]")
            say(f"    {who:<13} n={g.record.nunique():<4} floor {g.level_1s.median():.2f} uV   " + "   ".join(cells))
        if {("MGH", "published"), ("HMC", "published")} <= set(share):
            gp = share["MGH", "published"] - share["HMC", "published"]
            gf = share["MGH", "FC"] - share["HMC", "FC"]
            say(f"    MGH - HMC: published {100 * gp:+.1f}, floor-corrected {100 * gf:+.1f} points")
            verdict["PD2d MGH-HMC published >= 20 and FC halves it"] = gp >= 0.20 and abs(gf) <= abs(gp) / 2
        if ("BOAS", "published") in share:
            verdict["PD2e BOAS published >= 50% and FC halves it"] = \
                share["BOAS", "published"] >= 0.5 and share["BOAS", "FC"] <= share["BOAS", "published"] / 2
        say("  c) Nights without RBD, pooled: Spearman rho of the night's floor with RBDtector 'any' %")
        from scipy.stats import spearmanr
        g = nat[nat.who.isin(WITHOUT_RBD)]
        rho = {}
        for variant in ("published", "FC"):
            h = g[g.variant == variant][["level_1s", "any_pct"]].dropna()
            r = spearmanr(h.level_1s, h.any_pct)[0]
            rng = np.random.default_rng(0)
            bs = [spearmanr(*h.sample(len(h), replace=True, random_state=rng.integers(1 << 31)).to_numpy().T)[0]
                  for _ in range(1000)]
            rho[variant] = (r, *np.percentile(bs, [2.5, 97.5]))
            say(f"    {variant:<10} rho {r:+.2f} [{rho[variant][1]:+.2f} to {rho[variant][2]:+.2f}]  (n={len(h)})")
        verdict["PD2f published rho < 0 (CI) and FC weaker"] = rho["published"][2] < 0 and \
            abs(rho["FC"][0]) < abs(rho["published"][0])
        say("  d) RBDtector against the paper's SINBAR 'any' (published), same nights as recorded:")
        s = sel(ext, "SINBAR")[["cohort", "record", "any_pct"]].astype({"record": str})
        m = nat[nat.variant == "published"].merge(s, on=["cohort", "record"], suffixes=("", "_sinbar"))
        if len(m) > 3:
            say(f"    Spearman rho {spearmanr(m.any_pct, m.any_pct_sinbar)[0]:+.2f} (n={len(m)});  "
                f"RBDtector baseline / quiet-REM floor, median {np.nanmedian(m.baseline_uv / m.level_1s):.2f}")
        say()

    # PD3 ────────────────────────────────────────────────────────────────────
    say("PD3 Isolated RWA (RWA without RBD) by system, % of nights labeled (descriptive)")
    say(f"    DREAMER: RAI < {DREAMER_RAI}; RAI < 0.8; SINBAR and Montreal published / floor-corrected;")
    say(f"    RBDtector published / floor-corrected where scored")
    rai = ext[ext.method == "RAI"].drop_duplicates(["cohort", "record"]).set_index(["cohort", "record"]).rai
    groups = []
    for who in WITHOUT_RBD:
        g = ext[ext.who == who]
        age = pd.to_numeric(g.age, errors="coerce")
        groups.append((who, g))
        if age.notna().sum() >= 20:
            groups.append((f"{who} >= 50 y", g[age >= 50]))
    pd3 = {}
    for name, g in groups:
        base = g[(g.method == "Montreal") & (g.variant == "published")]
        if base.empty:
            continue
        r = rai.reindex(pd.MultiIndex.from_frame(base[["cohort", "record"]])).to_numpy(float)
        r = r[np.isfinite(r)]
        cells = {"RAI<0.85": np.mean(r < DREAMER_RAI) if len(r) else np.nan,
                 "RAI<0.8": np.mean(r < 0.8) if len(r) else np.nan}
        for meth in ("SINBAR", "Montreal"):
            for variant in ("published", "FC"):
                cells[f"{meth} {variant[:3]}"] = sel(g, meth, variant).y.mean()
        if len(rb):
            h = rb[(rb.step == "native") & rb.record.isin(set(base.record.astype(str)))
                   & rb.cohort.isin(set(base.cohort))]
            for variant in ("published", "FC"):
                v = h[h.variant == variant].y
                cells[f"RBDtector {variant[:3]}"] = v.mean() if len(v) else np.nan
        pd3[name] = cells
        say(f"  {name:<20} n={len(base):<4} floor {base.level_1s.median():.2f}  " + "  ".join(
            f"{k} {100 * v:4.0f}" if np.isfinite(v) else f"{k}    -" for k, v in cells.items()))
    say("  RAI < 0.85 on the noise ladder (same nights), %:")
    rl = lad[(lad.method == "RAI")]
    for who in ("CAP patients", "MGH", "HMC", "CAP RBD"):
        g = rl[rl.who == who]
        if g.empty:
            continue
        say(f"    {who:<13} " + "  ".join(f"{s} {100 * (g[g.step == s].rai < DREAMER_RAI).mean():4.0f}"
                                         for s in steps if (g.step == s).any()))
    say()

    # PD4 ────────────────────────────────────────────────────────────────────
    say("PD4 Per 1,000 sleep studies in people aged 50 or over (descriptive): flagged, true RBD")
    say("    found, positive predictive value, studies to review per RBD found, and people expected")
    say(f"    to develop a synucleinopathy within 12 years ({100 * CONVERT_12Y:.1f}%, Postuma 2019).")
    say("    False-positive rate: share flagged among MGH patients >= 50 y (an upper bound: a few")
    say("    may have RBD); sensitivity: CAP RBD.")
    mgh = ext[ext.who == "MGH"]
    old = mgh[pd.to_numeric(mgh.age, errors="coerce") >= 50]
    rbd = ext[ext.who == "CAP RBD"]
    rules = []
    for meth in ("Montreal", "SINBAR"):
        for variant in ("published", "FC"):
            rules.append((f"{meth} {variant}", sel(old, meth, variant).y, sel(rbd, meth, variant).y))
    fa, ra = sel(old, "SINBAR", "FC").any_pct, sel(rbd, "SINBAR", "FC").any_pct
    rules.append((f"SINBAR-FC >= {FC_CUT}%", (fa >= FC_CUT).astype(float).where(fa.notna()),
                  (ra >= FC_CUT).astype(float).where(ra.notna())))
    rules.append(("RAI < 0.8", sel(old, "RAI").y, sel(rbd, "RAI").y))
    if len(rb):
        for variant in ("published", "FC"):
            h = rb[(rb.step == "native") & (rb.variant == variant)]
            rules.append((f"RBDtector {variant}", h[(h.who == "MGH") & (h.age >= 50)].y,
                          h[h.who == "CAP RBD"].y))
    say(f"    MGH >= 50 y: n={old.record.nunique()};  CAP RBD: n={rbd.record.nunique()}")
    pd4 = []
    for name, fp_y, se_y in rules:
        fp, se = np.nanmean(fp_y), np.nanmean(se_y)
        for p in PREVALENCE:
            tp, f = 1000 * p * se, 1000 * (1 - p) * fp
            pd4.append(dict(rule=name, prevalence=p, fp=fp, se=se, flagged=tp + f, found=tp,
                            ppv=tp / (tp + f) if tp + f else np.nan, per_case=(tp + f) / tp if tp else np.nan,
                            convert=tp * CONVERT_12Y, n_fp=int(np.isfinite(fp_y).sum())))
        say(f"  {name:<20} FP {100 * fp:4.1f}% (n={int(np.isfinite(fp_y).sum())})  sens {100 * se:4.0f}%   " + "   ".join(
            f"{100 * p:.0f}%: flag {r['flagged']:4.0f}, find {r['found']:4.1f}, PPV {100 * r['ppv']:4.1f}%, "
            f"{r['per_case']:4.0f}/case, {r['convert']:4.1f} convert"
            for p, r in zip(PREVALENCE, pd4[-len(PREVALENCE):])))
    say("  The same at 2% prevalence with HMC's false-positive rate (all ages; HMC gives none):")
    hmc = ext[ext.who == "HMC"]
    for meth in ("Montreal", "SINBAR"):
        for variant in ("published", "FC"):
            fp, se = sel(hmc, meth, variant).y.mean(), sel(rbd, meth, variant).y.mean()
            tp, f = 20 * se, 980 * fp
            say(f"    {meth + ' ' + variant:<20} flag {tp + f:4.0f}, find {tp:4.1f}, PPV {100 * tp / (tp + f):4.1f}%")
    say()

    # PD5 ────────────────────────────────────────────────────────────────────
    say("PD5 Floor check by recording system (descriptive): floor b (5th percentile of 1-s REM RMS),")
    say(f"    nights inside the floor-corrected rule's range (>= {MIN_FS:g} Hz and b <= {MAX_FLOOR:.2f} uV),")
    say("    net N2/N3 tone (gain check), and the muscle activity 2 x b requires on top of the noise")
    one = ext[(ext.method == "Montreal") & (ext.variant == "published")]
    pd5 = {}
    for who in ["CAP RBD"] + WITHOUT_RBD:
        g = one[one.who == who]
        if g.empty:
            continue
        b = g.level_1s.median()
        t = thresholds(b)["SINBAR any (2 x b)"]
        inside = ((g.chin_fs >= MIN_FS) & (g.level_1s <= MAX_FLOOR)).mean()
        pd5[who] = dict(fs=g.chin_fs.median(), floor=b, inside=inside, net=g.nrem_p50_net.median(),
                        needs_pub=t["published_needs_uv"], needs_fc=t["fc_needs_uv"])
        say(f"  {who:<13} n={len(g):<4} fs {g.chin_fs.median():5g}  floor {b:.2f} "
            f"[{g.level_1s.quantile(.25):.2f}-{g.level_1s.quantile(.75):.2f}] uV  inside {100 * inside:3.0f}%  "
            f"net N2/N3 {g.nrem_p50_net.median():.2f} uV  2 x b needs {t['published_needs_uv']:.2f} uV "
            f"(floor-corrected {t['fc_needs_uv']:.2f})")
    say()

    say("Pre-specified predictions: " + "  ".join(f"{k}: {'met' if v else 'not met'}"
                                                 for k, v in verdict.items()))
    out = config.RESULTS / "parkinsons_report.md"
    out.write_text("```\n" + "\n".join(lines) + "\n```\n", encoding="utf-8")
    pd.DataFrame(pd4).to_csv(config.RESULTS / "parkinsons_recruitment.csv", index=False)
    print(f"\nwritten -> {out}")
    figure(pd1, lad, rb, steps)


def figure(pd1, lad, rb, steps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from run_figures import save

    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), layout="constrained",
                             gridspec_kw={"width_ratios": [1.45, 1, 1]})
    # A: recording vs disease, points of tonic RWA
    ax = axes[0]
    bars = [("Later Parkinson's vs no disease\n(baseline; Postuma 2010)", POSTUMA_PD, None, "#7f7f7f"),
            ("5-year rise in RBD\n(Iranzo 2009)", IRANZO_5Y, None, "#7f7f7f")]
    for label, key, col in (("Montreal, published", "Montreal tonic, published", "#d62728"),
                            ("Montreal, floor-corrected", "Montreal tonic, FC", "#1f77b4"),
                            ("RBDtector, published", "RBDtector tonic, published", "#ff7f0e"),
                            ("RBDtector, floor-corrected", "RBDtector tonic, FC", "#17becf")):
        if ("CAP RBD", key) in pd1:
            m, lo, hi, n = pd1["CAP RBD", key]
            a, b = sorted((abs(lo), abs(hi)))
            if np.sign(lo) != np.sign(hi):           # interval includes no change
                a = 0.0
            bars.append((label, abs(m), (abs(m) - a, b - abs(m)), col))
    n_rec = len(bars) - 2                            # literature bars on top, then a gap
    y = np.r_[n_rec + 1.6, n_rec + 0.6, np.arange(n_rec)[::-1]]
    for yi, (label, v, err, col) in zip(y, bars):
        ax.barh(yi, v, color=col, height=0.6)
        if err is not None:
            ax.errorbar(v, yi, xerr=[[err[0]], [err[1]]], fmt="none", ecolor="k", lw=0.8, capsize=2)
    ax.set_yticks(y, [b[0] for b in bars], fontsize=6)
    if n_rec:
        ax.text(0.98, n_rec - 0.2, "same RBD nights, noise floor raised to HMC's (1.5 µV):",
                transform=ax.get_yaxis_transform(), fontsize=5.5, ha="right", va="center", style="italic")
    ax.set_ylim(-0.6, n_rec + 2.0)
    ax.set_xlabel("tonic RWA, percentage points")
    ax.set_title("A  Disease vs recording", fontsize=8)
    # B: RBDtector on the noise ladder
    ax = axes[1]
    if len(rb):
        lv = sel(lad, "Montreal")
        for who, col in (("CAP RBD", "#d62728"), ("CAP patients", "#7f7f7f")):
            g = rb[rb.who == who]
            st = [s for s in steps if s != "h150" and (g.step == s).any()]
            x = [lv[(lv.who == who) & (lv.step == s)].background_phasic_uV.median() for s in st]
            for variant, ls in (("published", ":"), ("FC", "-")):
                h = g[g.variant == variant]
                ax.plot(x, [100 * h[h.step == s].y.mean() for s in st], ls, marker="o", ms=2.5, lw=1,
                        color=col, label=who if variant == "FC" else None)
        ax.plot([], [], ":", color="k", lw=1, label="published")
        ax.plot([], [], "-", color="k", lw=1, label="floor-corrected")
        ax.set_xscale("log")
        ax.set_xticks([0.5, 1, 2], ["0.5", "1", "2"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.legend(frameon=False, fontsize=5.5, loc="lower left")
    ax.set_ylim(0, 100)
    ax.set_xlabel("quiet-REM level (µV)")
    ax.set_ylabel("nights flagged by RBDtector (%)")
    ax.set_title("B  RBDtector + noise", fontsize=8)
    # C: RBDtector across systems
    ax = axes[2]
    if len(rb):
        nat = rb[rb.step == "native"]
        style = {"CAP RBD": ("#d62728", "*"), "CAP patients": ("#7f7f7f", "o"), "MGH": ("#1f77b4", "o"),
                 "HMC": ("#9467bd", "o"), "BOAS": ("#2ca02c", "s")}
        for who, (col, mk) in style.items():
            g = nat[nat.who == who]
            if g.empty:
                continue
            x = g.level_1s.median()
            p, f = (100 * g[g.variant == v].y.mean() for v in ("published", "FC"))
            ax.annotate("", xy=(x, f), xytext=(x, p), arrowprops=dict(arrowstyle="->", color=col, lw=0.8))
            ax.plot(x, p, mk, color=col, mfc="white", ms=5)
            ax.plot(x, f, mk, color=col, ms=5, label=who)
        ax.set_xscale("log")
        ax.set_xticks([0.3, 0.5, 1, 2], ["0.3", "0.5", "1", "2"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.legend(frameon=False, fontsize=5.5, loc="lower left")
    ax.set_ylim(0, 100)
    ax.set_xlabel("quiet-REM level (µV)")
    ax.set_title("C  RBDtector by system", fontsize=8)
    save(fig, "fig10_parkinsons")


if __name__ == "__main__":
    main()
