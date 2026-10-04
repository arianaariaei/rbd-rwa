# Measured against the noise floor: REM sleep without atonia across open sleep cohorts

Automated scoring of REM sleep without atonia (RWA) - the polysomnographic marker of REM
sleep behavior disorder (RBD) - with the published Montreal, SINBAR, AASM and REM Atonia
Index criteria, applied through one open pipeline to openly licensed polysomnograms.

Main findings so far (details in `paper/`):

- The published cut-offs flag very different shares of patients at different hospitals.
- The background the relative criteria are multiples of is, in effect, the recording
  system's noise floor: quieter systems flag more patients, noisier ones miss RBD.
- A floor-corrected version of the criteria (noise subtracted, not multiplied), fixed in
  advance, removes the dependence on noise and the site difference.
- For Parkinson's disease research, where RBD is the strongest prodromal marker: on the same
  RBD nights, a noisier recording system alone lowered tonic RWA by two-thirds of the
  difference that predicted later Parkinson's disease. RBDtector, the open scorer used in
  Parkinson's and RBD studies, behaves the same when run unchanged (it flagged 89% of healthy
  volunteers on the quietest system); the floor-corrected baseline removes most of this
  (9 of 10 pre-specified predictions met).

Check a recording system of your own with `check_floor.py` (an EDF and its 30-s stages):
it reports the system's noise floor, whether the floor-corrected criteria apply, and what
each RWA threshold means in microvolts.

## Data (all request-free)

| cohort | what | license |
|---|---|---|
| CAP (PhysioNet) | 22 RBD patients, other sleep disorders, healthy sleepers (Italy) | ODC-By |
| HMC (PhysioNet) | 151 clinical PSGs, Haaglanden Medisch Centrum (Netherlands) | CC BY 4.0 |
| Challenge 2018 (PhysioNet) | 994 clinical PSGs, Massachusetts General Hospital (USA) | ODC-By |
| BOAS (OpenNeuro ds005555) | 128 nights of adults from the general population (Spain) | CC0 |
| DOD-O / DOD-H (Zenodo 15900394) | 55 sleep-clinic patients (Stanford) / 25 healthy volunteers (France) | MIT |

## Running it

Everything runs in Google Colab; nothing is downloaded to the local machine. Open
`notebooks/RBD_RWA.ipynb` in Colab and choose Runtime -> Run all. The notebook carries its
own copy of the code (`%%writefile` cells), streams each recording from its open mirror,
reduces it to a 1-2 MB "pack" (REM chin EMG envelope at 50 Hz plus 1-s N2/N3 summaries),
copies the pack to Google Drive (`MyDrive/rbd-rwa`) and deletes the raw file, so a
disconnected session resumes where it stopped. Regenerate the notebook after changing any
source file:

    python tools/build_notebook.py

## Layout

    src/config.py     Colab/Drive-aware paths (durable vs scratch)
    src/fetch.py      resumable downloads; CAP record lists and ages
    src/edf.py        EDF reader at native sampling rates
    src/cap.py        CAP annotations and EDF clock alignment
    src/ecg.py        R-peak detection and heartbeat subtraction
    src/extract.py    band-pass, notch, envelopes (CAP full-night files)
    src/cohorts.py    cohort adapters, software re-recordings, the noise ladder
    src/pack.py       compact per-night storage
    src/rwa.py        the RWA methods, published and floor-corrected
    run_extract.py    CAP extraction
    run_cohort.py     download -> pack for any cohort (resumable, parallel)
    run_score.py      every method on every pack -> results/rwa_scores.csv
    run_report.py     the paper's tables (T1-T17)
    run_sensitivity.py  background definitions
    run_figures.py    figures 1-5
    run_ladder.py     the noise ladder (pre-specified), figures 6-7
    run_floor.py      floor-corrected criteria (pre-specified), figure 8
    run_external.py   external cohorts (pre-specified), figure 9
    src/rbdtector.py  RBDtector (open RWA scorer) run unchanged on our nights
    run_rbdtector.py  RBDtector on the noise ladder and three systems
    run_rbdtector_noise.py  RBDtector on noise alone (exploratory)
    run_parkinsons_colab.sh the Parkinson's runs and analysis in one command on Colab
    run_parkinsons.py what the floor means for Parkinson's research (pre-specified), figure 10
    src/floorcheck.py, check_floor.py   the floor check for one recording
    tools/build_notebook.py   writes notebooks/RBD_RWA.ipynb

## Paper

The assembled manuscript for the journal SLEEP and its supplement are in `paper/submission/` (Word files for submission and Markdown snapshots); the figures are the PNG/PDF files the pipeline writes. `docs/research_proposal_2026-10-04.docx` explains the whole project in research-proposal form for readers with a computer science background.

`paper/` holds the drafts (methods, results, discussion, abstract, figure legends,
references, STARD checklist), the result records, the audit, and four pre-registrations,
each committed before its analysis was run: `preregistration_noise_ladder.md`,
`preregistration_floor_corrected.md`, `preregistration_external.md`,
`preregistration_parkinsons.md`.

CAP annotations use wall-clock times, while the signal starts whenever the EDF header says
(in `rbd1` the two differ by 2.6 hours); `src/cap.py` computes the offset explicitly.
