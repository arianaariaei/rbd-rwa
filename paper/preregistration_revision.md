# Analyses added in revision (specified 2026-10-27, before they were computed)

In response to the pre-submission review (`paper/revision_plan_2026-10-27.md`). Committed
with the code that runs them (`run_noise_arms.py`, `src/noise_arms.py`, `run_revision.py`,
`run_rbdtector_checks.py`, the `noise_from` option of `src/rwa.py`) before any of them was
run. Two kinds of analysis are mixed here, and they are reported differently:

- **New runs on data** (R1, R5): the recordings are streamed again and manipulated in ways
  not done before. Their criteria are fixed here and judged as written.
- **Re-analyses** (R2-R4, R6): they use nights and scores that earlier analyses had already
  examined. They are specified before being computed, but they are post hoc with respect to
  the data and are reported as such, with intervals rather than verdicts where possible.

## R1. Noise that is not white (review M6)

The noise ladder added band-limited white noise. The same nights (the ladder's first 300 MGH
records; CAP's nights in microvolts) are raised to a quiet-REM level of 1.5 and 2.0 µV with
three further kinds of noise (`src/noise_arms.py`): pink (1/f) noise; white noise whose level
drifts through the night (log-normal random walk, 10-min correlation time, SD 0.3 of the log
level); and recorded noise (the quietest REM seconds of 30 HMC nights, spliced). The ladder's
own white noise is regenerated with its seeds as the reference. One set of nights throughout:
those with at least 10 min of REM in every copy.

Criteria, at 1.5 µV, paired on the same nights, published Montreal and SINBAR chin rules:

1. **R1a.** For each kind, the share of MGH nights flagged is within 5 points of the share
   with white noise. Met: the noise ladder's dose-response does not depend on the noise being
   white.
2. **R1b.** Floor-corrected (B = 1.0 µV, REM noise estimate as pre-specified): for each kind,
   the share of MGH nights flagged is within 5 points of the share as recorded.
3. **R1c.** CAP RBD sensitivity of the published Montreal criteria with each kind is within
   10 points of the sensitivity with white noise.

Expectation stated in advance: drifting noise is the hard case for both rules, because the
5th percentile of 1-s RMS samples the quietest part of the night; if R1b fails for drift only,
the correction needs a noise estimate that follows the night (for example per REM period).

## R2. A noise estimate that cannot contain REM muscle activity (review C3.2)

The floor-corrected rule takes its noise estimate from REM (n = b / 0.91), which in RBD also
holds tonic muscle activity (quiet-REM level 0.86 µV in RBD vs 0.48 µV in same-system
patients). Two alternatives are scored on every night as recorded and on R1's copies: the
quiet N2/N3 level (5th percentile of 1-s N2/N3 RMS, "FC-nrem") and the lower of the two
("FC-min"). Reported: CAP RBD sensitivity and same-system false positives, AUC, MGH-HMC
difference (R4), and invariance on R1's copies.

Criterion **R2a**: Montreal-FC-nrem sensitivity in CAP RBD is at least 85% (the
floor-corrected criterion 4 that the REM estimate missed with 81%). This is a new rule
judged on the same 21 patients, so a pass is a candidate, not a confirmation.

## R3. Nights inside the floor-corrected rule's range (review C3.3)

Every floor-corrected comparison is repeated on nights recorded at 200 Hz or more with a
quiet-REM level of at most 1.69 µV; the share of nights outside the range is reported for
every group.

## R4. Equivalence instead of point estimates (review C2)

Every between-site difference (MGH - HMC, BOAS - DOD-H, DOD-O - MGH, CAP same-system patients
- MGH; every rule) is reported with a 95% Newcombe hybrid-score interval. Agreement between
sites is claimed only where two one-sided tests show equivalence within ±10 percentage points
(90% interval inside the margin); ±5 points is also reported. Same-night ladder changes are
reported with paired intervals and exact McNemar tests. Rank correlations across the six groups
without RBD are reported with n and exact permutation p. The point-estimate criteria committed
earlier are reported unchanged and called descriptive.

## R5. RBDtector (review M7, M9)

1. **Verification.** Twelve nights (CAP rbd1-rbd6, nfle1, plm1, ins2; three of the 100 MGH
   nights) are scored by our runner and by RBDtector as released (its own `find_rem_blocks`,
   the whole night at the native rate, baseline recomputed for the floor-corrected run).
   Criterion **R5a**: tonic, phasic and "any" percentages within 0.1 points and baselines within
   0.01 µV on every night. If not met, the Parkinson's RBDtector results are re-run with the
   program as released.
2. **Arousals.** The 100 MGH nights are scored with the arousals of the Challenge 2018
   annotations passed to RBDtector, as its published cut-off assumes (descriptive: change in
   the share flagged and in "any" %).
3. **Heartbeat.** The same MGH nights and BOAS's first nights are scored with the heartbeat
   removed from the chin EMG (descriptive).

## R6. Descriptive additions

CAP nights by group and recording system (the 105 analyzed against 88 in Table 1); the CAP
analysis without the five narcolepsy patients and against patients aged 50 or over; AASM's
continuous measures along the ladder; the MGH ladder recomputed on one set of nights (those
with at least 10 min of REM as recorded and at every step).

Added 2026-10-27, before any run: secondary sources give the Montreal phasic burst as
0.1-5 s or 0.1-10 s, whereas the main analysis allowed up to 15 s (the original article could
not be checked here). Every night as recorded is also scored with bursts limited to 5 s and to
10 s (published and floor-corrected), and the share flagged in each group is reported.
