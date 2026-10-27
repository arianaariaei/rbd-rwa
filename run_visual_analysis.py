"""Analysis of the blinded visual-scoring substudy (paper/visual_substudy_protocol.md).

    python run_visual_analysis.py --sheets <folder with the scorer's two CSVs> --key <key.csv>

Per excerpt: visual SINBAR "any" % (3-s mini-epochs scored 1, artifacts "X" left
out) and tonic % (30-s epochs), against the automated scores of the same epochs.

  H1  agreement: ICC(2,1), absolute agreement, and Bland-Altman bias and 95% limits,
      visual vs automated published and vs floor-corrected (excerpts as recorded)
  H2  the noise floor in visual scoring: per night, the change in visual "any" %
      from the excerpt as recorded to its noisy copy (mean, 95% bootstrap CI, Wilcoxon);
      the same for the automated published and floor-corrected scores
  H3  the share of the automated published change that visual scoring reproduces:
      mean visual change / mean automated published change, with bootstrap CI
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


def icc_a1(x, y):
    """ICC(2,1): two-way random effects, absolute agreement, single rater (Shrout-Fleiss)."""
    m = np.c_[x, y].astype(float)
    m = m[np.isfinite(m).all(axis=1)]
    n, k = m.shape
    grand = m.mean()
    msr = k * ((m.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    msc = n * ((m.mean(axis=0) - grand) ** 2).sum() / (k - 1)
    sse = ((m - m.mean(axis=1, keepdims=True) - m.mean(axis=0, keepdims=True) + grand) ** 2).sum()
    mse = sse / ((n - 1) * (k - 1))
    return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)


def boot_mean(v, n=2000, seed=7):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheets", required=True)
    ap.add_argument("--key", required=True)
    args = ap.parse_args()
    key = pd.read_csv(args.key)
    minis = pd.read_csv(Path(args.sheets) / "scoring_minis.csv", dtype={"any": str})
    eps = pd.read_csv(Path(args.sheets) / "scoring_epochs.csv", dtype={"tonic": str})
    minis = minis[minis["any"].str.strip().isin(["0", "1"])]
    eps = eps[eps["tonic"].str.strip().isin(["0", "1"])]
    vis = pd.DataFrame({
        "vis_any": minis.groupby("excerpt")["any"].apply(lambda s: 100 * (s.str.strip() == "1").mean()),
        "vis_tonic": eps.groupby("excerpt")["tonic"].apply(lambda s: 100 * (s.str.strip() == "1").mean()),
        "artifact_minis": pd.read_csv(Path(args.sheets) / "scoring_minis.csv", dtype={"any": str})
        .groupby("excerpt")["any"].apply(lambda s: (s.str.strip().str.upper() == "X").sum())})
    d = key.merge(vis, left_on="excerpt", right_index=True, how="left")
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    rec = d[d["copy"] == "as recorded"]
    say("H1  Agreement on the excerpts as recorded (n = %d)" % rec.vis_any.notna().sum())
    for auto in ("published", "FC"):
        for meas in ("any", "tonic"):
            x, y = rec[f"vis_{meas}"], rec[f"auto_{meas}_{auto}"]
            diff = (y - x).dropna()
            say(f"    {meas:<6} visual vs automated {auto:<10} ICC(2,1) {icc_a1(x, y):.2f}  "
                f"bias {diff.mean():+.1f} points, 95% limits {diff.mean() - 1.96 * diff.std():+.1f} to "
                f"{diff.mean() + 1.96 * diff.std():+.1f}")
    for cohort, g in rec.groupby("cohort"):
        say(f"    {cohort:<7} visual any {g.vis_any.mean():.1f}%  automated published {g.auto_any_published.mean():.1f}%  "
            f"FC {g.auto_any_FC.mean():.1f}%")
    say()
    w = d.pivot_table(index=["cohort", "record"], columns="copy",
                      values=["vis_any", "auto_any_published", "auto_any_FC"])
    say("H2  Change from the excerpt as recorded to its noisy copy (points): mean [95% CI], Wilcoxon p")
    ch = {}
    for col, label in (("vis_any", "visual"), ("auto_any_published", "automated published"),
                       ("auto_any_FC", "automated floor-corrected")):
        c = (w[(col, "noise")] - w[(col, "as recorded")]).dropna()
        ch[label] = c
        m, lo, hi = boot_mean(c)
        p = wilcoxon(c).pvalue if (c != 0).any() else 1.0
        say(f"    {label:<28} {m:+6.1f} [{lo:+.1f} to {hi:+.1f}]  p {p:.3g}  (n = {len(c)} nights)")
        for cohort in ("cap", "chal18", "hmc"):
            cc = c.loc[cohort] if cohort in c.index.get_level_values(0) else pd.Series(dtype=float)
            if len(cc):
                say(f"        {cohort:<7} {cc.mean():+6.1f}")
    say()
    v, a = ch["visual"], ch["automated published"]
    both = pd.concat([v, a], axis=1, keys=["v", "a"]).dropna()
    rng = np.random.default_rng(8)
    ratios = []
    for _ in range(2000):
        i = rng.integers(0, len(both), len(both))
        s = both.iloc[i]
        if s.a.mean() != 0:
            ratios.append(s.v.mean() / s.a.mean())
    say(f"H3  Share of the automated published change reproduced visually: {both.v.mean() / both.a.mean():.2f} "
        f"[{np.percentile(ratios, 2.5):.2f} to {np.percentile(ratios, 97.5):.2f}]")
    out = Path(args.sheets) / "visual_report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    d.to_csv(Path(args.sheets) / "visual_scores.csv", index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
