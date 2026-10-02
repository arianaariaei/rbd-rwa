"""RBDtector on the noise ladder and on three recording systems.

Pre-specified in paper/preregistration_parkinsons.md. Every night is streamed,
scored by RBDtector itself (src/rbdtector.py) with its published rule and with
the floor-corrected baseline, and discarded. The noise is the noise ladder's
own: the same seeded track and the same scale per step as run_cohort.py
--ladder, added to the night's band-passed chin EMG (heartbeat left in).

    python run_rbdtector.py --cohort cap                 # CAP RBD + same-system patients, ladder steps
    python run_rbdtector.py --cohort chal18 --sample 100 # MGH, as recorded (seeded sample)
    python run_rbdtector.py --cohort hmc                 # HMC, as recorded
    python run_rbdtector.py --cohort boas                # BOAS first nights, as recorded

-> results/rbdtector_scores.csv: one row per night, step and variant. Re-running
skips nights already scored; --mirror copies the file to Drive after each night.
"""
import argparse
import shutil
import sys
import time
import traceback
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config

LADDER_STEPS = ["native", "n050", "n100", "n200", "h150"]
OUT = config.RESULTS / "rbdtector_scores.csv"
MIN_REM = 10.0


def records_for(name, sample, seed=0):
    """The nights to score, taken from the external-cohort scores (same nights,
    same labels as the rest of the paper)."""
    ext = pd.read_csv(config.RESULTS / "external_scores.csv")
    ext = ext[(ext.method == "Montreal") & (ext.variant == "published")
              & (ext.rem_minutes >= MIN_REM) & ext.primary.astype(bool)]
    want = {"cap": ["CAP RBD", "CAP patients"], "chal18": ["MGH"], "hmc": ["HMC"],
            "boas": ["BOAS"]}[name]
    g = ext[ext.who.isin(want)].drop_duplicates("record")
    recs = sorted(g.record.astype(str))
    if sample and sample < len(recs):
        recs = sorted(np.random.default_rng(seed).choice(recs, sample, replace=False))
    return recs, dict(zip(g.record.astype(str), g.who))


def _work(name, rec, steps, scratch):
    """One night: download, the ladder's noise, RBDtector per step and variant."""
    import warnings
    warnings.filterwarnings("ignore")
    from src import rbdtector as rt
    from src.cohorts import COHORTS, extract_ladder_pack
    from src.extract import bandpass
    rt.install()
    cohort = COHORTS[name]
    folder = Path(scratch) / f"rbdt_{name}_{rec}"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        t0 = time.time()
        d = cohort.read(rec, cohort.fetch(rec, folder))
        t_dl = time.time() - t0
        if not d["unit_known"]:
            raise ValueError("chin EMG has no physical units")
        fs, hyp = d["fs"], np.asarray(d["hypnogram"])
        xf, _ = bandpass(d["chin"], fs, mains=cohort.mains)
        added, level = {"native": 0.0}, {"native": np.nan}
        nf = None
        if steps != ["native"]:
            meta = extract_ladder_pack(cohort, rec, d)["meta"]
            level["native"] = meta["level_uv"]
            for s, v in meta["ladder"].items():
                added[s], level[s] = v["added_uv"], v["level_uv"]
            rng = np.random.default_rng(zlib.crc32(rec.encode()))
            nf, _ = bandpass(rng.normal(0.0, 1.0, len(d["chin"])), fs, mains=cohort.mains)
            edge = int(5 * fs)
            nf /= np.sqrt(np.mean(nf[edge:-edge] ** 2))
        del d
        rows = []
        for step in steps:
            if step not in added:
                continue
            x = xf if step == "native" else xf + added[step] * nf
            # RBDtector works at 256 Hz; it resamples by spline, which at 512 Hz
            # (every other sample) is plain decimation - done here to save time
            x, f = (x[::2], fs / 2) if fs == 512 else (x, fs)
            sub = rt.write_inputs(folder / step, x, f, hyp)
            for variant in ("published", "FC"):
                t1 = time.time()
                r = rt.run(sub, variant)
                rows.append({"cohort": name, "record": rec, "step": step, "variant": variant,
                             "added_uv": added[step], "level_uv": level[step], "fs": fs,
                             "seconds": round(time.time() - t1, 1), **r})
            shutil.rmtree(sub, ignore_errors=True)
        return rec, rows, None, round(t_dl, 1)
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc(limit=3)[-600:]}", 0.0
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True, choices=["cap", "chal18", "hmc", "boas"])
    ap.add_argument("--sample", type=int, default=0, help="seeded random subset of nights")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many nights (test)")
    ap.add_argument("--mirror", default=None, help="copy the scores file here after each night")
    ap.add_argument("--steps", default=None,
                    help="comma-separated ladder steps (CAP default: " + ",".join(LADDER_STEPS) + ")")
    args = ap.parse_args()

    from src import rbdtector as rt
    rt.install()
    steps = args.steps.split(",") if args.steps else \
        (LADDER_STEPS if args.cohort == "cap" else ["native"])
    recs, who = records_for(args.cohort, args.sample)
    done = set()
    if OUT.exists():
        old = pd.read_csv(OUT, dtype={"record": str})
        old = old[old.cohort == args.cohort]
        done = set(zip(old.record, old.step))
    todo = {r: [s for s in steps if (r, s) not in done] for r in recs}
    todo = {r: s for r, s in todo.items() if s}
    n_done = len(recs) - len(todo)
    if args.limit:
        todo = dict(list(todo.items())[: args.limit])
    print(f"{args.cohort}: {len(recs)} nights, {n_done} fully scored, "
          f"{len(todo)} to score now at steps {steps} with {args.workers} workers", flush=True)
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(_work, args.cohort, r, s, str(config.SCRATCH)) for r, s in todo.items()]
        for i, f in enumerate(as_completed(futs), 1):
            rec, rows, err, t_dl = f.result()
            if err:
                print(f"[{i}/{len(todo)}] {rec} FAILED {err}", flush=True)
                continue
            df = pd.DataFrame(rows).assign(who=who.get(rec, ""))
            df.to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
            if args.mirror:
                try:
                    Path(args.mirror).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(OUT, Path(args.mirror) / OUT.name)
                except OSError as e:
                    print(f"  (mirror failed: {e})", flush=True)
            pub = df[(df.variant == "published") & (df.step == "native")]
            print(f"[{i}/{len(todo)}] {rec}  download {t_dl}s  RBDtector {df.seconds.mean():.0f}s/run  "
                  f"native any {pub.any_pct.iloc[0] if len(pub) else float('nan'):.1f}%  "
                  f"({(time.time() - t_start) / 60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()
