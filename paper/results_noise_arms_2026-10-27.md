# Noise that is not white: results (run 2026-10-27)

Pre-specified in `paper/preregistration_revision.md`, R1 (commit 41252ad), before the run.
Source: `results/noise_arms_report.md` (run_noise_arms.py). Same nights in every copy:
MGH n = 280 (the ladder's first 300 records with >= 10 min REM in every copy), CAP RBD n = 21,
CAP same-system patients n = 51. Every noise was scaled per night to a quiet-REM level of 1.5
µV (h150) or 2.0 µV (h200); achieved medians 1.49-2.00 µV.

## Share flagged (%), MGH

| Rule | As recorded | white h150 | pink h150 | drift h150 | recorded (HMC) h150 | white h200 | pink h200 | drift h200 |
|---|---|---|---|---|---|---|---|---|
| Montreal published | 33.9 | 11.4 | 11.1 | 15.0 | 90.7 | 8.9 | 8.9 | 14.3 |
| SINBAR published | 83.0 | 33.2 | 34.6 | 76.1 | 98.6 | 22.5 | 22.9 | 75.0 |
| RAI | 11.8 | 10.7 | 10.4 | 10.4 | 88.6 | 10.4 | 10.4 | 10.0 |
| Montreal FC | 21.3 | 21.4 | 21.8 | 46.1 | 96.4 | 21.4 | 21.8 | 69.3 |
| SINBAR FC | 48.7 | 50.4 | 52.9 | 97.1 | 99.6 | 43.9 | 48.9 | 98.9 |
| Montreal FC-nrem | 19.9 | 19.0 | 19.4 | 33.3 | 94.6 | 18.6 | 19.4 | 52.7 |

CAP RBD (sensitivity, %): Montreal published 90.5 as recorded; h150 white 57.1, pink 57.1,
drift 61.9; Montreal FC 81.0, 81.0, 81.0, 90.5; SINBAR published 95.2 throughout white and pink.
CAP same-system patients: Montreal published 33.3 -> white 13.7, pink 13.7, drift 17.6; SINBAR
74.5 -> 25.5, 25.5, 70.6; Montreal FC 21.6 -> 21.6, 21.6, 52.9.

## Paired differences from white noise at 1.5 µV (points, 95% bootstrap CI), MGH

| Rule | pink | drift | recorded |
|---|---|---|---|
| Montreal published | -0.4 [-1.4, +0.7] | +3.6 [+1.4, +6.1] | +79.3 |
| SINBAR published | +1.4 [0.0, +3.2] | +42.9 [+36.8, +48.6] | +65.4 |
| Montreal FC | +0.4 [0.0, +1.1] | +24.6 [+19.6, +29.6] | +75.0 |
| SINBAR FC | +2.5 [+0.7, +4.6] | +46.8 [+40.7, +52.5] | +49.3 |

## Criteria (as written)

- **R1a** (published, MGH, each kind within 5 points of white): pink met (Montreal -0.4, SINBAR
  +1.4); drift met for Montreal (+3.6), **not met** for SINBAR (+42.9); recorded **not met**.
- **R1b** (FC, MGH, within 5 points of as recorded): pink met (Montreal +0.5, SINBAR +4.2);
  drift **not met** (Montreal +24.8, SINBAR +48.4); recorded **not met**.
- **R1c** (CAP RBD Montreal sensitivity within 10 points of white): pink met (0), drift met
  (+4.8); recorded not met (+33.3).

## Interpretation

1. Spectral shape does not matter: 1/f noise reproduced every white-noise result, published and
   floor-corrected, on patients and on RBD nights.
2. Noise whose level drifts through the night breaks the assumption of every rule that judges
   activity against one quiet level per night. As stated in advance, the quiet level (5th
   percentile of 1-s RMS) samples the quietest stretch, so in louder stretches the noise itself
   crosses the threshold: published SINBAR rose by 43 points and the floor-corrected rules by
   25-47 points. The published Montreal criteria moved little because their tonic rule needs
   activity in most of a 20-s epoch above twice the level, which drifting noise of this size
   rarely sustains.
3. The recorded-noise arm did not test what it was meant to. It was built, as specified, by
   splicing the quietest REM runs of 30 HMC nights without matching their levels; the
   nights' floors differ, so the spliced track jumps between levels every few seconds. That is
   an extreme form of drift, which is why every rule, the RAI included, flagged almost every
   night. A level-matched version (each night's runs scaled to a common RMS) is run as an
   exploratory analysis.

The paper therefore states that the floor-corrected rule, like the published relative rules,
assumes a noise level that is roughly stable through the night, and reports the drift result.
