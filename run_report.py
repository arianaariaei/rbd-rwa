"""Turn results/rwa_scores.csv into the paper's tables.

    python run_report.py

Prints (and writes to results/report.md):

  T1  cohort description: nights scored, REM minutes, age and sex where known
  T2  share of nights each method's published cut-off flags, per group, with
      95% Wilson intervals - sensitivity in CAP's RBD patients, false-positive
      rate everywhere else
  T3  agreement between methods on the same nights (Cohen's kappa)
  T4  what predicts a false positive in the MGH cohort: age, sex, apnea-
      hypopnea index (logistic regression, one model per method)
  T5  removing REM epochs that contain respiratory events or arousals
  T6  positive predictive value of each method if used to screen a
      population in which a given share has RBD
  T7  cut-offs re-derived for automated scoring (Youden, CAP RBD vs CAP
      patients recorded on the same system) and the external nights they flag
  T9  quiet-REM chin EMG level ("background") per group
  T10 T7 validated: leave-one-out cross-validation, and bootstrap intervals
      for the cut-offs and the external false-positive shares
  T11 positive calls by quiet-REM level within cohorts, and in MGH the odds
      ratio per halving of that level, adjusted for age, sex and AHI
  T12 simulated recordings (hardware, amplitude, noise floor) against the
      cohort they were made from, on the same nights
  T8  heartbeat artefact in the chin EMG before and after its removal

Nights with less than MIN_REM minutes of REM are left out, as clinical
scoring would.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config

MIN_REM = 10.0
DECIDING = ["Montreal", "SINBAR", "RAI"]          # methods with a published cut-off
METRICS = ["tonic_pct", "phasic_pct", "phasic_epoch_pct", "any_pct", "atonia_loss"]
# Software copies of a cohort (src/cohorts.py) and the cohort each one copies.
SIMULATED = {"hmc_q1uv": "hmc", "hmc_mgh": "hmc", "hmc_low": "hmc", "hmc_low_mgh": "hmc_low",
             "chal18_noise": "chal18"}
# Recordings withdrawn by the data providers (HMC v1.1: erroneous signal data).
# RECORDS no longer lists them; this guards against older downloads.
WITHDRAWN = {("hmc", "SN014"), ("hmc", "SN064"), ("hmc", "SN135")}


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def kappa(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    po = np.mean(a == b)
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def groups(df):
    """Label each night: CAP subgroups, and the external clinical cohorts."""
    who = np.where(df.cohort == "cap", "CAP " + df.group.astype(str), df.cohort)
    return df.assign(who=who)


def main():
    df = pd.read_csv(config.RESULTS / "rwa_scores.csv")
    df = df[~df.apply(lambda r: (r.cohort, r.record) in WITHDRAWN, axis=1)]
    df = groups(df)
    base = df[(df.excluded.fillna("") == "") & (df.rem_minutes >= MIN_REM)]
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    # T1 ─────────────────────────────────────────────────────────────────────
    nights = base.drop_duplicates(["cohort", "record"])
    say("T1  Nights scored (>= %.0f min REM)" % MIN_REM)
    t1 = nights.groupby("who").agg(nights=("record", "count"),
                                   rem_min_median=("rem_minutes", "median"),
                                   age_mean=("age", "mean"),
                                   male_pct=("sex", lambda s: 100 * (s == "M").mean()
                                             if s.notna().any() else np.nan),
                                   chin_fs=("chin_fs", "median"))
    say(t1.round(1).to_string())
    say()

    # T2 ─────────────────────────────────────────────────────────────────────
    say("T2  Share flagged POSITIVE by the published cut-off, % [95% CI]")
    rows = []
    for (band, meth, who), g in base[base.method.isin(DECIDING)].groupby(["band", "method", "who"]):
        v = g.positive.dropna().map(lambda x: float(x in (True, "True", 1, 1.0)))
        p, lo, hi = wilson(v.sum(), len(v))
        rows.append(dict(band=band, method=meth, who=who, n=len(v),
                         cell=f"{100 * p:.0f} [{100 * lo:.0f}-{100 * hi:.0f}]"))
    t2 = pd.DataFrame(rows).pivot_table(index=["band", "method"], columns="who",
                                        values="cell", aggfunc="first")
    say(t2.to_string())
    say()

    # T3 ─────────────────────────────────────────────────────────────────────
    say("T3  Agreement between methods on the same nights (Cohen's kappa, native band)")
    nat = base[(base.band == "native") & base.method.isin(DECIDING)]
    wide = nat.pivot_table(index=["who", "record"], columns="method", values="positive",
                           aggfunc="first").dropna()
    wide = wide.map(lambda x: float(x in (True, "True", 1, 1.0)))
    for who, g in wide.groupby(level="who"):
        pairs = [f"{a}-{b} {kappa(g[a], g[b]):.2f}" for i, a in enumerate(DECIDING)
                 for b in DECIDING[i + 1:] if a in g and b in g]
        disagree = (g.nunique(axis=1) > 1).mean() * 100
        say(f"  {who:<16} n={len(g):<5} {'  '.join(pairs)}   methods disagree on {disagree:.0f}% of nights")
    say()

    # T4 ─────────────────────────────────────────────────────────────────────
    mgh = base[(base.cohort == "chal18") & (base.band == "native") & base.method.isin(DECIDING)]
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        smf = None
        say("T4  skipped: statsmodels is not installed\n")
    if smf is not None and len(mgh) and mgh.age.notna().any():
        say("T4  What predicts a positive call in the MGH cohort (odds ratios [95% CI])")
        for meth, g in mgh.groupby("method"):
            g = g.dropna(subset=["positive", "age", "sex", "ahi"]).copy()
            g["y"] = g.positive.map(lambda x: float(x in (True, "True", 1, 1.0)))
            g["age10"] = g.age / 10.0
            g["male"] = (g.sex == "M").astype(float)
            g["ahi10"] = g.ahi / 10.0
            if g.y.nunique() < 2:
                say(f"  {meth}: all nights {'positive' if g.y.iloc[0] else 'negative'}")
                continue
            m = smf.logit("y ~ age10 + male + ahi10", data=g).fit(disp=False)
            ci = np.exp(m.conf_int())
            cells = [f"{k} {np.exp(m.params[k]):.2f} [{ci.loc[k, 0]:.2f}-{ci.loc[k, 1]:.2f}]"
                     for k in ("age10", "male", "ahi10")]
            say(f"  {meth:<9} n={len(g):<5} per 10 y: {cells[0].split(' ', 1)[1]}   "
                f"male: {cells[1].split(' ', 1)[1]}   per 10 AHI: {cells[2].split(' ', 1)[1]}")
        say()

    # T5 ─────────────────────────────────────────────────────────────────────
    ev = df[(df.cohort == "chal18") & (df.band == "native") & df.method.isin(DECIDING)
            & (df.rem_minutes >= MIN_REM)]
    if len(ev) and (ev.excluded.fillna("") != "").any():
        say("T5  Excluding REM epochs with respiratory events or arousals (MGH), % positive")
        w = ev.pivot_table(index=["record", "method"], columns=ev.excluded.fillna(""),
                           values="positive", aggfunc="first").dropna()
        w = w.map(lambda x: float(x in (True, "True", 1, 1.0)))
        for meth, g in w.groupby(level="method"):
            a, b = g.iloc[:, 0], g.iloc[:, 1]
            say(f"  {meth:<9} all REM {100 * a.mean():.0f}%  ->  event-free REM {100 * b.mean():.0f}%  "
                f"(changed on {100 * (a != b).mean():.0f}% of nights)")
        say()

    # T6 ─────────────────────────────────────────────────────────────────────
    say("T6  Screening: positive predictive value at a given RBD prevalence")
    say("    sensitivity from CAP RBD; specificity from the pooled external cohorts")
    for meth in DECIDING:
        g = base[(base.band == "native") & (base.method == meth)]
        y = lambda s: s.dropna().map(lambda x: float(x in (True, "True", 1, 1.0)))
        sens = y(g[g.who == "CAP RBD"].positive)
        spec = 1 - y(g[g.cohort.isin(["chal18", "hmc"])].positive)
        if len(sens) == 0 or len(spec) == 0:
            continue
        se, sp = sens.mean(), spec.mean()
        ppv = [se * p / (se * p + (1 - sp) * (1 - p)) for p in (0.01, 0.02, 0.05, 0.10)]
        say(f"  {meth:<9} sens {100 * se:.0f}%  spec {100 * sp:.0f}%   PPV at 1/2/5/10% prevalence: "
            + " / ".join(f"{100 * v:.0f}%" for v in ppv))

    say()

    # T7 ─────────────────────────────────────────────────────────────────────
    say("T7  Cut-offs re-derived for automated scoring (Youden, CAP RBD vs same-system")
    say("    patients) and the share of external nights they flag, native band")
    for (meth, metric), g in base[base.band == "native"].melt(
            id_vars=["cohort", "record", "who", "method", "chin_fs", "unit_known"],
            value_vars=[m for m in METRICS if m in base], var_name="metric") \
            .dropna(subset=["value"]).groupby(["method", "metric"]):
        s = (g.cohort == "cap") & (g.chin_fs == 512) & g.unit_known.astype(bool)
        pos = g.loc[s & (g.who == "CAP RBD"), "value"].to_numpy()
        neg = g.loc[s & ~g.who.isin(["CAP RBD", "CAP healthy"]), "value"].to_numpy()
        if len(pos) < 5 or len(neg) < 5:
            continue
        cands = np.unique(np.r_[pos, neg])
        j = [(pos >= c).mean() - (neg >= c).mean() for c in cands]
        c = cands[int(np.argmax(j))]
        ext = g.loc[g.cohort.isin(["chal18", "hmc"])]
        fp = {k: 100 * (v.value >= c).mean() for k, v in ext.groupby("cohort")}
        say(f"  {meth:<9} {metric:<17} cut-off {c:7.2f}: sens {100 * (pos >= c).mean():3.0f}%  "
            f"same-system FP {100 * (neg >= c).mean():3.0f}%  "
            + "  ".join(f"{k} FP {v:3.0f}%" for k, v in sorted(fp.items())))
    say()

    # T9 ─────────────────────────────────────────────────────────────────────
    say("T9  Background chin EMG level (5th percentile of 1 s REM RMS, uV), median [IQR]")
    bg = base[(base.band == "native") & (base.method == "Montreal")]
    if "background_phasic_uV" in bg:
        for who, g in bg.groupby("who"):
            v = g.background_phasic_uV.dropna()
            if len(v):
                say(f"  {who:<16} n={len(v):<5} {v.median():6.2f} [{v.quantile(.25):.2f}-{v.quantile(.75):.2f}]")
    say()

    # T10 ────────────────────────────────────────────────────────────────────
    say("T10 Re-derived cut-offs, validated: leave-one-out CV on CAP, and 2,000 bootstrap")
    say("    re-derivations for the uncertainty of the cut-off and of external false positives")
    rng = np.random.default_rng(0)

    def youden(p, n):
        c = np.unique(np.r_[p, n])
        j = (p[None, :] >= c[:, None]).mean(axis=1) - (n[None, :] >= c[:, None]).mean(axis=1)
        return c[int(np.argmax(j))]

    melted = base[base.band == "native"].melt(
        id_vars=["cohort", "record", "who", "method", "chin_fs", "unit_known"],
        value_vars=[m for m in METRICS if m in base], var_name="metric").dropna(subset=["value"])
    for (meth, metric), g in melted.groupby(["method", "metric"]):
        s = (g.cohort == "cap") & (g.chin_fs == 512) & g.unit_known.astype(bool)
        pos = g.loc[s & (g.who == "CAP RBD"), "value"].to_numpy(float)
        neg = g.loc[s & ~g.who.isin(["CAP RBD", "CAP healthy"]), "value"].to_numpy(float)
        if len(pos) < 5 or len(neg) < 5:
            continue
        cv_tp = np.mean([pos[i] >= youden(np.delete(pos, i), neg) for i in range(len(pos))])
        cv_fp = np.mean([neg[i] >= youden(pos, np.delete(neg, i)) for i in range(len(neg))])
        ext = {k: v.value.to_numpy(float) for k, v in g[g.cohort.isin(["chal18", "hmc"])].groupby("cohort")}
        cuts, fps = [], {k: [] for k in ext}
        for _ in range(2000):
            c = youden(rng.choice(pos, len(pos)), rng.choice(neg, len(neg)))
            cuts.append(c)
            for k, v in ext.items():
                fps[k].append((v >= c).mean())
        q = lambda a: f"{100 * np.median(a):.0f} [{100 * np.percentile(a, 2.5):.0f}-{100 * np.percentile(a, 97.5):.0f}]"
        say(f"  {meth:<9} {metric:<17} cut-off {np.median(cuts):6.2f} [{np.percentile(cuts, 2.5):.2f}-"
            f"{np.percentile(cuts, 97.5):.2f}]  CV sens {100 * cv_tp:3.0f}%  CV FP {100 * cv_fp:3.0f}%  "
            + "  ".join(f"{k} FP {q(v)}" for k, v in sorted(fps.items())))
    say()

    # T11 ────────────────────────────────────────────────────────────────────
    say("T11 Positive calls by quiet-REM level (tertiles of the background within each")
    say("    cohort, native band) and, in MGH, the odds ratio per halving of that level")
    quiet = base[(base.band == "native") & (base.method == "Montreal")][
        ["cohort", "record", "background_phasic_uV"]].rename(columns={"background_phasic_uV": "quiet"})
    nat = base[(base.band == "native") & base.method.isin(DECIDING)].merge(
        quiet, on=["cohort", "record"], how="left").dropna(subset=["quiet", "positive"])
    nat["y"] = nat.positive.map(lambda x: float(x in (True, "True", 1, 1.0)))
    for (who, meth), g in nat[nat.cohort.isin(["chal18", "hmc"])].groupby(["who", "method"]):
        t = pd.qcut(g["quiet"], 3, labels=False)
        say(f"  {who:<8} {meth:<9} " + "   ".join(
            f"{g['quiet'][t == k].median():.2f} uV: {100 * g.y[t == k].mean():3.0f}%" for k in range(3)))
    if smf is not None:
        for meth, g in nat[nat.cohort == "chal18"].groupby("method"):
            g = g.dropna(subset=["age", "sex", "ahi"]).copy()
            if g.y.nunique() < 2:
                continue
            g["halvings"] = -np.log2(g["quiet"])
            g["age10"], g["male"], g["ahi10"] = g.age / 10.0, (g.sex == "M").astype(float), g.ahi / 10.0
            m = smf.logit("y ~ halvings + age10 + male + ahi10", data=g).fit(disp=False)
            lo, hi = np.exp(m.conf_int().loc["halvings"])
            say(f"  MGH {meth:<9} OR per halving {np.exp(m.params['halvings']):.2f} [{lo:.2f}-{hi:.2f}]"
                f" adjusted for age, sex and AHI (n={len(g)})")
    say()

    # T12 ────────────────────────────────────────────────────────────────────
    say("T12 Simulated recordings against their source on the same nights (native band)")
    for sim, src in SIMULATED.items():
        pair = nat[nat.cohort == sim].merge(nat[nat.cohort == src], on=["record", "method"],
                                            suffixes=("", "_src"))
        if pair.empty:
            continue
        lvl = pair[pair.method == "Montreal"]
        cells = [f"{meth} {100 * g.y_src.mean():.0f}% -> {100 * g.y.mean():.0f}%"
                 for meth, g in pair.groupby("method")]
        say(f"  {sim:<12} vs {src:<8} n={len(lvl):<4} level {lvl.quiet_src.median():.2f} -> "
            f"{lvl.quiet.median():.2f} uV   " + "   ".join(cells))
    say()

    # T8 ─────────────────────────────────────────────────────────────────────
    say("T8  Heartbeat artefact in chin EMG (heartbeat-locked ratio; 1 = none), median [p90]")
    import json
    for cdir in sorted((config.DURABLE / "packs").glob("*")):
        before, after = [], []
        for p in cdir.glob("*.npz"):
            try:
                meta = json.loads(str(np.load(p)["meta"]))
            except Exception:
                continue
            e = meta.get("ecg") or meta.get("chin_info", {}).get("ecg") or {}
            if e.get("beats"):
                before.append(e.get("artifact_ratio_before", np.nan))
                after.append(e.get("artifact_ratio_after", np.nan))
        if before:
            b, a = np.array(before, float), np.array(after, float)
            say(f"  {cdir.name:<7} n={len(b):<5} before {np.nanmedian(b):.2f} [{np.nanpercentile(b, 90):.2f}]"
                f"   after {np.nanmedian(a):.2f} [{np.nanpercentile(a, 90):.2f}]")

    out = config.RESULTS / "report.md"
    out.write_text("```\n" + "\n".join(lines) + "\n```\n", encoding="utf-8")
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
