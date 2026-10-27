# Revision plan after the pre-submission review (2026-10-27)

Source: `Pre-submission review noise floor and automated RWA scoring.md` (25 October 2026).
Who: **code** = written here and run on Colab; **text** = manuscript change; **you** = needs
the author (a decision, a signature, a person, or permission to publish).

| Review item | Action | Who | Status |
|---|---|---|---|
| C1 No visual anchor (minimum fix) | Every claim reworded as about *automated implementations of background-relative criteria*; report the SINBAR phasic mismatch (69.0% vs 40.9%) next to the "any" match; same-system specificity stated plainly | text | to do |
| C1 (best fix) | Blinded visual-scoring substudy: protocol, OSF pre-registration text, blinded EDF excerpts (30 nights x as recorded / +noise), scoring sheet, analysis script | code + you (a scorer, OSF account) | to do |
| C2 Equivalence from point estimates | Every between-site difference with a 95% CI; TOST equivalence at +/-10 points (90% CI); n and exact p for the six-cohort Spearman correlations; pre-specified point-estimate criteria relabeled descriptive; paired ladder evidence leads | code (`run_revision.py`) + text | to do |
| C3.1 Gain | Gain dependence moved into Discussion and Conclusions; FC called "a correction for noise"; recommend reporting floor *and* net level | text | to do |
| C3.2 Muscle in the noise estimate | Second noise estimator that cannot contain REM muscle activity (N2/N3 quiet level; and the lower of the two): sensitivity, site gap, ladder invariance | code | to do |
| C3.3 Out-of-range nights | MGH-HMC comparison on nights inside FC's range only | code | to do |
| C4 One RBD center | (a) Injection experiment, pre-registered 2026-10-05 (09393b4): known activity on six systems, transplanted RBD activity; (b) RBD results framed as proof of mechanism; screening-yield numbers labeled illustrative and moved to the Supplement; (c) data requests and a run-it-locally kit for centers holding RBD/PD recordings | code + text + you (send requests) | (a) coded, not run |
| M1 Overreach | New title, Significance, Conclusions; no causal "drives"; no process in the title | text | to do |
| M2 Novelty | Credit Ferri's noise correction; state the gap; cite the Jung/Wing/Schenck editorial; Levendowski's sensor-placement point | text | to do |
| M3 Japanese thresholds | Combined SINBAR measure, visual scoring; equipment as one untested candidate | text | to do |
| M4 PD benchmarks | Add Nepožitek 2019; verify and add the 2019 Neurology study; Ferri night-to-night variability as a yardstick; "0.6 µV" labeled a scenario; "concerns scale" moved into the PD section; Postuma 72.9 vs 41.0 checked | text | to do |
| M5 Pre-specification | Repository public with history + Zenodo DOI; "committed before they were run"; discovery (CAP, MGH, HMC) vs confirmation (BOAS, DOD) everywhere; OSF registration of the visual substudy | text + you (permission to publish the repository) | to do |
| M6 White noise only | Ladder arms with pink noise, slowly drifting noise and real recorded noise (HMC quiet-REM library) on the same MGH and CAP nights | code | to do |
| M7 Heartbeat / BOAS | Periodicity-matched BOAS result in the main text; RBDtector on heartbeat-removed input | code + text | to do |
| M8 Confounders | Age-matched AUC in the main text; analysis without narcolepsy; medication paragraph with a bound | code + text | to do |
| M9 RBDtector | Modified runner vs unmodified program on 12 nights (6 RBD); MGH re-run with its scored arousals; letter to RBDtector's authors | code + you (send) | to do |
| M10 AASM | Removed from the abstract; one Results sentence on its continuous measures along the ladder | code + text | to do |
| M11 Authorship, AI | Co-author invitation letter (sleep physician, ideally also a statistician); AI disclosure kept explicit | you | draft letter |
| Numbers | 277/280 (one paired set throughout), interval types labeled, abstract trimmed, ladder criterion 3 counted as partly met, CAP 105 vs 88 explained (row + flow diagram), Table 3 re-rounded, "about 40", "(100)" in RBDtector cells, rho with n and p, Montreal 15-s source | code + text | to do |
| Montreal phasic duration | Sources disagree (0.1-5 s; 0.1-10 s; the code used 15 s): every night re-scored with 5 s and 10 s; **check the original Montplaisir 2010 Methods through the library** and use the original as primary | code + you (library access) | coded |
| References | Sakuma and Levendowski reworded; Postuma and DREAMER numbers checked; five new citations; dataset DOIs | text | to do |
| Writing | Results restructured around three questions; abstract ~12 numbers; one term (quiet-REM level, b); evidence numbered; tone; legends cleaned | text | to do |
| Compliance | MeSH keywords; Significance without methods; ethics (Helsinki + institutional exemption); disclosure; funding; figure files with alt text; graphical abstract; double-spaced Word file; cover letter | text + you (exemption letter, author details, US$50) | to do |
| More data | Requests to centers holding RBD/PD polysomnograms (NSRR and the CITI-gated set excluded, as agreed), plus the run-locally kit so no recordings have to change hands | code + you (send) | to do |
