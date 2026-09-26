"""Score every pack of every cohort with every RWA method.

Reads DURABLE/packs/<cohort>/*.npz (build them with run_cohort.py), writes one
tidy row per (recording, method, band, exclusion) to results/rwa_scores.csv,
and prints three summaries:

  1. RBD separation within CAP (AUC, 0.5 = chance), against CAP's healthy
     sleepers - most of whom were recorded on different equipment, so partly
     a hardware contrast - and against CAP patients recorded on the same
     system as the RBD group (512 Hz, microvolts), the fair comparison.
  2. How many people WITHOUT known RBD each method's published cut-off flags,
     per cohort: the false-positive burden a screening programme would face.
  3. The spread of each metric per cohort (median, 90th, 95th percentile).

    python run_score.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.pack import load_pack
from src.rwa import score_all

CAP_GROUPS = {"rbd": "RBD", "n": "healthy", "nfle": "NFLE", "plm": "PLM",
              "ins": "insomnia", "narco": "narcolepsy", "sdb": "SDB", "brux": "bruxism"}
METRICS = ["tonic_pct", "phasic_pct", "phasic_epoch_pct", "any_pct", "atonia_loss"]
MIN_REM_MIN = 10.0     # nights with less REM than this are not scored in summaries


def group_of(cohort, record):
    if cohort == "cap":
        return CAP_GROUPS.get("".join(c for c in record if not c.isdigit()), "other")
    return "clinical"


def auc(pos, neg):
    """Probability a random positive outscores a random negative (ties = 1/2)."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    pos, neg = pos[np.isfinite(pos)], neg[np.isfinite(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan"), len(pos), len(neg)
    diff = pos[:, None] - neg[None, :]
    return float(((diff > 0) + 0.5 * (diff == 0)).mean()), len(pos), len(neg)


def score_everything():
    rows = []
    for cohort_dir in sorted((config.DURABLE / "packs").glob("*")):
        files = sorted(p for p in cohort_dir.glob("*.npz") if ".tmp" not in p.name)
        print(f"{cohort_dir.name}: {len(files)} packs", flush=True)
        for p in files:
            pack = load_pack(p)
            m = pack["meta"]
            cohort = m.get("cohort", cohort_dir.name)
            info = dict(cohort=cohort, record=m["record"], group=group_of(cohort, m["record"]),
                        age=m.get("age"), sex=m.get("sex"), ahi=m.get("ahi"),
                        chin_fs=m.get("chin_fs", m.get("chin_info", {}).get("fs")),
                        unit_known=m.get("unit_known", True))
            exclusions = [()] + ([("resp", "arousal")] if pack["epoch_flags"] else [])
            for band in ("native", "harmonized"):
                for ex in exclusions:
                    for r in score_all(pack, band, ex):
                        rows.append({**info, **r})
    df = pd.DataFrame(rows)
    if "rai" in df:
        df["atonia_loss"] = 1 - df["rai"]              # higher = more RWA, like the rest
    return df


def main():
    import argparse
    import shutil
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=None, help="also copy the results table here")
    args = ap.parse_args()

    df = score_everything()
    for col in ["positive", "error", *METRICS]:          # absent if nothing produced them
        if col not in df:
            df[col] = np.nan
    out = config.RESULTS / "rwa_scores.csv"
    df.to_csv(out, index=False)
    print(f"\nsaved {len(df)} rows -> {out}")
    if args.mirror:
        try:
            Path(args.mirror).mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, Path(args.mirror) / out.name)
            print(f"copied -> {args.mirror}")
        except OSError as e:
            print(f"(could not copy to {args.mirror}: {e})")
    print()
    base = df[(df.excluded == "") & (df.rem_minutes >= MIN_REM_MIN)]

    # 1. RBD separation within CAP ────────────────────────────────────────────
    cap = base[base.cohort == "cap"]
    if len(cap):
        same = (cap.chin_fs == 512) & cap.unit_known.astype(bool)
        print("1. RBD separation in CAP (AUC)           vs healthy      vs same-system patients")
        for (band, meth), g in cap.groupby(["band", "method"], sort=False):
            for metric in METRICS:
                if metric not in g or g[metric].notna().sum() == 0:
                    continue
                s = same.loc[g.index]
                a1, n1, h1 = auc(g.loc[g.group == "RBD", metric], g.loc[g.group == "healthy", metric])
                a2, n2, h2 = auc(g.loc[s & (g.group == "RBD"), metric],
                                 g.loc[s & ~g.group.isin(["RBD", "healthy"]), metric])
                print(f"   {band:<10} {meth:<9} {metric:<17} {a1:6.3f} ({n1}v{h1:<3})   "
                      f"{a2:6.3f} ({n2}v{h2})")
        print()

    # 2. Share flagged positive by published cut-offs ─────────────────────────
    lab = base.assign(who=np.where(base.cohort == "cap", "CAP " + base.group, base.cohort))
    pos = lab.dropna(subset=["positive"])
    pos = pos.assign(positive=pos.positive.astype(float))
    tab = pos.pivot_table(index=["band", "method"], columns="who", values="positive",
                          aggfunc="mean")
    n = pos.groupby("who").record.nunique()
    print("2. Share classified POSITIVE by each published cut-off (%), nights with >= "
          f"{MIN_REM_MIN:.0f} min REM")
    print("   n per group: " + ", ".join(f"{k} {v}" for k, v in n.items()))
    print((100 * tab).round(1).to_string())
    print()

    # 3. Distribution of each metric per cohort ────────────────────────────────
    print("3. Metric distribution per group (native band): median / p90 / p95")
    nat = lab[lab.band == "native"]
    for meth, g in nat.groupby("method", sort=False):
        for metric in METRICS:
            if metric not in g or g[metric].notna().sum() == 0:
                continue
            q = g.groupby("who")[metric].quantile([0.5, 0.9, 0.95]).unstack()
            cells = "  ".join(f"{w}: {r[0.5]:.1f}/{r[0.9]:.1f}/{r[0.95]:.1f}"
                              for w, r in q.iterrows())
            print(f"   {meth:<9} {metric:<17} {cells}")

    # 4. Respiratory events and arousals (cohorts that annotate them) ─────────
    ev = df[df.cohort == "chal18"]
    if len(ev) and (ev.excluded != "").any():
        print("\n4. Effect of removing REM epochs with respiratory events or arousals "
              "(chal18, native band, share positive %)")
        e = ev[(ev.band == "native") & (ev.rem_minutes >= MIN_REM_MIN)].dropna(subset=["positive"])
        print((100 * e.assign(positive=e.positive.astype(float))
               .pivot_table(index="method", columns="excluded", values="positive",
                            aggfunc="mean")).round(1).to_string())


if __name__ == "__main__":
    main()
