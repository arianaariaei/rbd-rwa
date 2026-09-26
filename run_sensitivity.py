"""How much does the operational definition of "background" move the verdicts?

The visual methods judge activity against the background EMG a scorer sees by
eye. An automated version has to choose a number; this script re-scores every
night (native band, all REM) under several choices and reports, for Montreal,
SINBAR and AASM, the share of nights flagged positive per group and the RBD
separation (AUC vs same-system CAP patients). The RAI does not use a
background and is not affected.

    python run_sensitivity.py
"""
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.pack import load_pack
from src.rwa import METHODS, score_night

# name -> background used by the relative criteria. AASM's tonic criterion is
# defined against the minimum NREM amplitude and keeps that definition.
VARIANTS = ["p5_rem", "p10_rem", "p25_rem", "p50_rem", "min_rem", "p5_nrem"]
MIN_REM = 10.0
CAP_GROUPS = {"rbd": "RBD", "n": "healthy", "nfle": "NFLE", "plm": "PLM",
              "ins": "insomnia", "narco": "narcolepsy", "sdb": "SDB", "brux": "bruxism"}


def auc(pos, neg):
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    pos, neg = pos[np.isfinite(pos)], neg[np.isfinite(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    d = pos[:, None] - neg[None, :]
    return float(((d > 0) + 0.5 * (d == 0)).mean())


def main():
    rows = []
    for cdir in sorted((config.DURABLE / "packs").glob("*")):
        for p in sorted(cdir.glob("*.npz")):
            pack = load_pack(p)
            m = pack["meta"]
            cohort = m.get("cohort", cdir.name)
            group = CAP_GROUPS.get("".join(c for c in m["record"] if not c.isdigit()), "other") \
                if cohort == "cap" else "clinical"
            for v in VARIANTS:
                for key in ("montreal", "sinbar", "aasm"):
                    meth = METHODS[key]
                    meth = dataclasses.replace(meth, phasic_baseline=v, tonic_baseline=(
                        meth.tonic_baseline if key == "aasm" else v))
                    r = score_night(pack, meth)
                    rows.append({"cohort": cohort, "record": m["record"], "group": group,
                                 "chin_fs": m.get("chin_fs", m.get("chin_info", {}).get("fs")),
                                 "unit_known": m.get("unit_known", True), "variant": v, **r})
        print(f"{cdir.name}: done", flush=True)
    df = pd.DataFrame(rows)
    df = df[df.rem_minutes >= MIN_REM]
    df.to_csv(config.RESULTS / "sensitivity_background.csv", index=False)
    who = np.where(df.cohort == "cap", "CAP " + df.group, df.cohort)
    df = df.assign(who=who)

    print("\nShare flagged POSITIVE (%) by background definition")
    pos = df.dropna(subset=["positive"]).assign(
        positive=lambda d: d.positive.map(lambda x: float(x in (True, "True", 1, 1.0))))
    t = pos.pivot_table(index=["method", "variant"], columns="who", values="positive",
                        aggfunc="mean") * 100
    cols = [c for c in ["CAP RBD", "CAP healthy", "CAP NFLE", "CAP PLM", "chal18", "hmc",
                        "hmc_q1uv", "hmc_mgh", "hmc_low", "hmc_low_mgh", "chal18_noise"]
            if c in t.columns]
    print(t[cols].round(0).to_string())

    print("\nRBD vs same-system CAP patients (AUC) by background definition")
    same = (df.cohort == "cap") & (df.chin_fs == 512) & df.unit_known.astype(bool)
    out = []
    for (meth, v), g in df[same].groupby(["method", "variant"]):
        for metric in ("tonic_pct", "phasic_pct", "any_pct", "phasic_epoch_pct"):
            if metric in g and g[metric].notna().any():
                out.append(dict(method=meth, variant=v, metric=metric,
                                auc=auc(g.loc[g.group == "RBD", metric],
                                        g.loc[~g.group.isin(["RBD", "healthy"]), metric])))
    print(pd.DataFrame(out).pivot_table(index=["method", "metric"], columns="variant",
                                        values="auc").round(3).to_string())


if __name__ == "__main__":
    main()
