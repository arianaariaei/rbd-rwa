# RWA quantification agreement in REM sleep behaviour disorder

Do the different published ways of measuring **REM sleep without atonia (RWA)**
agree with each other on the same patients — and does the choice change who is
diagnosed?

RWA is the polysomnographic criterion for REM sleep behaviour disorder (RBD),
and isolated RBD is the strongest known prodromal marker of Parkinson's disease
and related synucleinopathies. Several quantification methods are in concurrent
use (Montreal, SINBAR, AASM, REM Atonia Index, and automated tools such as
RBDtector and Ikelos-RWA). They differ in mini-epoch length, which muscles are
scored, amplitude criteria, and diagnostic cut-offs.

Published comparisons pool performance figures reported *separately* across
different cohorts. The 2022 systematic review in *SLEEP* states that these
approaches have "not been systematically analyzed" and reports no concordance
between methods on identical recordings.

## Design

Runs on **Google Colab**. Raw recordings are disposable, derived data is not:

    download one recording  ->  extract envelope + hypnogram  ->  save to Drive
                            ->  delete the raw file

A raw CAP recording is ~430 MB; the derived file is a few MB. Disk use stays
flat regardless of cohort size, and losing a Colab session costs at most one
recording.

## Layout

    src/config.py    Colab/Drive-aware paths; durable vs scratch
    src/fetch.py     resumable downloads (PhysioNet TLS drops often)
    src/cap.py       CAP annotation parsing and EDF clock alignment
    src/extract.py   raw PSG -> rectified EMG envelope + hypnogram
    run_extract.py   streaming pipeline, resumable via a manifest
    notebooks/RBD_RWA_Colab.ipynb

## Data

| Source | Content | Access |
|---|---|---|
| CAP Sleep Database (PhysioNet) | 22 RBD + 16 healthy, chin EMG + leg EMG | open |
| NAPS (NSRR) | isolated RBD cohort, centrally scored at Mayo | data request |
| MrOS (NSRR) | 3,135 PSGs, older men | data request |

CAP is for building and validating the pipeline. Its RBD subjects are clinical
RBD, not *isolated* RBD — NAPS is the cohort that matters for the prodromal
Parkinson's framing, and results on CAP should not be presented as such.

## Alignment warning

CAP annotations use wall-clock times; the signal starts whenever the EDF header
says. In `rbd1` these differ by **2.6 hours**. Aligning annotation #0 to epoch #0
would shift every sleep stage against the signal and silently corrupt every
downstream measurement. `build_hypnogram` computes the offset explicitly and
reports it; the notebook checks REM latency as a sanity test.
