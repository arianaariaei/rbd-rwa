# Pre-registration: what the noise floor means for Parkinson's disease research

Written 2026-10-02, before any of the analyses below were run. Committed together with the
code that runs them (`src/rbdtector.py`, `run_rbdtector.py`, `run_parkinsons.py`,
`src/floorcheck.py`, `check_floor.py`).

## Why

Isolated RBD is the strongest known prodromal marker of Parkinson's disease (PD), dementia
with Lewy bodies (DLB) and multiple system atrophy: 73.5% of 1,280 patients in 24 centers
developed one of them within 12 years (Postuma et al., Brain 2019). REM sleep without atonia
(RWA) is the polysomnographic finding that confirms RBD, and PD research uses it in five ways:

1. **Diagnosis and trial eligibility.** People with RBD are the population for
   disease-modifying prevention trials; multi-center prodromal cohorts pool RWA across
   centers (NAPS: 9 North American centers).
2. **Conversion risk.** Baseline tonic chin RWA was 72.9% in patients with RBD who later
   developed PD against 41.0% in those who stayed disease-free, a 31.9-point difference
   (Postuma et al., Neurology 2010; 62.7% for any neurodegenerative disease).
3. **Progression.** Tonic chin RWA rose from 30% to 54% over a mean 5 years in 11 patients
   with isolated RBD, about 4.8 points per year (Iranzo et al., Sleep 2009).
4. **An earlier stage.** RWA without RBD ("isolated RWA") is followed as a possible stage
   before RBD (DREAMER, 4 Italian centers, RAI < 0.85; Ferri et al., PLoS One 2026) and
   separates subgroups of early PD (25% RBD, 25% isolated RWA, 50% normal; Dodet et al.,
   Mov Disord 2024).
5. **Lewy body disease diagnosis.** Polysomnographic RWA is an indicative biomarker of DLB
   (McKeith et al., Neurology 2017).

The paper has shown that background-relative RWA criteria measure the recording system's
noise floor as well as the patient. This pre-registration asks what that does to uses 2-4,
in their own units, and whether the open-source scorer used in PD and RBD research,
RBDtector (Röthenbacher et al., Sci Rep 2022: developed on 21 patients with PD and RBD, 16
with PD without RBD, 81 with isolated RBD and 72 controls; validated at a second center by
Joza et al., J Sleep Res 2025), behaves the same way. Its default rule counts chin activity
where the RMS of a 30-ms chunk exceeds twice a baseline, the lowest 30-s RMS window of each
REM period - on an atonic night, mostly the system's noise.

No dataset with PD patients is available without an application, so nothing here is
measured in people with PD; the CAP RBD patients are presumably isolated RBD.

## Already seen (not predicted here)

Shares flagged positive by the published and floor-corrected (FC) Montreal and SINBAR rules
and by the RAI (< 0.8) in every cohort, on every noise-ladder step and by age in BOAS and
CAP (results_floor_2026-09-26.md, results_external_2026-09-27.md). **Not seen:** per-night
changes of the continuous tonic, phasic and "any" percentages on the ladder; RAI < 0.85;
anything from RBDtector; the recruitment arithmetic.

## Data

- **Noise ladder:** CAP RBD (21 nights) and CAP patients on the same system (51), as recorded
  and with the ladder's own noise (the same seeded track and scale per step as
  `run_cohort.py --ladder`). RBDtector steps: as recorded, +0.5, +1.0, +2.0 uV and `h150`
  (quiet-REM level raised to 1.5 uV, HMC's floor). The primary contrast is as recorded ->
  `h150`. If run time forces it, +0.5 and +2.0 are dropped first; this will be reported.
- **Across systems (RBDtector, as recorded):** MGH, 100 nights drawn at random (numpy
  `default_rng(0)`, from the 925 with >= 10 min REM); HMC, all 147; BOAS, the 99 first nights.
- Our own methods are taken from `floor_ladder_scores.csv` and `external_scores.csv` as they
  stand (B = 1.0 uV for FC).

## RBDtector

Commit 7c9c73d (master, 19 May 2022), run through its own controller
(`PSGController.run_rbd_detection`) with default settings. Input per night: the chin EMG
as channel `EMG` in microvolts, band-passed 10-100 Hz and notched as an acquisition system
would (RBDtector does not filter), heartbeat left in; 256 Hz (CAP decimated from 512 Hz,
which is what RBDtector's own spline resampling does at 512 Hz; MGH's 200 Hz resampled by
RBDtector itself); the stages as its "Sleep profile"; no arousals (one dummy event in the
first second, which is wake). Positive: chin "any" >= 23.5%, RBDtector's own chin-only
cut-off (Röthenbacher 2022, Table 5).

Floor-corrected RBDtector: the baseline RBDtector computes is replaced, before detection, by
T / 2 with T = max(sqrt(n^2 + 3 B^2), 1.5 n), n = baseline / r, B = 1.0 uV and r the ratio of
RBDtector's baseline to the RMS of band-limited white noise (simulated in
`src/rbdtector.noise_ratio`). Nothing else in RBDtector changes.

## Predictions

**PD1 - the same RBD nights, as recorded -> `h150` (CAP RBD, mean per-night change).**

- a) Montreal tonic %, published: falls by >= 10 points (a third of the 31.9-point
  difference that predicted PD, two years of the 4.8-point yearly rise).
- b) Montreal tonic %, FC: |change| <= 3 points.
- c) RBDtector tonic %, published: falls by >= 10 points.
- d) RBDtector tonic %, FC: |change| <= 3 points.

**PD2 - RBDtector.**

- a) CAP patients: the published share flagged falls by >= 10 points, as recorded -> `h150`.
- b) CAP patients: the FC share flagged changes by <= 5 points.
- c) CAP RBD: FC sensitivity changes by <= 10 points.
- d) As recorded: published MGH - HMC >= 20 points, and FC |MGH - HMC| at most half of it.
- e) BOAS (healthy, quietest system): published >= 50%, and FC at most half of that.
- f) Nights without RBD pooled (CAP patients, MGH, HMC, BOAS): Spearman rho of the night's
  floor with RBDtector "any" % below 0 published (95% bootstrap interval below 0), and
  weaker (smaller |rho|) with FC.

**Reading.** PD1a and PD1c met: the recording system alone moves RWA by an amount on the
scale of the disease signals PD research uses. PD2a, d (published), e (published) and f
met: RBDtector inherits the dependence. PD1d, PD2b, c and the FC halves of d and e met: the
floor-corrected baseline removes it in RBDtector too. Each criterion is reported met or not
met, whatever the result.

## Descriptive (no predictions)

- **PD3** Isolated RWA by system: share of nights without RBD labeled by DREAMER's
  RAI < 0.85, RAI < 0.8, SINBAR and Montreal (published, FC) and RBDtector (published, FC);
  healthy adults and clinic patients, all and >= 50 y; RAI < 0.85 on the noise ladder.
- **PD4** Recruitment for prevention trials, per 1,000 sleep studies in people >= 50 y: false-
  positive rate from MGH patients >= 50 y (an upper bound), sensitivity from CAP RBD, RBD
  prevalence 1%, 2% and 5%; flagged, RBD found, positive predictive value, studies reviewed
  per RBD found, and people expected to develop a synucleinopathy within 12 years (73.5%).
- **PD5** The floor check for each recording system (floor, nights inside the FC rule's range
  of >= 200 Hz and b <= 1.7 uV, net N2/N3 tone), and the tool that reports it for a new
  recording (`check_floor.py`).
