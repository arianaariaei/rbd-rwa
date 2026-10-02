"""What RBDtector counts as chin activity in noise alone (exploratory).

Not pre-specified: added after prediction PD2b was missed. Under the
floor-corrected baseline, RBDtector flagged 11.8 points more of CAP's same-system
patients at HMC's floor (1.5 uV) than as recorded, where 5 had been allowed. At
that floor the floor-corrected threshold is only 1.5 times the noise RMS, and
RBDtector judges 30-ms chunks - about 8 samples at 256 Hz, whose RMS in noise
alone varies far more than that of the 1-s windows the guard was chosen for.

This scores nights of band-limited white noise and nothing else (no muscle, no
heartbeat) at quiet-REM levels from 0.5 to 2 uV, with RBDtector's published
baseline and with the floor-corrected one at the pre-specified guard (1.5) and at
2.0. Whatever it reports is noise counted as muscle activity.

    python run_rbdtector_noise.py   -> results/rbdtector_noise.csv
"""
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config

LEVELS = (0.5, 1.0, 1.5, 2.0)      # noise RMS, uV (CAP patients 0.48, HMC 1.52)
SEEDS = (0, 1, 2)
FS = 256
# Wake, then four cycles of 25 min N2 and 20 min REM (80 min of REM), then N2
HYPNOGRAM = np.r_[[0] * 10, ([2] * 50 + [4] * 40) * 4, [2] * 10]
RULES = (("published", "published", None), ("FC", "FC", 1.5), ("FC, guard 2.0", "FC", 2.0))


def _night(level, seed):
    import warnings
    warnings.filterwarnings("ignore")
    from src import rbdtector as rt
    from src.extract import bandpass
    rt.install()
    rng = np.random.default_rng(1000 + seed)
    x, _ = bandpass(rng.normal(0.0, 1.0, len(HYPNOGRAM) * 30 * FS), FS, mains=50.0)
    edge = 5 * FS
    x *= level / np.sqrt(np.mean(x[edge:-edge] ** 2))
    folder = config.SCRATCH / f"rbdt_noise_{level}_{seed}"
    rows = []
    try:
        sub = rt.write_inputs(folder, x, FS, HYPNOGRAM)
        for label, variant, guard in RULES:
            rt.GUARD = guard or 1.5
            t0 = time.time()
            r = rt.run(sub, variant)
            r.pop("keys", None)
            rows.append({"level_uv": level, "seed": seed, "rule": label,
                         "seconds": round(time.time() - t0, 1), **r})
    finally:
        rt.GUARD = 1.5
        shutil.rmtree(folder, ignore_errors=True)
    return rows


def main():
    with ProcessPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(_night, lv, s) for lv in LEVELS for s in SEEDS]
        rows = [r for f in futs for r in f.result()]
    df = pd.DataFrame(rows)
    out = config.RESULTS / "rbdtector_noise.csv"
    df.to_csv(out, index=False)
    pd.set_option("display.width", 200)
    t = df.groupby(["rule", "level_uv"])[["any_pct", "phasic_pct", "tonic_pct", "baseline_uv"]]
    print("Noise alone, mean of", len(SEEDS), "nights (% of REM mini-epochs or epochs):")
    print(t.mean().round(2).to_string())
    print("max any_pct per rule and level:")
    print(df.groupby(["rule", "level_uv"]).any_pct.max().round(2).to_string())
    print(f"written -> {out}")


if __name__ == "__main__":
    main()
