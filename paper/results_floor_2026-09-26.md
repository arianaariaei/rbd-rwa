# Floor-corrected criteria: results (2026-09-26)

Pre-specified in `preregistration_floor_corrected.md` (commit 20b9ec2, before any result for
MGH, HMC or the CAP patient groups existed). Output of `run_floor.py`
(`results/floor_report.md`, `floor_scores.csv`, `floor_ladder_scores.csv`, fig8).
CAP RBD and CAP patients = main system (512 Hz, microvolts): 21 RBD, 51 other patients.
Nights with >= 10 min REM; published % cut-offs; B = 1.0 uV unless stated.

The rule: "activity above k x background" becomes activity above
T = max( sqrt(n^2 + (k^2 - 1) B^2), 1.5 b ), with b the night's background (5th percentile
of 1-s REM RMS), n = b / 0.91 the noise RMS it implies, and B a reference background.

## FC1 As recorded, all nights: share flagged, % [95% CI]

| rule | CAP RBD (21) | CAP patients (51) | CAP healthy (15, mixed hardware) | MGH (925) | HMC (147) | MGH - HMC |
|---|---|---|---|---|---|---|
| Montreal, published | 90 [71-97] | 33 [22-47] | 13 [4-38] | 29 [27-32] | 9 [5-15] | +20.5 |
| Montreal, floor-corrected | 81 [60-92] | 22 [12-35] | 42 [19-68]* | 18 [16-21] | 16 [11-23] | **+1.6** |
| Montreal, clamp | 76 [55-89] | 18 [10-30] | 17 [5-45] | 16 [14-19] | 9 [5-15] | +7.5 |
| SINBAR, published | 95 [77-99] | 75 [61-84] | 60 [36-80] | 76 [73-79] | 25 [19-33] | +51.0 |
| SINBAR, floor-corrected | 95 [77-99] | 45 [32-59] | 42 [19-68]* | 45 [42-48] | 43 [35-51] | **+2.4** |
| SINBAR, clamp | 95 [77-99] | 35 [24-49] | 42 [19-68] | 40 [37-44] | 25 [19-33] | +15.2 |
| RAI, published | 57 [37-76] | 14 [7-26] | 25 [9-53] | 9 [7-11] | 7 [4-13] | +1.4 |

\* 12 nights: three of CAP's healthy recordings are stored without physical units and are
not scored by FC (a first run had scored them as if in microvolts; fixed and re-run - all
other numbers were unchanged). CAP's healthy group was recorded on several systems; see FC10.

## FC2 The same nights as the noise floor rises (noise ladder), % flagged

| group, rule | as recorded | +0.5 | +1.0 | +1.5 | +2.0 | +3.0 uV | harmonised 1.5 | harmonised 2.0 |
|---|---|---|---|---|---|---|---|---|
| CAP RBD level, uV | 0.86 | 0.99 | 1.31 | 1.71 | 2.13 | 3.02 | 1.50 | 2.00 |
| Montreal published | 90.5 | 85.7 | 71.4 | 57.1 | 52.4 | 19.0 | 57.1 | 57.1 |
| Montreal FC | 81.0 | 81.0 | 81.0 | 81.0 | 81.0 | 81.0 | 81.0 | 81.0 |
| SINBAR published | 95.2 | 95.2 | 95.2 | 95.2 | 81.0 | 66.7 | 95.2 | 85.7 |
| SINBAR FC | 95.2 | 95.2 | 95.2 | 95.2 | 95.2 | 90.5 | 95.2 | 95.2 |
| CAP patients level, uV | 0.48 | 0.68 | 1.06 | 1.49 | 1.93 | 2.82 | 1.50 | 2.00 |
| Montreal published | 33.3 | 17.6 | 15.7 | 11.8 | 11.8 | 9.8 | 13.7 | 11.8 |
| Montreal FC | 21.6 | 21.6 | 21.6 | 21.6 | 21.6 | 21.6 | 21.6 | 21.6 |
| SINBAR published | 74.5 | 52.9 | 37.3 | 23.5 | 21.6 | 19.6 | 25.5 | 23.5 |
| SINBAR FC | 45.1 | 43.1 | 43.1 | 43.1 | 39.2 | 25.5 | 45.1 | 37.3 |
| MGH (280) level, uV | 0.56 | 0.74 | 1.10 | 1.52 | 1.95 | 2.84 | 1.50 | 2.00 |
| Montreal published | 33.9 | 23.2 | 14.6 | 8.9 | 7.9 | 6.1 | 11.8 | 8.9 |
| Montreal FC | 21.3 | 21.4 | 21.4 | 21.4 | 21.4 | 20.4 | 21.4 | 21.4 |
| SINBAR published | 83.0 | 68.2 | 43.9 | 29.3 | 22.1 | 13.2 | 33.2 | 22.5 |
| SINBAR FC | 48.7 | 48.9 | 49.6 | 49.6 | 44.3 | 28.6 | 50.4 | 43.9 |
| HMC (147) level, uV | 1.52 | 1.59 | 1.79 | 2.07 | 2.40 | 3.16 | 1.52 | 2.00 |
| Montreal published | 8.8 | 8.8 | 8.8 | 8.2 | 7.5 | 6.8 | 8.8 | 8.2 |
| Montreal FC | 16.3 | 16.3 | 16.3 | 15.6 | 15.6 | 15.6 | 16.3 | 15.6 |
| SINBAR published | 25.2 | 21.1 | 17.0 | 15.0 | 12.2 | 7.5 | 21.8 | 17.0 |
| SINBAR FC | 42.9 | 41.5 | 40.1 | 35.4 | 26.5 | 18.4 | 42.9 | 34.7 |

Paired, as recorded -> harmonised 1.5 uV (same nights; exact McNemar):
- MGH Montreal: published 33.9 -> 11.9 (-22.0 [-26.9 to -17.1], 61 nights -, 0 +, p = 9e-19);
  **FC 21.3 -> 21.3 (0 nights changed)**; clamp 19.1 -> 11.9 (-7.2, 20 -).
- MGH SINBAR: published 83.0 -> 33.2 (-49.8 [-55.7 to -43.9], 138 -, p = 6e-42);
  **FC 48.7 -> 50.5 (+1.8 [+0.2 to +3.4], 5 +, 0 -, p = 0.06)**; clamp 45.1 -> 33.2 (-11.9).
- CAP RBD Montreal: published 90.5 -> 57.1 (-33.3, 7 -, p = 0.02); **FC 81.0 -> 81.0**.
- CAP RBD SINBAR: 95.2 -> 95.2 under every rule. CAP patients: Montreal FC and SINBAR FC
  unchanged (published -19.6 and -49.0). HMC: FC unchanged.
- Above ~2 uV the guard (1.5 b) binds and FC positivity falls (SINBAR FC in MGH 44% at
  +2 uV, 29% at +3 uV): below that floor small activity cannot be told from noise.

## Criteria (B = 1.0 uV)

| # | criterion | Montreal-FC | SINBAR-FC |
|---|---|---|---|
| 1 | MGH within 5 points at h150 | 21.3 -> 21.3: met | 48.7 -> 50.5: met |
| 2 | CAP RBD within 10 points at h150 | 81 -> 81: met | 95 -> 95: met |
| 3 | MGH - HMC <= 5 (Montreal) / <= 10 (SINBAR) as recorded | +1.6: met | +2.4: met |
| 4 | CAP RBD sensitivity >= 85% | 81% (17/21): **not met** | 95%: met |
| 5 | CAP patients not above published | 22% vs 33%: met | 45% vs 75%: met |

By the pre-specified reading: SINBAR-FC is a working remedy (1-5 met). Montreal-FC is
noise-invariant and removes the site gap, but at B = 1.0 uV its sensitivity (81%) is below
the pre-specified 85% (published on the same 21 nights: 90%). With B = 0.75 uV Montreal-FC
keeps 95% sensitivity with a +4.5-point gap (exploratory, not a pass).

What FC does not fix: at the published SINBAR chin cut-off (18.2%) it flags about 45% of
patients at both hospitals (and of CAP's patients). The site difference is gone; the
cut-off is still far too permissive for automated scoring (see FC5).

## FC3 Reference background B (as recorded; ladder change as recorded -> h150)

| rule | CAP RBD | CAP patients | MGH | HMC | gap | ladder MGH | ladder RBD |
|---|---|---|---|---|---|---|---|
| Montreal published | 90 | 33 | 29 | 9 | +20.5 | -22.0 | -33.3 |
| Montreal FC 0.5 | 95 | 41 | 41 | 35 | +5.5 | -1.1 | 0 |
| Montreal FC 0.75 | 95 | 27 | 26 | 21 | +4.5 | -1.1 | 0 |
| Montreal FC 1.0 | 81 | 22 | 18 | 16 | +1.6 | 0.0 | 0 |
| Montreal FC 1.25 | 71 | 22 | 13 | 12 | +1.9 | -0.7 | 0 |
| Montreal FC 1.5 | 62 | 18 | 11 | 11 | -0.2 | -0.4 | 0 |
| Montreal FC 2.0 | 57 | 14 | 8 | 9 | -0.6 | 0.0 | -4.8 |
| Montreal clamp 1.0 | 76 | 18 | 16 | 9 | +7.5 | -7.2 | -19.0 |
| SINBAR published | 95 | 75 | 76 | 25 | +51.0 | -49.8 | 0 |
| SINBAR FC 0.5 | 95 | 71 | 78 | 52 | +25.2 | -23.1 | 0 |
| SINBAR FC 0.75 | 95 | 51 | 59 | 51 | +7.8 | -6.9 | 0 |
| SINBAR FC 1.0 | 95 | 45 | 45 | 43 | +2.4 | +1.8 | 0 |
| SINBAR FC 1.25 | 95 | 29 | 35 | 31 | +3.7 | -0.4 | 0 |
| SINBAR FC 1.5 | 95 | 27 | 28 | 22 | +5.8 | -0.7 | 0 |
| SINBAR FC 2.0 | 86 | 25 | 19 | 18 | +1.2 | -0.4 | 0 |
| SINBAR clamp 1.0 | 95 | 35 | 40 | 25 | +15.2 | -11.9 | 0 |

- For B >= 1.0 uV both FC rules are noise-invariant (ladder changes <= 2 points) and the site
  gap is <= 6 points; B sets the operating point (sensitivity against false positives).
- B = 0.5 uV fails for SINBAR: it asks for less muscle activity than HMC's floor can reveal,
  so the guard binds at HMC and the rule behaves like the published one there.
- The clamp (an absolute floor without subtracting noise) keeps part of the gap and loses
  RBD sensitivity with noise: subtracting the noise is what makes the rule portable.

## FC4 Discrimination, CAP RBD vs CAP patients (AUC), as recorded

| measure | published | FC 0.5 | FC 0.75 | FC 1.0 | FC 1.25 | FC 1.5 | FC 2.0 |
|---|---|---|---|---|---|---|---|
| Montreal tonic | 0.844 | 0.864 | 0.847 | 0.827 | 0.811 | 0.812 | 0.788 |
| Montreal phasic | 0.846 | 0.866 | 0.860 | 0.847 | 0.833 | 0.825 | 0.803 |
| SINBAR any | 0.850 | 0.857 | 0.839 | 0.833 | 0.818 | 0.820 | 0.814 |

Within one recording system FC neither helps nor hurts discrimination much (CAP RBD and
patients share a system, so there is no floor difference to correct): its gain is
portability, not separation.

## FC5 Cut-offs re-derived on CAP (Youden; leave-one-out; 2,000 bootstraps)

| rule, measure | cut-off | LOO sens | LOO FP | MGH flagged [95% interval] | HMC flagged | gap |
|---|---|---|---|---|---|---|
| published Montreal tonic | 32.2 | 90 | 14 | 13 [6-13] | 7 [5-7] | +6 |
| published Montreal phasic | 27.7 | 86 | 18 | 8 [8-17] | 5 [5-7] | +3 |
| published SINBAR any | 62.9 | 86 | 20 | 10 [3-10] | 1 [1-1] | +9 |
| FC Montreal tonic | 6.6 | 76 | 35 | 33 [8-33] | 20 [7-20] | +12 |
| FC Montreal phasic | 7.9 | 86 | 27 | 32 [10-32] | 22 [10-22] | +10 |
| **FC SINBAR any** | **49.1** | **86** | 25 | **13 [10-17]** | **14 [11-20]** | **-1** |

By the pre-specified secondary definition (gap <= 5, LOO sensitivity >= 80%), the re-derived
SINBAR-FC cut-off is portable: it flags 13% of MGH and 14% of HMC patients while keeping
86% leave-one-out sensitivity. Re-deriving on the published SINBAR measure instead gives
10% vs 1% (gap +9). The Montreal-FC Youden cut-offs fall very low (6.6-7.9%) and do not
transfer (+10 to +12).

## FC6 Gain, and the size of muscle activity at each site

HMC scaled by 0.39 (same nights): Montreal published 8.8 -> 8.2; Montreal FC 16.3 -> 7.5
(-8.8, 13 -, p = 0.0002); SINBAR published 25.2 -> 25.2; SINBAR FC 42.9 -> 11.6 (-31.3,
46 -, p = 3e-14); RAI 7.5 -> 3.4. As expected, FC (like the RAI) depends on gain.

Whether real sites differ in gain was checked directly (1-s RMS, uV, median [IQR]; "net" =
noise b / 0.91 removed in power):

| | quiet-REM level | REM median, net | REM 95th pct, net | N2/N3 median, net |
|---|---|---|---|---|
| CAP RBD (21) | 0.86 [0.61-1.24] | 2.33 [1.55-4.05] | 11.77 [6.51-15.77] | 2.91 [1.36-5.18] |
| CAP patients (51) | 0.48 [0.44-0.69] | 0.39 [0.21-1.16] | 2.25 [1.38-6.39] | 1.61 [1.07-2.46] |
| MGH (925) | 0.59 [0.47-0.77] | 0.44 [0.27-0.79] | 2.91 [1.63-4.91] | 1.60 [0.93-2.90] |
| HMC (147) | 1.52 [1.23-1.79] | 0.45 [0.24-0.78] | 2.05 [1.47-3.39] | 1.70 [1.06-2.77] |
| HMC x0.39 | 0.59 | 0.18 | 0.80 | 0.66 |
| MGH / HMC | 0.39 | 0.99 | 1.42 | 0.95 |

With the noise removed, the three systems record the same muscle activity at the same size
(N2/N3 median 1.60, 1.70 and 1.61 uV; REM median 0.44, 0.45 and 0.39 uV): the sites differ in
noise, not in gain, which is what the floor-corrected rule assumes. MGH has somewhat more
large REM activity (95th percentile 2.91 vs 2.05 uV; ratio 1.42, inside the pre-specified
0.67-1.5 range).

## FC7 Montreal phasic bursts limited to 10 s instead of 15 s

Nights changed: CAP RBD 0, CAP patients 1 (33.3 -> 31.4%), MGH 9 (29.4 -> 29.1%), HMC 0.
The unresolved difference between sources is immaterial.

## FC8 MGH by record batch

| batch | n | quiet-REM level | Montreal % | SINBAR % |
|---|---|---|---|---|
| tr03 | 134 | 0.53 | 29 | 82 |
| tr04 | 102 | 0.60 | 39 | 82 |
| tr05 | 151 | 0.61 | 31 | 82 |
| tr06 | 87 | 0.62 | 26 | 76 |
| tr07 | 104 | 0.60 | 25 | 78 |
| tr08 | 34 | 0.47 | 29 | 82 |
| tr09 | 46 | 0.53 | 24 | 67 |
| tr10 | 49 | 0.59 | 18 | 69 |
| tr11 | 56 | 0.60 | 33 | 71 |
| tr12 | 83 | 0.63 | 22 | 62 |
| tr13 | 60 | 0.69 | 40 | 75 |
| tr14 | 19 | 0.69 | 37 | 58 |
| ladder subset (first 300) | 280 | 0.56 | 34 | 83 |
| the rest | 645 | 0.61 | 27 | 73 |

The 300 nights used for the ladder are a quieter, more often flagged part of MGH (level 0.56
vs 0.61 uV; SINBAR 83 vs 73%), so ladder percentages for MGH run a few points above the
whole cohort's; paired (same-night) comparisons are unaffected.

Across the 12 batches, the batch's median quiet-REM level correlated with its SINBAR
positivity at Spearman rho = -0.52 (Montreal +0.35, where the level also carries tone; see
T11): a weak within-site echo of the floor effect, to be read descriptively (the batch
labels are not documented).

## FC9 Age (CAP main system; ages from CAP's gender-age.xlsx)

Patients < 50: n = 35, 30 +/- 9 years (NFLE 28, narcolepsy 5, insomnia 1, PLM 1); patients
>= 50: n = 16, 59 +/- 6 (PLM 8, insomnia 6, NFLE 2); RBD: n = 21, 71 +/- 7.

| rule | patients < 50 | patients >= 50 | RBD |
|---|---|---|---|
| Montreal published | 29% | 44% | 90% |
| Montreal FC | 20% | 25% | 81% |
| SINBAR published | 74% | 75% | 95% |
| SINBAR FC | 37% | 62% | 95% |
| RAI | 11% | 19% | 57% |

| AUC, RBD vs | all patients | patients >= 50 |
|---|---|---|
| Montreal tonic, published / FC | 0.844 / 0.827 | 0.866 / 0.812 |
| Montreal phasic, published / FC | 0.846 / 0.847 | 0.812 / 0.833 |
| SINBAR any, published / FC | 0.850 / 0.833 | 0.884 / 0.845 |
| RAI | 0.842 | 0.814 |

Discrimination holds against patients of similar age, but older patients without RBD are
flagged more often (Montreal 29% -> 44%; SINBAR-FC 37% -> 62%): CAP's young controls flatter
specificity, and the external cohorts (mean age 55 in MGH) are the better guide.

## FC10 CAP healthy volunteers, night by night (published / FC; - = no physical units)

| night | system | quiet level, uV | Montreal | SINBAR |
|---|---|---|---|---|
| n1 | 256 Hz | 0.42 | 0/0 | 1/0 |
| n2, n3, n5, n10 | 512 Hz | 0.39-0.56 | 0/0 | n2, n5: 1/0; n3, n10: 0/0 |
| n11 | 512 Hz | 0.60 | 1/1 | 1/1 |
| n12 | 100 Hz | 0.49 | 0/0 | 0/0 |
| n4, n8 | 200 Hz (mylohyoid) | 1.32, 1.43 | n4 1/1, n8 0/0 | n4 1/1, n8 0/0 |
| n6, n7, n9 | 128 Hz | 2.52-3.71 | 0/1 | 1/1 |
| n13-n15 | 200 Hz, no units | 1.92-2.75 | 0/- | n15 1/- |

FC turned three healthy nights positive, all on CAP's 128-Hz system with very high floors
(2.5-3.7 uV). The rule's constants were calibrated on simulated noise at 200-512 Hz; at 128 Hz
the 5th percentile is 0.879 of the noise RMS (not 0.91) and the 1.5 b guard lets noise start
0.1-s runs in 2.3% of 3-s mini-epochs (0.5% at 200 Hz; 8.8% at 100 Hz). Those nights are
also above the rule's range for B = 1.0 uV (b <= B / 0.59 = 1.7 uV). FC should be applied
only to recordings at or above the AASM minimum of 200 Hz and within that range; this is
reported as a limitation, not re-tuned.

## Report additions (report.md)

T6, PPV by hospital at 1 / 2 / 5 / 10% prevalence (sensitivity from CAP RBD):
Montreal - MGH 3 / 6 / 14 / 26%, HMC 9 / 17 / 35 / 53%; SINBAR - MGH 1 / 2 / 6 / 12%, HMC
4 / 7 / 17 / 30%; RAI - MGH 6 / 11 / 24 / 41%, HMC 7 / 13 / 28 / 45%. The same criteria give
positive predictive values that differ up to three-fold by recording site.

T1 now includes CAP ages: RBD 70.7 years (86% men), NFLE 30.3, PLM 55.1, insomnia 60.9,
narcolepsy 31.6, healthy 31.6; MGH 54.7 (67% men).
