# Revision analyses: results (run 2026-10-27, Colab runtime 2)

Specified in `paper/preregistration_revision.md` (commits 41252ad, 65c7e99) before they were
computed. Source: `results/revision_report.md` (run_revision.py on every pack as recorded; the
ladder score files of the earlier runs). Shares are k/n with 95% Wilson intervals; differences
with 95% Newcombe intervals; TOST equivalence at +/-10 points = 90% interval inside the margin.

## V2 Share flagged as recorded (k/n, %)

| Group | Montreal pub | Montreal FC | Montreal FC-nrem | SINBAR pub | SINBAR FC | SINBAR FC-nrem | RAI | SINBAR-FC >= 49.1% |
|---|---|---|---|---|---|---|---|---|
| CAP RBD | 19/21 90.5 [71-97] | 17/21 81.0 | 17/21 81.0 | 20/21 95.2 [77-99] | 20/21 95.2 | 20/21 95.2 | 12/21 57.1 | 18/21 85.7 |
| CAP patients | 17/51 33.3 [22-47] | 11/51 21.6 | 12/51 23.5 | 38/51 74.5 [61-84] | 23/51 45.1 | 22/51 43.1 | 7/51 13.7 | 10/51 19.6 |
| MGH | 270/919 29.4 [27-32] | 165/919 18.0 [16-21] | 152/912 16.7 | 700/919 76.2 [73-79] | 416/919 45.3 [42-48] | 379/912 41.6 | 82/925 8.9 [7-11] | 121/925 13.1 [11-15] |
| HMC | 13/147 8.8 [5-15] | 24/147 16.3 [11-23] | 21/146 14.4 | 37/147 25.2 [19-33] | 63/147 42.9 [35-51] | 48/146 32.9 | 11/147 7.5 [4-13] | 21/147 14.3 [10-21] |
| BOAS | 41/99 41.4 [32-51] | 15/99 15.2 [9-24] | 15/99 15.2 | 90/99 90.9 [84-95] | 35/99 35.4 [27-45] | 35/99 35.4 | 13/99 13.1 | 11/99 11.1 [6-19] |
| DOD-O | 16/53 30.2 [20-44] | 13/53 24.5 | 12/53 22.6 | 31/53 58.5 [45-71] | 27/53 50.9 | 24/53 45.3 | 4/53 7.5 | 9/53 17.0 |
| DOD-H | 5/25 20.0 [9-39] | 3/25 12.0 [4-30] | 3/25 12.0 | 21/25 84.0 [65-94] | 8/25 32.0 [17-52] | 7/25 28.0 | 1/25 4.0 | 3/25 12.0 |

Denominators: the relative criteria scored 919 MGH nights (6 of the 925 had no estimable
background); the RAI and the re-derived cut-off all 925. MGH SINBAR-FC is 45.3% [42-48]
(416/919); the review's [42-49] assumed n = 925. Table 3 of the submitted version is otherwise
reproduced exactly.

## V3 Between-site differences (points, 95% CI; TOST +/-10)

| Comparison | Rule | All nights | Equivalent within 10? | In-range nights | Equivalent? |
|---|---|---|---|---|---|
| MGH - HMC | Montreal published | +20.5 [+14.2 to +25.2] | no | - | - |
| | Montreal FC | +1.6 [-5.6 to +7.4] | **yes** (p 0.006) | +2.6 [-5.9 to +8.4] (876/91) | yes (p 0.021) |
| | Montreal FC-nrem | +2.3 [-4.7 to +7.7] | yes (p 0.007) | +5.8 [-1.9 to +10.4] | yes (p 0.084)* |
| | Montreal FC-min | +1.5 [-5.7 to +7.3] | yes (p 0.005) | +3.7 [-4.7 to +9.3] | yes (p 0.037) |
| | SINBAR published | +51.0 [+42.9 to +57.9] | no | - | - |
| | SINBAR FC | +2.4 [-6.3 to +10.8] | **yes** (p 0.042) | -0.1 [-10.9 to +10.2] | yes (p 0.035) |
| | SINBAR FC-nrem | +8.7 [+0.1 to +16.5] | no | +7.5 [-3.2 to +16.9] | no |
| | SINBAR FC-min | +2.5 [-6.3 to +10.9] | yes (p 0.044) | +0.6 [-10.2 to +10.9] | yes (p 0.043) |
| | RAI | +1.4 [-4.3 to +5.2] | yes (p < 0.001; also within 5) | - | - |
| | SINBAR-FC >= 49.1% | -1.2 [-8.1 to +4.1] | yes (p 0.002) | -0.3 [-8.5 to +5.1] | yes (p 0.002) |
| BOAS - DOD-H | Montreal published | +21.4 [+0.2 to +36.3] | no | - | - |
| | Montreal FC | +3.2 [-15.7 to +14.6] | not shown (n = 25) | -2.1 [-20.6 to +9.0] | not shown |
| | SINBAR published | +6.9 [-5.1 to +26.0] | no | - | - |
| | SINBAR FC | +3.4 [-18.1 to +21.1] | not shown | +1.0 [-20.5 to +18.9] | not shown |

*The verdict uses the 90% Newcombe interval; the Wald p is reported alongside.

Nights outside the floor-corrected rule's range (below 200 Hz or quiet-REM level above
1.69 µV): CAP RBD 24%, CAP patients 14%, MGH 5%, HMC 38%, BOAS 8%, DOD-O 8%, DOD-H 0%.

## V4 / R2 Noise estimate from N2/N3

N2/N3 quiet level (median, µV): CAP RBD 1.12, CAP patients 0.66, MGH 0.75, HMC 1.73, BOAS 0.47,
DOD-O 1.01, DOD-H 0.68; quiet-REM level: 0.86, 0.48, 0.59, 1.52, 0.37, 0.82, 0.56. The N2/N3
quiet level is higher than the REM one in every group: it contains NREM muscle tone, so it is
not a cleaner noise estimate. RBD sensitivity: Montreal-FC-nrem 81% (17/21), unchanged;
AUC fell slightly (tonic 0.83 -> 0.78). **Criterion R2a (sensitivity >= 85%): not met.**
SINBAR-FC-nrem lost site equivalence (+8.7 points). The lower of the two estimates ("FC-min")
behaves like the pre-specified rule.

## V5 Rank correlations across the six groups without RBD (exact permutation p, n = 6)

Montreal published -0.77 (p 0.10), FC +0.31 (p 0.56); SINBAR published -0.83 (p 0.058), FC
+0.43 (p 0.42). With six groups none is significant at 5%; the correlations are descriptive.

## V6 CAP nights analyzed (>= 10 min REM), by group and system

512 Hz (main system): RBD 21, NFLE 30, PLM 9, insomnia 7, narcolepsy 5, healthy 5. Other systems:
RBD 1 (256 Hz); NFLE 10 (2 at 128, 8 at 256 Hz); PLM 1 (128); insomnia 2 (128, 256); SDB 3
(128); bruxism 1 (256); healthy 10 (100-256 Hz) and 3 without physical units. Total 105. Table 1's
groups: 22 RBD + 51 same-system patients + 15 healthy (5 of them on the main system) = 88; the
other 17 are the NFLE (10), PLM (1), insomnia (2), SDB (3) and bruxism (1) nights on other
systems, used only in Supplementary Table S1.

## V7 Narcolepsy and age (CAP's main system; AUC RBD vs same-system patients, FP rate)

| Comparison group | n | Montreal tonic AUC (FP) | SINBAR any AUC (FP) | Montreal-FC tonic AUC (FP) | SINBAR-FC any AUC (FP) |
|---|---|---|---|---|---|
| All same-system patients | 51 | 0.84 (33%) | 0.85 (75%) | 0.83 (22%) | 0.83 (45%) |
| Without narcolepsy | 46 | 0.86 (30%) | 0.86 (72%) | 0.84 (17%) | 0.84 (43%) |
| Aged 50 or over | 16 | 0.87 (44%) | 0.88 (75%) | 0.81 (25%) | 0.85 (62%) |

## V8 MGH ladder on one set of nights

Of the first 300 MGH records, 280 have at least 10 min of REM as recorded and at every step. In
3 of these (tr03-0086, tr04-1006, tr05-0443) the quiet-REM level as recorded is exactly zero
(flat chin signal in the quietest REM seconds), so the relative criteria cannot be applied as
recorded; they are excluded from every comparison of relative criteria (n = 277; RAI n = 280).

| Rule (n = 277) | As recorded | at 1.5 µV (h150) | Paired change [95% CI] | Nights changed | McNemar p |
|---|---|---|---|---|---|
| Montreal published | 33.9% | 11.9% | -22.0 [-26.7 to -17.3] | 61 pos->neg, 0 neg->pos | 8.7e-19 |
| SINBAR published | 83.0% | 33.2% | -49.8 [-55.6 to -44.4] | 138 / 0 | 5.7e-42 |
| RAI (n = 280) | 11.8% | 10.7% | -1.1 [-2.5 to 0.0] | 3 / 0 | 0.25 |
| Montreal FC | 21.3% | 21.3% | 0.0 | 0 / 0 | 1.0 |
| SINBAR FC | 48.7% | 50.5% | +1.8 [+0.4 to +3.6] | 0 / 5 | 0.062 |

Ladder steps on the same 277 nights (Montreal / SINBAR published): n050 23.1 / 67.9, n100 14.4
/ 44.0, n150 9.0 / 29.2, n200 7.9 / 22.0, n300 6.1 / 13.4, h200 9.0 / 22.4. Floor-corrected:
Montreal 21.3 at every step to n200, 20.2 at n300; SINBAR 49.1, 49.8, 49.8, 44.4, 28.5, h200 44.0.
(The fixed 1.5-µV-SD white-noise comparison of the Results, 34% -> 10% on 277 nights, is a
separate analysis.)

## V9 AASM along the ladder (mean tonic % / phasic-epoch %)

CAP RBD 74/42 as recorded -> 73/23 at h150; CAP patients 52/12 -> 42/7; MGH 39/12 -> 36/5;
HMC 36/4 -> 35/3. AASM tonic (referenced to the NREM minimum) hardly moves; its phasic measure
falls like the other relative criteria.

## V10 Montreal phasic bursts limited to 5 s or 10 s

Share flagged with 15 s / 10 s / 5 s: CAP RBD 90.5 / 90.5 / 90.5; CAP patients 33.3 / 31.4 /
31.4; MGH 29.4 / 29.1 / 28.6; HMC 8.8 / 8.8 / 8.8; BOAS 41.4 / 41.4 / 41.4. Floor-corrected: CAP
RBD 81.0 throughout; MGH 18.0 / 18.0 / 17.7. The burst limit changes nothing that matters.
