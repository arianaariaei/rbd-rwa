# Follow-up analyses (2026-09-26)

Floor-corrected criteria, age and per-site PPV: see `results_floor_2026-09-26.md`.

Same packs and scoring as `results_2026-09-26.md`; nights with >= 10 min REM, native band,
all REM epochs unless stated. MGH = PhysioNet Challenge 2018 (n=919-925 scored nights),
HMC = Haaglanden Medisch Centrum (n=147).

## F1 Quiet-REM chin EMG level by cohort (5th percentile of 1 s REM RMS, uV; median [IQR])

| cohort | n | level |
|---|---|---|
| CAP RBD | 22 | 0.80 [0.61-1.22] |
| CAP NFLE | 40 | 0.47 [0.43-0.55] |
| CAP PLM | 10 | 0.48 [0.41-0.56] |
| CAP insomnia | 9 | 0.50 [0.45-0.72] |
| CAP narcolepsy | 5 | 0.60 [0.58-0.95] |
| CAP healthy | 15 | 1.32 [0.49-2.38] (mixed hardware, median fs 200 Hz) |
| MGH | 919 | 0.59 [0.47-0.77] |
| HMC | 147 | 1.52 [1.23-1.79] |

The MGH level is below the 1 uV resolution at which MGH stores chin EMG; HMC's is above it.

## F2 Hardware simulation, part 1: HMC re-recorded at MGH resolution

HMC signals quantised to 1 uV steps (`hmc_q1uv`), and additionally resampled to 200 Hz
(`hmc_mgh`), then processed exactly like every other cohort.

| | HMC | HMC 1 uV | HMC 1 uV + 200 Hz | MGH |
|---|---|---|---|---|
| quiet-REM level, uV | 1.52 | 1.54 | 1.51 | 0.59 |
| Montreal positive, % | 9 [5-15] | 9 [5-15] | 9 [5-15] | 29 [27-32] |
| SINBAR positive, % | 25 [19-33] | 24 [18-32] | 22 [16-30] | 76 [73-79] |
| RAI positive, % | 7 [4-13] | 7 [4-13] | 7 [4-13] | 9 [7-11] |
| methods disagree, % of nights | 22 | 21 | 19 | 70 |
| heartbeat artefact after removal | 1.01 | 1.01 | 1.02 | 1.08 |

At HMC's signal level the MGH storage format changes nothing. This does not test the regime
MGH is in (signal below one quantisation step): see part 2.

Storage steps, read from the file headers: HMC chin EMG 0.024 uV (16 bits over +/-800 uV);
MGH 1 uV (WFDB gain 1 unit/uV) for chin and ECG alike.

## F2b Hardware simulation, part 2: HMC scaled to MGH's level first

HMC multiplied by 0.39 (= 0.59 / 1.52, the ratio of the median quiet-REM levels) before
anything else (`hmc_low`), and then also quantised to 1 uV and resampled to 200 Hz
(`hmc_low_mgh`). The scaled copy puts HMC where MGH sits relative to the storage step.

| | HMC | HMC x0.39 | HMC x0.39, 1 uV + 200 Hz | MGH |
|---|---|---|---|---|
| quiet-REM level, uV | 1.52 | 0.59 [0.48-0.70] | 0.63 [0.53-0.72] | 0.59 |
| Montreal positive, % | 9 [5-15] | 8 [5-14] | 8 [5-14] | 29 [27-32] |
| SINBAR positive, % | 25 [19-33] | 25 [19-33] | 20 [14-27] | 76 [73-79] |
| RAI positive, % | 7 [4-13] | 3 [1-8] | 3 [1-7] | 9 [7-11] |
| methods disagree, % of nights | 22 | 23 | 18 | 70 |

- Scaling alone leaves the relative criteria unchanged (as it should: every threshold is a
  multiple of the night's own level; the 10 uV absolute tonic limit is never reached) and
  halves the RAI's positives (its 1 uV amplitude bins are absolute).
- The MGH storage format applied at MGH's level still does not raise positivity (SINBAR
  even falls 25% -> 20%; quantisation noise lifts the quiet level 0.59 -> 0.63 uV).
- So neither the amplitude level nor the storage format explains MGH's 29% / 76%.

## F2e The reverse test: MGH with HMC's noise floor (T12)

White Gaussian noise (SD 1.5 uV, seeded by record name) added to the chin EMG of the first
300 MGH records (`chal18_noise`); paired with the same nights as recorded (n=277 with
>= 10 min REM in both).

| | MGH as recorded | MGH + noise | HMC |
|---|---|---|---|
| quiet-REM level, uV (median) | 0.56 | 1.37 [1.31-1.46] | 1.52 |
| Montreal positive, % | 34 | 10 | 9 |
| SINBAR positive, % | 83 | 36 | 25 |
| RAI positive, % | 12 | 10 | 7 |
| methods disagree, % of nights | 70 (all MGH) | 28 | 22 |
| kappa Montreal-RAI | 0.34 (all MGH) | 0.77 | 0.73 |

All changes were positive -> negative (Montreal 65 nights, SINBAR 131, RAI 4; none the
other way). Raising MGH's noise floor to HMC's reproduces HMC's verdicts: the relative
criteria are, in effect, multiples of the recording's noise floor, so the quieter MGH
system flags more patients. The RAI, which subtracts a moving-minimum noise estimate, is
nearly immune to added noise but not to gain (F2b) - the complementary weakness.

## F2c Within-cohort: does a night's quiet-REM level predict its verdict? (T11)

% positive by tertile of the night's level (tertile medians):

| cohort, method | low | middle | high |
|---|---|---|---|
| MGH Montreal | 27 (0.43 uV) | 27 (0.59) | 34 (0.92) |
| MGH SINBAR | 74 | 76 | 78 |
| MGH RAI | 2 | 6 | 19 |
| HMC Montreal | 0 (1.14 uV) | 12 (1.52) | 14 (1.96) |
| HMC SINBAR | 18 | 29 | 29 |
| HMC RAI | 0 | 6 | 16 |

MGH logistic regression, OR per halving of the level, adjusted for age, sex and AHI (n=919):
Montreal 0.64 [0.55-0.75], RAI 0.28 [0.21-0.37], SINBAR 1.20 [1.03-1.39]. A low level does
not make a night more likely to be flagged (except weakly for SINBAR); a high level goes
with more Montreal/RAI calls, consistent with raised tone lifting even the quietest seconds
(CAP RBD 0.80 vs 0.47-0.60 uV in the other CAP patients).

## F2d Within MGH: apnoea, artefact and age (T13, T14, T4)

% positive by AHI (n = 132 / 276 / 387 / 130 nights):

| | AHI <5 | 5-15 | 15-30 | >=30 |
|---|---|---|---|---|
| Montreal, all REM | 24 | 27 | 31 | 35 |
| Montreal, event-free REM | 21 | 20 | 24 | 19 |
| SINBAR, all REM | 69 | 76 | 76 | 82 |
| SINBAR, event-free REM | 65 | 69 | 67 | 70 |
| RAI, all REM | 6 | 9 | 8 | 12 |
| RAI, event-free REM | 6 | 9 | 7 | 7 |

The apnoea gradient is carried entirely by epochs with events; without them it vanishes,
and MGH patients without apnoea are still flagged at ~21-24% (Montreal) and ~65-69%
(SINBAR), against HMC's 9% and 25%.

By residual heartbeat artefact (tertile medians of the ratio after removal 1.01 / 1.08 /
1.38): Montreal 40 / 28 / 21%, RAI 17 / 7 / 3%, SINBAR 75 / 70 / 84%. No consistent
artefact effect (the ratio is itself lower when genuine EMG is higher). By age (<40, 40-60,
>60 y): Montreal 28 / 29 / 31%, SINBAR 76 / 78 / 74%, RAI 11 / 8 / 9%.

## F2f Does our automated scoring reproduce published values?

CAP, native band, all REM, mean +/- SD (median), % of mini-epochs or epochs:

| measure | our CAP RBD (n=22) | Frauscher 2012 RBD (n=30) | our CAP healthy (n=15) | our CAP patients (n=51) | Frauscher 2012 controls (n=30) |
|---|---|---|---|---|---|
| SINBAR "any" | 73.2 +/- 21.3 (80.9) | 66.5 +/- 25.2 | 28.2 +/- 20.8 (24.8) | 37.9 +/- 24.6 (32.3) | 8.4 +/- 4.6 |
| SINBAR phasic | 69.0 +/- 20.2 (77.2) | 40.9 +/- 19.0 | 21.9 +/- 11.0 (23.9) | 32.1 +/- 21.6 (27.6) | 7.3 +/- 3.7 |
| SINBAR tonic | 51.4 +/- 23.5 (59.8) | 51.8 +/- 32.8 | 12.8 +/- 21.5 (4.4) | 17.4 +/- 21.7 (9.1) | 1.4 +/- 1.9 |
| Montreal tonic | 51.4 +/- 22.7 (59.1) | - | 13.1 +/- 21.3 (5.2) | 17.9 +/- 21.4 (9.6) | - |
| Montreal phasic | 36.3 +/- 16.0 (36.7) | - | 10.5 +/- 10.8 (7.3) | 13.8 +/- 14.1 (8.8) | - |

The automated measures reproduce the published RBD levels for "any" and tonic activity
(phasic is higher), but patients without RBD score three to five times higher than the
published controls - the false-positive problem sits in the non-RBD distribution, which is
where a low noise floor lets small twitches cross a background-relative threshold. (Our
controls are not Frauscher's: theirs were treated sleep-apnoea patients recorded with the
full SINBAR montage and scored visually.) Montplaisir 2010 reports classification rates
(81.9% tonic, 83.8% phasic; 80 iRBD v 80 controls) rather than group means.

## F3 Background definition: share flagged positive (%) and RBD separation (AUC)

"Background" = the reference the relative thresholds are multiples of. Default p5_rem =
5th percentile of 1 s REM RMS; p5_nrem = 5th percentile of 1 s N2/N3 RMS; min = minimum.
AASM's tonic criterion keeps its NREM definition in all variants.

Positive, %:

| method | background | CAP RBD | CAP healthy | CAP NFLE | CAP PLM | MGH | HMC |
|---|---|---|---|---|---|---|---|
| Montreal | min REM | 91 | 33 | 40 | 50 | 47 | 15 |
| | p5 REM (default) | 91 | 13 | 22 | 40 | 29 | 9 |
| | p10 REM | 91 | 13 | 18 | 30 | 26 | 9 |
| | p25 REM | 55 | 13 | 15 | 20 | 21 | 9 |
| | p50 REM | 27 | 0 | 5 | 10 | 13 | 7 |
| | p5 NREM | 64 | 13 | 15 | 30 | 17 | 8 |
| SINBAR | min REM | 95 | 73 | 90 | 100 | 91 | 39 |
| | p5 REM (default) | 95 | 60 | 75 | 70 | 76 | 25 |
| | p10 REM | 95 | 60 | 72 | 70 | 72 | 21 |
| | p25 REM | 91 | 53 | 65 | 70 | 63 | 18 |
| | p50 REM | 86 | 33 | 45 | 40 | 45 | 12 |
| | p5 NREM | 95 | 33 | 57 | 70 | 55 | 16 |

(HMC 1 uV and HMC 1 uV + 200 Hz track HMC within 3 points in every row.)

AUC, CAP RBD (n=22) vs same-system CAP patients:

| method, metric | min | p5 (default) | p10 | p25 | p50 | p5 NREM |
|---|---|---|---|---|---|---|
| Montreal phasic | 0.869 | 0.846 | 0.800 | 0.728 | 0.556 | 0.751 |
| Montreal tonic | 0.794 | 0.844 | 0.818 | 0.711 | 0.473 | 0.734 |
| SINBAR phasic | 0.799 | 0.884 | 0.874 | 0.851 | 0.750 | 0.843 |
| SINBAR tonic | 0.800 | 0.845 | 0.819 | 0.671 | 0.511 | 0.741 |
| SINBAR any | 0.817 | 0.850 | 0.848 | 0.825 | 0.730 | 0.775 |
| AASM phasic (3 s) | 0.867 | 0.852 | 0.810 | 0.737 | 0.580 | 0.765 |
| AASM phasic epoch | 0.857 | 0.839 | 0.793 | 0.696 | 0.519 | 0.746 |
| AASM tonic (fixed) | 0.685 | 0.685 | 0.685 | 0.685 | 0.685 | 0.685 |

- The definition moves MGH positivity from 13% to 47% (Montreal) and 45% to 91% (SINBAR),
  and CAP healthy from 0% to 33% (Montreal): a larger effect than any clinical covariate.
- The lowest references (minimum, p5, p10 of REM) separate RBD best; higher percentiles
  move the reference into RBD's own excess activity and separation collapses (tonic AUC
  ~0.5 at p50).
- MGH > HMC under every definition, so the site gap is not an artefact of this choice.

## F4 Re-derived cut-offs, validated

Leave-one-out cross-validation on CAP (cut-off re-derived without the held-out night), and
2,000 bootstrap re-derivations (median cut-off [2.5-97.5 percentile], and the false-positive
share in the external cohorts it implies).

| metric | cut-off [95% interval] | CV sens | CV FP | MGH FP | HMC FP |
|---|---|---|---|---|---|
| Montreal phasic % | 27.7 [19.7-29.3] | 86 | 18 | 8 [7-17] | 5 [5-7] |
| Montreal tonic % | 32.2 [32.2-46.6] | 90 | 14 | 13 [6-13] | 7 [5-7] |
| SINBAR any % | 62.9 [62.9-80.4] | 86 | 20 | 10 [3-10] | 1 [1-1] |
| SINBAR phasic % | 60.1 [56.9-73.4] | 86 | 18 | 9 [3-11] | 2 [1-2] |
| SINBAR tonic % | 30.9 [30.9-47.0] | 90 | 14 | 13 [6-13] | 7 [5-7] |
| AASM phasic-epoch % | 31.6 [18.9-34.6] | 81 | 12 | 7 [6-18] | 4 [4-6] |
| AASM phasic % | 23.5 [23.5-34.2] | 86 | 12 | 16 [6-16] | 6 [4-6] |
| AASM tonic % | 42.0 [37.4-90.7] | 81 | 59 | 46 [9-51] | 34 [9-36] |
| RAI (1 - RAI) | 0.08 [0.08-0.16] | 95 | 24 | 25 [12-25] | 14 [9-14] |

Cross-validation costs 0-5 points of sensitivity (19 for AASM tonic) and at most 6 points
of false positives (Montreal phasic); the
re-derived thresholds still flag far fewer external nights than the published ones
(e.g. SINBAR any: MGH 76% -> 10%, HMC 25% -> 1%). With 22 RBD patients the cut-offs
themselves are uncertain (wide bootstrap intervals).

## F5 The noise ladder (pre-specified in preregistration_noise_ladder.md, commit 6d3cc6b)

Same nights re-streamed; white noise added in band (common random numbers). Published
cut-offs; nights >= 10 min REM. CAP RBD and CAP patients = main system (512 Hz, uV).

Share flagged positive (%) at each step; median quiet-REM level (uV) in brackets:

| group | as recorded | +0.5 | +1.0 | +1.5 | +2.0 | +3.0 uV | harmonised 1.5 | harmonised 2.0 |
|---|---|---|---|---|---|---|---|---|
| CAP RBD (n=21) level | 0.86 | 0.99 | 1.31 | 1.71 | 2.13 | 3.02 | 1.50 | 2.00 |
| - Montreal | 90 | 86 | 71 | 57 | 52 | 19 | 57 | 57 |
| - SINBAR | 95 | 95 | 95 | 95 | 81 | 67 | 95 | 86 |
| - RAI | 57 | 57 | 57 | 57 | 52 | 43 | 57 | 52 |
| CAP patients (n=51) level | 0.48 | 0.68 | 1.06 | 1.49 | 1.93 | 2.82 | 1.50 | 2.00 |
| - Montreal | 33 | 18 | 16 | 12 | 12 | 10 | 14 | 12 |
| - SINBAR | 75 | 53 | 37 | 24 | 22 | 20 | 25 | 24 |
| - RAI | 14 | 14 | 12 | 12 | 12 | 12 | 14 | 14 |
| MGH (n=280) level | 0.56 | 0.74 | 1.10 | 1.52 | 1.95 | 2.84 | 1.50 | 2.00 |
| - Montreal | 34 | 23 | 15 | 9 | 8 | 6 | 12 | 9 |
| - SINBAR | 83 | 68 | 44 | 29 | 22 | 13 | 33 | 22 |
| - RAI | 12 | 11 | 10 | 10 | 10 | 8 | 11 | 10 |
| HMC (n=147) level | 1.52 | 1.59 | 1.79 | 2.07 | 2.40 | 3.16 | 1.52 | 2.00 |
| - Montreal | 9 | 9 | 9 | 8 | 7 | 7 | 9 | 8 |
| - SINBAR | 25 | 21 | 17 | 15 | 12 | 7 | 22 | 17 |
| - RAI | 7 | 7 | 7 | 7 | 6 | 6 | 7 | 7 |

### Criteria

| # | criterion | result | verdict |
|---|---|---|---|
| 1 | harmonised to 2.0 uV, MGH - HMC <= 3 (Montreal) / <= 5 (SINBAR) points | Montreal 9 [6-13] vs 8 [5-14]: +0.8; SINBAR 22 [18-28] vs 17 [12-24]: +5.5 (as recorded: +25.1 and +57.9) | met for Montreal; narrowly missed for SINBAR (90% of the gap removed) |
| 2 | MGH's ladder at HMC's own level (1.52 uV) within 3 / 5 points of HMC | Montreal 8.9 vs 8.8 (+0.1); SINBAR 29.2 vs 25.2 (+4.1); RAI 10.4 vs 7.5 | met |
| 3 | RBD sensitivity < 70% at 2.0 uV = noisier systems miss RBD | Montreal 57%; SINBAR 86%; RAI 52% | supported (Montreal) |
| 4 | remedy: harmonise to 2.0 uV, re-derive on CAP; gap <= 5 and LOO sens >= 80% | Montreal phasic cut 5.4%: LOO 76%, MGH 21 [8-47] vs HMC 10 [5-16]; Montreal tonic cut 1.5%: LOO 71%, 40 vs 19; SINBAR any cut 13.7%: LOO 90%, 30 vs 20 | not met: harmonisation plus re-derivation is not a working remedy |
| 5 | HMC/MGH EEG 40-90 Hz floor >= 1.5 = system-wide | EEG N2/N3 floor: CAP 0.16 [0.15-0.20], MGH 0.23 [0.22-0.25], HMC 0.46 [0.41-0.82]; ratio 1.98 | met: HMC's system is noisier on EEG too |
| 6 | dropping transitional REM epochs changes the Montreal gap by < 3 points | Montreal gap +20 -> +16; SINBAR +51 -> +52; RAI +1 -> +1 | narrowly not met: REM-boundary epochs carry ~4 of the 20 Montreal points, none of SINBAR's |

Notes:
- Without harmonisation, the cut-offs re-derived on CAP (as in T10) give, on these 300 MGH
  nights: Montreal phasic 27.7% -> MGH 9%, HMC 5% (gap +5); Montreal tonic 32.2% -> 16% vs
  7%; SINBAR any 62.9% -> 16% vs 1%.
- Why the remedy fails: harmonising to 2 uV makes MGH and HMC agree under the published
  cut-offs (Montreal 9 vs 8%) but costs RBD sensitivity (Montreal 90 -> 57%). Re-deriving
  cut-offs on the harmonised CAP data to win sensitivity back pushes them very low (1.5-14%),
  into the part of the distributions where the two sites still differ.
- MGH's EEG floor (0.23 uV) is near its 1-uV quantisation noise in that band (~0.2 uV), so
  its amplifier noise may be lower still; the HMC/MGH ratio is then a lower bound.
- The CAP healthy group (mixed hardware; 12 with physical units) is not used for criteria.

## F6 Paired tests for the simulations (T12)

| simulation vs source | n | Montreal | SINBAR | RAI |
|---|---|---|---|---|
| HMC 1 uV vs HMC | 147 | 9 -> 9 (0 changed) | 25 -> 24 (1 -) | 7 -> 7 |
| HMC 1 uV + 200 Hz vs HMC | 147 | 9 -> 9 | 25 -> 22: -2.7 [-5.4 to -0.1], 4 -, p=0.1 | 7 -> 7 |
| HMC x0.39 vs HMC | 147 | 9 -> 8 (1 -) | 25 -> 25 | 7 -> 3: -4.1 [-7.3 to -0.9], 6 -, p=0.03 |
| HMC x0.39 MGH-format vs HMC x0.39 | 147 | 8 -> 8 | 25 -> 20: -5.4 [-9.1 to -1.8], 8 -, p=0.008 | 3 -> 3 |
| MGH + 1.5 uV noise vs MGH | 277 | 34 -> 10: -23.5 [-28.5 to -18.5], 65 -, 0 +, p=5e-20 | 83 -> 36: -47.3 [-53.2 to -41.4], 131 -, 0 +, p=7e-40 | 12 -> 10: -1.4 [-2.8 to 0.0], 4 -, p=0.1 |
