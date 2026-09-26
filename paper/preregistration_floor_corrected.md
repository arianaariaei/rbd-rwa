# Pre-specified analysis: floor-corrected RWA criteria (written 2026-09-26, before running it)

Committed together with the code that runs it (`run_floor.py`, `src/rwa.py: threshold`)
before any floor-corrected result exists for MGH, HMC or the CAP patient groups, so the
criteria below cannot have been tuned to the outcome. The rule was developed on simulated
white noise and checked on three local CAP nights (rbd1, n1, n2) only.

## Why

The noise ladder (preregistration_noise_ladder.md, results F5) showed that the relative
criteria are, in effect, multiples of the recording's noise floor: a rule "activity above
k x background" requires muscle activity of about sqrt(k^2 - 1) x background, so quiet
systems count small twitches (false positives) and noisy systems miss RBD. Harmonising the
noise floor removed the site gap but cost sensitivity, and re-deriving cut-offs on
harmonised data did not give portable thresholds (criterion 4 not met).

## The floor-corrected (FC) rule

For a night with background b (5th percentile of 1-s REM RMS, as in the published
implementation), "activity above k x background" becomes activity above

    T = max( sqrt(n^2 + (k^2 - 1) B^2),  g b ),   n = b / 0.91

- B = reference background, **1.0 uV** (primary; pre-specified, between the quiet systems'
  0.5-0.9 uV and HMC's 1.5 uV, and equal to the REM Atonia Index's 1-uV atonia bin). At
  b = B the rule is (within 3%) the published one; below B it is an absolute threshold;
  above B the noise is subtracted in power instead of multiplied.
- n = the noise RMS implied by b: for band-limited white noise the 5th percentile of 1-s RMS
  is 0.91 of the RMS (0.910-0.913 at 200, 256 and 512 Hz, simulated).
- g = **1.5**, a guard against counting noise: on simulated white noise, runs >= 0.1 s above
  1.5 b occur in 0.4-0.7% of 3-s mini-epochs and never make an epoch tonic (1.3 b: 11%).
- Everything else is unchanged: epochs, mini-epochs, burst durations, the 10-uV tonic
  alternative, and the published % cut-offs (Montreal tonic >= 30% or phasic >= 15%;
  SINBAR mentalis "any" >= 18.2%).

Methods: Montreal-FC and SINBAR-FC. The RAI (already noise-subtracted) is the comparator.
Secondary variants: FC with B = 0.5, 0.75, 1.25, 1.5, 2.0 uV; "clamp" (threshold
k max(b, B), B = 1.0: an absolute floor without subtraction).

## Data

The existing packs (every scored night as recorded: CAP, MGH n~925, HMC n=147; and HMC
scaled by 0.39, for gain) and the existing noise-ladder packs (the same 300 MGH, 151 HMC and
all CAP nights with in-band white noise; steps as in the ladder analysis). CAP RBD and CAP
patients = nights on CAP's main system (512 Hz, microvolts): 21 RBD, 51 other patients.
Nights with >= 10 min REM. Published % cut-offs unless stated.

## Criteria (B = 1.0 uV)

1. **Noise invariance, patients without RBD.** On the same MGH ladder nights, the share
   flagged at the 1.5-uV harmonised floor (`h150`) is within 5 percentage points of the
   share as recorded, for Montreal-FC and for SINBAR-FC (published: -22 and -50 points).
2. **Noise invariance, RBD.** CAP RBD sensitivity at `h150` is within 10 points of
   sensitivity as recorded, for each FC method (published Montreal: 90% -> 57%).
3. **Site agreement as recorded.** All scored nights: MGH and HMC differ by <= 5 points
   (Montreal-FC) and <= 10 points (SINBAR-FC) (published: +20 and +51).
4. **Sensitivity kept.** CAP RBD sensitivity as recorded >= 85% for each FC method.
5. **No more false positives on the quiet system.** CAP patients' share flagged under FC is
   not above the published share (each method).

Interpretation, per method:
- 1, 2, 3 and 4 met: the floor-corrected rule is a working remedy for automated scoring.
- 1 and 2 met, 3 not met: the rule is noise-robust, but the remaining MGH-HMC difference is
  not produced by the noise floor (population, or recording properties such as gain; see
  the scale check below).
- 1 not met: the rule is not noise-robust at HMC's floor.
- 5 not met: FC moves the operating point towards more positive calls in patients.

If B = 1.0 fails a criterion that another B passes, that is reported as exploratory, not as
a pass.

## Secondary (reported, no pass/fail)

- Reference background B from 0.5 to 2.0 uV, and the clamp: the same quantities.
- Discrimination (AUC, CAP RBD vs CAP patients) of the FC tonic, phasic and "any" measures.
- Cut-offs re-derived under FC (Youden on CAP; leave-one-out; 2,000 bootstrap re-derivations)
  and the MGH and HMC shares they flag; "portable" if the gap is <= 5 points with
  leave-one-out sensitivity >= 80%.
- Gain: FC thresholds are absolute below B, so unlike the relative criteria FC is expected to
  change when HMC is scaled by 0.39; the paired change is reported.
- Scale of muscle activity: per cohort, the median 1-s RMS in REM (50th, 95th percentile) and
  N2/N3 (50th), each with the noise (b / 0.91) removed in power. If MGH/HMC ratios are within
  0.67-1.5, the two systems record muscle activity on a comparable scale and absolute
  thresholds are comparable between them; outside that range, cross-site FC comparisons are
  confounded by gain.
- Montreal phasic bursts limited to 10 s instead of 15 s (the sources differ).
- MGH by record batch (the first four characters of the record name), and the 300 ladder
  nights against the rest (representativeness of the ladder subset).
