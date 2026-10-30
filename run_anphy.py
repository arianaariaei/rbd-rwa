"""ANPHY-Sleep: the noise floor and the floor-corrected rule on a seventh recording system.

Scores the ANPHY-Sleep packs with the published and floor-corrected (B = 1.0 uV) Montreal
and SINBAR rules and the RAI, as run_external.py does for the other cohorts, and evaluates
the predictions fixed in paper/preregistration_anphy.md against the earlier groups
(results/external_scores.csv):

  N1  the cohort: nights, REM, age, floor, floor signature, heartbeat removal
  A1  scale: net N2/N3 level against MGH's
  N2  share flagged (A2, A3, A4, A6), plus the exploratory FC-window variant
  A5  across the seven groups without RBD: floor against share flagged

The packs were built before the dataset's authors confirmed (2026-10-30) that the chin
EMG is stored in microvolts, so their unit flag is set here; the stored values are the
file's physical values, which are microvolts.

    python run_anphy.py -> results/anphy_scores.csv, results/anphy_report.md
"""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from src import config
from src.pack import load_pack
from src.rwa import METHODS, floor_corrected, score_night
from run_floor import YES, _info, pct, scale, score_rows, sel
from run_report import MIN_REM
from run_external import CUT_FC_SINBAR, MGH_NREM_NET, WITHOUT_RBD

HEALTHY_EARLIER = ["BOAS", "DOD-H"]


def score_file(path):
    pack = load_pack(path)
    pack["meta"]["unit_known"] = True        # confirmed by the authors (preregistration_anphy.md)
    info = _info(pack["meta"], "anphy")
    rows = score_rows(pack, "native", info)
    rows[0].update(scale(pack))
    for key in ("montreal", "sinbar"):       # exploratory: noise estimate per 11-epoch window
        m = floor_corrected(METHODS[key], 1.0, noise_scope="window")
        rows.append({**info, **score_night(pack, m, "native"), "variant": "FC-window", "ref_uv": 1.0})
    return rows


def spearman_exact(x, y):
    """Spearman rho and its exact two-sided permutation p (small n)."""
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    rho = np.corrcoef(rx, ry)[0, 1]
    perms = [np.corrcoef(rx, np.array(p))[0, 1] for p in itertools.permutations(ry)]
    return rho, float(np.mean(np.abs(perms) >= abs(rho) - 1e-12))


def main():
    from src.cohorts import COHORTS
    packs = sorted(p for p in (config.DURABLE / "packs" / "anphy").glob("*.npz") if ".tmp" not in p.name)
    print(f"scoring {len(packs)} ANPHY packs", flush=True)
    df = pd.DataFrame([r for p in packs for r in score_file(p)])
    demo = COHORTS["anphy"].demographics()
    df["age"] = df.record.map(lambda r: demo.get(r, {}).get("age"))
    df["who"], df["primary"] = "ANPHY", True
    df["y"] = df.positive.map(lambda x: float(x in YES) if pd.notna(x) else np.nan)
    df["ref_key"] = df.ref_uv.fillna(0.0)
    df.to_csv(config.RESULTS / "anphy_scores.csv", index=False)

    ext = pd.read_csv(config.RESULTS / "external_scores.csv", dtype={"record": str}, low_memory=False)
    ext = ext[ext.primary.astype(bool) & (ext.who.fillna("") != "")]
    allg = pd.concat([ext, df], ignore_index=True)
    d = allg[allg.rem_minutes >= MIN_REM]
    one = d[(d.method == "Montreal") & (d.variant == "published")]
    one = one.assign(signature=one.nrem_p5 / one.level_1s)

    lines = []
    say = lambda s="": (print(s), lines.append(s))
    verdict = {}

    a_all = df[(df.method == "Montreal") & (df.variant == "published")]
    a = one[one.who == "ANPHY"]
    say("N1  ANPHY-Sleep (one night each; nights with >= 10 min REM are analysed)")
    short = sorted(set(a_all.record) - set(a.record))
    age = pd.to_numeric(a.age, errors="coerce")
    say(f"  nights {len(a_all)}, with >= 10 min REM {len(a)}" + (f" (excluded: {', '.join(short)})" if short else ""))
    say(f"  REM {a.rem_minutes.median():.1f} min  age {age.mean():.0f} ({age.min():.0f}-{age.max():.0f})  "
        f"fs {a.chin_fs.median():g}  floor {a.level_1s.median():.2f} [{a.level_1s.quantile(.25):.2f}-"
        f"{a.level_1s.quantile(.75):.2f}] uV  signature {a.signature.median():.2f}  "
        f"heartbeat removed {int((a.beats > 0).sum())}/{len(a)}")
    floor = one.groupby("who").level_1s.median()
    say("  median floor of the earlier groups (uV): " +
        ", ".join(f"{w} {floor[w]:.2f}" for w in WITHOUT_RBD + ["CAP RBD"] if w in floor))
    say()

    v = a.nrem_p50_net
    ok = 0.67 * MGH_NREM_NET <= v.median() <= 1.5 * MGH_NREM_NET
    verdict["A1"] = ok
    say(f"A1  Scale: net N2/N3 {v.median():.2f} [{v.quantile(.25):.2f}-{v.quantile(.75):.2f}] uV = "
        f"{v.median() / MGH_NREM_NET:.2f} x MGH's {MGH_NREM_NET} (0.67-1.5) -> {'met' if ok else 'not met'}"
        f"; REM {a.rem_p50_net.median():.2f}, REM p95 {a.rem_p95_net.median():.2f}")
    say()

    say(f"N2  Share flagged, % [95% CI] (SINBAR-FC at the CAP cut-off {CUT_FC_SINBAR}%)")
    g = d[d.who == "ANPHY"]
    cells = {}
    for meth in ("Montreal", "SINBAR", "RAI"):
        for variant in (("published",) if meth == "RAI" else ("published", "FC")):
            cells[f"{meth} {variant}"] = pct(sel(g, meth, variant).y)
    fc_any = sel(g, "SINBAR", "FC").any_pct
    cells["SINBAR-FC >= 49.1"] = pct((fc_any >= CUT_FC_SINBAR).astype(float).where(fc_any.notna()))
    for meth in ("Montreal", "SINBAR"):
        cells[f"{meth} FC-window (exploratory)"] = pct(g[(g.method == meth) & (g.variant == "FC-window")].y)
    for k, (p, lo, hi, n) in cells.items():
        say(f"    {k:<32} {100 * p:5.1f} [{100 * lo:.0f}-{100 * hi:.0f}]  (n={n})")
    fl = floor["ANPHY"]
    if fl < 1.0:
        verdict["A2"] = cells["SINBAR published"][0] >= 0.30
        verdict["A3"] = cells["SINBAR published"][0] - cells["SINBAR FC"][0] >= 0.20
    else:
        say(f"  A2, A3 not applicable: median floor {fl:.2f} uV >= 1.0")
    pooled = {}
    h = d[d.who.isin(HEALTHY_EARLIER)]
    for meth in ("Montreal", "SINBAR"):
        for variant in ("published", "FC"):
            pooled[f"{meth} {variant}"] = pct(sel(h, meth, variant).y)[0]
    say("  earlier healthy cohorts pooled (BOAS first nights + DOD-H): " +
        ", ".join(f"{k} {100 * p:.1f}" for k, p in pooled.items()))
    for meth in ("SINBAR", "Montreal"):
        pub = cells[f"{meth} published"][0] - pooled[f"{meth} published"]
        fc = cells[f"{meth} FC"][0] - pooled[f"{meth} FC"]
        applies = meth == "SINBAR" or abs(pub) >= 0.05
        if applies:
            verdict[f"A4 {meth}"] = abs(fc) < abs(pub)
        say(f"  A4 {meth}: ANPHY - pooled healthy, published {100 * pub:+.1f}, floor-corrected "
            f"{100 * fc:+.1f} points" + ("" if applies else " (published difference < 5 points: not evaluated)"))
    verdict["A6"] = cells["SINBAR-FC >= 49.1"][0] <= 0.10
    say()

    groups = [w for w in WITHOUT_RBD + ["ANPHY"] if w in floor]
    say(f"A5  Across the {len(groups)} groups without RBD: median floor against share flagged")
    x = [floor[w] for w in groups]
    res = {}
    for meth in ("SINBAR", "Montreal"):
        for variant in ("published", "FC"):
            y = [pct(sel(d[d.who == w], meth, variant).y)[0] for w in groups]
            res[(meth, variant)] = spearman_exact(x, y)
            say(f"    {meth} {variant:<9} rho {res[(meth, variant)][0]:+.2f}  exact p {res[(meth, variant)][1]:.3f}  "
                f"(shares: {', '.join(f'{w} {100 * s:.0f}' for w, s in zip(groups, y))})")
    rp, rf = res[("SINBAR", "published")][0], res[("SINBAR", "FC")][0]
    verdict["A5"] = rp < 0 and abs(rf) < abs(rp)
    say()

    say("Verdicts (paper/preregistration_anphy.md)")
    for k, ok in verdict.items():
        say(f"  {k:<12} {'met' if ok else 'not met'}")
    (config.RESULTS / "anphy_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
