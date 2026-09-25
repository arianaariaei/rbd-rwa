"""Score every derived recording with every RWA method.

Writes one tidy row per (recording, method) to results/cap_rwa_scores.csv and
prints, per method, the median score in each cohort and how well the score
separates RBD from healthy sleepers (AUC, 0.5 = chance).

    python run_score.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.extract import load_derived
from src.rwa import score_all

COHORT_NAMES = {"rbd": "RBD", "n": "healthy", "nfle": "NFLE", "plm": "PLM",
                "ins": "insomnia", "narco": "narcolepsy", "sdb": "SDB",
                "brux": "bruxism"}


def cohort_of(record):
    return COHORT_NAMES.get("".join(c for c in record if not c.isdigit()), "other")


def auc(pos, neg):
    """Probability a random positive outscores a random negative (ties = 1/2)."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    pos, neg = pos[np.isfinite(pos)], neg[np.isfinite(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    diff = pos[:, None] - neg[None, :]
    return float(((diff > 0) + 0.5 * (diff == 0)).mean())


def main():
    files = sorted(p for p in config.DERIVED.glob("*.npz") if ".tmp" not in p.name)
    print(f"{len(files)} derived recordings in {config.DERIVED}\n")
    rows = []
    for p in files:
        env, hyp, meta = load_derived(p)
        for r in score_all(env, hyp, meta):
            r = dict(r)
            r["record"] = meta["record"]
            r["cohort"] = cohort_of(meta["record"])
            rows.append(r)
    df = pd.DataFrame(rows)
    out = config.RESULTS / "cap_rwa_scores.csv"
    df.to_csv(out, index=False)
    print(f"saved {len(df)} rows -> {out}\n")

    # One continuous score per method, oriented so that higher = more RWA
    score = np.where(df["method"] == "RAI", 1 - df.get("rai", np.nan),
                     df.get("any_pct", np.nan))
    df = df.assign(score=score)
    order = [c for c in COHORT_NAMES.values() if c in set(df["cohort"])]
    table = df.pivot_table(index="method", columns="cohort", values="score",
                           aggfunc="median")[order]
    print("Median score per cohort (any-activity %, or 1 - RAI):")
    print(table.round(2).to_string())

    print("\nRBD vs healthy separation:")
    for m, g in df.groupby("method"):
        a = auc(g.loc[g.cohort == "RBD", "score"], g.loc[g.cohort == "healthy", "score"])
        n_r, n_h = (g.cohort == "RBD").sum(), (g.cohort == "healthy").sum()
        print(f"  {m:<9} AUC = {a:.3f}   ({n_r} RBD, {n_h} healthy)")


if __name__ == "__main__":
    main()
