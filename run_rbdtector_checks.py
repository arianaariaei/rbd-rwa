"""RBDtector checks asked for in review (paper/preregistration_revision.md, R5).

  verify      12 nights (6 CAP RBD, 3 CAP same-system patients, 3 MGH) scored twice:
              by our runner (vectorized find_rem_blocks, input trimmed to the REM
              stretch, 512 Hz decimated to 256 Hz, floor-corrected run reusing the
              published baseline) and by the program as released (its own
              find_rem_blocks, the whole night at the native rate, baseline
              recomputed). The tonic, phasic and "any" percentages and the baseline
              must agree.
  mgh         the 100 MGH nights of the Parkinson's analysis, each downloaded once and
              scored as before (heartbeat in, no arousals), with the arousals scored
              in the Challenge 2018 annotations passed to RBDtector (as its published
              cut-off assumes), and with the heartbeat removed from the chin EMG
  boas        the BOAS first nights as before and with the heartbeat removed (BOAS
              has no ECG; beats are found on the chin EMG, where detection passes)

    python run_rbdtector_checks.py --part verify|mgh|boas
    python run_rbdtector_checks.py --report
-> results/rbdtector_checks_<part>.csv (one row per night, check and variant),
   results/rbdtector_checks_report.md
"""
import argparse
import shutil
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from run_rbdtector import records_for

PARTS = ("verify", "mgh", "boas")
out_file = lambda part: config.RESULTS / f"rbdtector_checks_{part}.csv"
VERIFY = {"cap": ["rbd1", "rbd2", "rbd3", "rbd4", "rbd5", "rbd6", "nfle1", "plm1", "ins2"]}


def _work(name, rec, part, scratch):
    import warnings
    warnings.filterwarnings("ignore")
    from src import rbdtector as rt
    from src.cohorts import COHORTS, _beats
    from src.ecg import subtract_heartbeat
    from src.extract import bandpass
    rt.install()
    cohort = COHORTS[name]
    folder = Path(scratch) / f"rbdtc_{name}_{rec}"
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        d = cohort.read(rec, cohort.fetch(rec, folder))
        if not d["unit_known"]:
            raise ValueError("chin EMG has no physical units")
        fs, hyp = float(d["fs"]), np.asarray(d["hypnogram"])
        xf, _ = bandpass(d["chin"], fs, mains=cohort.mains)
        info = {"cohort": name, "record": rec, "fs": fs}

        def score(check, x, f, trim=True, fast=True, cache=True, arousals=None):
            rt.set_mode(fast=fast, cache=cache)
            sub = rt.write_inputs(folder / check, x, f, hyp, trim=trim, arousals=arousals)
            for variant in ("published", "FC"):
                t1 = time.time()
                r = rt.run(sub, variant)
                rows.append({**info, "check": check, "variant": variant,
                             "seconds": round(time.time() - t1, 1), **r})
            shutil.rmtree(sub, ignore_errors=True)

        half = (xf[::2], fs / 2) if fs == 512 else (xf, fs)
        if part == "verify":
            score("modified", *half)                               # as in run_rbdtector.py
            score("released", xf, fs, trim=False, fast=False, cache=False)
        else:
            beats = _beats(d)
            ev = d.get("events", {}).get("arousal", [])
            info.update(beats=int(len(beats)), n_arousals=len(ev))
            score("as_before", *half)
            if part == "mgh":
                score("arousals", *half, arousals=ev)
            if len(beats):
                xc = subtract_heartbeat(xf, fs, beats)
                score("heartbeat_removed", *((xc[::2], fs / 2) if fs == 512 else (xc, fs)))
        rt.set_mode()
        return rec, rows, None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc(limit=3)[-600:]}"
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def jobs(part):
    if part == "verify":
        mgh, _ = records_for("chal18", 100)
        return [("cap", r) for r in VERIFY["cap"]] + [("chal18", r) for r in mgh[:3]]
    if part == "mgh":
        mgh, _ = records_for("chal18", 100)
        return [("chal18", r) for r in mgh]
    boas, _ = records_for("boas", 0)
    return [("boas", r) for r in boas]


def report():
    df = pd.concat([pd.read_csv(out_file(p), dtype={"record": str}).assign(part=p)
                    for p in PARTS if out_file(p).exists()], ignore_index=True)
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    cols = ["tonic_pct", "phasic_pct", "any_pct", "baseline_uv"]
    v = df[df.part == "verify"]
    if not v.empty:
        say("V  Our runner against RBDtector as released (same nights; max |difference|)")
        w = v.pivot_table(index=["cohort", "record", "variant"], columns="check", values=cols)
        for c in cols:
            if ("modified", c) in [(b, a) for a, b in w.columns]:
                d = (w[(c, "modified")] - w[(c, "released")]).abs()
                say(f"    {c:<12} max {d.max():.4f}  nights identical (< 0.01) {int((d < 0.01).sum())} of {d.notna().sum()}")
        say()
    for part, a, b, label in (("mgh", "as_before", "arousals", "MGH with its scored arousals"),
                              ("mgh", "as_before", "heartbeat_removed", "MGH, heartbeat removed"),
                              ("boas", "as_before", "heartbeat_removed", "BOAS, heartbeat removed")):
        g = df[df.part == part]
        if g.empty:
            continue
        say(f"   RBDtector, {label}: share flagged (chin any >= 23.5%) and median any %")
        for (cohort, variant), s in g.groupby(["cohort", "variant"]):
            w = s.pivot_table(index="record", columns="check", values="any_pct")
            if a not in w or b not in w:
                continue
            w = w.dropna(subset=[a, b])
            pa, pb = (w[a] >= 23.5).mean(), (w[b] >= 23.5).mean()
            say(f"    {cohort:<7}{variant:<10} n={len(w):3d}  flagged {100 * pa:5.1f}% -> {100 * pb:5.1f}% "
                f"({100 * (pb - pa):+.1f} points)  median any {w[a].median():5.1f} -> {w[b].median():5.1f}")
        say()
    (config.RESULTS / "rbdtector_checks_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=list(PARTS))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--mirror", default=None)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.report:
        report()
        return
    from src import rbdtector as rt
    rt.install()
    todo = jobs(args.part)
    OUT = out_file(args.part)
    if OUT.exists():
        old = pd.read_csv(OUT, dtype={"record": str})
        seen = set(zip(old.cohort, old.record))
        todo = [j for j in todo if j not in seen]
    print(f"{args.part}: {len(todo)} nights to score", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(_work, c, r, args.part, str(config.SCRATCH)) for c, r in todo]
        for i, f in enumerate(as_completed(futs), 1):
            rec, rows, err = f.result()
            if err:
                print(f"[{i}/{len(todo)}] {rec} FAILED {err}", flush=True)
                continue
            new = pd.DataFrame(rows)
            if OUT.exists():                    # same columns in every row of a part
                new = pd.concat([pd.read_csv(OUT, dtype={"record": str}), new], ignore_index=True)
            new.to_csv(OUT, index=False)
            if args.mirror:
                try:
                    shutil.copy2(OUT, Path(args.mirror) / OUT.name)
                except OSError as e:
                    print(f"  (mirror failed: {e})", flush=True)
            print(f"[{i}/{len(todo)}] {rec} done ({len(rows)} runs)", flush=True)


if __name__ == "__main__":
    main()
