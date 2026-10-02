# Parkinson's analyses: results (2026-10-02)

Pre-specified in `preregistration_parkinsons.md` (commit 1e7acf0, committed before any
RBDtector run). Output of `run_rbdtector.py` (`rbdtector_scores*.csv`, one row per night,
ladder step and rule) and `run_parkinsons.py` (`results/parkinsons_report.md`,
`parkinsons_recruitment.csv`, fig10). Our own methods are read unchanged from
`floor_ladder_scores.csv` and `external_scores.csv`. FC = floor-corrected, B = 1.0 uV.
RBDtector positive = chin "any" >= 23.5% (Röthenbacher 2022, Table 5).

## How the runs went

All 1,412 pre-specified RBDtector runs were completed: 72 CAP nights (21 RBD, 51
same-system patients) at all five ladder steps, 100 MGH, 147 HMC and 99 BOAS nights as
recorded, each with the published and the floor-corrected baseline. No night failed and
every night passed the 10-minute REM minimum, so no ladder step was dropped. Before the
full runs, one CAP patient's night was scored to time the program and check its output.
Deviations from the plan, none of which changes a score:

- **Speed.** The two speed-ups and the trimming to each night's REM stretch (Methods 2.9)
  were committed (b59ff82, cc80caf) before the full runs and checked on the test night:
  same tonic, phasic, "any" and baseline as the unchanged program on the whole night.
- **Two runtimes.** The work was split between two Colab runtimes (CAP on one; MGH and HMC
  on the other; BOAS moved to the first so that both finished within Colab's 12-hour
  limit). The second runtime had no Google Drive access, because its authorization prompt
  could not be answered, so its record lists were passed to it from the first runtime and
  its scores file came back through the browser. The returned file had the same MD5
  checksum, and its MGH and HMC nights were exactly those the pre-specified selection
  gives (`records_for`, seed 0) on the first runtime.
- **One restart.** The CAP run stopped after 61 of 72 nights when the BOAS run, started
  alongside it, exhausted the runtime's memory and the operating system ended a worker.
  It was resumed for the remaining 11 nights. Scores are written only when a night is
  complete, so no night was partly scored.

## P1 The same RBD nights as recorded and at HMC's floor (PD1)

Mean per-night change from the night as recorded to the copy whose quiet-REM level was
raised to 1.5 uV (`h150`), percentage points [95% bootstrap CI]; median [IQR]. Benchmarks:
baseline tonic RWA 31.9 points higher in RBD patients who later developed Parkinson's
disease than in those who stayed disease-free (Postuma 2010); a rise of 24 points over a
mean 5 years, 4.8 per year (Iranzo 2009).

**CAP RBD (n = 21)**

| measure | as recorded | at 1.5 uV | change | median [IQR] | share of 31.9 | years of 4.8/yr |
|---|---|---|---|---|---|---|
| Montreal tonic, published | 53.3 | 31.8 | -21.4 [-29.7 to -13.2] | -17.5 [-29.2 to 0.0] | 67% | 4.5 |
| Montreal phasic, published | 37.1 | 22.8 | -14.3 [-18.4 to -9.7] | -15.3 [-24.5 to -1.5] | | |
| SINBAR any, published | 74.8 | 54.1 | -20.7 [-28.9 to -12.4] | -13.3 [-39.0 to -4.0] | | |
| RBDtector tonic, published | 40.3 | 28.3 | -12.1 [-17.0 to -7.3] | -9.9 [-16.5 to 0.0] | 38% | 2.5 |
| RBDtector phasic, published | 31.4 | 27.3 | -4.1 [-8.1 to -0.6] | 0.0 [-4.1 to +0.8] | | |
| RBDtector any, published | 69.0 | 54.9 | -14.1 [-19.4 to -8.7] | -9.4 [-23.0 to -3.0] | | |
| Montreal tonic, FC | 44.7 | 43.6 | -1.1 [-1.7 to -0.5] | -0.6 [-1.7 to 0.0] | 3% | 0.2 |
| Montreal phasic, FC | 39.4 | 39.0 | -0.4 [-0.6 to -0.2] | -0.3 [-0.5 to 0.0] | | |
| SINBAR any, FC | 68.7 | 67.5 | -1.1 [-1.9 to -0.5] | -0.9 [-1.3 to 0.0] | | |
| RBDtector tonic, FC | 47.4 | 47.5 | +0.1 [-0.9 to +1.3] | 0.0 [-0.9 to 0.0] | 0% | 0.0 |
| RBDtector phasic, FC | 33.7 | 33.2 | -0.4 [-1.2 to +0.3] | 0.0 [-1.5 to +0.7] | | |
| RBDtector any, FC | 77.0 | 76.9 | -0.1 [-1.0 to +0.6] | 0.0 [-0.9 to +0.6] | | |

**CAP patients on the same system (n = 51)**

| measure | as recorded | at 1.5 uV | change | median [IQR] |
|---|---|---|---|---|
| Montreal tonic, published | 17.9 | 9.8 | -8.1 [-10.4 to -6.0] | -5.7 [-12.8 to -2.1] |
| Montreal phasic, published | 13.8 | 7.8 | -6.0 [-7.7 to -4.5] | -4.6 [-6.8 to -2.1] |
| SINBAR any, published | 37.9 | 20.2 | -17.7 [-21.7 to -14.1] | -16.2 [-24.2 to -10.2] |
| RBDtector tonic, published | 13.2 | 6.9 | -6.3 [-8.2 to -4.5] | -4.6 [-8.8 to -0.9] |
| RBDtector phasic, published | 23.8 | 12.9 | -10.9 [-14.0 to -8.4] | -9.4 [-14.2 to -4.3] |
| RBDtector any, published | 36.9 | 20.1 | -16.8 [-20.4 to -13.5] | -18.8 [-24.4 to -6.3] |
| Montreal tonic, FC | 14.0 | 13.8 | -0.2 [-0.4 to 0.0] | 0.0 [-0.1 to 0.0] |
| Montreal phasic, FC | 12.1 | 12.3 | +0.2 [-0.1 to +0.6] | 0.0 [-0.1 to 0.0] |
| SINBAR any, FC | 27.3 | 27.4 | +0.0 [-0.2 to +0.3] | 0.0 [-0.2 to +0.4] |
| RBDtector tonic, FC | 12.1 | 12.7 | +0.6 [+0.2 to +0.9] | 0.0 [0.0 to +1.3] |
| RBDtector phasic, FC | 19.2 | 21.5 | +2.3 [+1.2 to +3.3] | +2.4 [0.0 to +3.9] |
| RBDtector any, FC | 31.1 | 34.0 | +2.9 [+1.7 to +4.1] | +3.1 [0.0 to +4.9] |

**Dose-response, CAP RBD, mean tonic %** (quiet-REM level 0.86 uV as recorded; 0.99, 1.31
and 2.13 uV at +0.5, +1.0 and +2.0 uV; 1.50 at `h150`)

| rule | as recorded | +0.5 | +1.0 | +1.5 | +2.0 | +3.0 | level 1.5 uV |
|---|---|---|---|---|---|---|---|
| Montreal, published | 53.3 | 45.9 | 33.9 | 25.6 | 19.8 | 11.3 | 31.8 |
| RBDtector, published | 40.3 | 37.5 | 31.0 | - | 20.1 | - | 28.3 |
| Montreal, FC | 44.7 | 44.4 | 43.3 | 41.5 | 35.2 | 25.0 | 43.6 |
| RBDtector, FC | 47.4 | 48.0 | 48.5 | - | 38.7 | - | 47.5 |

Beyond a floor of about 1.7 uV (+2.0 uV and above) the floor-corrected rules leave their
valid range and fall, as pre-registered for the floor-corrected criteria.

## P2 RBDtector (PD2)

**a) Noise ladder, % of nights flagged**

| group | | as recorded | +0.5 | +1.0 | +2.0 | level 1.5 uV | as recorded -> 1.5 uV |
|---|---|---|---|---|---|---|---|
| CAP RBD (n = 21) | quiet-REM level, uV | 0.86 | 0.99 | 1.31 | 2.13 | 1.50 | |
| | published | 95.2 | 95.2 | 95.2 | 85.7 | 95.2 | 0 nights changed |
| | FC | 95.2 | 95.2 | 95.2 | 95.2 | 95.2 | 0 nights changed |
| CAP patients (n = 51) | quiet-REM level, uV | 0.48 | 0.68 | 1.06 | 1.93 | 1.50 | |
| | published | 78.4 | 47.1 | 31.4 | 19.6 | 25.5 | -52.9 [-66.6 to -39.2]; 27 to negative, 0 to positive; McNemar p = 1e-8 |
| | FC | 37.3 | 39.2 | 45.1 | 37.3 | 49.0 | +11.8 [+2.9 to +20.6]; 0 to negative, 6 to positive; p = 0.03 |

**b) As recorded, by system, % flagged [95% CI]**

| group | nights | floor, uV | published | FC |
|---|---|---|---|---|
| CAP RBD | 21 | 0.86 | 95.2 [77-99] | 95.2 [77-99] |
| CAP patients | 51 | 0.48 | 78.4 [65-88] | 37.3 [25-51] |
| MGH (random 100) | 100 | 0.53 | 65.0 [55-74] | 55.0 [45-64] |
| HMC | 147 | 1.52 | 20.4 [15-28] | 55.8 [48-64] |
| BOAS (healthy) | 99 | 0.37 | 88.9 [81-94] | 34.3 [26-44] |

MGH - HMC: published +44.6 points, floor-corrected -0.8.

**c) Nights without RBD pooled (n = 397):** Spearman rho of the night's floor with its
RBDtector "any" %: published -0.52 [-0.59 to -0.43], floor-corrected +0.31 [+0.21 to +0.40].

**d) Agreement with our SINBAR "any" (published), same 418 nights as recorded:** Spearman
rho +0.79. RBDtector's baseline was 1.14 times our quiet-REM floor (median): on these
nights it is essentially the recording's noise floor.

## P3 Isolated RWA by system (PD3, descriptive)

% of nights without RBD labeled by each definition (RBDtector where scored: MGH's random
100, all HMC and BOAS nights, all CAP patients).

| group | nights | floor, uV | RAI < 0.85 (DREAMER) | RAI < 0.8 | SINBAR pub / FC | Montreal pub / FC | RBDtector pub / FC |
|---|---|---|---|---|---|---|---|
| CAP patients | 51 | 0.48 | 16 | 14 | 75 / 45 | 33 / 22 | 78 / 37 |
| CAP patients >= 50 y | 16 | 0.53 | 25 | 19 | 75 / 62 | 44 / 25 | 75 / 62 |
| MGH | 925 | 0.59 | 12 | 9 | 76 / 45 | 29 / 18 | 65 / 55 |
| MGH >= 50 y | 610 | 0.59 | 12 | 8 | 75 / 43 | 30 / 17 | 69 / 53 |
| HMC | 147 | 1.52 | 9 | 7 | 25 / 43 | 9 / 16 | 20 / 56 |
| DOD-O | 53 | 0.82 | 13 | 8 | 58 / 51 | 30 / 25 | - |
| BOAS (healthy) | 99 | 0.37 | 15 | 13 | 91 / 35 | 41 / 15 | 89 / 34 |
| BOAS >= 50 y | 24 | 0.38 | 17 | 17 | 96 / 50 | 58 / 17 | 96 / 54 |
| DOD-H (healthy) | 25 | 0.56 | 8 | 4 | 84 / 32 | 20 / 12 | - |

RAI < 0.85 on the noise ladder (same nights, as recorded -> level 1.5 uV; most noise +3.0
uV): CAP patients 16 -> 16 (14); MGH 15 -> 13 (11); HMC 9 -> 9 (8); CAP RBD 76 -> 67 (62).

## P4 Recruitment for prevention trials (PD4, descriptive)

Per 1,000 sleep studies in people aged 50 or over, RBD prevalence 2%. False-positive rate
from MGH patients >= 50 y (an upper bound: a few may have RBD; RBDtector: the 68 of the
random 100), sensitivity from CAP RBD (n = 21). People expected to develop a
synucleinopathy within 12 years: 73.5% of those found (Postuma 2019). 1% and 5% in
`parkinsons_recruitment.csv`.

| rule | false positives | sensitivity | flagged | RBD found | PPV | studies per RBD found | expected to convert |
|---|---|---|---|---|---|---|---|
| Montreal, published | 29.5% | 90% | 308 | 18.1 | 5.9% | 17 | 13.3 |
| Montreal, FC | 17.3% | 81% | 186 | 16.2 | 8.7% | 11 | 11.9 |
| SINBAR, published | 74.8% | 95% | 752 | 19.0 | 2.5% | 39 | 14.0 |
| SINBAR, FC | 42.9% | 95% | 440 | 19.0 | 4.3% | 23 | 14.0 |
| SINBAR-FC >= 49.1% (re-derived) | 11.4% | 86% | 129 | 17.1 | 13.3% | 8 | 12.6 |
| RAI < 0.8 | 8.4% | 57% | 93 | 11.4 | 12.2% | 8 | 8.4 |
| RBDtector, published | 69.1% | 95% | 696 | 19.0 | 2.7% | 37 | 14.0 |
| RBDtector, FC | 52.9% | 95% | 538 | 19.0 | 3.5% | 28 | 14.0 |

PPV across 1-5% prevalence: 1.3-6.3% (SINBAR, published) to 7.1-28.4% (SINBAR-FC >= 49.1%).
With HMC's false-positive rate instead (all ages, 2%), the published Montreal rule would
flag 105 and find 18.1 (PPV 17.3%) - but that uses CAP's sensitivity, which HMC's floor
lowers (57% on the ladder; then about 11 found, PPV about 12%).

## P5 Floor check by system (PD5, descriptive)

Floor b = 5th percentile of 1-s REM RMS. "Inside": sampling rate >= 200 Hz and b <= 1.69 uV,
the floor-corrected rule's range. "Muscle needed": the muscle activity (RMS, on top of the
noise) that a threshold of 2 x b requires; the floor-corrected rule requires 1.73 uV on
every system.

| group | nights | fs, Hz | floor, uV [IQR] | inside | net N2/N3, uV | muscle needed at 2 x b, uV |
|---|---|---|---|---|---|---|
| CAP RBD | 21 | 512 | 0.86 [0.61-1.24] | 76% | 2.91 | 1.44 |
| CAP patients | 51 | 512 | 0.48 [0.44-0.69] | 86% | 1.61 | 0.81 |
| MGH | 925 | 200 | 0.59 [0.47-0.77] | 95% | 1.60 | 0.99 |
| HMC | 147 | 256 | 1.52 [1.23-1.79] | 63% | 1.70 | 2.54 |
| DOD-O | 53 | 250 | 0.82 [0.76-0.92] | 92% | 1.68 | 1.37 |
| BOAS | 99 | 256 | 0.37 [0.28-0.49] | 92% | 1.04 | 0.61 |
| DOD-H | 25 | 250 | 0.56 [0.54-0.65] | 100% | 1.05 | 0.94 |

Under the published rule, what counts as RWA differs four-fold between systems (0.61 uV of
muscle activity on BOAS's, 2.54 uV on HMC's).

## Predictions

| # | prediction | result | verdict |
|---|---|---|---|
| PD1a | Montreal tonic, published: mean change <= -10 points | -21.4 [-29.7 to -13.2] | met |
| PD1b | Montreal tonic, FC: \|change\| <= 3 | -1.1 [-1.7 to -0.5] | met |
| PD1c | RBDtector tonic, published: <= -10 | -12.1 [-17.0 to -7.3] | met |
| PD1d | RBDtector tonic, FC: \|change\| <= 3 | +0.1 [-0.9 to +1.3] | met |
| PD2a | CAP patients, published: share flagged falls >= 10 points | 78.4% -> 25.5% (-52.9) | met |
| PD2b | CAP patients, FC: share flagged changes <= 5 points | 37.3% -> 49.0% (+11.8 [+2.9 to +20.6]) | **not met** |
| PD2c | CAP RBD, FC: sensitivity changes <= 10 points | 95.2% -> 95.2% | met |
| PD2d | MGH - HMC published >= 20 points, FC at most half | +44.6 -> -0.8 | met |
| PD2e | BOAS published >= 50%, FC at most half | 88.9% -> 34.3% | met |
| PD2f | rho(floor, "any") < 0 published (CI), weaker with FC | -0.52 [-0.59 to -0.43] -> +0.31 [+0.21 to +0.40] | met |

Nine of the ten pre-specified predictions were met. On the reading fixed in advance:
PD1a and PD1c met - the recording system alone moved RWA by an amount on the scale of the
disease signals Parkinson's research uses (Montreal tonic: two-thirds of the difference
that predicted Parkinson's disease, 4.5 years of progression; RBDtector: 38%, 2.5 years);
PD2a, d, e and f (published halves) met - RBDtector, run unchanged, inherits the
dependence; PD1d, PD2c and the floor-corrected halves of d and e met - the floor-corrected
baseline removes it from RBDtector's continuous measures and from its verdicts across
hospitals and in RBD. PD2b was not met: under the floor-corrected baseline RBDtector
flagged 6 more of the 51 same-system patients, and none fewer, at HMC's floor; the
continuous drift behind it was small (+2.9 points of "any", +0.6 of tonic) but
systematic. Under PD2f, floor correction did more than weaken the relation: it reversed
it, which these data cannot separate from population (the quietest system recorded
healthy volunteers, the noisiest patients) and from the drift behind PD2b.

## X1 RBDtector on noise alone (exploratory, added after PD2b was missed)

`run_rbdtector_noise.py`: 12 simulated nights of band-limited white noise and nothing else
(10-100 Hz with a 50-Hz notch, 256 Hz; 80 minutes of REM in four 20-minute periods), three
per noise level, scored by RBDtector with its published baseline and with the
floor-corrected baseline at the pre-specified guard (1.5) and at 2.0. Percentage of REM
mini-epochs counted as "any" activity, mean of the three nights (highest in brackets);
tonic was 0 everywhere.

| noise RMS, uV | 0.5 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|
| RBDtector baseline, uV | 0.46 | 0.95 | 1.43 | 1.92 |
| published | 0 | 0 | 0 | 0 |
| floor-corrected, guard 1.5 (pre-specified) | 0 | 0 | 0.40 (0.62) | 1.06 (1.62) |
| floor-corrected, guard 2.0 | 0 | 0 | 0 | 0 |

Noise alone accounts for about 0.4 of the 2.9-point rise in "any" among CAP's patients at
1.5 uV. The rest presumably comes from small muscle activity just below the corrected
threshold, which added noise lifts over it more often than it pushes larger activity
below it: below-threshold activity is far more common in REM without RBD, and over a
30-ms window of about eight samples the RMS of noise varies widely. This was not tested
further. In the RBD nights, whose activity lies mostly far above the threshold, the
floor-corrected percentages did not move. A guard of 2.0 removed the little activity that
noise produced alone, but its effect on real nights was not tested, and at floors near
1.5 uV it would raise the threshold above what the floor-corrected rule is meant to ask.
