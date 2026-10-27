"""Run the RWA analyses on recordings that cannot leave their center.

For a sleep center holding polysomnograms of patients with RBD or Parkinson's
disease: everything runs on the center's own computer, and the output is one row
of numbers per night (no signal, no date, no identifier beyond the center's own
code), which the center can share or keep.

    python run_site.py manifest.csv --out site_results
    python run_site.py manifest.csv --out site_results --ladder   # + a 1.5-uV copy

manifest.csv, one row per night (header required):
    code,edf,stages,group[,age,sex,chin,ecg,mains]
  code    the center's own pseudonym for the night (e.g. RBD017)
  edf     path to the EDF/EDF+ file (chin EMG in physical units, uV or mV)
  stages  30-s stages from the start of the EDF, one per line: W, N1, N2, N3, R
  group   e.g. iRBD, PD+RBD, PD-RBD, control
  age, sex           optional
  chin, ecg          optional channel labels (default: found by name)
  mains              50 or 60 (default 50)

Outputs (in --out):
  site_scores.csv    per night: REM minutes, quiet-REM level (noise floor), net
                     N2/N3 level (gain check), and for the Montreal and SINBAR chin
                     criteria (published and floor-corrected, with the REM and the
                     N2/N3 noise estimate) and the REM Atonia Index: tonic, phasic
                     and "any" percentages and the verdict. With --ladder, the same
                     night again with white noise raising its quiet-REM level to
                     1.5 uV (the paper's noise ladder), so the effect of a noisier
                     system can be measured on the center's own patients.
  site_summary.md    by group: nights, floor, share flagged by each rule.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src.config import ENV_FS
from src.ecg import find_ecg, plausible, r_peaks, subtract_heartbeat
from src.edf import read_header
from src.extract import bandpass, bin_envelope, find_emg, read_source
from src.floorcheck import read_stages
from src.pack import build_pack
from src.rwa import METHODS, floor_corrected, rem_atonia_index, score_night

EPOCH_SEC = 30


def variants():
    out = []
    for key in ("montreal", "sinbar"):
        m = METHODS[key]
        out += [("published", m), ("FC", floor_corrected(m, 1.0)),
                ("FC-nrem", floor_corrected(m, 1.0, noise_from="nrem"))]
    return out


def find_chin(hdr):
    """The pipeline's chin finder, then any single channel named like a chin EMG."""
    src = find_emg(hdr)[0]
    if src is None:
        norm = lambda c: c.label.upper().replace(" ", "").replace("-", "")
        hits = [c for c in hdr.channels if any(k in norm(c) for k in ("CHIN", "MENT", "SUBM"))]
        src = hits[0] if len(hits) >= 1 else None
    return src


def one_night(row, ladder):
    hdr = read_header(row["edf"])
    src = hdr.find(row["chin"]) if row.get("chin") else find_chin(hdr)
    if src is None:
        raise ValueError(f"no chin EMG among {[c.label for c in hdr.channels]}")
    chin, fs, unit_known, label, _ = read_source(hdr, src)
    if not unit_known:
        raise ValueError(f"{label}: no physical unit in the EDF header")
    mains = float(row.get("mains") or 50)
    ecg_src = hdr.find(row["ecg"]) if row.get("ecg") else find_ecg(hdr)
    beats = np.empty(0)
    if ecg_src is not None:
        e, fs_e = read_source(hdr, ecg_src)[:2]
        beats = r_peaks(e, fs_e)
        if not plausible(beats, len(e) / fs_e):
            beats = np.empty(0)
    xf, band = bandpass(chin, fs, mains=mains)
    if len(beats):
        xf = subtract_heartbeat(xf, fs, beats)
    hyp = np.asarray(read_stages(row["stages"]))
    rows_env = {}
    rms, mav = bin_envelope(xf, fs)
    rows_env["rms"], rows_env["mav"] = rms, mav
    if ladder:
        from src.noise_arms import harmonized, white
        r, m, s, got = harmonized(xf, white(len(xf), fs, mains, row["code"]), fs, hyp, 1.5)
        rows_env["rms_white_h150"], rows_env["mav_white_h150"] = r, m
    pack = build_pack(rows_env, [], hyp, ENV_FS, EPOCH_SEC, {"record": row["code"], "unit_known": True})
    from run_floor import scale
    info = {"code": row["code"], "group": row["group"], "age": row.get("age"), "sex": row.get("sex"),
            "chin": label, "fs": fs, "band": f"{band[0]:g}-{band[1]:g}", "beats": int(len(beats)),
            **{k: round(v, 3) for k, v in scale(pack).items()}}
    out = []
    for copy in (("native", "white_h150") if ladder else ("native",)):
        for variant, m in variants():
            r = score_night(pack, m, copy)
            out.append({**info, "copy": copy, "variant": variant, **{k: r.get(k) for k in (
                "method", "rem_minutes", "background_phasic_uV", "tonic_pct", "phasic_pct", "any_pct",
                "positive", "error")}})
        r = rem_atonia_index(pack, copy)
        out.append({**info, "copy": copy, "variant": "published", "method": "RAI",
                    "rem_minutes": r.get("rem_minutes"), "rai": r.get("rai"), "positive": r.get("positive"),
                    "error": r.get("error")})
    return out


def summary(df):
    lines = ["# RWA site summary", "",
             "Share of nights flagged positive (%), by group; floor = quiet-REM level (uV, median).", ""]
    if df.empty:
        return "# RWA site summary\n\nNo night could be scored.\n"
    d = df[(df["copy"] == "native") & (df.rem_minutes >= 10)]
    for group, g in d.groupby("group"):
        floor = g[(g.method == "Montreal") & (g.variant == "published")].background_phasic_uV.median()
        lines.append(f"## {group}: {g.code.nunique()} nights, floor {floor:.2f} uV")
        for (meth, variant), s in g.groupby(["method", "variant"]):
            v = s.positive.map(lambda x: x in (True, "True")).astype(float)
            lines.append(f"- {meth} {variant}: {100 * v.mean():.0f}% ({int(v.sum())}/{len(v)})")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", default="site_results")
    ap.add_argument("--ladder", action="store_true", help="also score a copy at a 1.5-uV floor")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(args.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    results, failed = [], []
    for i, row in enumerate(rows, 1):
        try:
            results += one_night(row, args.ladder)
            print(f"[{i}/{len(rows)}] {row['code']} done", flush=True)
        except Exception as e:
            failed.append((row["code"], f"{type(e).__name__}: {e}"))
            print(f"[{i}/{len(rows)}] {row['code']} FAILED {e}", flush=True)
    df = pd.DataFrame(results)
    df.to_csv(out / "site_scores.csv", index=False)
    (out / "site_summary.md").write_text(summary(df) + "\n" + "\n".join(
        f"- failed: {c}: {e}" for c, e in failed) + "\n", encoding="utf-8")
    print(f"wrote {out / 'site_scores.csv'} and {out / 'site_summary.md'}")


if __name__ == "__main__":
    main()
