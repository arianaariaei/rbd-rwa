"""The noise ladder: how each method's verdict moves with the noise floor.

Every ladder pack (run_cohort.py --ladder) holds one night's chin EMG as
recorded and with white noise added in band: at fixed levels (n050 ... n300 =
0.5 ... 3 uV RMS) and at the level that brings its quiet-REM level to a common
target (h150, h200 = 1.5 and 2.0 uV). This scores every copy with every method
and reports, against the criteria fixed in paper/preregistration_noise_ladder.md:

  L1  dose-response: quiet-REM level and share flagged, per group and step
  L2  matched floor: MGH against HMC after harmonising both (criteria 1, 2)
  L3  RBD sensitivity as the floor rises (criterion 3)
  L4  the remedy: cut-offs re-derived on harmonised CAP, leave-one-out and
      bootstrap, applied to harmonised MGH and HMC (criterion 4)
  L5  the recording systems' own noise, measured on EEG (criterion 5)

    python run_ladder.py   -> results/ladder_scores.csv, results/ladder_report.md,
                              figures/fig6_noise_ladder, figures/fig7_harmonisation
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.pack import load_pack
from src.rwa import score_all
from run_report import MIN_REM, WITHDRAWN, wilson
from run_score import group_of

LADDER = ["native", "n050", "n100", "n150", "n200", "n300"]
STEPS = LADDER + ["h150", "h200"]
TARGET = "h200"
DECIDING = ["Montreal", "SINBAR", "RAI"]
WHO = ["CAP RBD", "CAP patients", "CAP healthy", "MGH", "HMC"]
REMEDY = [("Montreal", "phasic_pct"), ("Montreal", "tonic_pct"), ("SINBAR", "any_pct"),
          ("SINBAR", "phasic_pct"), ("SINBAR", "tonic_pct"), ("AASM", "phasic_epoch_pct"),
          ("RAI", "atonia_loss")]
KEY = [("Montreal", "phasic_pct"), ("Montreal", "tonic_pct"), ("SINBAR", "any_pct")]
YES = (True, "True", 1, 1.0)


def score_file(path):
    pack = load_pack(path)
    m = pack["meta"]
    eeg = m.get("eeg") or {}
    info = dict(cohort=m["cohort"], record=m["record"], group=group_of(m["cohort"], m["record"]),
                chin_fs=m.get("chin_fs"), unit_known=m.get("unit_known", True),
                eeg_nrem=eeg.get("floor_nrem_uv"), eeg_rem=eeg.get("floor_rem_uv"),
                eeg_channel=eeg.get("channel"))
    rows = []
    for step in STEPS:
        if step != "native" and f"rms_{step}" not in m["rows"]:
            continue
        for r in score_all(pack, step):
            r.pop("band", None)
            rows.append({**info, "step": step, **r})
    return rows


def load_scores():
    files = sorted(p for p in (config.DURABLE / "ladder").glob("*/*.npz") if ".tmp" not in p.name)
    print(f"scoring {len(files)} ladder packs", flush=True)
    with ProcessPoolExecutor(max_workers=2) as ex:
        rows = [r for part in ex.map(score_file, files, chunksize=4) for r in part]
    df = pd.DataFrame(rows)
    df = df[~df.apply(lambda r: (r.cohort, r.record) in WITHDRAWN, axis=1)]
    df["atonia_loss"] = 1 - df["rai"]
    df["y"] = df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan)
    # a night's quiet-REM level belongs to the night and step, not to the method:
    # take it from the Montreal row and attach it to every method's row
    level = df[df.method == "Montreal"].set_index(["cohort", "record", "step"]).background_phasic_uV
    df["level"] = level.reindex(pd.MultiIndex.from_frame(df[["cohort", "record", "step"]])).to_numpy()
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512) & df.unit_known.astype(bool)
    df["who"] = np.select(
        [cap & same & (df.group == "RBD"), cap & same & ~df.group.isin(["RBD", "healthy"]),
         cap & (df.group == "healthy"), df.cohort == "chal18", df.cohort == "hmc"],
        ["CAP RBD", "CAP patients", "CAP healthy", "MGH", "HMC"], default="")
    return df


def youden(p, n):
    c = np.unique(np.r_[p, n])
    j = (p[None, :] >= c[:, None]).mean(axis=1) - (n[None, :] >= c[:, None]).mean(axis=1)
    return c[int(np.argmax(j))]


def pct(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    p, lo, hi = wilson(v.sum(), len(v))
    return p, lo, hi, len(v)


def main():
    df = load_scores()
    df.to_csv(config.RESULTS / "ladder_scores.csv", index=False)
    base = df[df.rem_minutes >= MIN_REM]
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    # L1 ─────────────────────────────────────────────────────────────────────
    say("L1  Dose-response: median quiet-REM level (uV) and % flagged by the published cut-offs")
    for who in WHO:
        g = base[base.who == who]
        if g.empty:
            continue
        say(f"  {who} (n={g[g.step == 'native'].record.nunique()})")
        for step in STEPS:
            s = g[g.step == step]
            if s.empty:
                continue
            cells = "  ".join(f"{m} {100 * s[s.method == m].y.mean():5.1f}%" for m in DECIDING)
            say(f"    {step:<7} level {s[s.method == 'Montreal'].level.median():5.2f}   {cells}")
    say()

    # L2 ─────────────────────────────────────────────────────────────────────
    say("L2  Matched floor: MGH against HMC (criterion 1: <= 3 points Montreal, <= 5 SINBAR)")
    for step in ["native", "h150", "h200"]:
        cells = []
        for m in DECIDING:
            a = pct(base[(base.who == "MGH") & (base.step == step) & (base.method == m)].y)
            b = pct(base[(base.who == "HMC") & (base.step == step) & (base.method == m)].y)
            cells.append(f"{m} MGH {100 * a[0]:.0f} [{100 * a[1]:.0f}-{100 * a[2]:.0f}] vs HMC "
                         f"{100 * b[0]:.0f} [{100 * b[1]:.0f}-{100 * b[2]:.0f}] (diff {100 * (a[0] - b[0]):+.1f})")
        say(f"  {step:<7} " + ";  ".join(cells))
    say("  criterion 2: MGH's ladder interpolated at HMC's native median level")
    hmc_level = base[(base.who == "HMC") & (base.step == "native")].level.median()
    for m in DECIDING:
        g = base[(base.who == "MGH") & (base.method == m) & base.step.isin(LADDER)]
        x = np.log([g[g.step == s].level.median() for s in LADDER])
        y = [100 * g[g.step == s].y.mean() for s in LADDER]
        at = np.interp(np.log(hmc_level), x, y)
        h = 100 * base[(base.who == "HMC") & (base.step == "native") & (base.method == m)].y.mean()
        say(f"    {m:<9} MGH at {hmc_level:.2f} uV: {at:.1f}%   HMC native: {h:.1f}%   (diff {at - h:+.1f})")
    say()

    # L3 ─────────────────────────────────────────────────────────────────────
    say("L3  Sensitivity for RBD (CAP, main system) as the floor rises (criterion 3: < 70% at h200)")
    for m in DECIDING:
        cells = []
        for step in STEPS:
            p, lo, hi, n = pct(base[(base.who == "CAP RBD") & (base.step == step) & (base.method == m)].y)
            if n:
                cells.append(f"{step} {100 * p:.0f}")
        say(f"  {m:<9} " + "  ".join(cells) + f"   (n={n})")
    say()

    # L4 ─────────────────────────────────────────────────────────────────────
    say("L4  Remedy: cut-offs re-derived on CAP, applied to MGH and HMC, with and without")
    say("    harmonising every night to 2.0 uV (criterion 4 for Montreal phasic/tonic and")
    say("    SINBAR any: |FP MGH - FP HMC| <= 5 points and leave-one-out sensitivity >= 80%)")
    rng = np.random.default_rng(0)
    remedy = []
    for step in ["native", TARGET]:
        for meth, metric in REMEDY:
            g = base[(base.step == step) & (base.method == meth)]
            pos = g.loc[g.who == "CAP RBD", metric].dropna().to_numpy(float)
            neg = g.loc[g.who == "CAP patients", metric].dropna().to_numpy(float)
            if len(pos) < 5 or len(neg) < 5:
                continue
            cut = youden(pos, neg)
            cv_s = np.mean([pos[i] >= youden(np.delete(pos, i), neg) for i in range(len(pos))])
            cv_f = np.mean([neg[i] >= youden(pos, np.delete(neg, i)) for i in range(len(neg))])
            ext = {k: g.loc[g.who == k, metric].dropna().to_numpy(float) for k in ("MGH", "HMC")}
            boot = {k: [] for k in ext}
            for _ in range(2000):
                c = youden(rng.choice(pos, len(pos)), rng.choice(neg, len(neg)))
                for k, v in ext.items():
                    boot[k].append((v >= c).mean())
            fp = {k: (v >= cut).mean() for k, v in ext.items()}
            ci = {k: np.percentile(v, [2.5, 97.5]) for k, v in boot.items()}
            remedy.append(dict(step=step, method=meth, metric=metric, cut=cut, cv_sens=cv_s, cv_fp=cv_f,
                               fp_mgh=fp["MGH"], fp_hmc=fp["HMC"], ci_mgh=ci["MGH"], ci_hmc=ci["HMC"]))
            r = remedy[-1]
            ok = ""
            if (meth, metric) in KEY:
                ok = "  PASS" if abs(r["fp_mgh"] - r["fp_hmc"]) <= 0.05 and cv_s >= 0.80 else "  fail"
            say(f"  {step:<7} {meth:<9} {metric:<17} cut {cut:7.2f}  CV sens {100 * cv_s:3.0f}%  "
                f"CV FP {100 * cv_f:3.0f}%  MGH FP {100 * fp['MGH']:3.0f} [{100 * ci['MGH'][0]:.0f}-"
                f"{100 * ci['MGH'][1]:.0f}]  HMC FP {100 * fp['HMC']:3.0f} [{100 * ci['HMC'][0]:.0f}-"
                f"{100 * ci['HMC'][1]:.0f}]  gap {100 * (fp['MGH'] - fp['HMC']):+.0f}{ok}")
    say()

    # L5 ─────────────────────────────────────────────────────────────────────
    say("L5  The systems' own noise: EEG 40-90 Hz floor (uV), median [IQR], and the chin's")
    say("    quiet-REM level (criterion 5: HMC/MGH EEG ratio >= 1.5 = system-wide)")
    nat = base[(base.step == "native") & (base.method == "Montreal")]
    by = {"CAP (main system)": nat[(nat.cohort == "cap") & (nat.chin_fs == 512)],
          "MGH": nat[nat.cohort == "chal18"], "HMC": nat[nat.cohort == "hmc"]}
    med = {}
    for name, g in by.items():
        e = g.eeg_nrem.dropna().astype(float)
        r = g.eeg_rem.dropna().astype(float)
        if len(e):
            med[name] = e.median()
            say(f"  {name:<18} n={len(e):<4} EEG N2/N3 {e.median():.2f} [{e.quantile(.25):.2f}-{e.quantile(.75):.2f}]"
                f"   EEG REM {r.median():.2f}   chin quiet-REM {g.level.median():.2f}")
    if "MGH" in med and "HMC" in med:
        say(f"  HMC/MGH EEG floor ratio {med['HMC'] / med['MGH']:.2f}")

    out = config.RESULTS / "ladder_report.md"
    out.write_text("```\n" + "\n".join(lines) + "\n```\n", encoding="utf-8")
    print(f"\nwritten -> {out}")
    figures(base, remedy)


def figures(base, remedy):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from run_figures import COLOR, save

    colors = {"CAP RBD": "#d62728", "CAP patients": "#7f7f7f", "MGH": "#1f77b4", "HMC": "#9467bd"}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), sharey=True, layout="constrained")
    for ax, m in zip(axes, DECIDING):
        for who, col in colors.items():
            g = base[(base.who == who) & (base.method == m)]
            if g.empty:
                continue
            x = [g[g.step == s].level.median() for s in LADDER]
            y = [100 * g[g.step == s].y.mean() for s in LADDER]
            ax.plot(x, y, "o-", ms=3, lw=1, color=col, mfc="white", label=who)
            ax.plot(x[0], y[0], "o", ms=5, color=col)                  # as recorded
            h = g[g.step == TARGET]
            ax.plot(h.level.median(), 100 * h.y.mean(), "*", ms=8, color=col)
        ax.set_xscale("log")
        ax.set_xticks([0.5, 1, 2, 4], ["0.5", "1", "2", "4"])
        ax.set_xlabel("quiet-REM level (µV)")
        ax.set_title(m)
    axes[0].set_ylabel("nights flagged positive (%)")
    axes[0].set_ylim(0, 100)
    axes[0].legend(frameon=False, loc="upper right", fontsize=6.5)
    save(fig, "fig6_noise_ladder")

    rem = pd.DataFrame(remedy)
    if rem.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), layout="constrained")
    # A: published cut-offs, as recorded vs harmonised
    ax = axes[0]
    groups = ["CAP RBD", "MGH", "HMC"]
    for j, (m, step, hatch) in enumerate([("Montreal", "native", ""), ("Montreal", TARGET, "//"),
                                          ("SINBAR", "native", ""), ("SINBAR", TARGET, "//")]):
        vals = [100 * base[(base.who == w) & (base.step == step) & (base.method == m)].y.mean()
                for w in groups]
        ax.bar(np.arange(3) + (j - 1.5) * 0.2, vals, width=0.19, color=COLOR[m], hatch=hatch,
               edgecolor="white", label=f"{m}, {'as recorded' if step == 'native' else 'harmonised 2 µV'}")
    ax.set_xticks(range(3), groups)
    ax.set_ylabel("nights flagged positive (%)")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=6, loc="upper right")
    ax.set_title("A  Published cut-offs")
    # B: re-derived cut-offs on harmonised data: external false positives
    ax = axes[1]
    k = rem[(rem.step == TARGET) & rem.apply(lambda r: (r.method, r.metric) in KEY, axis=1)]
    for i, r in enumerate(k.itertuples()):
        for dx, fp, ci, col in ((-0.12, r.fp_mgh, r.ci_mgh, "#1f77b4"), (0.12, r.fp_hmc, r.ci_hmc, "#9467bd")):
            ax.errorbar(i + dx, 100 * fp, yerr=[[100 * (fp - ci[0])], [100 * (ci[1] - fp)]],
                        fmt="o", ms=4, capsize=2, color=col)
    ax.plot([], [], "o", color="#1f77b4", label="MGH")
    ax.plot([], [], "o", color="#9467bd", label="HMC")
    ax.set_xticks(range(len(k)), [f"{r.method} {r.metric.split('_')[0]}\nLOO sens {100 * r.cv_sens:.0f}%"
                                  for r in k.itertuples()], fontsize=7)
    ax.set_ylabel("external nights flagged (%)")
    ax.set_ylim(0, max(30, 100 * k[["fp_mgh", "fp_hmc"]].to_numpy().max() + 10))
    ax.legend(frameon=False, fontsize=6.5)
    ax.set_title("B  Re-derived on harmonised CAP")
    save(fig, "fig7_harmonisation")


if __name__ == "__main__":
    main()
