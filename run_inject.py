"""Known muscle activity added to every night (paper/preregistration_injection.md).

    python run_inject.py --donors                    # CAP's RBD nights -> donors
    python run_inject.py --cohort cap                # CAP nights without RBD
    python run_inject.py --cohort hmc
    python run_inject.py --cohort chal18 --every 3   # MGH: every third record
    python run_inject.py --cohort boas
    python run_inject.py --cohort dodo / dodh

A donor is one RBD night's REM chin EMG, as the main pipeline sees it (src/inject.py,
make_donor); only nights on CAP's main system (512 Hz, microvolts) are used. Every
other night is streamed once and all its copies are scored at once: as recorded,
with synthetic tonic and phasic activity at 49 amplitudes, and with its assigned
donor's RBD activity at full and half amplitude. Only the scores are kept, one file
per night (DURABLE/inject/<cohort>/<record>.csv.gz); re-running skips nights done.

Donors are assigned in turn within each cohort: the cohort's records (after --every)
sorted by name, record i receives donor i mod 21, donors sorted by name. Every donor
therefore contributes about equally to every recording system.
"""
import argparse
import json
import shutil
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from run_cohort import Mirror

OUT = config.DURABLE / "inject"


def _rbd(rec):
    return "".join(c for c in rec if not c.isdigit()) == "rbd"


def _donor_work(rec, scratch, out_path, keep_raw):
    from src.cohorts import COHORTS
    from src.inject import make_donor, save_donor
    cohort = COHORTS["cap"]
    folder = Path(scratch) / f"donor_{rec}"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        d = cohort.read(rec, cohort.fetch(rec, folder))
        if not (float(d["fs"]) == 512.0 and d["unit_known"]):
            return rec, None, f"not on CAP's main system ({d['fs']} Hz, units known: {d['unit_known']})"
        donor = make_donor(cohort, rec, d)
        save_donor(Path(out_path), donor)
        return rec, {k: donor[k] for k in ("fs", "level_uv", "rem_epochs")}, None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc(limit=2)[-300:]}"
    finally:
        if not keep_raw:
            shutil.rmtree(folder, ignore_errors=True)


def _work(name, rec, demo, scratch, out_path, donor_path, keep_raw):
    """Runs in a worker process: one night from download to scores."""
    import pandas as pd
    from src.cohorts import COHORTS
    from src.inject import load_donor, run_night
    cohort = COHORTS[name]
    t0 = time.time()
    folder = Path(scratch) / rec
    folder.mkdir(parents=True, exist_ok=True)
    try:
        files = cohort.fetch(rec, folder)
        t_dl = time.time() - t0
        d = cohort.read(rec, files)
        donor = load_donor(donor_path) if donor_path else None
        rows = run_night(cohort, rec, d, donor, info=dict(demo or {}))
        out = Path(out_path)
        tmp = out.with_name(out.name.replace(".csv.gz", ".tmp.csv.gz"))
        pd.DataFrame(rows).to_csv(tmp, index=False, compression="gzip")
        tmp.replace(out)
        return rec, {"seconds": round(time.time() - t0, 1), "download_s": round(t_dl, 1),
                     "rem_min": rows[0]["rem_minutes"], "level_uv": rows[0]["level_uv"],
                     "donor": donor["record"] if donor else None}, None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc(limit=2)[-300:]}"
    finally:
        if not keep_raw:
            shutil.rmtree(folder, ignore_errors=True)


def _manifest(name):
    p = config.MANIFESTS / f"inject_{name}.json"
    return p, (json.loads(p.read_text()) if p.exists() else {"done": {}, "failed": {}})


def _save(path, m):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=1))
    tmp.replace(path)


def run(jobs, workers, manifest_name, fn, report):
    path, m = _manifest(manifest_name)
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(fn, *args) for args in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            rec, info, err = f.result()
            if err:
                m["failed"][rec] = err
                print(f"[{i}/{len(jobs)}] {rec} FAILED {err[:200]}", flush=True)
            else:
                m["done"][rec] = info
                m["failed"].pop(rec, None)
                report(rec, info)
                print(f"[{i}/{len(jobs)}] {rec}  {info}", flush=True)
            _save(path, m)
    print(f"{manifest_name}: {len(m['done'])} done, {len(m['failed'])} failed, "
          f"{(time.time() - t_start) / 60:.1f} min", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort")
    ap.add_argument("--donors", action="store_true", help="build the RBD donors from CAP")
    ap.add_argument("--every", type=int, default=1, help="use every k-th record (MGH: 3)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many (testing)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--mirror", default=None, help="also copy each result here (Drive)")
    args = ap.parse_args()
    config.describe()

    if args.donors:
        from src.fetch import cap_records
        out_dir = OUT / "donors"
        out_dir.mkdir(parents=True, exist_ok=True)
        mirror = Mirror(Path(args.mirror) / "donors" if args.mirror else None)
        mirror.restore(out_dir)
        recs = sorted((r for g in cap_records().values() for r in g if _rbd(r)),
                      key=lambda r: int("".join(c for c in r if c.isdigit())))
        todo = [r for r in recs if not (out_dir / f"{r}.npz").exists()]
        if args.limit:
            todo = todo[: args.limit]
        print(f"donors: {len(recs)} CAP RBD nights, {len(todo)} to extract", flush=True)
        run([(r, str(config.SCRATCH), str(out_dir / f"{r}.npz"), args.keep_raw) for r in todo],
            args.workers, "donors", _donor_work, lambda r, i: mirror.push(out_dir / f"{r}.npz"))
        return

    from src.cohorts import COHORTS
    name = args.cohort
    cohort = COHORTS[name]
    donors = sorted((p for p in (config.DURABLE / "inject" / "donors").glob("rbd*.npz")
                     if ".tmp" not in p.name),
                    key=lambda p: int("".join(c for c in p.stem if c.isdigit())))
    if not donors:
        print("no donors yet: run with --donors first; continuing without the transplant",
              flush=True)
    records = [r for r in cohort.records() if not (name == "cap" and _rbd(r))]
    records = sorted(records[:: args.every])
    donor_of = {r: (str(donors[i % len(donors)]) if donors else None)
                for i, r in enumerate(records)}
    out_dir = OUT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    mirror = Mirror(Path(args.mirror) / name if args.mirror else None)
    if mirror.ok:
        try:
            for p in mirror.path.glob("*.csv.gz"):
                if not (out_dir / p.name).exists():
                    shutil.copy2(p, out_dir / p.name)
        except OSError as e:
            mirror._fail(e)
    todo = [r for r in records if not (out_dir / f"{r}.csv.gz").exists()]
    if args.limit:
        todo = todo[: args.limit]
    demo = cohort.demographics()
    print(f"\n{name}: {len(records)} nights (every {args.every}), {len(todo)} to process with "
          f"{args.workers} workers; {len(donors)} donors\n", flush=True)
    run([(name, r, demo.get(r), str(config.SCRATCH), str(out_dir / f"{r}.csv.gz"),
          donor_of[r], args.keep_raw) for r in todo],
        args.workers, name, _work, lambda r, i: mirror.push(out_dir / f"{r}.csv.gz"))


if __name__ == "__main__":
    main()
