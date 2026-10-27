"""The ladder's harmonized steps with pink, drifting and recorded noise (review M6).

Pre-specified in paper/preregistration_revision.md (R1, R2). The same nights as the
noise ladder (the first 300 MGH records; CAP's nights in microvolts) are streamed
once more; each is raised to a quiet-REM level of 1.5 and 2.0 uV with each kind of
noise in src/noise_arms.py and scored with the published rules and with the
floor-corrected rules under three noise estimates (REM as pre-specified, N2/N3, and
the lower of the two). Only scores are kept.

    python run_noise_arms.py --library           # recorded-noise library from 30 HMC nights
    python run_noise_arms.py --cohort chal18     # the ladder's 300 MGH nights
    python run_noise_arms.py --cohort cap        # CAP (RBD and same-system patients)
    python run_noise_arms.py --report
-> DURABLE/noise_arms/<cohort>/<record>.csv.gz, results/noise_arms_scores.csv,
   results/noise_arms_report.md
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

OUT = config.DURABLE / "noise_arms"
LIB = config.DURABLE / "noise_library.npz"
REF_UV = 1.0


def variants():
    from src.rwa import METHODS, floor_corrected
    out = []
    for key in ("montreal", "sinbar"):
        m = METHODS[key]
        out.append((m.name, "published", m))
        for src in ("rem", "nrem", "min"):
            out.append((m.name, "FC" if src == "rem" else f"FC-{src}",
                        floor_corrected(m, REF_UV, noise_from=src)))
    out.append(("AASM", "published", METHODS["aasm"]))
    return out


def _library_work(rec, scratch):
    from src.cohorts import COHORTS, _beats
    from src.ecg import subtract_heartbeat
    from src.extract import bandpass
    from src.noise_arms import quiet_runs
    cohort = COHORTS["hmc"]
    folder = Path(scratch) / f"lib_{rec}"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        d = cohort.read(rec, cohort.fetch(rec, folder))
        fs = float(d["fs"])
        if fs != 256.0:
            return rec, None, f"rate {fs}"
        xf, _ = bandpass(d["chin"], fs, mains=cohort.mains)
        beats = _beats(d)
        if len(beats):
            xf = subtract_heartbeat(xf, fs, beats)
        return rec, quiet_runs(xf, fs, d["hypnogram"]), None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e}"
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def build_library(workers):
    from src.cohorts import COHORTS
    from src.noise_arms import build_library as splice, save_library
    recs = [r for r in COHORTS["hmc"].records() if r not in ("SN014", "SN064", "SN135")][::5][:30]
    pieces, used = [], []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for f in as_completed([ex.submit(_library_work, r, str(config.SCRATCH)) for r in recs]):
            rec, runs, err = f.result()
            if err or not runs:
                print(f"  {rec}: skipped ({err or 'no quiet REM runs'})", flush=True)
                continue
            pieces.append((rec, runs))
            used.append(rec)
            print(f"  {rec}: {sum(len(p) for p in runs) / 256:.0f} s of quiet REM", flush=True)
    pieces.sort()
    lib = splice([p for _, p in pieces])
    save_library(LIB, lib, {"nights": sorted(used), "seconds": round(len(lib) / 256.0, 1)})
    print(f"library: {len(used)} nights, {len(lib) / 256 / 60:.1f} min -> {LIB}", flush=True)


def _work(name, rec, scratch, out_path):
    import warnings
    warnings.filterwarnings("ignore")
    from src import noise_arms as na
    from src.cohorts import COHORTS, _beats, quiet_level
    from src.config import ENV_FS
    from src.ecg import subtract_heartbeat
    from src.extract import bandpass, bin_envelope
    from src.pack import build_pack
    from src.rwa import rem_atonia_index, score_night
    cohort = COHORTS[name]
    folder = Path(scratch) / f"arms_{name}_{rec}"
    folder.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        d = cohort.read(rec, cohort.fetch(rec, folder))
        if not d["unit_known"]:
            raise ValueError("chin EMG has no physical units")
        fs, hyp = float(d["fs"]), np.asarray(d["hypnogram"])
        xf, _ = bandpass(d["chin"], fs, mains=cohort.mains)
        beats = _beats(d)
        if len(beats):
            xf = subtract_heartbeat(xf, fs, beats)
        rms, mav = bin_envelope(xf, fs)
        chin = {"rms": rms, "mav": mav}
        added = {"native": (0.0, quiet_level(rms, hyp))}
        lib = na.load_library(LIB)[0] if LIB.exists() else None
        for kind in na.KINDS:
            if kind == "hmc" and lib is None:
                continue
            track = na.hmc(len(xf), fs, cohort.mains, rec, lib) if kind == "hmc" \
                else getattr(na, kind)(len(xf), fs, cohort.mains, rec)
            for t in na.TARGETS_UV:
                r, m, s, got = na.harmonized(xf, track, fs, hyp, t)
                band = f"{kind}_h{round(t * 100):03d}"
                chin[f"rms_{band}"], chin[f"mav_{band}"] = r, m
                added[band] = (s, got)
            del track
        pack = build_pack(chin, [], hyp, ENV_FS, EPOCH_SEC_, {"record": rec, "unit_known": True})
        rows = []
        info = {"cohort": name, "record": rec, "chin_fs": fs, "beats": int(len(beats))}
        for band, (s, lvl) in added.items():
            for meth, variant, m in variants():
                rows.append({**info, "band": band, "added_uv": round(s, 4), "level_uv": round(lvl, 4),
                             **score_night(pack, m, band), "variant": variant})
            rows.append({**info, "band": band, "added_uv": round(s, 4), "level_uv": round(lvl, 4),
                         **rem_atonia_index(pack, band), "variant": "published"})
        out = Path(out_path)
        tmp = out.with_name(out.name.replace(".csv.gz", ".tmp.csv.gz"))
        pd.DataFrame(rows).to_csv(tmp, index=False, compression="gzip")
        tmp.replace(out)
        return rec, round(time.time() - t0, 1), None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc(limit=2)[-400:]}"
    finally:
        shutil.rmtree(folder, ignore_errors=True)


EPOCH_SEC_ = 30


def records(name):
    from src.cohorts import COHORTS
    recs = COHORTS[name].records()
    return recs[:300] if name == "chal18" else recs


def run_cohort(name, workers, mirror):
    out_dir = OUT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    m = Path(mirror) / "noise_arms" / name if mirror else None
    if m:
        try:
            m.mkdir(parents=True, exist_ok=True)
            for p in m.glob("*.csv.gz"):
                if not (out_dir / p.name).exists():
                    shutil.copy2(p, out_dir / p.name)
        except OSError as e:
            print(f"(mirror unavailable: {e})", flush=True)
            m = None
    todo = [r for r in records(name) if not (out_dir / f"{r}.csv.gz").exists()]
    print(f"{name}: {len(todo)} nights to process", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_work, name, r, str(config.SCRATCH), str(out_dir / f"{r}.csv.gz")) for r in todo]
        for i, f in enumerate(as_completed(futs), 1):
            rec, secs, err = f.result()
            if err:
                print(f"[{i}/{len(todo)}] {rec} FAILED {err[:300]}", flush=True)
                continue
            if m:
                try:
                    shutil.copy2(out_dir / f"{rec}.csv.gz", m / f"{rec}.csv.gz")
                except OSError:
                    pass
            print(f"[{i}/{len(todo)}] {rec} {secs}s", flush=True)


def report():
    from run_report import MIN_REM, wilson
    from run_score import group_of
    files = [p for c in ("chal18", "cap") for p in sorted((OUT / c).glob("*.csv.gz"))
             if ".tmp" not in p.name]
    df = pd.concat((pd.read_csv(p) for p in files), ignore_index=True)
    df["group"] = [group_of(c, r) for c, r in zip(df.cohort, df.record)]
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512)
    df["who"] = np.select([same & (df.group == "RBD"), same & ~df.group.isin(["RBD", "healthy"]),
                           df.cohort == "chal18"], ["CAP RBD", "CAP patients", "MGH"], default="")
    df = df[df.who != ""]
    # one set of nights throughout: >= 10 min REM in every copy
    ok = df.groupby(["cohort", "record"]).rem_minutes.min() >= MIN_REM
    keep = ok[ok].index
    df = df.set_index(["cohort", "record"]).loc[keep].reset_index()
    df["y"] = df.positive.map(lambda x: float(x in (True, "True", 1, 1.0)) if pd.notna(x) else np.nan)
    df.to_csv(config.RESULTS / "noise_arms_scores.csv", index=False)
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    say("N1  Share flagged (%) by kind of noise at a quiet-REM level of 1.5 uV (h150) and 2.0 uV;")
    say("    the same nights (>= 10 min REM in every copy); native = as recorded")
    bands = ["native"] + [f"{k}_h{t}" for t in ("150", "200") for k in ("white", "pink", "drift", "hmc")]
    for who in ("MGH", "CAP RBD", "CAP patients"):
        g = df[df.who == who]
        say(f"  {who} (n={g.record.nunique()})  level: " + "  ".join(
            f"{b} {g[(g.band == b) & (g.method == 'Montreal') & (g.variant == 'published')].level_uv.median():.2f}"
            for b in bands if (g.band == b).any()))
        for meth, variant in (("Montreal", "published"), ("SINBAR", "published"), ("RAI", "published"),
                              ("Montreal", "FC"), ("SINBAR", "FC"), ("Montreal", "FC-nrem"),
                              ("SINBAR", "FC-nrem"), ("Montreal", "FC-min"), ("SINBAR", "FC-min")):
            s = g[(g.method == meth) & (g.variant == variant)]
            cells = "  ".join(f"{b} {100 * s[s.band == b].y.mean():5.1f}" for b in bands if (s.band == b).any())
            say(f"    {meth + ' ' + variant:<18} {cells}")
    say()
    say("N2  Paired differences from white noise at the same step (points; 95% bootstrap CI over nights)")
    rng = np.random.default_rng(4)
    for who in ("MGH", "CAP RBD", "CAP patients"):
        for meth, variant in (("Montreal", "published"), ("SINBAR", "published"),
                              ("Montreal", "FC"), ("SINBAR", "FC")):
            s = df[(df.who == who) & (df.method == meth) & (df.variant == variant)]
            w = s.pivot_table(index="record", columns="band", values="y")
            cells = []
            for t in ("150", "200"):
                for k in ("pink", "drift", "hmc"):
                    a, b = f"{k}_h{t}", f"white_h{t}"
                    if a not in w or b not in w:
                        continue
                    d = (w[a] - w[b]).dropna().to_numpy()
                    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
                    cells.append(f"{k}{t} {100 * d.mean():+5.1f} [{100 * np.percentile(bs, 2.5):+.1f},"
                                 f"{100 * np.percentile(bs, 97.5):+.1f}]")
            say(f"  {who:<13}{meth + ' ' + variant:<18} " + "  ".join(cells))
    say()
    (config.RESULTS / "noise_arms_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", action="store_true")
    ap.add_argument("--cohort", choices=["chal18", "cap"])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--mirror", default=None, help="Drive folder (e.g. MyDrive/rbd-rwa)")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.library:
        if args.mirror and (Path(args.mirror) / LIB.name).exists() and not LIB.exists():
            shutil.copy2(Path(args.mirror) / LIB.name, LIB)
        if not LIB.exists():
            build_library(args.workers)
            if args.mirror:
                shutil.copy2(LIB, Path(args.mirror) / LIB.name)
    if args.cohort:
        run_cohort(args.cohort, args.workers, args.mirror)
    if args.report:
        report()


if __name__ == "__main__":
    main()
