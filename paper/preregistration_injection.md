# Pre-specified analysis: known muscle activity added to every night (written 2026-10-05, before running it)

Committed together with the code that runs it (`src/inject.py`, `run_inject.py`,
`run_inject_report.py`, `sim_injection.py`, the `masks` output of `src/rwa.py: score_night`)
and with its white-noise predictions (`paper/preregistration_injection_whitenoise.csv`),
before any real night has been scored with added activity. The code was tested on synthetic
white-noise nights only.

## Why

Two limitations of the study are about data that do not exist openly. The only open RBD
recordings are 21 nights from one center on one quiet recording system (CAP), and there are
no open recordings of people with Parkinson's disease. More patients cannot be added without
a data request. What can be tested is whether the conclusions depend on those 21 patients,
on CAP's recording system and on the white noise the noise ladder added:

1. that the amount of muscle activity a published rule can detect is set by the recording's
   noise floor (the ladder showed this for 21 RBD nights with white noise only);
2. that the floor-corrected (FC) rule removes that dependence;
3. that a noisier system misses RBD (shown so far only by adding white noise to CAP);
4. that the measured amount of RWA, the quantity Parkinson's research uses, shifts with the
   recording system, whoever's muscle activity is measured.

Here the muscle activity is known. It is added to the REM sleep of nights recorded without RBD
on six systems at six centers, each with its real background (noise that is colored and varies
through the night, artifacts, heartbeat residue, the sleeper's own twitches). The experiment
does not add patients; it removes the need for them in claims 1-4.

## Data

Recipients: every night without RBD that the study already uses, streamed again from the
same open sources and scored as recorded.

| system | nights | rate |
|---|---|---|
| CAP patients (CAP's main system, Parma) | the 51 same-system patients without RBD | 512 Hz |
| MGH (Challenge 2018, Boston) | every third training record in RECORDS order (332 of 994) | 200 Hz |
| HMC (The Hague) | all (withdrawn SN014, SN064, SN135 excluded) | 256 Hz |
| BOAS (OpenNeuro ds005555) | all 128; each participant's first night is primary | 256 Hz |
| DOD-H (Dreem, France) | 25 | 250 Hz |
| DOD-O (Dreem, Stanford) | 55 | 250 Hz |

CAP's healthy volunteers (several systems, some below 200 Hz) are processed and reported
separately. Nights with at least 10 minutes of REM and chin EMG in physical units. The
floor of a night is its quiet-REM level as recorded (5th percentile of 1-s REM RMS).

Donors (part B): the 21 CAP RBD nights on the main system (512 Hz, microvolts). A donor is the
night's REM chin EMG as the main pipeline sees it: native band (10-100 Hz), 50-Hz notch,
heartbeat removed.

## What is added

Everything is added to the night's chin EMG after its own filtering and heartbeat removal,
exactly where the noise ladder added its noise, and only in REM. Every copy of a night is then
reduced to the 20-ms envelope and scored by the unchanged code (`src/rwa.py`).

**A. Synthetic activity**, two patterns per night, placed at random but seeded by cohort and
record (the same placement and the same noise at every amplitude):

- *tonic*: episodes of 1-4 whole REM epochs separated by 2-6 epochs without (about 40% of REM),
  never across two REM periods;
- *phasic*: bursts of 0.25, 0.5, 1 and 2 s in turn, 4-14 s apart, inside REM periods;
- each episode is Gaussian noise passed through the night's own EMG filter (band and mains
  notch), with 25-ms raised-cosine onset and offset, scaled so that its RMS in the night's band
  during activity is the stated amplitude;
- 49 amplitudes from 0.25 to 16 µV in steps of 9% (2^(1/8)).

A scoring unit (the method's tonic epoch, phasic mini-epoch or SINBAR mini-epoch, on the
night's concatenated REM) is *injected* if the activity covers >= 75% of it (tonic units) or
holds >= 0.1 s of full activity (mini-epochs); *clean* if it holds no activity (mini-epochs:
none within 0.1 s either); other units are left out. For each copy, rule and unit type, the
detection rate h on injected units is corrected for the detection rate p0 on clean units of the
same copy: h' = (h - p0) / (1 - p0). The night's **detection threshold A50** is the amplitude at
which h', made non-decreasing in amplitude (isotonic fit), first reaches 0.5, interpolated in
log amplitude; it is censored if reached at 0.25 µV or never reached by 16 µV.

**B. Transplanted RBD activity**: within each system, recipients sorted by record name receive
the donors in turn (recipient i gets donor i mod 21, donors in numerical order), so every donor
contributes about equally to every system. Recipient REM epoch j receives donor REM epoch
floor(j n_d / n_r) (the donor's night sampled evenly), resampled to the recipient's rate; each
of the recipient's REM periods is passed through its EMG filter. Two amplitudes: x1 (as
recorded) and x0.5 (half the muscle activity and half the donor's own noise). The donor's own
noise means that at x1 the hybrid floor cannot be lower than about CAP's; x0.5 reaches lower.

Rules: Montreal and SINBAR, published and floor-corrected (B = 1.0 µV, guard 1.5, as
pre-specified in preregistration_floor_corrected.md); AASM (published); RAI. Published %
cut-offs. FC is evaluated only where it applies: >= 200 Hz and a floor <= 1.69 µV (the
night's own floor for synthetic activity, the hybrid's floor for transplants).

## White-noise predictions (`sim_injection.py`, 144 synthetic nights)

The same code on nights whose chin EMG is band-limited white noise at floors 0.3-2.0 µV, at
200, 250, 256 and 512 Hz, three seeds each (frozen in
`paper/preregistration_injection_whitenoise.csv`):

| measure (pattern) | published A50 | log-log slope | FC A50 at 0.4 / 1.0 / 1.4 µV | FC slope (floor <= 1.69) |
|---|---|---|---|---|
| Montreal tonic (tonic) | 1.91 x floor | 1.00 | 1.91 / 1.93 / 2.04 | 0.04 |
| Montreal phasic (phasic) | 4.39 x floor | 1.00 | 4.35 / 4.41 / 4.41 | 0.01 |
| SINBAR "any" (phasic) | 1.96 x floor | 1.00 | 1.95 / 2.02 / 2.08 | 0.05 |

These three are the primary measures. AASM tonic (threshold = the NREM floor itself) is
detected by noise alone (p0 0.4-0.8) and is not analyzed.

## Criteria

**A. Synthetic activity** (primary measures, primary nights of the six systems, >= 200 Hz;
slopes by ordinary least squares of log A50 on log floor over nights whose A50 is not
censored, with 95% bootstrap intervals over nights; the criterion uses the point estimate):

1. **A1. The published rules' threshold follows the floor**: slope 0.75-1.25 for each measure.
2. **A2. The floor-corrected threshold does not**: slope -0.25 to +0.25 for each measure, on
   nights where FC applies.
3. **A3. Across systems**: the highest system median A50 divided by the lowest is >= 2.5 for
   each published measure and <= 1.3 for each FC measure (medians include censored nights at
   the grid's ends).
4. **A4. Real backgrounds behave like the ladder's white noise**: a night's A50 is within
   +/-25% of the white-noise A50 at its floor (nearest simulated rate, log-log interpolation)
   in >= 80% of nights, for each measure and variant (censored nights count as outside).

**B. Transplanted RBD activity** (primary nights; differences between systems with 95%
intervals from 2,000 bootstrap resamples of the 21 donors):

5. **B1. A noisier system misses real RBD activity**: at x1, the share of hybrid nights flagged
   by the published Montreal criteria is >= 20 points lower on HMC than on BOAS (ladder:
   Montreal RBD sensitivity 90% -> 57% at 1.5-2 µV).
6. **B2. The ladder predicts a real background**: for each system, the median difference
   between a hybrid's published Montreal tonic % (x1) and its donor's noise-ladder tonic % at
   the hybrid's floor (log-floor interpolation in results/ladder_scores.csv) is within +/-10
   points.
7. **B3. Sensitivity at half amplitude**: at x0.5, published Montreal: HMC >= 20 points below
   BOAS; Montreal-FC and SINBAR-FC (hybrids where FC applies): HMC within +/-10 points of BOAS.
8. **B4. The same activity measured on two systems** (the quantity used in Parkinson's
   research): at x0.5, the mean Montreal tonic % per donor on HMC minus on BOAS (paired by
   donor) is <= -10 points published and within +/-5 points FC.

Interpretation:
- A1-A3 met: with known activity on six systems, what the published rules can detect is set by
  the noise floor, and the FC rule removes the dependence; claims 1 and 2 do not rest on the
  21 patients or on CAP's system.
- A4 not met: real backgrounds change detection beyond what the floor alone predicts; the
  direction (easier or harder than white noise) and the systems are reported, and the ladder's
  white-noise results are treated as approximate.
- B1 met: claim 3 holds for real RBD activity on a real noisy background, not only in white
  noise. B2 met: the ladder's white-noise model predicts such backgrounds.
- B3 (FC parts) and B4 (FC) met: FC keeps real RBD activity comparable across the quietest and
  the noisiest system where it applies. B4 (published) met: claim 4 holds for real muscle
  activity measured through two real systems.
A criterion that fails is reported as failed; thresholds, units or nights are not changed
after the data are seen.

## Secondary (reported, no pass/fail)

- Detection curves (h' against amplitude) and p0 by system, for every measure and variant.
- Night-level dose-response: share of nights flagged against amplitude, by system and rule,
  and the amplitude at which half of a system's nights are flagged.
- Slopes within each system; CAP's healthy volunteers; BOAS with all nights.
- Transplant: every rule at both amplitudes and in every system, the same nights without the
  donor (false positives) and each donor's own night on CAP (the reference).

## What the design cannot do

The synthetic activity is band-limited Gaussian noise with flat envelopes, not real motor-unit
firing. The transplant carries CAP's own noise and the recipient's own twitches, and the
added activity bypasses the target system's amplifier and filters: the experiment isolates the
noise floor and leaves gain and bandwidth differences between systems aside. RBDtector is not
run (35 s per night and copy). Nothing here adds RBD or Parkinson's patients.

## Deviations

MGH is fixed at every third record. If a runtime ends early, the analysis runs on the nights
completed and the shortfall is reported; DOD-H and DOD-O are dropped only if Zenodo cannot be
reached, and that is reported.
