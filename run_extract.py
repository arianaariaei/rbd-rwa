"""Stream CAP recordings: download -> extract -> discard raw.

Designed for Colab, where the session can vanish at any moment. Progress is
written to a manifest after every recording, so re-running continues from where
it stopped and never re-downloads finished work. Raw EDFs are deleted as soon
as their derived file exists, so disk use stays flat no matter how many
recordings are processed.

    python run_extract.py                  # default cohort: RBD + healthy
    python run_extract.py rbd1 rbd2 n1     # specific records
    python run_extract.py --all            # every CAP record
    python run_extract.py --keep-raw       # keep EDFs (local debugging only)
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.fetch import fetch_cap, cap_records
from src.extract import extract_recording, summarise

MANIFEST = config.MANIFESTS / "cap_extract.json"


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
    ap.add_argument("--all", action="store_true", help="every CAP record")
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    config.describe()
    groups = cap_records()
    if args.all:
        records = [r for g in groups.values() for r in g]
    elif args.records:
        records = args.records
    else:
        records = groups.get("rbd", []) + groups.get("n", [])
    print(f"\n{len(records)} records queued "
          f"(cohorts available: { {k: len(v) for k, v in groups.items()} })\n")

    m = load_manifest()
    todo = [r for r in records
            if r not in m["done"] or args.overwrite
            or not (config.DERIVED / f"{r}.npz").exists()]
    print(f"{len(m['done'])} already done, {len(todo)} to process\n")

    for i, rec in enumerate(todo, 1):
        t0 = time.time()
        print(f"[{i}/{len(todo)}] {rec}")
        try:
            edf, txt = fetch_cap(rec, config.SCRATCH)
            out = extract_recording(edf, txt, rec, overwrite=args.overwrite)
            print(f"    {summarise(out)}")
            if not args.keep_raw:
                # Raw is disposable the moment the derived file exists.
                for p in (edf, txt):
                    Path(p).unlink(missing_ok=True)
            m["done"][rec] = {"file": out.name, "seconds": round(time.time() - t0, 1)}
            m["failed"].pop(rec, None)
        except Exception as e:
            print(f"    FAILED: {type(e).__name__}: {e}")
            traceback.print_exc(limit=2)
            m["failed"][rec] = f"{type(e).__name__}: {e}"
        save_manifest(m)

    derived = sorted(config.DERIVED.glob("*.npz"))
    size = sum(p.stat().st_size for p in derived)
    print(f"\n{'='*70}")
    print(f"  {len(m['done'])} recordings extracted, {len(m['failed'])} failed")
    print(f"  derived data: {len(derived)} files, {size/1e6:.0f} MB total")
    print(f"  location: {config.DERIVED}")
    if m["failed"]:
        print("\n  failures:")
        for k, v in m["failed"].items():
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
