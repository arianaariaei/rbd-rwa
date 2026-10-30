# Results of the runs finished on 2026-10-30

Reports on Drive (MyDrive/rbd-rwa/results): inject_report.md, noise_arms_x_report.md,
rbdtector_checks_report.md, anphy_report.md. Key numbers below; the manuscript draft
(paper/submission/manuscript_revision_draft.md) was filled from them.

## Injection experiment (preregistration_injection.md)

686 nights without RBD on six systems (CAP same-system patients 51, MGH 311, HMC 147, BOAS 99,
DOD-H 25, DOD-O 53); 21 CAP RBD donors.

- A1 (published A50 against floor, log-log slope 0.75-1.25): Montreal tonic 0.99 [0.97-1.00],
  Montreal phasic 1.00 [0.99-1.00], SINBAR any 1.00 [0.99-1.01] - met.
- A2 (FC slope within +/-0.25): -0.01, -0.01, +0.02 - met (SINBAR any on tonic -0.08).
- A3 (system median A50, max/min >= 2.5 published, <= 1.3 FC): published 4.34 / 4.22 / 4.19;
  FC 1.02 / 1.02 / 1.06 - met.
- A4 (real backgrounds like white noise, >= 80% of nights within 0.75-1.25): 95-100% - met.
- B1 (Montreal published, full amplitude, BOAS - HMC >= 20): 92% - 61% = +30.7 [donor bootstrap
  17.1-44.9] - met.
- B2 (hybrid minus donor's ladder value, |median| <= 10): -0.1 to +2.0 points by system - met.
- B3 (half amplitude): Montreal published HMC 28% - BOAS 83% = -54.9 [-66.0 to -43.7] - met;
  **Montreal FC 48% - 66% = -18.0 [-34.2 to -2.0], criterion within +/-10 - NOT met**;
  SINBAR FC 95% - 98% = -2.8 [-7.1 to 0.0] - met.
- B4 (same donors' tonic %, HMC - BOAS): published -24.0 [-29.5 to -19.2] (x1), -28.4 (x0.5) - met;
  FC -4.6 [-7.5 to -1.9] (x1), -4.8 [-8.5 to -1.6] (x0.5) - met.
- AASM tonic (referenced to the minimum NREM amplitude): published slope 0.47, 151 of 683 nights
  censored - descriptive.

## Exploratory: noise that follows the night (preregistration_revision.md, addendum)

MGH, 280 nights, paired differences from white noise at the same level (points, 95% CI):

| rule | drift 1.5 uV | level-matched recorded noise 1.5 uV | drift 2.0 uV |
|---|---|---|---|
| Montreal published | +3.6 [1.8, 5.7] | 0.0 | +5.4 |
| SINBAR published | +42.9 [37.1, 48.6] | +2.5 | +52.5 |
| Montreal FC (one estimate per night) | +24.6 [19.6, 29.6] | +0.4 | +47.9 |
| SINBAR FC | +46.8 [40.7, 52.5] | +10.0 | +55.0 |
| Montreal FC-window | +0.4 [-1.1, 2.1] | -0.4 | +10.0 |
| SINBAR FC-window | +34.6 [28.9, 40.0] | +9.6 | +43.2 |

CAP RBD sensitivity under every noise kind: Montreal FC-window 76-81%, SINBAR FC-window 95-100%.
As recorded (revision_exploratory_report): Montreal FC-window MGH - HMC +2.9 [-3.9, 8.0], equivalent
within +/-10; SINBAR FC-window +8.2 [-0.4, 16.1], not; same-system CAP patients SINBAR 33% (FC 45%,
published 75%); AUC 0.87.

Reading: a windowed noise estimate protects the Montreal rule against drifting noise; SINBAR's
"any" rule, which counts any 3-s mini-epoch above threshold, is still reached by the loudest
stretches. Level-matched recorded noise behaves like white noise at 1.5 uV for every rule except
SINBAR-FC (+10); at 2.0 uV (outside the FC range of 1.69 uV) SINBAR-FC rises by 40 points.

## RBDtector checks (preregistration_revision.md, R5)

- Verify: our runner against RBDtector as released, 12 nights x 2 baselines: tonic, phasic, any and
  baseline identical in 24 of 24 runs (max |difference| 0.0000).
- MGH (n = 100) with the scored arousals passed to RBDtector: published 65.0% -> 65.0% flagged;
  FC 55.0% -> 56.0%.
- MGH (n = 99) with the heartbeat removed: published 64.6% -> 71.7%; FC 55.6% -> 35.4%.
- BOAS, heartbeat removed (only 6 nights where beats were found on the chin EMG): published 100% ->
  100%; FC 66.7% -> 33.3%.

## ANPHY-Sleep (preregistration_anphy.md)

28 nights (all >= 10 min REM), age 20-44, 1000 Hz, floor 0.62 [0.36-0.90] uV, signature 1.11,
heartbeat removed in 26. Units confirmed as uV by the authors after the pre-specification.

- A1 net N2/N3 1.38 uV = 0.87 x MGH's - met.
- Shares: Montreal published 0.0% [0-12], FC 3.6% [1-18]; SINBAR published 50.0% [33-67], FC 14.3%
  [6-31]; RAI 0.0%; SINBAR-FC >= 49.1% 7.1% [2-23]; FC-window (exploratory) Montreal 3.6%, SINBAR 10.7%.
- A2 SINBAR published >= 30% - met. A3 published - FC = 36 points >= 20 - met. A6 7.1% <= 10% - met.
- A4 against the pooled earlier healthy cohorts: SINBAR -39.5 published -> -20.4 FC; Montreal
  -37.1 -> -10.9 - met (both smaller in absolute value).
- A5 seven groups without RBD: SINBAR published rho -0.86 (exact p 0.024), FC +0.21 (p 0.66);
  Montreal published -0.68 (p 0.11), FC +0.14 - met.
- Note: at a floor similar to MGH and DOD-H, ANPHY's young adults were flagged far less by the
  published Montreal rule (0% against 29% and 20%): age and population matter beside the floor.
