"""External cohorts: the noise floor and the floor-corrected rule on new systems.

Scores the packs of the development cohorts (CAP, MGH, HMC) and of the external
ones (BOAS, DOD-H, DOD-O) with the published and floor-corrected (B = 1.0 uV)
Montreal and SINBAR rules and the RAI, and reports against the predictions
fixed in paper/preregistration_external.md:

  X1  cohorts: nights, REM, age, floor, floor signature, heartbeat removal
  X2  scale: net N2/N3 and REM levels (E1)
  X3  share flagged: published, floor-corrected, SINBAR-FC at 49.1% (E2, E3, E5)
  X4  floor against share flagged across all groups without RBD (E4)
  X5  DOD-O against MGH's noise ladder (E6)
  X6  BOAS: every night, and by age (descriptive)
  X7  heartbeat check (exploratory, not pre-specified)

BOAS has several nights for some participants; its primary rows are each
participant's first recording. CAP RBD and CAP patients are the nights on
CAP's main system (512 Hz, microvolts).

    python run_external.py -> results/external_scores.csv, external_report.md,
                              figures/fig9_external
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from run_floor import YES, pct, score, score_pack_file, sel
from run_report import MIN_REM, WITHDRAWN

COHORTS = ("cap", "chal18", "hmc", "boas", "dodh", "dodo")
NAME = {"chal18": "MGH", "hmc": "HMC", "boas": "BOAS", "dodh": "DOD-H", "dodo": "DOD-O"}
HEALTHY = ["BOAS", "DOD-H"]
WITHOUT_RBD = ["CAP patients", "MGH", "HMC", "BOAS", "DOD-H", "DOD-O"]
CUT_FC_SINBAR = 49.1          # SINBAR-FC "any" cut-off re-derived on CAP (results_floor, FC5)
MGH_NREM_NET = 1.60           # MGH's median net N2/N3 level, uV (results_floor, FC6)


def label(df):
    gone = {f"{c}/{r}" for c, r in WITHDRAWN}
    df = df[~(df.cohort + "/" + df.record).isin(gone)].copy()
    cap = df.cohort == "cap"
    same = cap & (df.chin_fs == 512) & df.unit_known.astype(bool)
    df["who"] = np.select([same & (df.group == "RBD"), same & ~df.group.isin(["RBD", "healthy"])],
                          ["CAP RBD", "CAP patients"],
                          default=df.cohort.map(NAME).fillna(""))
    df["y"] = df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan)
    df["ref_key"] = df.ref_uv.fillna(0.0)
    # BOAS: a participant's first recording is primary
    df["primary"] = True
    b = df.cohort == "boas"
    if b.any():
        num = df.loc[b, "record"].str.extract(r"(\d+)")[0].astype(int)
        pid = df.loc[b, "pid"].fillna(df.loc[b, "record"]).astype(str)
        first = num.groupby(pid).transform("min")
        df.loc[b, "primary"] = (num == first).to_numpy()
    return df


def periodicity(pack, band):
    """How strongly the REM envelope repeats at a heart rate: the largest spectral peak of
    the envelope between 0.7 and 2 Hz over the median in 0.5-3 Hz (Welch, 20-s windows,
    REM stretches of at least a minute); higher = more heartbeat in the EMG."""
    from scipy.signal import welch
    from src.rwa import _segments, _select
    ep, env, _, _ = _select(pack, band)
    if env is None or len(ep) < 2:
        return np.nan
    fs = pack["meta"]["env_fs"]
    acc, n = None, 0
    for a, b in _segments(ep):
        x = env[a:b].reshape(-1).astype(float)
        if len(x) >= fs * 60:
            f, p = welch(x - x.mean(), fs=fs, nperseg=int(fs * 20))
            acc, n = (p if acc is None else acc + p), n + 1
    if not n:
        return np.nan
    band_, hr = (f >= 0.5) & (f <= 3.0), (f >= 0.7) & (f <= 2.0)
    return float(acc[hr].max() / np.median(acc[band_]))


def heartbeat_check(path):
    """Exploratory (not pre-specified): the heartbeat periodicity of the REM envelope with
    and without heartbeat removal, and the calls with the heartbeat left in."""
    from src.pack import load_pack
    from src.rwa import METHODS, floor_corrected, score_night
    pack = load_pack(path)
    m = pack["meta"]
    out = {"cohort": m.get("cohort", path.parent.name), "record": m["record"],
           "period_native": periodicity(pack, "native"),
           "period_with_ecg": periodicity(pack, "native_with_ecg")}
    for key in ("montreal", "sinbar"):
        for tag, meth in (("pub", METHODS[key]), ("fc", floor_corrected(METHODS[key], 1.0))):
            r = score_night(pack, meth, "native_with_ecg")
            out[f"{key}_{tag}_with_ecg"] = float(bool(r.get("positive"))) if r.get("positive") is not None else np.nan
    return [out]


def main():
    packs = [p for c in COHORTS for p in sorted((config.DURABLE / "packs" / c).glob("*.npz"))
             if ".tmp" not in p.name]
    print(f"scoring {len(packs)} packs", flush=True)
    df = label(score(packs, score_pack_file))
    from src.fetch import cap_demographics
    demo = cap_demographics()
    if demo:
        c = df.cohort == "cap"
        df.loc[c, "age"] = df.loc[c, "record"].map(lambda r: demo.get(r, {}).get("age"))
    df.to_csv(config.RESULTS / "external_scores.csv", index=False)
    hb = score([p for p in packs if p.parent.name in ("chal18", "hmc", "boas", "dodo", "dodh")],
               heartbeat_check)
    all_nights = df[(df.rem_minutes >= MIN_REM) & (df.who != "")]
    d = all_nights[all_nights.primary]

    lines = []
    say = lambda s="": (print(s), lines.append(s))
    verdict = {}
    groups = ["CAP RBD"] + WITHOUT_RBD
    one = d[(d.method == "Montreal") & (d.variant == "published")]
    one = one.assign(signature=one.nrem_p5 / one.level_1s)

    # X1 ─────────────────────────────────────────────────────────────────────
    say("X1  Cohorts (nights with >= 10 min REM; BOAS: first night per participant)")
    for w in groups:
        g = one[one.who == w]
        if g.empty:
            continue
        age = pd.to_numeric(g.age, errors="coerce")
        say(f"  {w:<13} n={len(g):<4} REM {g.rem_minutes.median():5.1f} min  age "
            f"{age.mean():4.0f} ({age.min():.0f}-{age.max():.0f})  fs {g.chin_fs.median():g}  "
            f"floor {g.level_1s.median():.2f} [{g.level_1s.quantile(.25):.2f}-{g.level_1s.quantile(.75):.2f}] uV  "
            f"signature {g.signature.median():.2f}  heartbeat removed {int((g.beats > 0).sum())}/{len(g)}")
    say()

    # X2 ─────────────────────────────────────────────────────────────────────
    say("X2  Scale: 1 s RMS with the noise removed (uV, median [IQR]); E1: net N2/N3 within")
    say(f"    0.67-1.5 x MGH's {MGH_NREM_NET} uV")
    for w in groups:
        g = one[one.who == w]
        if g.empty:
            continue
        v = g.nrem_p50_net
        ok = 0.67 * MGH_NREM_NET <= v.median() <= 1.5 * MGH_NREM_NET
        if w in ("BOAS", "DOD-H", "DOD-O"):
            verdict[f"E1 {w}"] = ok
        say(f"  {w:<13} N2/N3 {v.median():.2f} [{v.quantile(.25):.2f}-{v.quantile(.75):.2f}]  "
            f"REM {g.rem_p50_net.median():.2f}  REM p95 {g.rem_p95_net.median():.2f}"
            + (f"   E1 {'met' if ok else 'not met'}" if w in ("BOAS", "DOD-H", "DOD-O") else ""))
    say()

    # X3 ─────────────────────────────────────────────────────────────────────
    say("X3  Share flagged, % [95% CI]: published cut-offs; floor-corrected (B = 1.0 uV);")
    say(f"    SINBAR-FC at the cut-off re-derived on CAP ({CUT_FC_SINBAR}%)")
    rows = {}
    for w in groups:
        g = d[d.who == w]
        if g.empty:
            continue
        cells = {}
        for meth in ("Montreal", "SINBAR", "RAI"):
            for variant in (("published",) if meth == "RAI" else ("published", "FC")):
                cells[f"{meth} {variant}"] = sel(g, meth, variant).y
        fc_any = sel(g, "SINBAR", "FC").any_pct
        cells["SINBAR-FC >= 49.1"] = (fc_any >= CUT_FC_SINBAR).astype(float).where(fc_any.notna())
        rows[w] = {k: pct(v) for k, v in cells.items()}
        say(f"  {w}")
        for k, (p, lo, hi, n) in rows[w].items():
            say(f"    {k:<22} {100 * p:5.1f} [{100 * lo:.0f}-{100 * hi:.0f}]  (n={n})")
    floor = one.groupby("who").level_1s.median()
    # E2: quiet healthy systems flag healthy people
    for w in HEALTHY:
        if w in rows and floor.get(w, np.inf) < 1.0:
            verdict[f"E2 {w}"] = rows[w]["SINBAR published"][0] >= 0.30
    # E3: two healthy cohorts, floors differing >= 1.5x
    if all(w in rows for w in HEALTHY):
        a, b = sorted(HEALTHY, key=lambda w: floor[w])          # a = quieter
        if floor[b] / floor[a] >= 1.5:
            for meth, need in (("SINBAR", 0.0), ("Montreal", 0.05)):
                pub = rows[a][f"{meth} published"][0] - rows[b][f"{meth} published"][0]
                fc = rows[a][f"{meth} FC"][0] - rows[b][f"{meth} FC"][0]
                if meth == "SINBAR" or pub >= need:
                    verdict[f"E3 {meth}"] = pub > 0 and abs(fc) <= abs(pub) / 2
                    say(f"  E3 {meth}: {a} - {b} published {100 * pub:+.1f}, floor-corrected {100 * fc:+.1f} points")
        else:
            say(f"  E3 not applicable: healthy floors {floor[a]:.2f} and {floor[b]:.2f} uV differ < 1.5x")
    # E5: the portable cut-off stays specific
    for w, limit in (("BOAS", 0.10), ("DOD-H", 0.10), ("DOD-O", 0.20)):
        if w in rows:
            verdict[f"E5 {w}"] = rows[w]["SINBAR-FC >= 49.1"][0] <= limit
    say()

    # X4 ─────────────────────────────────────────────────────────────────────
    from scipy.stats import spearmanr
    say("X4  Across groups without RBD: median floor against share flagged (Spearman rho)")
    have = [w for w in WITHOUT_RBD if w in rows]
    x = [floor[w] for w in have]
    for meth in ("SINBAR", "Montreal"):
        pub = [rows[w][f"{meth} published"][0] for w in have]
        fc = [rows[w][f"{meth} FC"][0] for w in have]
        rp, rf = spearmanr(x, pub)[0], spearmanr(x, fc)[0]
        say(f"  {meth:<9} published rho {rp:+.2f}   floor-corrected rho {rf:+.2f}   ({len(have)} groups: "
            + ", ".join(f"{w} {floor[w]:.2f} uV" for w in have) + ")")
        if meth == "SINBAR":
            verdict["E4"] = rp < 0 and abs(rf) < abs(rp)
    say()

    # X5 ─────────────────────────────────────────────────────────────────────
    say("X5  DOD-O against MGH's noise ladder (published cut-offs; E6: within 10 points)")
    lad_path = config.RESULTS / "ladder_scores.csv"
    if "DOD-O" in rows and lad_path.exists():
        lad = pd.read_csv(lad_path)
        lad = lad[(lad.who == "MGH") & (lad.rem_minutes >= MIN_REM)]
        steps = ["native", "n050", "n100", "n150", "n200", "n300"]
        f0 = floor["DOD-O"]
        ok_all = True
        for meth in ("Montreal", "SINBAR"):
            g = lad[lad.method == meth]
            lv = [g[g.step == s].level.median() for s in steps]
            yy = [100 * g[g.step == s].y.mean() for s in steps]
            if not (min(lv) <= f0 <= max(lv)):
                say(f"  {meth}: DOD-O floor {f0:.2f} uV outside the ladder's {min(lv):.2f}-{max(lv):.2f} uV: not applicable")
                ok_all = None
                continue
            pred = float(np.interp(np.log(f0), np.log(lv), yy))
            obs = 100 * rows["DOD-O"][f"{meth} published"][0]
            say(f"  {meth:<9} predicted at {f0:.2f} uV: {pred:5.1f}%   observed {obs:5.1f}%   (diff {obs - pred:+.1f})")
            if ok_all is not None:
                ok_all = ok_all and abs(obs - pred) <= 10
        if ok_all is not None:
            verdict["E6"] = ok_all
    say()

    # X6 ─────────────────────────────────────────────────────────────────────
    b = all_nights[all_nights.cohort == "boas"]
    if len(b):
        say("X6  BOAS: every night (n=%d) and first nights by age, %% flagged" % b.record.nunique())
        for name, g in (("all nights", b), ("first nights < 50 y", d[(d.cohort == "boas") & (pd.to_numeric(d.age, errors='coerce') < 50)]),
                        ("first nights >= 50 y", d[(d.cohort == "boas") & (pd.to_numeric(d.age, errors='coerce') >= 50)])):
            cells = []
            for meth in ("Montreal", "SINBAR"):
                for variant in ("published", "FC"):
                    cells.append(f"{meth} {variant} {100 * sel(g, meth, variant).y.mean():4.0f}")
            n = g.record.nunique()
            say(f"  {name:<22} n={n:<4} " + "  ".join(cells))
        say()

    # X7 ─────────────────────────────────────────────────────────────────────
    say("X7  Heartbeat check (exploratory, not pre-specified): periodicity of the REM envelope")
    say("    at a heart rate (higher = more heartbeat), and the share flagged with it left in")
    h = hb.merge(d[(d.method == "Montreal") & (d.variant == "published")][["cohort", "record", "who"]],
                 on=["cohort", "record"])
    for w in ("MGH", "HMC", "DOD-O", "DOD-H", "BOAS"):
        g = h[h.who == w]
        if g.empty:
            continue
        cells = []
        for meth in ("Montreal", "SINBAR"):
            for variant, tag in (("published", "pub"), ("FC", "fc")):
                removed = sel(d[d.who == w], meth, variant).set_index("record").y
                left = g.set_index("record")[f"{meth.lower()}_{tag}_with_ecg"].reindex(removed.index)
                cells.append(f"{meth} {variant} {100 * removed.mean():.0f} -> {100 * left.mean():.0f}")
        say(f"  {w:<6} n={len(g):<4} periodicity after removal {g.period_native.median():.2f} "
            f"[p90 {g.period_native.quantile(.9):.2f}], left in {g.period_with_ecg.median():.2f}")
        say("         % flagged, removed -> left in: " + "   ".join(cells))
    ref = h[h.who == "MGH"].period_native.quantile(0.9)
    b = h[h.who == "BOAS"]
    if len(b):
        clean = set(b[b.period_native <= ref].record)
        say(f"  BOAS nights no more periodic than MGH's after removal (<= {ref:.2f}, MGH p90): "
            f"{len(clean)}/{len(b)}; % flagged among them:")
        say("    " + "   ".join(
            f"{meth} {variant} {100 * sel(d[(d.who == 'BOAS') & d.record.isin(clean)], meth, variant).y.mean():.0f}"
            for meth in ("Montreal", "SINBAR") for variant in ("published", "FC")))
    say()

    say("Pre-specified predictions: " + "  ".join(
        f"{k}: {'met' if v else 'not met'}" for k, v in sorted(verdict.items())))
    out = config.RESULTS / "external_report.md"
    out.write_text("```\n" + "\n".join(lines) + "\n```\n", encoding="utf-8")
    print(f"\nwritten -> {out}")
    figure(one, rows, floor)


def figure(one, rows, floor):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from run_figures import save

    style = {"CAP RBD": ("#d62728", "*"), "CAP patients": ("#7f7f7f", "o"), "MGH": ("#1f77b4", "o"),
             "HMC": ("#9467bd", "o"), "DOD-O": ("#17becf", "o"), "BOAS": ("#2ca02c", "s"),
             "DOD-H": ("#bcbd22", "s")}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True, layout="constrained")
    for ax, meth in zip(axes, ("SINBAR", "Montreal")):
        for w, (col, mk) in style.items():
            if w not in rows:
                continue
            x = floor[w]
            p, f = 100 * rows[w][f"{meth} published"][0], 100 * rows[w][f"{meth} FC"][0]
            ax.annotate("", xy=(x, f), xytext=(x, p),
                        arrowprops=dict(arrowstyle="->", color=col, lw=0.8, alpha=0.7))
            ax.plot(x, p, mk, color=col, mfc="white", ms=6)
            ax.plot(x, f, mk, color=col, ms=6, label=w)
        ax.set_xscale("log")
        ax.set_xticks([0.3, 0.5, 1, 2, 3], ["0.3", "0.5", "1", "2", "3"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_xlabel("median quiet-REM level of the cohort (µV)")
        ax.set_ylim(0, 100)
        ax.set_title(f"{'AB'[meth == 'Montreal']}  {meth}")
    axes[0].set_ylabel("nights flagged positive (%)")
    axes[0].plot([], [], "o", color="k", mfc="white", label="published")
    axes[0].plot([], [], "o", color="k", label="floor-corrected")
    axes[0].legend(frameon=False, fontsize=6, loc="upper right")
    axes[1].legend(frameon=False, fontsize=6, loc="upper right", ncol=2)
    save(fig, "fig9_external")


if __name__ == "__main__":
    main()
