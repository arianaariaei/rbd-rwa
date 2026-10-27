"""Build the self-contained Colab notebook from the source tree.

The notebook carries its own copy of every source file (written out with
%%writefile), so running it needs nothing but a Google account: no git clone,
no copying code to Drive. Re-run this script after changing any source file.

Results go straight to Google Drive (MyDrive/rbd-rwa): each night is reduced
to a 1-2 MB pack, so even a thousand nights fit, and a disconnected session
loses nothing - re-running continues where it stopped.

    python tools/build_notebook.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "RBD_RWA.ipynb"
CODE_DIR = "/content/rbd-rwa"
WORK_DIR = "/content/durable"
DRIVE_DIR = "/content/drive/MyDrive/rbd-rwa"
FILES = ["src/__init__.py", "src/config.py", "src/edf.py", "src/ecg.py", "src/fetch.py",
         "src/cap.py", "src/extract.py", "src/pack.py", "src/cohorts.py", "src/rwa.py",
         "run_extract.py", "run_cohort.py", "run_score.py", "run_sensitivity.py",
         "run_report.py", "run_figures.py", "run_ladder.py", "run_floor.py", "run_external.py",
         "src/rbdtector.py", "src/floorcheck.py", "run_rbdtector.py", "run_parkinsons.py",
         "run_rbdtector_noise.py", "check_floor.py", "run_parkinsons_colab.sh",
         "src/inject.py", "run_inject.py", "sim_injection.py", "run_inject_report.py",
         "run_inject_colab.sh", "src/noise_arms.py", "run_noise_arms.py", "run_revision.py",
         "run_rbdtector_checks.py", "run_visual_package.py", "run_visual_analysis.py",
         "run_site.py", "run_revision_colab.sh"]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.strip("\n")}


def main():
    cells = [
        md("""
# REM sleep without atonia across open sleep cohorts

Everything runs in the cloud; nothing is downloaded to your computer. Every
dataset used here is open (no application, no credential):

| cohort | what | license |
|---|---|---|
| CAP | 22 RBD patients + healthy sleepers + other sleep disorders (Italy) | ODC-By |
| HMC | 151 clinical PSGs, Haaglanden Medisch Centrum (Netherlands) | CC BY 4.0 |
| Challenge 2018 | 994 clinical PSGs, Massachusetts General Hospital (USA) | ODC-By |

Each night is streamed from PhysioNet's open mirror, reduced to a 1-2 MB file
on this Colab machine and copied to Google Drive (`MyDrive/rbd-rwa/packs`),
and the raw file is deleted. If the session disconnects, run the cells again:
nights already copied to Drive are restored and skipped.

Run order: **Runtime -> Run all**. The first cell asks for access to Drive;
if nobody answers within 3 minutes the run continues without it.
"""),
        code(f"""
# Work happens on this machine's disk; finished nights are ALSO copied to
# Google Drive when it is connected. (Colab's Drive connection can drop out
# under heavy use, so it is never the working copy.)
import os
from google.colab import drive
try:
    drive.mount('/content/drive', timeout_ms=180000)
    os.makedirs('{DRIVE_DIR}', exist_ok=True)
    MIRROR = '{DRIVE_DIR}'
except Exception as e:
    print('Drive not connected:', e, '- results stay on this Colab machine for now')
    MIRROR = ''
PACK_MIRROR = f'--mirror {{MIRROR}}/packs' if MIRROR else ''
RESULT_MIRROR = f'--mirror {{MIRROR}}/results' if MIRROR else ''
os.environ['RBD_DURABLE_DIR'] = '{WORK_DIR}'
!pip -q install wfdb pyedflib
!mkdir -p {CODE_DIR}/src {WORK_DIR}
%cd {CODE_DIR}
"""),
    ]
    for rel in FILES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        cells.append(code(f"%%writefile {CODE_DIR}/{rel}\n{src}"))
    cells += [
        md("## 1. CAP: extract every night (~12 minutes), then pack"),
        code(f"!cd {CODE_DIR} && python run_extract.py && python run_cohort.py --cohort cap {{PACK_MIRROR}}"),
        md("## 2. HMC: 151 nights (about 15 GB streamed, ~10 minutes)"),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort hmc --workers 3 {{PACK_MIRROR}}"),
        md("## 3. Challenge 2018: 994 nights (about 130 GB streamed, roughly an hour)"),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort chal18 --workers 3 {{PACK_MIRROR}}"),
        md("""
## 4. Hardware simulation: HMC recorded the way MGH records chin EMG

The same 151 HMC nights again, quantized to 1 uV steps (`hmc_q1uv`), and also
resampled to 200 Hz (`hmc_mgh`), as the MGH chin EMG is stored. MGH's quiet
REM level (~0.6 uV) is below that step while HMC's (~1.5 uV) is above it, so
both are repeated after scaling HMC down to the MGH level (`hmc_low`,
`hmc_low_mgh`). Any change against the matching undegraded copy is caused by
the recording hardware alone (~25 minutes).
"""),
        code(f"!cd {CODE_DIR} && " + " && ".join(
            f"python run_cohort.py --cohort {c} --workers 3 {{PACK_MIRROR}}"
            for c in ("hmc_q1uv", "hmc_mgh", "hmc_low", "hmc_low_mgh"))),
        md("""
The reverse test: 300 MGH nights with white noise added to the chin EMG, which raises
their quiet-REM level from ~0.6 uV to HMC's ~1.5 uV (`chal18_noise`, ~15 minutes).
"""),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort chal18_noise --limit 300 "
             f"--workers 3 {{PACK_MIRROR}}"),
        md("""
## 5. The noise ladder

CAP, HMC and 300 MGH nights streamed once more; each night's chin EMG is kept as
recorded and with white noise added at 0.5-3 uV, and at the level that brings its
quiet-REM level to 1.5 and 2.0 uV. The analysis and its decision criteria were fixed
in advance (paper/preregistration_noise_ladder.md). About 40 minutes; the ladder
files stay on this machine (they are large) and only the results go to Drive.
"""),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort cap --ladder --workers 3 "
             f"&& python run_cohort.py --cohort hmc --ladder --workers 3 "
             f"&& python run_cohort.py --cohort chal18 --ladder --limit 300 --workers 3 "
             f"&& python run_ladder.py"),
        md("""
## 5b. Floor-corrected criteria

The published rules with the noise floor subtracted instead of multiplied, scored on
every night as recorded and on the noise ladder, against the criteria fixed in advance
(paper/preregistration_floor_corrected.md). About 15 minutes.
"""),
        code(f"!cd {CODE_DIR} && python run_floor.py"),
        md("""
## 5c. External cohorts

Three recording systems not used to find the effect: BOAS (OpenNeuro, 128 nights of adults
from the general population), DOD-O (55 patients, Stanford) and DOD-H (25 healthy
volunteers, France), scored against the predictions fixed in advance
(paper/preregistration_external.md). BOAS takes ~15 minutes; the Dreem sets come from
Zenodo at a few MB/s and take about an hour each.
"""),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort boas --workers 3 {{PACK_MIRROR}} "
             f"&& python run_cohort.py --cohort dodo --workers 3 {{PACK_MIRROR}} "
             f"&& python run_cohort.py --cohort dodh --workers 3 {{PACK_MIRROR}} "
             f"&& python run_external.py"),
        md("""
## 5d. What the noise floor means for Parkinson's disease research

RBDtector, the open-source RWA scorer used in Parkinson's and RBD research, run unchanged
(and with the floor-corrected baseline) on the CAP noise ladder and on MGH, HMC and BOAS
as recorded; then the analyses fixed in advance in paper/preregistration_parkinsons.md
(change in RWA against the disease signals PD research uses, isolated RWA by system,
recruitment arithmetic, the floor check), and the exploratory check of RBDtector on noise
alone. RBDtector runs in the 2021 environment its requirements specify, which the script
creates. About seven hours on one runtime (about 35 s per night, step and rule); to split
it, run `PART=2 sh run_parkinsons_colab.sh` (MGH, HMC, BOAS) on a second runtime and
`PART=1 sh run_parkinsons_colab.sh` (CAP, then the analysis) here; both need Drive.
"""),
        code(f"!cd {CODE_DIR} && sh run_parkinsons_colab.sh"),
        md("""
## 5e. Known muscle activity added to every night

Ground truth that does not depend on the 21 RBD patients: muscle activity of known size is
added to the REM sleep of every night without RBD on the six recording systems (synthetic
tonic and phasic activity at 49 amplitudes), and the REM muscle activity of the 21 CAP RBD
patients is transplanted into the same nights at full and half amplitude. Scored with the
published and floor-corrected rules against the criteria fixed in advance
(paper/preregistration_injection.md). All nights are streamed again; about five hours on one
runtime. To split it, run `PART=2 sh run_inject_colab.sh` (the Dreem sets) on a second
runtime and `PART=1 sh run_inject_colab.sh` here; both need Drive.
"""),
        code(f"!cd {CODE_DIR} && sh run_inject_colab.sh"),
        md("""
## 5f. Analyses added in revision

Specified in paper/preregistration_revision.md before they were run: every between-site
difference with confidence intervals and equivalence tests, the floor-corrected rule on
in-range nights and with a noise estimate from N2/N3, the noise ladder with pink, drifting
and recorded noise, the RBDtector checks (against the program as released, with MGH's
scored arousals, with the heartbeat removed), and the blinded excerpts for the visual-scoring
substudy (paper/visual_substudy_protocol.md). About eight hours; `PART=1` (re-analyses,
noise, excerpts) and `PART=2` (RBDtector) can run on two runtimes.
"""),
        code(f"!cd {CODE_DIR} && sh run_revision_colab.sh"),
        md("""
The floor check for a recording of your own: an EDF on Drive and its 30-s stages (one per
line: W, N1, N2, N3, R). It reports the system's noise floor, whether the floor-corrected
criteria apply, and what each RWA threshold means in microvolts.
"""),
        code(f"# !cd {CODE_DIR} && python check_floor.py /content/drive/MyDrive/night.edf "
             f"/content/drive/MyDrive/night_stages.txt --mains 50"),
        md("## 6. Score every night with every method"),
        code(f"!cd {CODE_DIR} && python run_score.py {{RESULT_MIRROR}}"),
        md("## 7. Background definition sensitivity, then the report tables"),
        code(f"""
!cd {CODE_DIR} && python run_sensitivity.py && python run_report.py
if MIRROR:
    !mkdir -p {{MIRROR}}/results && cp {WORK_DIR}/results/* {{MIRROR}}/results/
"""),
        md("## 8. Figures"),
        code(f"""
!cd {CODE_DIR} && python run_figures.py
if MIRROR:
    !mkdir -p {{MIRROR}}/figures && cp {WORK_DIR}/figures/* {{MIRROR}}/figures/
from IPython.display import Image, display
for name in sorted(os.listdir('{WORK_DIR}/figures')):
    if name.endswith('.png'):
        display(Image(f'{WORK_DIR}/figures/{{name}}', width=900))
"""),
    ]
    nb = {"cells": cells,
          "metadata": {"colab": {"provenance": []},
                       "kernelspec": {"name": "python3", "display_name": "Python 3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({len(cells)} cells, {OUT.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
