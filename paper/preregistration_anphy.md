# Pre-specified analysis: ANPHY-Sleep (written 2026-10-30, before any of its chin EMG was read)

Committed before any chin EMG of ANPHY-Sleep has been processed. Read beforehand: the
licence, the subject table, the zip directory, the EDF header of one night (EPCTL01) and its
stage file, and, on that night only, the ECG and EOG channels for the unit check below. The
rules, code paths and parameters are those already fixed (published criteria as implemented;
floor-corrected criteria of preregistration_floor_corrected.md with B = 1.0 uV, guard 1.5,
n = b / 0.91) and the predictions mirror those of preregistration_external.md.

## Why

ANPHY-Sleep adds a seventh recording system and a fourth group of healthy adults, from the
laboratory of the senior author of the SINBAR criteria (Montreal Neurological Institute).
The question is the same as for the earlier external cohorts: do the dependence of the
published rules on the noise floor, and its removal by the floor-corrected rule, hold on a
system not used so far?

## Cohort

| cohort | source, licence | population | system | chin EMG |
|---|---|---|---|---|
| ANPHY-Sleep | OSF 10.17605/OSF.IO/R26FH (Wei et al., Sci Data 2024); open download | 29 healthy adults aged 20-44 (28 released; EPCTL08 is not on OSF), one night each, Montreal, Canada | Nihon Kohden JE-120, 1000 Hz | two chin electrodes ChEMG1, ChEMG2; derivation ChEMG1 - ChEMG2 |

Mains 60 Hz. Stages: the released text file (stage, start in s, 30-s duration; "L" lines
mark lights and are ignored). ECG: ECG1 - ECG2 for R-peak detection and heartbeat
subtraction as for the other cohorts.

## Units (decided before the chin EMG is read)

The EDF stores ChEMG1/2, ECG1, EOG1 and the leg channels with physical dimension "?" and a
range of +/-10000; ECG2, EOG2 and the EEG are stored in uV (+/-8000). The data paper gives the
polygraphic channels in "a.u.". The floor and every threshold are in uV, so the cohort is
used for floor-based comparisons only if the "?" channels are in uV. Check, on the night
EPCTL01 only and before any chin EMG is processed: ECG1 against ECG2 (5-40 Hz) and EOG1
against EOG2 (0.3-10 Hz), 99th percentile of the absolute amplitude over two hours.
Rule: the "?" unit is taken as uV if both ratios lie within 0.67-1.5. If they do not, the
chin EMG is in unknown units: ANPHY-Sleep is then reported descriptively (shares flagged,
which are unaffected by a constant gain for the published relative rules, but not the floor,
the floor-corrected rules or the predictions below). The result of the check is recorded
under "Unit check" before the chin EMG is processed.

### Unit check (EPCTL01, done 2026-10-30 before this file was committed)

| pair | p99 of the "?" channel | p99 of the uV channel | ratio | correlation |
|---|---|---|---|---|
| EOG1 / EOG2 (0.3-10 Hz) | 25.4 | 19.7 | 1.29 | +0.81 |
| ECG1 / ECG2 (5-40 Hz) | 95.6 | 810.7 | 0.12 | +0.76 |

The EOG pair is consistent with the "?" channels being in uV; the ECG pair is not. ECG1 and
ECG2 are most likely the two electrodes of the single D-II lead, which need not have equal
amplitudes, so the ECG comparison probably does not test the unit; but that explanation was
reached after seeing the result, and the rule above is kept as written. **The check is
therefore not passed: ANPHY-Sleep's chin EMG is in unverified units.** Consequences: (1) the
cohort is processed and reported descriptively (shares flagged by the published relative
rules, which a constant gain does not change; the floor and floor-corrected results labeled
"units unverified"); (2) predictions A1-A6 are evaluated only if the dataset's authors
confirm that the polygraphic channels are stored in uV. Such a confirmation would be
recorded here with its date, and the analysis would note that it arrived after this commit.

## Inclusion and processing

As for the other cohorts: expert sleep stages in 30-s epochs, >= 10 min of REM, chin EMG
>= 200 Hz; 10-100 Hz band-pass, 60 Hz notch, heartbeat subtraction where R-peaks pass the
plausibility test (35-130 beats/min, > 90% regular intervals). Nights excluded and why are
reported.

## Measures per night

Quiet-REM level (floor), floor signature, net N2/N3 and REM levels, and the positive calls of
the published Montreal, SINBAR and RAI criteria, of Montreal-FC and SINBAR-FC (B = 1.0 uV), and
of SINBAR-FC at the cut-off re-derived on CAP (49.1%). The exploratory FC-period and FC-window
variants (preregistration_revision.md, addendum) are reported as exploratory.

## Predictions (evaluated only if the unit check passes)

A1. **Scale.** ANPHY's median net N2/N3 level is within 0.67-1.5 times MGH's (1.60 uV). If not,
    floor-corrected comparisons with ANPHY are flagged as confounded by gain.
A2. **A quiet system flags healthy people.** If ANPHY's median floor is below 1.0 uV, the
    published SINBAR criterion flags at least 30% of its nights.
A3. **The correction removes most of it.** If ANPHY's median floor is below 1.0 uV, SINBAR-FC
    flags at least 20 points fewer nights than published SINBAR.
A4. **Healthy cohorts agree once the floor is subtracted.** The difference between ANPHY and
    the earlier healthy cohorts pooled (BOAS first nights and DOD-H: published SINBAR 89.5%,
    SINBAR-FC 34.7%; published Montreal 37.1%, Montreal-FC 14.5%) is smaller in absolute value
    under SINBAR-FC than under published SINBAR, and likewise for Montreal if its published
    difference is at least 5 points.
A5. **Across all groups without RBD** (CAP same-system patients, MGH, HMC, BOAS, DOD-H, DOD-O,
    ANPHY), the Spearman correlation between median floor and published SINBAR positivity is
    negative, and its absolute value is smaller under SINBAR-FC.
A6. **The portable cut-off stays specific.** SINBAR-FC at 49.1% flags at most 10% of ANPHY's
    nights.

With about 28 nights, the shares have wide intervals (about +/-18 points); A2-A4 and A6 are
point-estimate predictions and are reported with their intervals. Everything else (Montreal
and RAI beyond A4, floor signature, the exploratory variants) is descriptive.
