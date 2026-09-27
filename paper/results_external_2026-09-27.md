# External cohorts: results (2026-09-27)

Pre-specified in `preregistration_external.md` (commit 48053f3, before any external EMG was
read). Output of `run_external.py` (`results/external_report.md`, `external_scores.csv`,
fig9). BOAS rows are each participant's first night unless stated. Published % cut-offs;
floor-corrected (FC) rules with B = 1.0 uV.

## X1 Cohorts

| group | nights | REM, min | age | system | floor (quiet-REM level), uV | floor signature | heartbeat removed |
|---|---|---|---|---|---|---|---|
| CAP RBD | 21 | 72 | 71 | 512 Hz | 0.86 [0.61-1.24] | 1.35 | 21/21 |
| CAP patients | 51 | 89 | 30 / 59 (<50 / >=50) | 512 Hz | 0.48 [0.44-0.69] | 1.16 | 43/51 |
| MGH | 925 | 60 | 55 | 200 Hz | 0.59 [0.47-0.77] | 1.20 | 914/925 |
| HMC | 147 | 69 | - | 256 Hz | 1.52 [1.23-1.79] | 1.08 | 142/147 |
| BOAS (healthy) | 99 | 79 | 38 (18-82) | Micromed, 256 Hz | 0.37 [0.28-0.49] | 1.20 | 6/99 (no ECG) |
| DOD-O (patients) | 53 | 73 | - | Somno HD, 250 Hz | 0.82 [0.76-0.92] | 1.16 | 52/53 |
| DOD-H (healthy) | 25 | 98 | 18-65 | Siesta, 250 Hz | 0.56 [0.54-0.65] | 1.10 | 25/25 |

BOAS is the quietest system in the study; DOD-O had 53 of its 55 nights with >= 10 min REM.

## X3 Share flagged, % [95% CI]

| group | Montreal published | Montreal FC | SINBAR published | SINBAR FC | RAI | SINBAR-FC >= 49.1% |
|---|---|---|---|---|---|---|
| CAP RBD | 90.5 [71-97] | 81.0 [60-92] | 95.2 [77-99] | 95.2 [77-99] | 57.1 [37-76] | 85.7 [65-95] |
| CAP patients | 33.3 [22-47] | 21.6 [12-35] | 74.5 [61-84] | 45.1 [32-59] | 13.7 [7-26] | 19.6 [11-32] |
| MGH | 29.4 [27-32] | 18.0 [16-21] | 76.2 [73-79] | 45.3 [42-48] | 8.9 [7-11] | 13.2 [11-16] |
| HMC | 8.8 [5-15] | 16.3 [11-23] | 25.2 [19-33] | 42.9 [35-51] | 7.5 [4-13] | 14.3 [10-21] |
| BOAS (healthy) | 41.4 [32-51] | 15.2 [9-24] | 90.9 [84-95] | 35.4 [27-45] | 13.1 [8-21] | 11.1 [6-19] |
| DOD-O (patients) | 30.2 [20-44] | 24.5 [15-38] | 58.5 [45-71] | 50.9 [38-64] | 7.5 [3-18] | 17.0 [9-29] |
| DOD-H (healthy) | 20.0 [9-39] | 12.0 [4-30] | 84.0 [65-94] | 32.0 [17-52] | 4.0 [1-20] | 12.0 [4-30] |

BOAS, all 127 nights: Montreal 41 / FC 12; SINBAR 91 / FC 35. First nights by age: < 50 y
(n = 74) Montreal 36 / 15, SINBAR 89 / 31; >= 50 y (n = 24) Montreal 58 / 17, SINBAR 96 / 50.

## X2 Scale (1-s RMS with the noise removed, uV, median)

| group | N2/N3 | REM | REM 95th pct |
|---|---|---|---|
| CAP patients | 1.61 | 0.39 | 2.25 |
| MGH | 1.60 | 0.44 | 2.91 |
| HMC | 1.70 | 0.45 | 2.05 |
| BOAS | 1.04 [0.69-2.00] | 0.33 | 2.20 |
| DOD-O | 1.68 [0.91-4.04] | 0.45 | 3.21 |
| DOD-H | 1.05 [0.78-1.97] | 0.27 | 3.09 |

## X7 Heartbeat check (exploratory, added after the first look at BOAS)

Periodicity of the REM envelope at a heart rate (spectral peak 0.7-2 Hz over the 0.5-3 Hz
median): MGH 2.67 after removal (p90 4.66), 3.17 with the heartbeat left in; HMC 2.33 / 2.50;
DOD-O 2.25 / 2.74; DOD-H 2.67 / 2.61; BOAS 3.07 (p90 5.61; removal possible on 6 nights).

Leaving the heartbeat in, in the cohorts with ECG (% flagged, removed -> left in): MGH
Montreal 29 -> 22, Montreal FC 18 -> 25, SINBAR 76 -> 78, SINBAR FC 45 -> 60; HMC 9 -> 9,
16 -> 18, 25 -> 25, 43 -> 52; DOD-O 30 -> 23, 25 -> 28, 58 -> 58, 51 -> 62; DOD-H 20 -> 12, 12 -> 12, 84 -> 80, 32 -> 40. The heartbeat barely moves the published rules (it raises the
background they are multiples of) but inflates the floor-corrected SINBAR rule by 9-15
points.

BOAS nights no more periodic than MGH's after removal (80 of 99): Montreal 44 / FC 14,
SINBAR 92 / FC 35 - the same as all BOAS nights. Residual heartbeat does not explain BOAS's
positivity.

## Predictions

| # | prediction | result | verdict |
|---|---|---|---|
| E1 | net N2/N3 within 0.67-1.5 x MGH (1.60 uV) | BOAS 1.04 (0.65x); DOD-H 1.05 (0.66x); DOD-O 1.68 (1.05x) | not met for the two healthy cohorts (just outside); met for DOD-O |
| E2 | healthy cohorts with floor < 1 uV: published SINBAR flags >= 30% | BOAS (0.37 uV) 90.9%; DOD-H (0.56 uV) 84.0% | met (both) |
| E3 | floors 0.37 vs 0.56 uV (x1.51): published difference higher in the quieter cohort and at least halved under FC | SINBAR BOAS - DOD-H +6.9 -> +3.4 points; Montreal +21.4 -> +3.2 | met (both) |
| E4 | across 6 groups without RBD, rho(floor, published SINBAR) < 0 and weaker under FC | SINBAR rho -0.83 -> +0.43; Montreal -0.77 -> +0.31 | met |
| E5 | SINBAR-FC >= 49.1% flags <= 10% healthy, <= 20% DOD-O | BOAS 11.1%; DOD-H 12.0%; DOD-O 17.0% | narrowly not met for the healthy cohorts; met for DOD-O |
| E6 | DOD-O within 10 points of MGH's ladder at its floor (0.82 uV) | Montreal predicted 20.9%, observed 30.2% (+9.3); SINBAR 61.5% vs 58.5% (-3.0) | met |

Eight of the twelve pre-specified checks were met. The four misses were narrow and share an
explanation: the two healthy cohorts, recorded on different systems, had the same lower
net N2/N3 tone (1.04 and 1.05 uV against 1.6-1.7 uV in the three patient cohorts), which
points to their population rather than to gain, and the re-derived SINBAR-FC cut-off
flagged 11-12% of their nights against the <= 10% set in advance.
