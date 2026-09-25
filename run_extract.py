"""Stream CAP recordings: download -> extract -> discard raw.

Designed for hosted notebooks, where the session can vanish at any moment.
Progress is written to a manifest after every recording, so re-running
continues from where it stopped and never re-downloads finished work. The next
few recordings download in the background while the current one is being
extracted, and raw EDFs are deleted as soon as their derived file exists, so
disk use stays flat no matter how many recordings are processed.

    python run_extract.py                  # every CAP record (default)
    python run_extract.py rbd1 rbd2 n1     # specific records
    python run_extract.py --cohorts rbd n  # whole cohorts by prefix
    python run_extract.py --keep-raw       # keep EDFs (local debugging only)
"""
import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.fetch import fetch_cap, cap_records
from src.extract import extract_recording, summarise

MANIFEST = config.MANIFESTS / "cap_extract.json"
PREFETCH = 3          # recordings downloading ahead of the one being extracted


def load_manifest():
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except json.JSONDecodeError:
            pass
    return {"done": {}, "failed": {}}


def save_manifest(m):
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=2))
    tmp.replace(MANIFEST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="*")
    ap.add_argument("--cohorts", nargs="*", help="cohort prefixes, e.g. rbd n")
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    config.describe()
    groups = cap_records()
    if args.records:
        records = args.records
    elif args.cohorts:
        records = [r for c in args.cohorts for r in groups.get(c, [])]
    else:
        records = [r for g in groups.values() for r in g]
    print(f"\n{len(records)} records queued "
          f"(cohorts available: { {k: len(v) for k, v in groups.items()} })\n")

    m = load_manifest()
    todo = [r for r in records
            if r not in m["done"] or args.overwrite
            or not (config.DERIVED / f"{r}.npz").exists()]
    print(f"{len(m['done'])} already done, {len(todo)} to process\n")

    pool = ThreadPoolExecutor(max_workers=PREFETCH)
    pending = {}

    def prefetch(i):
        if i < len(todo) and i not in pending:
            pending[i] = pool.submit(fetch_cap, todo[i], config.SCRATCH)

    for i in range(PREFETCH):
        prefetch(i)

    t_start = time.time()
    for i, rec in enumerate(todo):
        prefetch(i + PREFETCH)
        t0 = time.time()
        print(f"[{i + 1}/{len(todo)}] {rec}", flush=True)
        edf = txt = None
        try:
            edf, txt = pending.pop(i).result()
            t_dl = time.time() - t0
            out = extract_recording(edf, txt, rec, overwrite=args.overwrite)
            print(f"    {summarise(out)}  (waited {t_dl:.0f}s for download, "
                  f"{time.time() - t0 - t_dl:.0f}s to extract)", flush=True)
            m["done"][rec] = {"file": out.name, "seconds": round(time.time() - t0, 1)}
            m["failed"].pop(rec, None)
        except Exception as e:
            print(f"    FAILED: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc(limit=2)
            m["failed"][rec] = f"{type(e).__name__}: {e}"
        finally:
            if not args.keep_raw:
                # Raw is disposable once the derived file exists (or failed).
                for p in (edf, txt):
                    if p is not None:
                        Path(p).unlink(missing_ok=True)
        save_manifest(m)
    pool.shutdown(wait=True)

    derived = sorted(p for p in config.DERIVED.glob("*.npz") if ".tmp" not in p.name)
    size = sum(p.stat().st_size for p in derived)
    print(f"\n{'=' * 70}")
    print(f"  {len(m['done'])} recordings extracted, {len(m['failed'])} failed "
          f"in {(time.time() - t_start) / 60:.1f} min")
    print(f"  derived data: {len(derived)} files, {size / 1e6:.0f} MB total")
    print(f"  location: {config.DERIVED}")
    if m["failed"]:
        print("\n  failures:")
        for k, v in m["failed"].items():
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
