"""The injection experiment, against the criteria fixed in paper/preregistration_injection.md.

  I1  nights and floors by recording system
  I2  detection thresholds (A50) of synthetic activity against the floor: slopes (A1, A2)
  I3  thresholds by recording system (A3)
  I4  real backgrounds against white noise (A4)
  I5  transplanted RBD activity: sensitivity by system (B1, B3)
  I6  transplanted RBD activity against the white-noise ladder (B2)
  I7  the same RBD activity measured on different systems, paired by donor (B4)
  I8  secondary: night-level dose-response, every measure, the donors' own nights

    python run_inject_report.py -> results/inject_a50.csv, inject_transplant.csv,
                                   inject_report.md, figures/fig11_injection
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.inject import AMPLITUDES_UV, MEASURES, PRIMARY, a50_table, load_donor
from run_report import MIN_REM, WITHDRAWN, wilson
from run_score import group_of

COHORTS = ("cap", "chal18", "hmc", "boas", "dodh", "dodo")
NAME = {"chal18": "MGH", "hmc": "HMC", "boas": "BOAS", "dodh": "DOD-H", "dodo": "DOD-O"}
SYSTEMS = ["CAP patients", "MGH", "HMC", "BOAS", "DOD-H", "DOD-O"]
FC_MAX_FLOOR, FC_MIN_FS = 1.69, 200.0
DECIDING = [("Montreal", "published"), ("Montreal", "FC"), ("SINBAR", "published"),
            ("SINBAR", "FC"), ("RAI", "published")]
YES = (True, "True", 1, 1.0)
N_BOOT = 2000


# ══════════════════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════════════════

def load():
    files = [p for c in COHORTS for p in sorted((config.DURABLE / "inject" / c).glob("*.csv.gz"))
             if ".tmp" not in p.name]
    print(f"reading {len(files)} nights", flush=True)
    df = pd.concat((pd.read_csv(p, low_memory=False) for p in files), ignore_index=True)
    gone = {f"{c}/{r}" for c, r in WITHDRAWN}
    df = df[~(df.cohort + "/" + df.record.astype(str)).isin(gone)].copy()
    df["group"] = [group_of(c, r) for c, r in zip(df.cohort, df.record)]
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512) & df.unit_known.astype(bool)
    df["who"] = np.select([same & ~df.group.isin(["RBD", "healthy"]), cap & (df.group == "healthy")],
                          ["CAP patients", "CAP healthy"], default=df.cohort.map(NAME).fillna(""))
    # BOAS: a participant's first night is primary (as in run_external.py)
    df["primary"] = True
    b = df.cohort == "boas"
    if b.any():
        num = df.loc[b, "record"].astype(str).str.extract(r"(\d+)")[0].astype(int)
        pid = df.loc[b, "pid"].fillna(df.loc[b, "record"]).astype(str) if "pid" in df \
            else df.loc[b, "record"].astype(str)
        df.loc[b, "primary"] = (num == num.groupby(pid).transform("min")).to_numpy()
    df["y"] = df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan)
    return df


def nights(df):
    """One row per night: system, rate, floor (quiet-REM level as recorded), REM."""
    n = df[df.pattern == "none"].drop_duplicates(["cohort", "record"])
    return n[["cohort", "record", "who", "group", "primary", "chin_fs", "unit_known",
              "rem_minutes", "level_uv", "beats"] + [c for c in ("age", "sex") if c in n]] \
        .reset_index(drop=True)


def fc_valid(fs, level):
    return (np.asarray(fs, float) >= FC_MIN_FS) & (np.asarray(level, float) <= FC_MAX_FLOOR)


def loglog_interp(x, xp, fp):
    """Piecewise-linear interpolation in log-log, extrapolated with the end slopes."""
    lx, lxp, lfp = np.log(np.asarray(x, float)), np.log(xp), np.log(fp)
    y = np.interp(lx, lxp, lfp)
    lo, hi = lx < lxp[0], lx > lxp[-1]
    s0 = (lfp[1] - lfp[0]) / (lxp[1] - lxp[0])
    s1 = (lfp[-1] - lfp[-2]) / (lxp[-1] - lxp[-2])
    y[lo] = lfp[0] + s0 * (lx[lo] - lxp[0])
    y[hi] = lfp[-1] + s1 * (lx[hi] - lxp[-1])
    return np.exp(y)


def slope_ci(x, y, seed=1):
    """OLS slope of log y on log x, with a 95% bootstrap interval over nights."""
    lx, ly = np.log(np.asarray(x, float)), np.log(np.asarray(y, float))
    if len(lx) < 5:
        return np.nan, np.nan, np.nan
    s = np.polyfit(lx, ly, 1)[0]
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(lx), len(lx))
        if np.ptp(lx[i]) > 0:
            boots.append(np.polyfit(lx[i], ly[i], 1)[0])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(s), float(lo), float(hi)


def share(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    p, lo, hi = wilson(v.sum(), len(v))
    return p, lo, hi, len(v)


def fmt_share(v):
    p, lo, hi, n = share(v)
    return f"{100 * p:3.0f} [{100 * lo:.0f}-{100 * hi:.0f}] (n={n})" if n else "-"


def donor_boot(t, value, systems, seed=2):
    """Bootstrap over donors: resample the 21 donors, recompute `value(sub)` (a dict
    system -> number) on the hybrids of the resampled donors."""
    rng = np.random.default_rng(seed)
    donors = np.array(sorted(t.donor.dropna().unique()))
    by = {d: t[t.donor == d] for d in donors}
    out = []
    for _ in range(N_BOOT):
        pick = rng.choice(donors, len(donors), replace=True)
        out.append(value(pd.concat([by[d] for d in pick], ignore_index=True)))
    return pd.DataFrame(out)


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    df = load()
    df = df[df.unit_known.astype(bool)]
    nt = nights(df)
    keep = nt[(nt.rem_minutes >= MIN_REM)][["cohort", "record"]]
    df = df.merge(keep, on=["cohort", "record"])
    nt = nights(df)
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    verdict = {}

    # I1 ─────────────────────────────────────────────────────────────────────
    say("I1  Nights (>= 10 min REM, units known) and quiet-REM level as recorded (µV)")
    for who in SYSTEMS + ["CAP healthy"]:
        g = nt[(nt.who == who) & nt.primary]
        if g.empty:
            continue
        say(f"    {who:<13} n={len(g):4d}  rate {'/'.join(f'{f:g}' for f in sorted(g.chin_fs.unique()))} Hz"
            f"  floor median {g.level_uv.median():.2f} [IQR {g.level_uv.quantile(.25):.2f}-"
            f"{g.level_uv.quantile(.75):.2f}]  FC-valid {fc_valid(g.chin_fs, g.level_uv).mean():.0%}"
            f"  REM {g.rem_minutes.median():.0f} min")
    say()

    # A50 per night ──────────────────────────────────────────────────────────
    a = a50_table(df)
    a = a.merge(nt, on=["cohort", "record"])
    a.to_csv(config.RESULTS / "inject_a50.csv", index=False)
    main_ = a[a.who.isin(SYSTEMS) & a.primary & (a.chin_fs >= FC_MIN_FS)]

    # I2 ─────────────────────────────────────────────────────────────────────
    say("I2  Detection threshold A50 (µV) against the floor: log-log slope over nights")
    say("    (six systems, >= 200 Hz; FC also floor <= 1.69 uV; A50 not censored)")
    say("    criteria A1: published slope 0.75-1.25;  A2: FC slope -0.25 to +0.25")
    for meth, measure, pattern in MEASURES:
        for variant in ("published", "FC"):
            g = main_[(main_.method == meth) & (main_.measure == measure) &
                      (main_.pattern == pattern) & (main_.variant == variant)]
            if variant == "FC":
                g = g[fc_valid(g.chin_fs, g.level_uv)]
            ok = g[(g.censored == 0) & np.isfinite(g.a50) & (g.level_uv > 0)]
            s, lo, hi = slope_ci(ok.level_uv, ok.a50)
            cens = f"censored {(g.censored != 0).sum()} of {len(g)}"
            tag = ""
            if (meth, measure, pattern) in PRIMARY:
                key = ("A1 " if variant == "published" else "A2 ") + f"{meth} {measure}"
                verdict[key] = (0.75 <= s <= 1.25) if variant == "published" else (-0.25 <= s <= 0.25)
                tag = f"  -> {'met' if verdict[key] else 'NOT met'}"
            say(f"    {meth:<9}{measure:<7}({pattern:<6}) {variant:<10} slope {s:5.2f} "
                f"[{lo:5.2f} to {hi:5.2f}]  n={len(ok)}  {cens}{tag}")
    say()

    # I3 ─────────────────────────────────────────────────────────────────────
    say("I3  Median A50 (µV) by system (censored values at the grid's ends);")
    say("    criterion A3: highest/lowest system median >= 2.5 published, <= 1.3 FC")
    say(f"    {'':<34}" + "".join(f"{w:<13}" for w in SYSTEMS) + "max/min")
    for meth, measure, pattern in PRIMARY:
        for variant in ("published", "FC"):
            g = main_[(main_.method == meth) & (main_.measure == measure) &
                      (main_.pattern == pattern) & (main_.variant == variant)]
            if variant == "FC":
                g = g[fc_valid(g.chin_fs, g.level_uv)]
            med = {w: g[g.who == w].a50.median() for w in SYSTEMS if (g.who == w).any()}
            ratio = max(med.values()) / min(med.values()) if med else np.nan
            key = f"A3 {meth} {measure} {variant}"
            verdict[key] = ratio >= 2.5 if variant == "published" else ratio <= 1.3
            say(f"    {meth + ' ' + measure + ' ' + variant:<34}" +
                "".join(f"{med.get(w, np.nan):<13.2f}" for w in SYSTEMS) +
                f"{ratio:.2f} -> {'met' if verdict[key] else 'NOT met'}")
    say()

    # I4 ─────────────────────────────────────────────────────────────────────
    say("I4  Real backgrounds against white noise: A50 / white-noise A50 at the night's floor")
    say("    criterion A4: within 0.75-1.25 in >= 80% of nights (censored nights count as outside)")
    wn_path = config.RESULTS / "inject_whitenoise_a50.csv"
    if wn_path.exists():
        wn = pd.read_csv(wn_path)
        rates = np.array(sorted(wn.sim_fs.unique()), float)
        rows = []
        for meth, measure, pattern in PRIMARY:
            for variant in ("published", "FC"):
                g = main_[(main_.method == meth) & (main_.measure == measure) &
                          (main_.pattern == pattern) & (main_.variant == variant)].copy()
                if variant == "FC":
                    g = g[fc_valid(g.chin_fs, g.level_uv)]
                w = wn[(wn.method == meth) & (wn.measure == measure) & (wn.pattern == pattern) &
                       (wn.variant == variant) & (wn.censored == 0)]
                pred = np.full(len(g), np.nan)
                for fs in g.chin_fs.unique():
                    near = rates[np.argmin(np.abs(rates - fs))]
                    c = w[w.sim_fs == near].groupby("sim_floor_uv")[["level_uv", "a50"]].mean()
                    m = (g.chin_fs == fs).to_numpy()
                    pred[m] = loglog_interp(g.level_uv[m], c.level_uv.to_numpy(), c.a50.to_numpy())
                g["ratio"] = g.a50 / pred
                inside = (g.censored == 0) & g.ratio.between(0.75, 1.25)
                key = f"A4 {meth} {measure} {variant}"
                verdict[key] = inside.mean() >= 0.80
                by = "  ".join(f"{s} {g[g.who == s].ratio.median():.2f}" for s in SYSTEMS
                               if (g.who == s).any())
                say(f"    {meth + ' ' + measure + ' ' + variant:<34} within {100 * inside.mean():3.0f}% "
                    f"-> {'met' if verdict[key] else 'NOT met'};  median ratio {by}")
                rows.append(g.assign(wn_a50=pred))
        pd.concat(rows).to_csv(config.RESULTS / "inject_a50_vs_whitenoise.csv", index=False)
    else:
        say("    results/inject_whitenoise_a50.csv missing: run sim_injection.py first")
    say()

    # Transplant ─────────────────────────────────────────────────────────────
    t = df[(df.pattern == "transplant") & df.who.isin(SYSTEMS + ["CAP healthy"]) & df.primary].copy()
    lvl = t[(t.method == "Montreal") & (t.variant == "published")] \
        .set_index(["cohort", "record", "amp_uv"]).background_phasic_uV
    t["hybrid_level"] = lvl.reindex(pd.MultiIndex.from_frame(t[["cohort", "record", "amp_uv"]])).to_numpy()
    t["fc_ok"] = fc_valid(t.chin_fs, t.hybrid_level)
    t.to_csv(config.RESULTS / "inject_transplant.csv", index=False)
    nat = df[(df.pattern == "none") & df.who.isin(SYSTEMS) & df.primary]
    donors = {}
    for p in sorted((config.DURABLE / "inject" / "donors").glob("*.npz")):
        if ".tmp" not in p.name:
            d = load_donor(p)
            donors[d["record"]] = d
    say(f"I5  Transplanted RBD activity ({len(donors)} donors from CAP's main system):")
    say("    share of hybrid nights flagged, % [95% CI]; native = the same nights as recorded")
    if not t.empty:
        for c in sorted(t.amp_uv.unique(), reverse=True):
            say(f"  donor activity x{c:g}; hybrid floor median by system: " + "  ".join(
                f"{w} {t[(t.who == w) & (t.amp_uv == c)].hybrid_level.median():.2f}"
                for w in SYSTEMS if (t.who == w).any()))
            for meth, variant in DECIDING:
                g = t[(t.amp_uv == c) & (t.method == meth) & (t.variant == variant)]
                if variant == "FC":
                    g = g[g.fc_ok]
                cells = "  ".join(f"{w} {fmt_share(g[g.who == w].y)}" for w in SYSTEMS
                                  if (g.who == w).any())
                say(f"    {meth + ' ' + variant:<20} {cells}")
        if donors:
            own = pd.DataFrame([{"donor": k, **{f"{m}": v.get("positive") for m, v in d["own"].items()}}
                                for k, d in donors.items()])
            say("    the donors' own nights on CAP (as recorded): " + "  ".join(
                f"{col} {100 * own[col].map(lambda x: float(x in YES)).mean():.0f}%"
                for col in ("Montreal/published", "Montreal/FC", "SINBAR/published",
                            "SINBAR/FC", "RAI/published") if col in own))
        say("    native (no donor) share flagged: " + "  ".join(
            f"{meth} {variant}: " + ", ".join(
                f"{w} {100 * nat[(nat.who == w) & (nat.method == meth) & (nat.variant == variant)].y.mean():.0f}"
                for w in SYSTEMS if (nat.who == w).any())
            for meth, variant in DECIDING[:4]))

        # B1: published Montreal, full amplitude, BOAS minus HMC
        def sens(sub, meth, variant, c):
            g = sub[(sub.amp_uv == c) & (sub.method == meth) & (sub.variant == variant)]
            if variant == "FC":
                g = g[g.fc_ok]
            return {w: 100 * g[g.who == w].y.mean() for w in SYSTEMS if (g.who == w).any()}
        s1 = sens(t, "Montreal", "published", 1.0)
        if "BOAS" in s1 and "HMC" in s1:
            bt = donor_boot(t, lambda sub: sens(sub, "Montreal", "published", 1.0), SYSTEMS)
            d = bt["BOAS"] - bt["HMC"]
            diff = s1["BOAS"] - s1["HMC"]
            verdict["B1"] = diff >= 20
            say(f"  B1 Montreal published, full amplitude: BOAS {s1['BOAS']:.0f}% - HMC {s1['HMC']:.0f}% = "
                f"{diff:+.1f} points [donor bootstrap {np.nanpercentile(d, 2.5):+.1f} to "
                f"{np.nanpercentile(d, 97.5):+.1f}] (criterion >= 20) -> {'met' if verdict['B1'] else 'NOT met'}")
        # B3: half amplitude, HMC minus BOAS (FC: hybrids within its range only)
        for meth, variant in (("Montreal", "published"), ("Montreal", "FC"), ("SINBAR", "FC")):
            s = sens(t, meth, variant, 0.5)
            if "BOAS" in s and "HMC" in s:
                bt = donor_boot(t, lambda sub: sens(sub, meth, variant, 0.5), SYSTEMS)
                d = bt["HMC"] - bt["BOAS"]
                diff = s["HMC"] - s["BOAS"]
                key = f"B3 {meth} {variant}"
                verdict[key] = diff <= -20 if variant == "published" else abs(diff) <= 10
                say(f"  B3 {meth} {variant}, half amplitude: HMC {s['HMC']:.0f}% - BOAS {s['BOAS']:.0f}% = "
                    f"{diff:+.1f} points [donor bootstrap {np.nanpercentile(d, 2.5):+.1f} to "
                    f"{np.nanpercentile(d, 97.5):+.1f}] (criterion "
                    f"{'<= -20' if variant == 'published' else 'within +/-10'}) -> "
                    f"{'met' if verdict[key] else 'NOT met'};  range over all systems "
                    f"{max(s.values()) - min(s.values()):.0f} points")
    say()

    # I6 ─────────────────────────────────────────────────────────────────────
    say("I6  Transplanted RBD against the white-noise ladder (same donors, published Montreal tonic %,")
    say("    full amplitude): hybrid minus the donor's ladder value at the hybrid's floor;")
    say("    criterion B2: |median| <= 10 points in each system")
    lad_path = config.RESULTS / "ladder_scores.csv"
    if lad_path.exists() and not t.empty:
        lad = pd.read_csv(lad_path, low_memory=False)
        lad = lad[(lad.cohort == "cap") & (lad.method == "Montreal") & lad.record.isin(donors.keys())]
        curves = {}
        for rec, g in lad.groupby("record"):
            g = g.dropna(subset=["level", "tonic_pct"]).sort_values("level")
            g = g.drop_duplicates("level")
            if len(g) >= 3:
                curves[rec] = (np.log(g.level.to_numpy(float)), g.tonic_pct.to_numpy(float))
        h = t[(t.amp_uv == 1.0) & (t.method == "Montreal") & (t.variant == "published")].copy()
        h["ladder_tonic"] = [np.interp(np.log(l), *curves[dn]) if dn in curves and l > 0 else np.nan
                             for dn, l in zip(h.donor, h.hybrid_level)]
        h["diff"] = h.tonic_pct - h.ladder_tonic
        oks = []
        for w in SYSTEMS:
            g = h[h.who == w].dropna(subset=["diff"])
            if g.empty:
                continue
            med = g["diff"].median()
            oks.append(abs(med) <= 10)
            say(f"    {w:<13} median {med:+5.1f} points [IQR {g['diff'].quantile(.25):+.1f} to "
                f"{g['diff'].quantile(.75):+.1f}]  n={len(g)}")
        verdict["B2"] = bool(oks) and all(oks)
        say(f"    -> {'met' if verdict['B2'] else 'NOT met'}")
        h.to_csv(config.RESULTS / "inject_transplant_vs_ladder.csv", index=False)
    else:
        say("    results/ladder_scores.csv missing: not evaluated")
    say()

    # I7 ─────────────────────────────────────────────────────────────────────
    say("I7  The same RBD activity on different systems: Montreal tonic %, mean per donor, HMC minus")
    say("    BOAS (paired by donor); criterion B4 (half amplitude): published <= -10, FC within +/-5")
    if not t.empty:
        for c in sorted(t.amp_uv.unique(), reverse=True):
            for variant in ("published", "FC"):
                g = t[(t.amp_uv == c) & (t.method == "Montreal") & (t.variant == variant)]
                if variant == "FC":
                    g = g[g.fc_ok]
                per = g.groupby(["donor", "who"]).tonic_pct.mean().unstack()
                if not {"HMC", "BOAS"} <= set(per.columns):
                    continue
                dd = (per["HMC"] - per["BOAS"]).dropna()
                if dd.empty:
                    continue
                rng = np.random.default_rng(3)
                boots = [rng.choice(dd.to_numpy(), len(dd)).mean() for _ in range(N_BOOT)]
                line = (f"    x{c:g} {variant:<10} HMC - BOAS {dd.mean():+5.1f} points "
                        f"[{np.percentile(boots, 2.5):+.1f} to {np.percentile(boots, 97.5):+.1f}], "
                        f"{len(dd)} donors;  by system: " + "  ".join(
                            f"{w} {per[w].mean():.1f}" for w in SYSTEMS if w in per))
                if c == 0.5:
                    key = f"B4 {variant}"
                    verdict[key] = dd.mean() <= -10 if variant == "published" else abs(dd.mean()) <= 5
                    line += f" -> {'met' if verdict[key] else 'NOT met'}"
                say(line)
    say()

    # I8 ─────────────────────────────────────────────────────────────────────
    say("I8  Secondary: share of nights flagged as injected activity grows (night-level dose-response),")
    say("    amplitude at which half of a system's nights are flagged (µV), by pattern")
    syn = df[df.pattern.isin(["tonic", "phasic"]) & df.who.isin(SYSTEMS) & df.primary]
    dose = (syn.groupby(["pattern", "method", "variant", "who", "amp_uv"]).y.mean()
            .rename("share").reset_index())
    dose.to_csv(config.RESULTS / "inject_dose_response.csv", index=False)
    for pattern in ("tonic", "phasic"):
        for meth, variant in DECIDING:
            cells = []
            for w in SYSTEMS:
                g = dose[(dose.pattern == pattern) & (dose.method == meth) &
                         (dose.variant == variant) & (dose.who == w)].sort_values("amp_uv")
                if g.empty:
                    continue
                hit = g[g.share >= 0.5]
                cells.append(f"{w} " + ("-" if hit.empty else
                                        ("<=0.25" if hit.amp_uv.iloc[0] == g.amp_uv.iloc[0]
                                         else f"{hit.amp_uv.iloc[0]:.2f}")))
            say(f"    {pattern:<7}{meth + ' ' + variant:<20} " + "  ".join(cells))
    say()

    say("VERDICTS")
    for k, v in verdict.items():
        say(f"    {k:<32} {'met' if v else 'NOT met'}")
    (config.RESULTS / "inject_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (config.RESULTS / "inject_verdicts.json").write_text(json.dumps(
        {k: bool(v) for k, v in verdict.items()}, indent=1))
    try:
        figure(a, t, dose)
    except Exception as e:                       # the numbers matter more than the figure
        print(f"figure failed: {type(e).__name__}: {e}", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FIGURE
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {"CAP patients": "#1b9e77", "MGH": "#d95f02", "HMC": "#7570b3", "BOAS": "#e7298a",
          "DOD-H": "#66a61e", "DOD-O": "#e6ab02"}


def figure(a, t, dose):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    shown = (0.3, 0.4, 0.6, 0.8, 1, 1.5, 2, 3, 4, 6, 8, 10, 15)
    plain = FuncFormatter(lambda v, _: f"{v:g}" if any(np.isclose(v, t) for t in shown) else "")
    fig, ax = plt.subplots(2, 2, figsize=(11, 9))
    wn_path = config.RESULTS / "inject_whitenoise_a50.csv"
    wn = pd.read_csv(wn_path) if wn_path.exists() else None
    for k, (meth, measure, pattern, title) in enumerate(
            [("Montreal", "tonic", "tonic", "A  Montreal tonic (20-s epochs)"),
             ("SINBAR", "any", "phasic", "B  SINBAR \"any\" (3-s mini-epochs)")]):
        axk = ax[0, k]
        for variant, marker in (("published", "o"), ("FC", "s")):
            g = a[(a.method == meth) & (a.measure == measure) & (a.pattern == pattern) &
                  (a.variant == variant) & a.who.isin(SYSTEMS) & a.primary &
                  (a.chin_fs >= FC_MIN_FS) & (a.censored == 0)]
            if variant == "FC":
                g = g[fc_valid(g.chin_fs, g.level_uv)]
            for w in SYSTEMS:
                s = g[g.who == w]
                axk.scatter(s.level_uv, s.a50, s=9, marker=marker, alpha=0.45,
                            facecolors=COLORS[w] if variant == "FC" else "none",
                            edgecolors=COLORS[w], linewidths=0.6,
                            label=w if variant == "published" else None)
            if wn is not None:
                c = wn[(wn.method == meth) & (wn.measure == measure) & (wn.pattern == pattern) &
                       (wn.variant == variant) & (wn.sim_fs == 256)].groupby("sim_floor_uv")[
                    ["level_uv", "a50"]].mean()
                if variant == "FC":
                    c = c[c.level_uv <= FC_MAX_FLOOR]
                axk.plot(c.level_uv, c.a50, color="k", lw=1.4,
                         ls="-" if variant == "published" else "--",
                         label=f"white noise, {'published' if variant == 'published' else 'floor-corrected'}")
        axk.set_xscale("log")
        axk.set_yscale("log")
        for axis in (axk.xaxis, axk.yaxis):
            axis.set_major_formatter(plain)
            axis.set_minor_formatter(plain)
        axk.set_xlabel("quiet-REM level of the night as recorded (µV)")
        axk.set_ylabel("amplitude detected in half of injected units, A50 (µV)")
        axk.set_title(title + "\nopen = published, filled = floor-corrected", fontsize=10)
        axk.legend(fontsize=7, loc="upper left")
    # C: transplant sensitivity
    axc = ax[1, 0]
    if not t.empty:
        xs = np.arange(len(SYSTEMS))
        for j, (c, variant, color, off) in enumerate(
                [(1.0, "published", "#444444", -0.27), (1.0, "FC", "#1f78b4", -0.09),
                 (0.5, "published", "#999999", 0.09), (0.5, "FC", "#a6cee3", 0.27)]):
            for i, w in enumerate(SYSTEMS):
                g = t[(t.amp_uv == c) & (t.method == "Montreal") & (t.variant == variant) & (t.who == w)]
                if variant == "FC":
                    g = g[g.fc_ok]
                if g.empty:
                    continue
                p, lo, hi, n = share(g.y)
                axc.errorbar(i + off, 100 * p, yerr=[[100 * (p - lo)], [100 * (hi - p)]], fmt="o",
                             color=color, ms=5, capsize=2,
                             label=f"x{c:g} {'published' if variant == 'published' else 'floor-corrected'}"
                             if i == 0 else None)
        axc.set_xticks(xs)
        axc.set_xticklabels(SYSTEMS, fontsize=8)
        axc.set_ylim(0, 105)
        axc.set_ylabel("hybrid nights flagged by the Montreal criteria (%)")
        axc.set_title("C  RBD activity of 21 CAP patients added to each system's nights", fontsize=10)
        axc.legend(fontsize=7, loc="lower left")
    # D: dose-response, SINBAR any, phasic pattern
    axd = ax[1, 1]
    for variant, ls in (("published", "-"), ("FC", "--")):
        for w in SYSTEMS:
            g = dose[(dose.pattern == "phasic") & (dose.method == "SINBAR") &
                     (dose.variant == variant) & (dose.who == w)].sort_values("amp_uv")
            if not g.empty:
                axd.plot(g.amp_uv, 100 * g.share, ls=ls, color=COLORS[w], lw=1.2,
                         label=w if variant == "published" else None)
    axd.set_xscale("log")
    axd.xaxis.set_major_formatter(plain)
    axd.set_xlabel("amplitude of the injected phasic bursts (µV)")
    axd.set_ylabel("nights flagged by SINBAR \"any\" >= 18.2% (%)")
    axd.set_title("D  Nights flagged as injected bursts grow\nsolid = published, dashed = floor-corrected",
                  fontsize=10)
    axd.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig11_injection.{ext}", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
