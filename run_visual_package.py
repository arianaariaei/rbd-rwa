"""Blinded visual-scoring substudy: the excerpts, the scoring sheets and the key.

Protocol: paper/visual_substudy_protocol.md (to be registered on OSF before any
scoring). Thirty nights are drawn with a fixed seed: 10 CAP RBD (CAP's main
system), 10 MGH and 10 HMC. Each group's nights are taken in a seeded random order
and a night is used only if it has a stretch of 20 consecutive REM epochs and a
quiet-REM level below 1.2 uV as recorded (amendment of 27 Oct 2026, before any
scoring; skipped nights are listed in <out>_KEY/skipped.csv). From each night the
first such stretch is exported with 4 epochs of context on each side, twice: as
recorded, and with
band-limited white noise added to the chin EMG at the level that raises the
night's quiet-REM level to 1.5 uV (the noise ladder's step h150). The 60 excerpts
are numbered in random order, so the scorer cannot tell the two copies of a night
apart or which cohort an excerpt comes from.

    python run_visual_package.py --out /content/drive/MyDrive/rbd-rwa/visual_study

-> <out>/excerpts/V01.edf ... V60.edf (chin EMG, central EEG, ECG; stages and the
   epochs to score as EDF+ annotations), <out>/scoring_minis.csv and
   <out>/scoring_epochs.csv (blank sheets), <out>/README_for_scorer.md;
   <out>_KEY/key.csv (which night and copy each excerpt is, and the automated
   scores of the same epochs) - for the organizer only, never for the scorer.
"""
import argparse
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

SEED = 20261027
N_PER = 10
N_SCORE, CONTEXT = 20, 4
MAX_LEVEL = 1.2      # uV as recorded: the noisy copy must differ from the recorded one
STAGE = {0: "W", 1: "N1", 2: "N2", 3: "N3", 4: "R"}


def candidates():
    """Each group's nights in a seeded random order; the first N_PER eligible ones are used."""
    from run_rbdtector import records_for
    rng = np.random.default_rng(SEED)
    out = []
    for cohort, who in (("cap", "CAP RBD"), ("chal18", "MGH"), ("hmc", "HMC")):
        recs, labels = records_for(cohort, 0)
        out.append((cohort, list(rng.permutation(sorted(r for r in recs if labels[r] == who)))))
    return out


def scored_stretch(hyp):
    """Epoch numbers of the 20 REM epochs to score."""
    rem = np.flatnonzero(np.asarray(hyp) == 4)
    runs = np.split(rem, np.flatnonzero(np.diff(rem) != 1) + 1) if len(rem) else []
    long = [r for r in runs if len(r) >= N_SCORE]
    return long[0][:N_SCORE] if long else np.array([], int)


def automated(xf, fs, hyp, epochs):
    """Automated SINBAR "any" % (3-s mini-epochs) and tonic % (30-s epochs) on the
    scored epochs, published and floor-corrected, with the whole night's background."""
    from src.config import ENV_FS
    from src.extract import bin_envelope
    from src.pack import build_pack
    from src.rwa import METHODS, floor_corrected, score_night
    rms, mav = bin_envelope(xf, fs)
    pack = build_pack({"rms": rms, "mav": mav}, [], hyp, ENV_FS, 30, {"unit_known": True})
    pos = np.flatnonzero(np.isin(pack["rem_epochs"], epochs))
    out = {}
    for name, m in (("published", METHODS["sinbar"]), ("FC", floor_corrected(METHODS["sinbar"], 1.0))):
        masks = {}
        score_night(pack, m, "native", masks=masks)
        anym = masks["any"].reshape(-1, 10)[pos]
        out[f"auto_any_{name}"] = round(100 * anym.mean(), 2)
        out[f"auto_tonic_{name}"] = round(100 * masks["tonic"][pos].mean(), 2)
    return out


def write_edf(path, signals, start_s, hyp, epochs, a):
    import pyedflib
    from pyedflib import highlevel
    import inspect
    rate = "sample_frequency" if "sample_frequency" in \
        inspect.signature(highlevel.make_signal_header).parameters else "sample_rate"
    sigs, heads = [], []
    for label, x, fs in signals:
        lim = float(np.ceil(np.percentile(np.abs(x), 99.99) * 1.5 + 1))
        sigs.append(np.clip(x, -lim, lim))
        heads.append(highlevel.make_signal_header(label, dimension="uV", physical_min=-lim,
                                                  physical_max=lim, **{rate: int(fs)}))
    ann = [[float(i * 30), 30.0, f"Sleep stage {STAGE.get(int(c), '?')}"] for i, c in enumerate(hyp)]
    ann += [[float((e - a) * 30), 30.0, "SCORE THIS EPOCH"] for e in epochs]
    hdr = highlevel.make_header()
    hdr["annotations"] = ann          # pyedflib takes annotations in the header dict
    highlevel.write_edf(str(path), sigs, heads, hdr, file_type=pyedflib.FILETYPE_EDFPLUS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import shutil
    from src.cohorts import COHORTS, _beats, quiet_level
    from src.config import SCRATCH
    from src.ecg import subtract_heartbeat
    from src.extract import bandpass, bin_envelope
    from src.noise_arms import harmonized, white
    out, key_dir = Path(args.out), Path(str(args.out).rstrip("/") + "_KEY")
    (out / "excerpts").mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)
    groups = candidates()
    ids = np.random.default_rng(SEED + 1).permutation(2 * N_PER * len(groups)) + 1
    key, minis, eps, skipped = [], [], [], []
    i = 0
    for name, recs in groups:
      cohort, taken = COHORTS[name], 0
      for rec in recs:
        if taken == N_PER:
            break
        folder = SCRATCH / f"vis_{rec}"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            d = cohort.read(rec, cohort.fetch(rec, folder))
        except Exception as e:                       # unreadable night: skip and record why
            skipped.append({"cohort": name, "record": rec, "reason": f"read: {e}"[:200]})
            shutil.rmtree(folder, ignore_errors=True)
            continue
        fs, hyp = float(d["fs"]), np.asarray(d["hypnogram"])
        xf, _ = bandpass(d["chin"], fs, mains=cohort.mains)
        beats = _beats(d)
        if len(beats):
            xf = subtract_heartbeat(xf, fs, beats)
        epochs = scored_stretch(hyp)
        level0 = quiet_level(bin_envelope(xf, fs)[0], hyp) if len(epochs) else np.nan
        if len(epochs) < N_SCORE or not level0 < MAX_LEVEL:
            why = "no 20-epoch REM stretch" if len(epochs) < N_SCORE else f"level {level0:.2f} uV"
            skipped.append({"cohort": name, "record": rec, "reason": why})
            print(f"skip {name} {rec}: {why}", flush=True)
            shutil.rmtree(folder, ignore_errors=True)
            continue
        track = white(len(xf), fs, cohort.mains, rec)
        _, _, s, level = harmonized(xf, track, fs, hyp, 1.5)
        a = max(0, int(epochs[0]) - CONTEXT)
        b = min(len(hyp), int(epochs[-1]) + CONTEXT + 1)
        for j, (copy, add) in enumerate((("as recorded", 0.0), ("noise", s))):
            vid = f"V{ids[2 * i + j]:02d}"
            sl = lambda x, f: np.asarray(x[int(a * 30 * f): int(b * 30 * f)], float)
            chin = sl(d["chin"], fs) + add * sl(track, fs)
            signals = [("Chin EMG", chin, fs)]
            if d.get("eeg") is not None:
                signals.append(("EEG central", sl(d["eeg"], d["fs_eeg"]), d["fs_eeg"]))
            if d.get("ecg") is not None:
                signals.append(("ECG", sl(d["ecg"], d["fs_ecg"]), d["fs_ecg"]))
            write_edf(out / "excerpts" / f"{vid}.edf", signals, a * 30, hyp[a:b], epochs, a)
            auto = automated(xf + add * track, fs, hyp, epochs)
            key.append({"excerpt": vid, "cohort": name, "record": rec, "copy": copy,
                        "added_uv": round(add, 3), "level_recorded_uv": round(level0, 3),
                        "level_after_uv": round(level if add else np.nan, 3),
                        "scored_epochs": len(epochs), **auto})
            for k, e in enumerate(epochs):
                t0 = (int(e) - a) * 30
                eps.append({"excerpt": vid, "epoch": k + 1, "start_s": t0, "tonic": ""})
                minis += [{"excerpt": vid, "epoch": k + 1, "mini": m + 1, "start_s": t0 + 3 * m, "any": ""}
                          for m in range(10)]
        print(f"[{i + 1}/{N_PER * len(groups)}] {name} {rec}: level {level0:.2f} -> {level:.2f} uV, "
              f"noise {s:.2f} uV", flush=True)
        shutil.rmtree(folder, ignore_errors=True)
        taken += 1
        i += 1
      if taken < N_PER:
          print(f"only {taken} eligible {name} nights", flush=True)
    pd.DataFrame(skipped, columns=["cohort", "record", "reason"]).to_csv(key_dir / "skipped.csv", index=False)
    pd.DataFrame(key).sort_values("excerpt").to_csv(key_dir / "key.csv", index=False)
    pd.DataFrame(minis).sort_values(["excerpt", "epoch", "mini"]).to_csv(out / "scoring_minis.csv", index=False)
    pd.DataFrame(eps).sort_values(["excerpt", "epoch"]).to_csv(out / "scoring_epochs.csv", index=False)
    (out / "README_for_scorer.md").write_text(README, encoding="utf-8")
    print(f"wrote {len(key)} excerpts to {out}; key in {key_dir} (do not share with the scorer)")


README = """# Visual scoring of chin EMG in REM sleep - instructions

You have 60 EDF+ excerpts (V01-V60). Each holds a stretch of REM sleep with a few epochs of
context, with the chin EMG, a central EEG channel and (where recorded) the ECG. Sleep stages
are given as annotations; the 20 epochs to score are annotated "SCORE THIS EPOCH".

Please score the chin EMG of those epochs only, following the SINBAR rules (Frauscher et al.,
Sleep 2012):

1. scoring_minis.csv: for each 3-s mini-epoch, any = 1 if it contains any chin EMG activity
   (tonic or phasic) of at least 0.1 s and at least twice the amplitude of the background EMG,
   otherwise 0. Mark artifacts you would exclude as "X".
2. scoring_epochs.csv: for each 30-s epoch, tonic = 1 if at least 50% of the epoch shows tonic
   chin activity at least twice the background (or above 10 uV), otherwise 0.

Use your usual display settings (filters, gain) and record them in a note. Score the excerpts
in numerical order, independently of each other, and do not look for other copies of the same
night. Return the two CSV files.
"""

if __name__ == "__main__":
    main()
