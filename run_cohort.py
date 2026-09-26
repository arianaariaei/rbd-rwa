"""Build packs for a whole open cohort: download -> extract -> discard raw.

    python run_cohort.py --cohort chal18             # 994 MGH PSGs
    python run_cohort.py --cohort hmc                # 148 Haaglanden PSGs
    python run_cohort.py --cohort chal18 --limit 5   # quick test
    python run_cohort.py --cohort cap                # repack CAP's derived files

Several records are processed at once (--workers), each in its own process,
so downloads overlap with computation. Progress is written to a manifest
after every record, so re-running continues where it stopped. Raw files are
deleted as soon as their pack exists.
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
from src.pack import save_pack


def _work(name, rec, demo, scratch, out_path, keep_raw):
    """Runs in a worker process: one record from download to pack."""
    from src.cohorts import COHORTS, extract_pack
    cohort = COHORTS[name]
    t0 = time.time()
    folder = Path(scratch) / rec
    folder.mkdir(parents=True, exist_ok=True)
    try:
        files = cohort.fetch(rec, folder)
        t_dl = time.time() - t0
        d = cohort.read(rec, files)
        pack = extract_pack(cohort, rec, d, demo)
        save_pack(Path(out_path), pack)
        m = pack["meta"]
        return rec, {"seconds": round(time.time() - t0, 1), "download_s": round(t_dl, 1),
                     "rem_min": round(m["n_rem_epochs"] * 0.5, 1),
                     "ecg": m["ecg"]["artifact_ratio_before"]}, None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc(limit=2)[-300:]}"
    finally:
        if not keep_raw:
            shutil.rmtree(folder, ignore_errors=True)


def repack_cap(out_dir):
    """CAP was extracted to full-night files; convert them to packs."""
    from src.extract import load_derived
    from src.pack import pack_from_full
    files = sorted(p for p in config.DERIVED.glob("*.npz") if ".tmp" not in p.name)
    for p in files:
        out = out_dir / p.name
        if out.exists():
            continue
        pack = pack_from_full(load_derived(p))
        pack["meta"]["cohort"] = "cap"
        save_pack(out, pack)
    print(f"cap: {len(list(out_dir.glob('*.npz')))} packs in {out_dir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()

    out_dir = config.DURABLE / "packs" / args.cohort
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.cohort == "cap":
        repack_cap(out_dir)
        return

    from src.cohorts import COHORTS
    cohort = COHORTS[args.cohort]
    manifest = config.MANIFESTS / f"{args.cohort}_packs.json"
    m = json.loads(manifest.read_text()) if manifest.exists() else {"done": {}, "failed": {}}
    records = cohort.records()
    demo = cohort.demographics()
    todo = [r for r in records if not (out_dir / f"{r}.npz").exists()]
    if args.limit:
        todo = todo[: args.limit]
    config.describe()
    print(f"\n{args.cohort}: {len(records)} records, {len(records) - len(todo)} done, "
          f"{len(todo)} to process with {args.workers} workers\n", flush=True)

    t_start = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(_work, args.cohort, r, demo.get(r), str(config.SCRATCH),
                          str(out_dir / f"{r}.npz"), args.keep_raw) for r in todo]
        for i, f in enumerate(as_completed(futs), 1):
            rec, info, err = f.result()
            if err:
                m["failed"][rec] = err
                print(f"[{i}/{len(todo)}] {rec} FAILED {err[:160]}", flush=True)
            else:
                m["done"][rec] = info
                m["failed"].pop(rec, None)
                print(f"[{i}/{len(todo)}] {rec}  REM {info['rem_min']} min  "
                      f"ECG x{info['ecg']}  ({info['download_s']}s download, "
                      f"{info['seconds']}s total)", flush=True)
            tmp = manifest.with_suffix(".tmp")
            tmp.write_text(json.dumps(m, indent=1))
            tmp.replace(manifest)

    packs = list(out_dir.glob("*.npz"))
    size = sum(p.stat().st_size for p in packs) / 1e9
    print(f"\n{args.cohort}: {len(packs)} packs ({size:.2f} GB), {len(m['failed'])} failed, "
          f"{(time.time() - t_start) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
