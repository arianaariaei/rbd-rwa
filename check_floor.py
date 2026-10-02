"""Floor check for one recording (see src/floorcheck.py).

    python check_floor.py night.edf stages.txt                 # chin found by name
    python check_floor.py night.edf stages.txt --chin "Chin1-Chin2" --mains 60
    python check_floor.py night.edf stages.txt --rem 5         # numeric stage file

stages.txt: one 30 s stage per line from the start of the EDF (W, N1, N2, N3, R),
or numbers with --rem (and --nrem) giving the codes for REM and N2/N3.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.ecg import find_ecg
from src.edf import read_header, read_channel
from src.extract import find_emg, read_source
from src.floorcheck import floor_report, format_report, read_stages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edf")
    ap.add_argument("stages")
    ap.add_argument("--chin", default=None, help="chin EMG channel label (default: found by name)")
    ap.add_argument("--mains", type=float, default=50.0, help="mains frequency to notch (50 or 60)")
    ap.add_argument("--rem", type=int, default=None, help="REM code in a numeric stage file")
    ap.add_argument("--nrem", default="2,3", help="N2/N3 codes in a numeric stage file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    hdr = read_header(args.edf)
    src = hdr.find(args.chin) if args.chin else find_emg(hdr)[0]
    if src is None:
        sys.exit(f"no chin EMG found among {[c.label for c in hdr.channels]}; use --chin")
    chin, fs, unit_known, label, _ = read_source(hdr, src)
    if not unit_known:
        sys.exit(f"{label}: no physical unit in the EDF header - the floor needs microvolts")
    ecg_src = find_ecg(hdr)
    ecg, fs_e = read_source(hdr, ecg_src)[:2] if ecg_src is not None else (None, None)
    stages = read_stages(args.stages, args.rem, tuple(int(v) for v in args.nrem.split(",")))
    r = floor_report(chin, fs, stages, ecg, fs_e, args.mains)
    print(json.dumps(r, indent=1) if args.json else f"{Path(args.edf).name}, {label}\n" + format_report(r))


if __name__ == "__main__":
    main()
