"""Score every derived recording with every RWA method.

Writes one tidy row per (recording, method, band) to
results/cap_rwa_scores.csv, then prints, for every metric, the median in each
cohort and how well it separates RBD from two comparison groups (AUC, 0.5 =
chance):

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
METRICS = ["tonic_pct", "phasic_pct", "phasic_epoch_pct", "any_pct", "atonia_loss"]


def cohort_of(record):
    return COHORT_NAMES.get("".join(c for c in record if not c.isdigit()), "other")


def auc(pos, neg):
    """Probability a random positive outscores a random negative (ties = 1/2)."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    pos, neg = pos[np.isfinite(pos)], neg[np.isfinite(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan"), len(pos), len(neg)
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
        for band in ("native", "harmonized", "native_with_ecg"):
            for r in score_all(d, band=band):
                r.update(record=meta["record"], cohort=cohort_of(meta["record"]),
                         chin_fs=ci["fs"], chin_label=ci["label"],
                         unit_known=ci["unit_known"], n_legs=len(meta["leg_info"]))
                rows.append(r)
    df = pd.DataFrame(rows)
    if "rai" in df:
        df["atonia_loss"] = 1 - df["rai"]              # higher = more RWA, like the rest
    out = config.RESULTS / "cap_rwa_scores.csv"
    df.to_csv(out, index=False)
    print(f"saved {len(df)} rows -> {out}\n")

    same_system = (df.chin_fs == 512) & df.unit_known.astype(bool)
    order = [c for c in COHORT_NAMES.values() if c in set(df["cohort"])]
    for band, g in df.groupby("band"):
        print(f"=== {band} band " + "=" * 60)
        print(f"{'method':<9} {'metric':<17} " + " ".join(f"{c[:8]:>8}" for c in order)
              + f" | {'AUC v healthy':>14} {'AUC v same-sys':>15}")
        for m, gm in g.groupby("method", sort=False):
            ss = same_system.loc[gm.index]
            for metric in METRICS:
                if metric not in gm or gm[metric].notna().sum() == 0:
                    continue
                med = gm.groupby("cohort")[metric].median()
                a1, n1, h1 = auc(gm.loc[gm.cohort == "RBD", metric],
                                 gm.loc[gm.cohort == "healthy", metric])
                a2, n2, h2 = auc(gm.loc[ss & (gm.cohort == "RBD"), metric],
                                 gm.loc[ss & ~gm.cohort.isin(["RBD", "healthy"]), metric])
                print(f"{m:<9} {metric:<17} "
                      + " ".join(f"{med.get(c, np.nan):>8.2f}" for c in order)
                      + f" | {a1:>6.3f} ({n1}v{h1}) {a2:>7.3f} ({n2}v{h2})")
        pos = g.dropna(subset=["positive"]).pivot_table(
            index="method", columns="cohort", values="positive", aggfunc="mean")
        print("\nshare classified POSITIVE by each method's published cut-off:")
        print((100 * pos.reindex(columns=order)).round(0).to_string())
        print()


if __name__ == "__main__":
    main()
