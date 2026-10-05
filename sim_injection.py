"""White-noise predictions for the injection experiment.

The same injection and scoring as run_inject.py, on synthetic nights whose chin
EMG is band-limited white noise at a known floor: the detection threshold each
rule would have if a night's background were only the noise the ladder adds.
Real nights are compared with these (criterion A4, paper/preregistration_injection.md),
and the relation between floor and threshold here is the theoretical one the
real nights are expected to follow.

    python sim_injection.py           -> results/inject_whitenoise.csv (every copy)
                                         results/inject_whitenoise_a50.csv
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.extract import bandpass
from src.inject import a50_table, run_night
from src.rwa import NOISE_P5_RATIO

FLOORS_UV = (0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0)
RATES = (200, 250, 256, 512)
SEEDS = (0, 1, 2)
# 10 epochs awake, four cycles of 20 min N2 and 12.5 min REM, 5 min N2: 100 REM epochs
HYPNOGRAM = np.r_[[0] * 10, ([2] * 40 + [4] * 25) * 4, [2] * 10].astype(np.int8)


class WhiteNoise:
    name, mains = "whitenoise", 50.0


def night(fs, floor, seed):
    """Raw white noise scaled so that its in-band RMS is floor / 0.91, the noise
    a quiet-REM level (5th percentile of 1-s RMS) of `floor` implies."""
    rng = np.random.default_rng(seed)
    w = rng.normal(0.0, 1.0, int(len(HYPNOGRAM) * 30 * fs))
    k = floor / NOISE_P5_RATIO / np.sqrt(np.mean(bandpass(w, fs, mains=50.0)[0] ** 2))
    return dict(chin=w * k, fs=float(fs), unit_known=True, hypnogram=HYPNOGRAM)


def one(args):
    fs, floor, seed = args
    rec = f"f{fs}_b{floor:g}_s{seed}"
    rows = run_night(WhiteNoise(), rec, night(fs, floor, seed),
                     info={"sim_fs": fs, "sim_floor_uv": floor, "seed": seed})
    return rows


def main(workers=3):
    jobs = [(fs, b, s) for fs in RATES for b in FLOORS_UV for s in SEEDS]
    print(f"{len(jobs)} synthetic nights", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = [r for part in ex.map(one, jobs) for r in part]
    df = pd.DataFrame(rows)
    df.to_csv(config.RESULTS / "inject_whitenoise.csv", index=False)
    a = a50_table(df)
    info = df.drop_duplicates(["cohort", "record"]).set_index(["cohort", "record"])
    for col in ("sim_fs", "sim_floor_uv", "seed", "level_uv"):
        a[col] = info[col].reindex(pd.MultiIndex.from_frame(a[["cohort", "record"]])).to_numpy()
    a.to_csv(config.RESULTS / "inject_whitenoise_a50.csv", index=False)
    print(a.groupby(["method", "measure", "pattern", "variant", "sim_floor_uv"]).a50.median()
          .unstack("sim_floor_uv").round(2).to_string())
    return a


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
