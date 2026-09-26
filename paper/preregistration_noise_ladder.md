# Pre-specified analysis: the noise ladder (written 2026-09-26, before running it)

Committed before any ladder result exists, so the criteria below cannot have been tuned
to the outcome.

## Data

Every recording is streamed again and its chin EMG kept as recorded and with white
Gaussian noise added *in band* (after the same 10-100 Hz band-pass and mains notch as the
signal). One noise track per night, seeded by record name, is scaled to each level
(common random numbers).

- Cohorts: CAP (all recordings with a chin EMG in physical units), HMC (all 151), MGH (the
  first 300 records of the Challenge 2018 list - the same 300 as the earlier noise test).
- Fixed ladder: added in-band RMS 0.5, 1.0, 1.5, 2.0, 3.0 uV (`n050` ... `n300`).
- Harmonisation: per night, the in-band noise that raises its quiet-REM level (5th
  percentile of 1-s REM RMS) to 1.5 or 2.0 uV (`h150`, `h200`); nights already above the
  target are left as they are.
- Independent measure: the 40-90 Hz floor (5th percentile of 1-s RMS) of one central EEG
  channel (C4/C3), in N2/N3 and in REM.

## Criteria (published cut-offs unless stated; nights with >= 10 min REM)

1. **Matched floor.** After harmonising to 2.0 uV, MGH and HMC differ by <= 3 percentage
   points (Montreal) and <= 5 points (SINBAR): the noise floor accounts for the site
   difference. A remaining gap > 10 points means it does not on its own.
2. **Dose-response continuity.** MGH's ladder, interpolated (on log quiet-REM level) at
   HMC's median native level, lies within 3 (Montreal) / 5 (SINBAR) points of HMC's native
   positivity.
3. **Sensitivity.** CAP RBD patients recorded on the main system (n = 21): if sensitivity
   at the 2.0 uV floor falls below 70% for Montreal or SINBAR, "noisier systems miss RBD"
   is supported.
4. **Remedy.** With every cohort harmonised to 2.0 uV, cut-offs re-derived on CAP (Youden,
   RBD vs same-system patients) "work" if MGH and HMC false-positive shares differ by <= 5
   points for Montreal phasic, Montreal tonic and SINBAR "any", with leave-one-out
   sensitivity >= 80%. If leave-one-out sensitivity is < 70%, we recommend floor-specific
   cut-offs instead of harmonisation.
5. **Equipment.** If HMC's EEG 40-90 Hz floor in N2/N3 is >= 1.5x MGH's, the noise
   difference is system-wide; within +/-20%, it is specific to the chin recording
   (electrodes, montage).
6. **REM boundaries.** Excluding the first and last epoch of every REM period changes the
   MGH-HMC gap by < 3 points (Montreal): scoring conventions at REM boundaries do not
   explain the gap.
