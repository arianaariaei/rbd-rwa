# The recording system's noise floor and automated scoring of REM sleep without atonia

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23816641.svg)](https://doi.org/10.5281/zenodo.23816641)

Code and analysis plans for a study of automated scoring of REM sleep without atonia (RWA), the
polysomnographic hallmark of REM sleep behavior disorder (RBD). The published Montreal and SINBAR
chin criteria and the REM Atonia Index are applied through one open pipeline to openly licensed
polysomnograms from seven recording systems.

## Findings

- Automated implementations of the background-relative criteria judge chin activity against a
  multiple of each recording's quiet REM level, which is largely the recording system's noise
  floor. The same rules flagged 29% of patients at one hospital and 9% at another.
- Adding noise to the same nights reproduced the difference. Muscle activity of known size,
  added to nights from six systems, was detected only above an amplitude proportional to each
  night's noise floor.
- A floor-corrected version of the criteria, which subtracts each recording's noise instead of
  multiplying it, removed most of the dependence on noise, at the price of a dependence on
  amplifier gain.
- On the same RBD nights, a noisier recording system lowered tonic RWA by 21 points.

A manuscript is in preparation. The results of every analysis are in `paper/`.

## Data

All recordings are openly licensed and can be downloaded without an application or an account.

| dataset | content | licence | source to cite |
|---|---|---|---|
| CAP Sleep Database (PhysioNet) | 22 patients with RBD, other sleep disorders, healthy sleepers (Italy) | ODC-By 1.0 | Terzano et al., Sleep Med 2001; Goldberger et al., Circulation 2000 |
| HMC sleep staging database 1.1 (PhysioNet) | 151 clinical polysomnograms (the Netherlands) | CC BY 4.0 | Alvarez-Estevez and Rijsman, PLoS One 2021 |
| PhysioNet/CinC Challenge 2018 (PhysioNet) | 994 clinical polysomnograms, Massachusetts General Hospital (USA) | ODC-By 1.0 | Ghassemi et al., Comput Cardiol 2018 |
| BOAS (OpenNeuro ds005555) | 128 nights of adults from the general population (Spain) | CC0 | López-Larraz et al., OpenNeuro, doi:10.18112/openneuro.ds005555.v1.1.3 |
| Dreem Open Datasets (Zenodo 15900394) | 55 sleep-clinic patients (USA), 25 healthy volunteers (France) | MIT | Guillot et al., IEEE TNSRE 2020 |
| ANPHY-Sleep (OSF r26fh) | 29 healthy adults, high-density EEG with polysomnography (Canada) | CC0 | Wei et al., Sci Data 2024 |

## Running the analyses

Everything runs in Google Colab; nothing needs to be downloaded to a local machine.

1. Open `notebooks/RBD_RWA.ipynb` in Colab and choose Runtime > Run all. Each recording is
   streamed from its open mirror and reduced to a 1-2 MB file (the REM chin EMG envelope and
   N2/N3 summaries), which is copied to Google Drive before the raw file is deleted, so an
   interrupted session resumes where it stopped.
2. The later analyses each have a one-command runner for Colab: `run_parkinsons_colab.sh`,
   `run_inject_colab.sh` and `run_revision_colab.sh`.

After changing a source file, regenerate the notebook with `python tools/build_notebook.py`.

## Tools for other centers

- `python check_floor.py night.edf stages.txt` reports a recording system's noise floor, whether
  the floor-corrected criteria apply, and what each RWA threshold means in microvolts.
- `python run_site.py manifest.csv --out results` runs the analyses on recordings that cannot
  leave a center and writes one row of numbers per night (no signals, dates or identifiers).

## Pre-specified analyses

Each analysis plan was committed before its analysis was run; the commit history shows the
order: `paper/preregistration_noise_ladder.md`, `preregistration_floor_corrected.md`,
`preregistration_external.md`, `preregistration_parkinsons.md`, `preregistration_injection.md`
(with its white-noise predictions), `preregistration_revision.md`, `preregistration_anphy.md`,
and the protocol of a blinded visual-scoring substudy, `paper/visual_substudy_protocol.md`.
Snapshots are archived on Zenodo:
[10.5281/zenodo.23697366](https://doi.org/10.5281/zenodo.23697366) (analysis plans before the
revision results) and [10.5281/zenodo.23816641](https://doi.org/10.5281/zenodo.23816641)
(visual-scoring protocol, before any scoring).

## Repository layout

    src/                    dataset readers, signal processing, heartbeat removal, the RWA
                            criteria (published and floor-corrected), known-activity injection
    run_*.py                one script per analysis; each writes its tables and report
    check_floor.py          noise-floor check for one recording
    run_site.py             the analyses on recordings held at a sleep center
    notebooks/              the Colab notebook
    tools/build_notebook.py builds the notebook from the source files
    paper/                  analysis plans, result records, manuscript and supplement

## Citation and licence

If you use this code, please cite the article and this repository (see `CITATION.cff`). The code
is released under the MIT licence; the recordings remain under their own licences listed above.
