"""Analyses requested by the pre-submission review (paper/revision_plan_2026-10-27.md),
specified in paper/preregistration_revision.md (R2-R4, R6) before they were computed.

From the packs (every night as recorded) and the score files of the earlier runs:

  V1  every night re-scored: published rules, floor-corrected with the pre-specified
      REM noise estimate, with the N2/N3 estimate, and with the lower of the two
  V2  Table 3 recomputed from counts (k/n, Wilson intervals)
  V3  between-site differences with 95% Newcombe intervals and TOST equivalence
      (90% interval within +/-10 and +/-5 points), all nights and in-range nights
  V4  the noise estimators: RBD sensitivity, same-system false positives, AUC
  V5  six-group rank correlations with n and exact permutation p
  V6  CAP: every night by group and recording system (105 analyzed, 88 in Table 1)
  V7  narcolepsy excluded; patients aged 50 or over
  V8  the MGH ladder on one set of nights (as recorded and every step)
  V9  AASM's continuous measures along the ladder

    python run_revision.py -> results/revision_scores.csv, results/revision_report.md
"""
import itertools
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

from src import config
from src.pack import load_pack
from run_report import MIN_REM, WITHDRAWN, wilson
from run_score import auc, group_of

COHORTS = ("cap", "chal18", "hmc", "boas", "dodh", "dodo")
NAME = {"chal18": "MGH", "hmc": "HMC", "boas": "BOAS", "dodh": "DOD-H", "dodo": "DOD-O"}
GROUPS = ["CAP RBD", "CAP patients", "MGH", "HMC", "BOAS", "DOD-O", "DOD-H"]
WITHOUT_RBD = ["CAP patients", "MGH", "HMC", "BOAS", "DOD-O", "DOD-H"]
FC_MAX_FLOOR, FC_MIN_FS = 1.69, 200.0
CUT_FC_SINBAR = 49.1
YES = (True, "True", 1, 1.0)
RULES = [("Montreal", "published"), ("Montreal", "FC"), ("Montreal", "FC-nrem"), ("Montreal", "FC-min"),
         ("SINBAR", "published"), ("SINBAR", "FC"), ("SINBAR", "FC-nrem"), ("SINBAR", "FC-min"),
         ("RAI", "published")]


# ══════════════════════════════════════════════════════════════════════════════
#  STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def newcombe(k1, n1, k2, n2, z=1.96):
    """Difference of two independent proportions with Newcombe's hybrid score
    interval (method 10)."""
    p1, l1, u1 = wilson(k1, n1, z)
    p2, l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    return d, d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def tost(k1, n1, k2, n2, margin):
    """Two one-sided tests of |p1 - p2| < margin: equivalence at 5% when the 90%
    Newcombe interval lies inside (-margin, margin); p from the Wald statistic."""
    d, lo, hi = newcombe(k1, n1, k2, n2, z=1.6449)
    p1, p2 = k1 / n1, k2 / n2
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    p = max(1 - norm.cdf((d + margin) / se), 1 - norm.cdf((margin - d) / se)) if se > 0 else np.nan
    return bool(-margin < lo and hi < margin), float(p), lo, hi


def spearman_exact(x, y):
    """Spearman's rho with an exact two-sided permutation p (small n)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    rho = spearmanr(x, y).correlation
    perms = [spearmanr(x, np.asarray(p)).correlation for p in itertools.permutations(y)]
    p = np.mean(np.abs(perms) >= abs(rho) - 1e-12)
    return float(rho), float(p), len(x)


def mcnemar_exact(b, c):
    from scipy.stats import binomtest
    return binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0


def paired_ci(a, b, n_boot=2000, seed=5):
    d = np.asarray(a, float) - np.asarray(b, float)
    rng = np.random.default_rng(seed)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n_boot)]
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


# ══════════════════════════════════════════════════════════════════════════════
#  SCORING
# ══════════════════════════════════════════════════════════════════════════════

def variants():
    import dataclasses
    from src.rwa import METHODS, floor_corrected
    out = []
    for key in ("montreal", "sinbar"):
        m = METHODS[key]
        out.append(("published", m))
        out += [("FC" if s == "rem" else f"FC-{s}", floor_corrected(m, 1.0, noise_from=s))
                for s in ("rem", "nrem", "min")]
    # Montreal phasic bursts: sources give 0.1-5 s and 0.1-10 s; the main analysis used 15 s
    for mx in (5.0, 10.0):
        m = dataclasses.replace(METHODS["montreal"], phasic_max_s=mx)
        out += [(f"published-max{mx:g}", m), (f"FC-max{mx:g}", floor_corrected(m, 1.0))]
    out.append(("published", METHODS["aasm"]))
    return out


def score_file(path):
    from run_floor import _info, scale
    from src.rwa import rem_atonia_index, score_night
    pack = load_pack(path)
    m = pack["meta"]
    info = _info(m, m.get("cohort", path.parent.name))
    info.update(scale(pack))
    rows = [{**info, **score_night(pack, meth, "native"), "variant": v} for v, meth in variants()]
    rows.append({**info, **rem_atonia_index(pack, "native"), "variant": "published"})
    return rows


def restore_packs():
    """Copy packs from Drive (MyDrive/rbd-rwa/packs) to the working disk if needed."""
    import shutil
    drive = config.DRIVE / "rbd-rwa" / "packs" if config.DRIVE else None
    for c in COHORTS:
        d = config.DURABLE / "packs" / c
        d.mkdir(parents=True, exist_ok=True)
        if drive and (drive / c).exists():
            for p in (drive / c).glob("*.npz"):
                if not (d / p.name).exists():
                    shutil.copy2(p, d / p.name)


def label(df):
    gone = {f"{c}/{r}" for c, r in WITHDRAWN}
    df = df[~(df.cohort + "/" + df.record.astype(str)).isin(gone)].copy()
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512) & df.unit_known.astype(bool)
    df["who"] = np.select([same & (df.group == "RBD"), same & ~df.group.isin(["RBD", "healthy"]),
                           cap & (df.group == "healthy")], ["CAP RBD", "CAP patients", "CAP healthy"],
                          default=df.cohort.map(NAME).fillna(""))
    df["primary"] = True
    b = df.cohort == "boas"
    if b.any():
        num = df.loc[b, "record"].astype(str).str.extract(r"(\d+)")[0].astype(int)
        pid = df.loc[b, "pid"].fillna(df.loc[b, "record"]).astype(str)
        df.loc[b, "primary"] = (num == num.groupby(pid).transform("min")).to_numpy()
    df["y"] = df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan)
    lvl = df[(df.method == "Montreal") & (df.variant == "published")] \
        .set_index(["cohort", "record"]).background_phasic_uV
    df["level"] = lvl.reindex(pd.MultiIndex.from_frame(df[["cohort", "record"]])).to_numpy()
    df["in_range"] = (df.chin_fs >= FC_MIN_FS) & (df.level <= FC_MAX_FLOOR)
    return df


def flagged(df, who, meth, variant, cut=None, in_range=False):
    g = df[(df.who == who) & (df.method == meth) & (df.variant == variant) & df.primary
           & (df.rem_minutes >= MIN_REM)]
    if in_range:
        g = g[g.in_range]
    if cut is not None:
        v = (g.any_pct >= cut).astype(float)
        return int(v.sum()), int(v.notna().sum())
    v = g.y.dropna()
    return int(v.sum()), len(v)


# ══════════════════════════════════════════════════════════════════════════════

def main():
    restore_packs()
    files = [p for c in COHORTS for p in sorted((config.DURABLE / "packs" / c).glob("*.npz"))
             if ".tmp" not in p.name]
    print(f"scoring {len(files)} packs", flush=True)
    with ProcessPoolExecutor(max_workers=2) as ex:
        rows = [r for part in ex.map(score_file, files, chunksize=8) for r in part]
    df = label(pd.DataFrame(rows))
    df.to_csv(config.RESULTS / "revision_scores.csv", index=False)
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    # V2 ─────────────────────────────────────────────────────────────────────
    say("V2  Share flagged as recorded: k/n, % [95% Wilson]")
    for who in GROUPS:
        cells = []
        for meth, variant in RULES:
            k, n = flagged(df, who, meth, variant)
            if n:
                p, lo, hi = wilson(k, n)
                cells.append(f"{meth[0]}{variant.replace('published', 'pub')} {k}/{n} {100 * p:.1f} "
                             f"[{100 * lo:.0f}-{100 * hi:.0f}]")
        k, n = flagged(df, who, "SINBAR", "FC", cut=CUT_FC_SINBAR)
        if n:
            p, lo, hi = wilson(k, n)
            cells.append(f"SFC>=49.1 {k}/{n} {100 * p:.1f} [{100 * lo:.0f}-{100 * hi:.0f}]")
        say(f"  {who}: " + ";  ".join(cells))
    say()

    # V3 ─────────────────────────────────────────────────────────────────────
    say("V3  Between-site differences, points: estimate [95% Newcombe]; TOST at +/-10 and +/-5")
    say("    (equivalent = 90% interval inside the margin); FC rows also on in-range nights only")
    say("    (>= 200 Hz and quiet-REM level <= 1.69 uV)")
    pairs = [("MGH", "HMC"), ("BOAS", "DOD-H"), ("DOD-O", "MGH"), ("CAP patients", "MGH")]
    out = []
    for a, b in pairs:
        for meth, variant in RULES + [("SINBAR", "FC>=49.1")]:
            for rng_only in ((False, True) if variant.startswith("FC") else (False,)):
                cut = CUT_FC_SINBAR if variant == "FC>=49.1" else None
                v = "FC" if cut else variant
                k1, n1 = flagged(df, a, meth, v, cut, rng_only)
                k2, n2 = flagged(df, b, meth, v, cut, rng_only)
                if not (n1 and n2):
                    continue
                d, lo, hi = newcombe(k1, n1, k2, n2)
                e10, p10, _, _ = tost(k1, n1, k2, n2, 0.10)
                e5, p5, _, _ = tost(k1, n1, k2, n2, 0.05)
                out.append(dict(pair=f"{a} - {b}", method=meth, variant=variant, in_range=rng_only,
                                n1=n1, n2=n2, diff=100 * d, lo=100 * lo, hi=100 * hi,
                                equiv10=e10, p10=p10, equiv5=e5, p5=p5))
                say(f"    {a + ' - ' + b:<20}{meth + ' ' + variant:<20}{'in-range' if rng_only else 'all':<9}"
                    f"n {n1}/{n2}  {100 * d:+5.1f} [{100 * lo:+.1f} to {100 * hi:+.1f}]  "
                    f"TOST10 {'equivalent' if e10 else 'not shown'} (p {p10:.3f})  "
                    f"TOST5 {'equivalent' if e5 else 'not shown'} (p {p5:.3f})")
    pd.DataFrame(out).to_csv(config.RESULTS / "revision_site_differences.csv", index=False)
    say("    nights outside FC's range: " + "  ".join(
        f"{w} {100 * (1 - df[(df.who == w) & df.primary & (df.method == 'Montreal') & (df.variant == 'FC') & (df.rem_minutes >= MIN_REM)].in_range.mean()):.0f}%"
        for w in GROUPS))
    say()

    # V4 ─────────────────────────────────────────────────────────────────────
    say("V4  Noise estimate of the floor-corrected rule (B = 1.0 uV): REM (pre-specified), N2/N3, lower")
    for meth in ("Montreal", "SINBAR"):
        for variant in ("published", "FC", "FC-nrem", "FC-min"):
            k1, n1 = flagged(df, "CAP RBD", meth, variant)
            k2, n2 = flagged(df, "CAP patients", meth, variant)
            g = df[(df.method == meth) & (df.variant == variant) & (df.rem_minutes >= MIN_REM)]
            measures = ["any_pct"] if meth == "SINBAR" else ["tonic_pct", "phasic_pct"]
            aucs = "  ".join(f"AUC {mm} {auc(g[g.who == 'CAP RBD'][mm], g[g.who == 'CAP patients'][mm])[0]:.2f}"
                             for mm in measures)
            say(f"    {meth + ' ' + variant:<20} RBD {k1}/{n1} ({100 * k1 / n1:.0f}%)  same-system patients "
                f"{k2}/{n2} ({100 * k2 / n2:.0f}%)  {aucs}")
    nb = df[(df.method == "Montreal") & (df.variant == "FC-nrem") & (df.rem_minutes >= MIN_REM)]
    say("    noise basis (N2/N3 quiet level) median by group: " + "  ".join(
        f"{w} {nb[nb.who == w].noise_basis_uV.median():.2f}" for w in GROUPS)
        + "   REM quiet level: " + "  ".join(
        f"{w} {nb[nb.who == w].level.median():.2f}" for w in GROUPS))
    say()

    # V5 ─────────────────────────────────────────────────────────────────────
    say("V5  Six groups without RBD: rank correlation of median floor and share flagged")
    floors = [df[(df.who == w) & df.primary & (df.method == "Montreal") & (df.variant == "published")
                 & (df.rem_minutes >= MIN_REM)].level.median() for w in WITHOUT_RBD]
    for meth, variant in RULES:
        shares = []
        for w in WITHOUT_RBD:
            k, n = flagged(df, w, meth, variant)
            shares.append(k / n if n else np.nan)
        rho, p, n = spearman_exact(floors, shares)
        say(f"    {meth + ' ' + variant:<20} rho {rho:+.2f}  exact p {p:.3f}  (n = {n} groups)")
    say()

    # V6 ─────────────────────────────────────────────────────────────────────
    say("V6  CAP nights by group and recording system (>= 10 min REM)")
    cap = df[(df.cohort == "cap") & (df.method == "Montreal") & (df.variant == "published")]
    cap = cap.assign(system=np.where(cap.unit_known.astype(bool), cap.chin_fs.map(lambda f: f"{f:g} Hz"),
                                     "no units"), scored=cap.rem_minutes >= MIN_REM)
    say(cap.pivot_table(index="group", columns="system", values="scored", aggfunc="sum",
                        fill_value=0).to_string())
    say(f"    scored in total: {int(cap.scored.sum())}")
    say()

    # V7 ─────────────────────────────────────────────────────────────────────
    say("V7  Without narcolepsy, and patients aged 50 or over (CAP's main system)")
    from src.fetch import cap_demographics
    ages = {k: v.get("age") for k, v in cap_demographics().items()}
    g = df[df.who.isin(["CAP RBD", "CAP patients"]) & (df.rem_minutes >= MIN_REM)].copy()
    g["age"] = g.record.map(ages)
    for label_, sel in (("all", g), ("no narcolepsy", g[g.group != "narcolepsy"]),
                        ("patients >= 50", g[(g.who == "CAP RBD") | (g.age >= 50)])):
        cells = []
        for meth, variant, mm in (("Montreal", "published", "tonic_pct"), ("Montreal", "published", "phasic_pct"),
                                  ("SINBAR", "published", "any_pct"), ("Montreal", "FC", "tonic_pct"),
                                  ("SINBAR", "FC", "any_pct")):
            s = sel[(sel.method == meth) & (sel.variant == variant)]
            a, n1, n0 = auc(s[s.who == "CAP RBD"][mm], s[s.who == "CAP patients"][mm])
            fp = s[s.who == "CAP patients"].y.mean()
            cells.append(f"{meth[0]}{variant[:3]} {mm[:5]} AUC {a:.2f} (FP {100 * fp:.0f}%)")
        say(f"    {label_:<15} n patients {sel[sel.who == 'CAP patients'].record.nunique():3d}  " + "; ".join(cells))
    say()

    # V8, V9 ─────────────────────────────────────────────────────────────────
    lad_path, flad_path = config.RESULTS / "ladder_scores.csv", config.RESULTS / "floor_ladder_scores.csv"
    if lad_path.exists() and flad_path.exists():
        lad = pd.read_csv(lad_path, low_memory=False)
        flad = pd.read_csv(flad_path, low_memory=False)
        mg = lad[(lad.who == "MGH")]
        rem_ok = mg.groupby("record").rem_minutes.min() >= MIN_REM
        steps_present = mg.groupby("record").step.nunique()
        nat = df[(df.who == "MGH") & (df.method == "Montreal") & (df.variant == "published")]
        nat_ok = set(nat[nat.rem_minutes >= MIN_REM].record.astype(str))
        common = sorted(set(rem_ok[rem_ok].index.astype(str)) & nat_ok
                        & set(steps_present[steps_present == steps_present.max()].index.astype(str)))
        say(f"V8  MGH ladder: {mg.record.nunique()} records; >= 10 min REM at every step: {int(rem_ok.sum())}; "
            f"in the as-recorded scores with >= 10 min REM: {len(set(mg.record.astype(str)) & nat_ok)}; "
            f"common set: {len(common)}")
        dropped = sorted(set(mg.record.astype(str)) - set(common))
        say(f"    left out: {', '.join(dropped[:20])}" + (" ..." if len(dropped) > 20 else ""))
        for name_, src, var in (("published", lad, None), ("FC", flad, "FC")):
            s = src[(src.who == "MGH") & src.record.astype(str).isin(common)]
            if var:
                s = s[(s.variant == var) & np.isclose(s.ref_uv.fillna(0), 1.0)]
            for meth in ("Montreal", "SINBAR", "RAI"):
                w = s[s.method == meth].pivot_table(index="record", columns="step", values="y")
                if "native" not in w or "h150" not in w:
                    continue
                w = w.dropna(subset=["native", "h150"])
                b_ = int(((w.native == 1) & (w.h150 == 0)).sum())
                c_ = int(((w.native == 0) & (w.h150 == 1)).sum())
                d, lo, hi = paired_ci(w.h150, w.native)
                say(f"    {meth + ' ' + name_:<18} n={len(w)}  {100 * w.native.mean():.1f}% -> {100 * w.h150.mean():.1f}% "
                    f"at h150 ({100 * d:+.1f} [{100 * lo:+.1f} to {100 * hi:+.1f}]; {b_} pos->neg, {c_} neg->pos; "
                    f"McNemar p {mcnemar_exact(b_, c_):.1e})  steps: " + "  ".join(
                        f"{st} {100 * w[st].mean():.1f}" for st in
                        ("n050", "n100", "n150", "n200", "n300", "h200") if st in w))
        say()
        say("V9  AASM along the ladder: mean tonic % and phasic-epoch % (no published cut-off)")
        a = lad[(lad.method == "AASM") & (lad.rem_minutes >= MIN_REM)]
        for who in ("CAP RBD", "CAP patients", "MGH", "HMC"):
            s = a[a.who == who]
            if s.empty:
                continue
            say(f"    {who:<13}" + "  ".join(
                f"{st} {s[s.step == st].tonic_pct.mean():.0f}/{s[s.step == st].phasic_epoch_pct.mean():.0f}"
                for st in ("native", "n050", "n100", "n150", "n200", "n300", "h150", "h200")
                if (s.step == st).any()))
        say()
    else:
        say("V8, V9: ladder score files not found in results/ (copy them from Drive)")

    say("V10 Montreal phasic bursts limited to 5 s or 10 s instead of 15 s: share flagged (%)")
    for who in GROUPS:
        cells = []
        for variant in ("published", "published-max10", "published-max5", "FC", "FC-max10", "FC-max5"):
            k, n = flagged(df, who, "Montreal", variant)
            if n:
                cells.append(f"{variant} {100 * k / n:.1f}")
        g = df[(df.who == who) & (df.method == "Montreal") & (df.rem_minutes >= MIN_REM) & df.primary]
        ph = "  ".join(f"phasic {v} {g[g.variant == v].phasic_pct.mean():.1f}"
                       for v in ("published", "published-max5") if (g.variant == v).any())
        say(f"    {who:<13} " + "  ".join(cells) + "   mean " + ph)
    say()
    (config.RESULTS / "revision_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
