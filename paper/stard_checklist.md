# STARD 2015 checklist (draft mapping)

The index tests are the automated Montreal, SINBAR (chin), AASM and RAI criteria; the
reference standard is the clinical RBD diagnosis in CAP (positives) and "RBD not suspected"
in the clinical cohorts. Status: done / partial / TO DO.

| # | Item | Where / status |
|---|---|---|
| 1 | Title identifies a diagnostic accuracy study, with an accuracy measure | Working title - TO DO: add "diagnostic accuracy" and "sensitivity/false-positive rate" to title or abstract |
| 2 | Structured abstract | abstract_draft.md - done |
| 3 | Background, intended use and clinical role of the index tests | Introduction - done (screening PSGs for prodromal synucleinopathy) |
| 4 | Objectives and hypotheses | Introduction final paragraph - partial: state the noise-floor hypothesis explicitly |
| 5 | Prospective or retrospective data collection | Methods 2.1 - TO DO: state "retrospective analysis of open databases" (all recordings pre-existing; two analyses pre-specified before running) |
| 6 | Eligibility criteria | Methods 2.1/2.3 - done (usable chin EMG, >= 10 min REM) |
| 7 | Basis for identifying eligible participants | Methods 2.1 - done (all records of each database) |
| 8 | Setting, location, dates | Methods 2.1 - partial: add recording periods where the databases state them |
| 9 | Consecutive, random or convenience series | Methods 2.1 - TO DO: CAP convenience; MGH/HMC as released by the providers |
| 10a | Index test in replicable detail | Methods 2.2-2.4 + open code - done |
| 10b | Reference standard in replicable detail | Methods 2.1 - partial: CAP gives no RBD criteria; say so, and that the clinical diagnosis itself requires PSG RWA (incorporation bias; sensitivity optimistic) |
| 11 | Rationale for the reference standard | Methods 2.1 - partial |
| 12a | Index-test cut-offs, pre-specified vs exploratory | Methods 2.4-2.7 - done (published = pre-specified; re-derived = exploratory; noise ladder and floor-corrected criteria pre-registered, commits 6d3cc6b and 20b9ec2) |
| 12b | Reference-standard cut-offs | not applicable (clinical diagnosis) |
| 13a | Index-test readers blinded to reference | done by design (fully automated) |
| 13b | Reference readers blinded to index test | not applicable / unknown for CAP - state |
| 14 | Methods for accuracy estimates and comparisons | Methods 2.5 - done (Wilson CIs, AUC, kappa, McNemar, LOOCV, bootstrap) |
| 15 | Handling of indeterminate results | TO DO: nights where background could not be estimated or RAI undefined are excluded - report counts |
| 16 | Handling of missing data | TO DO: missing ECG (no heartbeat removal), missing units (absolute criteria skipped), missing demographics (HMC) |
| 17 | Analyses of variability, pre-specified vs exploratory | Methods 2.6 - done; label background and boundary analyses as exploratory, ladder as pre-specified |
| 18 | Intended sample size and how determined | TO DO: state that all available open data were used; report precision instead |
| 19 | Participant flow diagram | TO DO: 1,252 recordings -> exclusions (no chin EMG, < 10 min REM, withdrawn) -> 1,177 scored |
| 20 | Baseline characteristics | T1 - done incl. CAP ages (gender-age.xlsx); add HMC aggregate demographics from the database description |
| 21a | Severity distribution in those with the target condition | partial: CAP gives no severity; established clinical RBD (spectrum bias) - report RWA metric distribution (F2f) and age (T17) |
| 21b | Alternative diagnoses in those without | T1/T2 - done for CAP groups; MGH/HMC unspecified |
| 22 | Interval between index test and reference standard | TO DO: same recording (CAP) - state |
| 23 | Cross-tabulation of index test by reference standard | TO DO: 2x2 tables per method (CAP RBD vs same-system patients) as a supplementary table |
| 24 | Accuracy estimates with precision | T2, T6, T7, T10, L4 - done |
| 25 | Adverse events | not applicable (secondary analysis) |
| 26 | Limitations | Discussion - done |
| 27 | Implications for practice | Discussion/Conclusion - done |
| 28 | Registration | not registered; noise ladder (commit 6d3cc6b) and floor-corrected criteria (commit 20b9ec2) pre-specified in the repository |
| 29 | Protocol access | repository: paper/preregistration_noise_ladder.md, paper/preregistration_floor_corrected.md, code, notebook |
| 30 | Funding | TO DO: state "no funding" |
