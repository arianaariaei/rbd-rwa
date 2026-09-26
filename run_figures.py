"""The paper's figures, drawn from the tables that run_score.py and
run_sensitivity.py write.

    python run_figures.py        # -> figures/fig1..fig5 (.png and .pdf)

  fig1  share of nights each method flags, per group, with 95% intervals
  fig2  quiet-REM chin EMG level per cohort (A) and the hardware simulation (B)
  fig3  how the definition of "background" moves the verdicts and the separation
  fig4  where the published and the re-derived cut-offs fall on each group
  fig5  positive calls by quiet-REM level within the MGH and HMC cohorts
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config
from run_report import MIN_REM, WITHDRAWN, wilson
from run_sensitivity import auc

YES = (True, "True", 1, 1.0)
GROUPS = ["CAP RBD", "CAP patients", "CAP healthy", "chal18", "hmc"]
LABEL = {"CAP RBD": "CAP\nRBD", "CAP patients": "CAP\npatients", "CAP healthy": "CAP\nhealthy",
         "chal18": "MGH", "hmc": "HMC", "hmc_q1uv": "HMC\n1 µV", "hmc_mgh": "HMC\n1 µV\n200 Hz",
         "hmc_low": "HMC\n×0.39", "hmc_low_mgh": "HMC\n×0.39\n1 µV\n200 Hz",
         "chal18_noise": "MGH\n+1.5 µV\nnoise"}
COLOR = {"Montreal": "#1b9e77", "SINBAR": "#d95f02", "RAI": "#7570b3", "AASM": "#e7298a"}
GROUP_COLOR = {"CAP RBD": "#d62728", "CAP patients": "#7f7f7f", "CAP healthy": "#2ca02c",
               "chal18": "#1f77b4", "hmc": "#9467bd"}
VARIANTS = ["min_rem", "p5_rem", "p10_rem", "p25_rem", "p50_rem", "p5_nrem"]
VARIANT_LABEL = ["min", "p5\n(default)", "p10", "p25", "p50", "p5\nNREM"]

plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 9, "axes.titleweight": "bold", "axes.titlelocation": "left",
                     "legend.fontsize": 7, "savefig.dpi": 300})


def label_groups(df):
    """CAP RBD / CAP healthy / CAP patients on CAP's main system (512 Hz), and cohorts."""
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512) & df.unit_known.astype(bool)
    who = np.select([cap & (df.group == "RBD"), cap & (df.group == "healthy"),
                     same & ~df.group.isin(["RBD", "healthy"])],
                    ["CAP RBD", "CAP healthy", "CAP patients"], default="")
    return df.assign(who=np.where(cap, who, df.cohort), same=same)


def load_scores():
    df = pd.read_csv(config.RESULTS / "rwa_scores.csv")
    df = df[~df.apply(lambda r: (r.cohort, r.record) in WITHDRAWN, axis=1)]
    df = df[(df.excluded.fillna("") == "") & (df.rem_minutes >= MIN_REM) & (df.band == "native")]
    df = label_groups(df)
    return df.assign(y=df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan))


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"{name}.{ext}")
    plt.close(fig)
    print(f"  {name}")


def dots_with_ci(ax, df, groups, methods=("Montreal", "SINBAR", "RAI"), show_n=True):
    width = 0.8 / len(methods)
    for j, meth in enumerate(methods):
        xs, ps, err = [], [], [[], []]
        for i, g in enumerate(groups):
            v = df[(df.who == g) & (df.method == meth)].y.dropna()
            p, lo, hi = wilson(v.sum(), len(v))
            xs.append(i + (j - (len(methods) - 1) / 2) * width)
            ps.append(100 * p)
            err[0].append(100 * (p - lo))
            err[1].append(100 * (hi - p))
        ax.errorbar(xs, ps, yerr=err, fmt="o", ms=4, capsize=2, lw=1, color=COLOR[meth], label=meth)
    n = [df[(df.who == g) & (df.method == methods[0])].y.notna().sum() for g in groups]
    ax.set_xticks(range(len(groups)),
                  [f"{LABEL[g]}\nn={k}" if show_n else LABEL[g] for g, k in zip(groups, n)])
    ax.set_ylim(0, 100)
    ax.set_ylabel("nights flagged positive (%)")


def fig1(df):
    fig, ax = plt.subplots(figsize=(6.5, 3.0), layout="constrained")
    dots_with_ci(ax, df, GROUPS)
    ax.axvline(0.5, color="0.85", lw=0.8, zorder=0)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.set_title("Published cut-offs: sensitivity in RBD, positives everywhere else")
    save(fig, "fig1_positivity")


def fig2(df):
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.2), layout="constrained",
                               gridspec_kw={"width_ratios": [1, 1.3]})
    lvl = df[df.method == "Montreal"]
    data = [lvl.loc[lvl.who == g, "background_phasic_uV"].dropna() for g in GROUPS]
    rng = np.random.default_rng(0)
    for i, (g, v) in enumerate(zip(GROUPS, data)):
        a.scatter(i + rng.uniform(-0.25, 0.25, len(v)), v, s=3, alpha=0.35 if len(v) > 200 else 0.7,
                  color=GROUP_COLOR[g], lw=0)
    a.boxplot(data, positions=range(len(GROUPS)), widths=0.55, showfliers=False,
              medianprops={"color": "k"}, boxprops={"lw": 0.8}, whiskerprops={"lw": 0.8})
    a.axhline(1.0, ls="--", color="k", lw=0.8, label="MGH storage step (1 µV)")
    a.legend(frameon=False, loc="upper left")
    a.set_yscale("log")
    ticks = [0.2, 0.5, 1, 2, 5, 10, 20, 50]
    a.set_yticks(ticks, [f"{t:g}" for t in ticks])
    a.set_ylim(0.15, 1.3 * max(v.max() for v in data if len(v)))
    a.set_xticks(range(len(GROUPS)), [LABEL[g] for g in GROUPS])
    a.set_ylabel("quiet-REM chin EMG level (µV)")
    a.set_title("A  Quiet-REM level")
    sims = [c for c in ["hmc", "hmc_q1uv", "hmc_mgh", "hmc_low", "hmc_low_mgh", "chal18",
                        "chal18_noise"] if (df.who == c).any()]
    dots_with_ci(b, df, sims, show_n=False)
    b.tick_params(axis="x", labelsize=7)
    b.legend(frameon=False, ncol=3, loc="upper left")
    b.set_title("B  Recording simulations")
    save(fig, "fig2_level_and_hardware")


def fig3(df):
    sens = pd.read_csv(config.RESULTS / "sensitivity_background.csv")
    sens = label_groups(sens)
    sens = sens.assign(y=sens.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan))
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1), layout="constrained")
    x = np.arange(len(VARIANTS))
    for k, (ax, meth) in enumerate(zip(axes[:2], ["Montreal", "SINBAR"])):
        for g in GROUPS:
            s = sens[(sens.method == meth) & (sens.who == g)].groupby("variant").y.mean() * 100
            ax.plot(x, [s.get(v, np.nan) for v in VARIANTS], "o-", ms=3, lw=1,
                    color=GROUP_COLOR[g], label=LABEL[g].replace("\n", " "))
        ax.set_ylim(0, 100)
        ax.set_ylabel("nights flagged positive (%)")
        ax.set_title(f"{'AB'[k]}  {meth}")
    same = sens[sens.who.isin(["CAP RBD", "CAP patients"])]
    for meth, metric, ls in [("Montreal", "phasic_pct", "-"), ("Montreal", "tonic_pct", "--"),
                             ("SINBAR", "phasic_pct", "-"), ("SINBAR", "tonic_pct", "--"),
                             ("AASM", "phasic_pct", "-")]:
        g = same[same.method == meth]
        vals = [auc(g.loc[(g.variant == v) & (g.who == "CAP RBD"), metric],
                    g.loc[(g.variant == v) & (g.who == "CAP patients"), metric]) for v in VARIANTS]
        axes[2].plot(x, vals, "o" + ls, ms=3, lw=1, color=COLOR[meth],
                     label=f"{meth} {metric.split('_')[0]}")
    axes[2].axhline(0.5, color="0.7", lw=0.8)
    axes[2].set_ylim(0.4, 1.0)
    axes[2].set_ylabel("AUC, RBD vs other CAP patients")
    axes[2].legend(frameon=False, loc="lower left")
    axes[2].set_title("C  Separation")
    for ax in axes:
        ax.set_xticks(x, VARIANT_LABEL, fontsize=7)
        ax.set_xlabel("background definition")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=5,
               frameon=False)
    save(fig, "fig3_background_definition")


def youden(pos, neg):
    c = np.unique(np.r_[pos, neg])
    j = (pos[None, :] >= c[:, None]).mean(axis=1) - (neg[None, :] >= c[:, None]).mean(axis=1)
    return c[int(np.argmax(j))]


def fig4(df):
    panels = [("Montreal", "phasic_pct", 15.0, "Montreal phasic (% of 2 s mini-epochs)"),
              ("SINBAR", "any_pct", 18.2, "SINBAR any (% of 3 s mini-epochs)")]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), layout="constrained")
    rng = np.random.default_rng(0)
    for k, (ax, (meth, metric, published, title)) in enumerate(zip(axes, panels)):
        d = df[df.method == meth]
        # derived as in run_report.py T7: RBD and other patients on the same system
        pos = d.loc[(d.who == "CAP RBD") & d.same, metric].dropna().to_numpy(float)
        neg = d.loc[d.who == "CAP patients", metric].dropna().to_numpy(float)
        cut = youden(pos, neg)
        ticks = []
        for i, g in enumerate(GROUPS):
            v = d.loc[d.who == g, metric].dropna().to_numpy(float)
            ax.scatter(i + rng.uniform(-0.25, 0.25, len(v)), v, s=3, lw=0, color=GROUP_COLOR[g],
                       alpha=0.35 if len(v) > 200 else 0.8)
            ticks.append(f"{LABEL[g]}\n{100 * (v >= published).mean():.0f}→"
                         f"{100 * (v >= cut).mean():.0f}%")
        ax.axhline(published, color="k", ls="--", lw=0.8, label=f"published cut-off ({published:g}%)")
        ax.axhline(cut, color="k", lw=0.8, label=f"re-derived cut-off ({cut:.1f}%)")
        ax.set_xticks(range(len(GROUPS)), ticks, fontsize=7)
        ax.set_xlabel("flagged positive: published → re-derived cut-off")
        ax.set_ylim(0, 100)
        ax.set_ylabel(title)
        ax.legend(frameon=False, loc="upper right", fontsize=6.5)
        ax.set_title(f"{'AB'[k]}  {meth}")
    save(fig, "fig4_cutoffs")


def fig5(df):
    quiet = df[df.method == "Montreal"][["cohort", "record", "background_phasic_uV"]].rename(
        columns={"background_phasic_uV": "quiet"})
    d = df[df.method.isin(["Montreal", "SINBAR", "RAI"])].merge(quiet, on=["cohort", "record"])
    d = d.dropna(subset=["quiet", "y"])
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.8), sharey=True, layout="constrained")
    for ax, cohort, name in zip(axes, ["chal18", "hmc"], ["A  MGH", "B  HMC"]):
        g = d[d.cohort == cohort]
        edges = g[g.method == "Montreal"].quiet.quantile([0, 1 / 3, 2 / 3, 1]).to_numpy()
        t = np.clip(np.searchsorted(edges, g.quiet, side="right") - 1, 0, 2)
        for j, meth in enumerate(["Montreal", "SINBAR", "RAI"]):
            m = g.method.to_numpy() == meth
            ys = [100 * g.y.to_numpy()[m & (t == k)].mean() for k in range(3)]
            ax.bar(np.arange(3) + (j - 1) * 0.27, ys, width=0.26, color=COLOR[meth], label=meth)
        ax.set_xticks(range(3), [f"lowest third\n< {edges[1]:.2f} µV", "middle third",
                                 f"highest third\n> {edges[2]:.2f} µV"])
        ax.set_xlabel("night's quiet-REM chin EMG level")
        ax.set_title(name)
    axes[0].set_ylabel("nights flagged positive (%)")
    axes[1].legend(frameon=False, loc="upper left")
    save(fig, "fig5_level_vs_verdict")


def main():
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    df = load_scores()
    print(f"figures -> {config.FIGURES}")
    fig1(df)
    fig2(df)
    if (config.RESULTS / "sensitivity_background.csv").exists():
        fig3(df)
    fig4(df)
    fig5(df)


if __name__ == "__main__":
    main()
