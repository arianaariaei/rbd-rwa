"""Score every derived recording with every RWA method.

Writes one tidy row per (recording, method, band) to
results/cap_rwa_scores.csv, then prints how well each method's score separates
RBD from two comparison groups (AUC, 0.5 = chance):

  healthy        CAP's healthy sleepers. CAUTION: most were recorded on
                 different equipment from the RBD patients (chin EMG sampled
                 at 100-200 Hz, some without physical units), so amplitude
                 differences are partly hardware differences.
  same-system    other CAP patients (epilepsy, PLM, insomnia, narcolepsy...)
                 whose chin EMG was recorded like the RBD patients' (512 Hz,
                 microvolts). The fairer comparison.

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
        return float("nan"), 0, 0
    diff = pos[:, None] - neg[None, :]
    return float(((diff > 0) + 0.5 * (diff == 0)).mean()), len(pos), len(neg)


def main():
    files = sorted(p for p in config.DERIVED.glob("*.npz") if ".tmp" not in p.name)
    print(f"{len(files)} derived recordings in {config.DERIVED}\n")
    rows = []
    for p in files:
        d = load_derived(p)
        meta = d["meta"]
        ci = meta["chin_info"]
        for band in ("native", "harmonized"):
            for r in score_all(d, band=band):
                r.update(record=meta["record"], cohort=cohort_of(meta["record"]),
                         chin_fs=ci["fs"], chin_label=ci["label"],
                         unit_known=ci["unit_known"], n_legs=len(meta["leg_info"]))
                rows.append(r)
    df = pd.DataFrame(rows)
    out = config.RESULTS / "cap_rwa_scores.csv"
    df.to_csv(out, index=False)
    print(f"saved {len(df)} rows -> {out}\n")

    # One continuous score per method, oriented so that higher = more RWA
    rai = df["rai"] if "rai" in df else np.nan
    score = np.where(df["method"] == "RAI", 1 - rai, df.get("any_pct", np.nan))
    df = df.assign(score=pd.to_numeric(score, errors="coerce"))
    same_system = (df.chin_fs == 512) & df.unit_known

    for band, g in df.groupby("band"):
        order = [c for c in COHORT_NAMES.values() if c in set(g["cohort"])]
        print(f"=== {band} band: median score per cohort (any-activity %, or 1 - RAI)")
        print(g.pivot_table(index="method", columns="cohort", values="score",
                            aggfunc="median")[order].round(2).to_string())
        print(f"\n    RBD separation (AUC):          vs healthy      vs same-system patients")
        for m, gm in g.groupby("method"):
            ss = same_system.loc[gm.index]
            rbd = gm.loc[gm.cohort == "RBD", "score"]
            a1, n1, h1 = auc(rbd, gm.loc[gm.cohort == "healthy", "score"])
            others = gm[ss & ~gm.cohort.isin(["RBD", "healthy"])]
            a2, n2, h2 = auc(gm.loc[ss & (gm.cohort == "RBD"), "score"], others["score"])
            print(f"    {m:<9} {a1:>8.3f} ({n1} v {h1:<3})   {a2:>8.3f} ({n2} v {h2})")
        print()


if __name__ == "__main__":
    main()
