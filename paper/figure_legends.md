# Figure legends (draft)

**Figure 1. Share of nights flagged positive by each method's published cut-off.**
Points are the percentage of nights classified positive, with 95% Wilson intervals, for the
Montreal (tonic >= 30% of 20-s epochs or phasic >= 15% of 2-s mini-epochs), SINBAR (chin
"any" activity >= 18.2% of 3-s mini-epochs) and REM Atonia Index (< 0.8) criteria, applied
by the same automated pipeline. CAP RBD: patients with REM sleep behaviour disorder; CAP
patients: CAP patients with other sleep disorders recorded on the same system as the RBD
patients (512 Hz); CAP healthy: healthy volunteers (recorded on other systems); MGH:
Massachusetts General Hospital clinical cohort (PhysioNet Challenge 2018); HMC:
Haaglanden Medisch Centrum clinical cohort. For CAP RBD the share is the sensitivity; for
the other groups it is the false-positive rate if none of them has RBD.

**Figure 2. The quiet-REM chin EMG level, and recordings re-made in software.**
(A) Each night's quiet-REM level - the 5th percentile of 1-s RMS chin EMG amplitude during
REM sleep, the reference against which the relative criteria judge activity - by group
(log scale; boxes: median and interquartile range; whiskers: 1.5 IQR). The dashed line is
the 1-uV step in which MGH stores chin EMG. (B) Share of nights flagged positive (95%
Wilson intervals) in HMC as recorded; HMC quantised to 1-uV steps; HMC quantised and
resampled to 200 Hz (MGH's storage format); HMC scaled by 0.39 to MGH's median quiet-REM
level; the scaled signal in MGH's storage format; MGH as recorded (all nights); and MGH
with 1.5 uV of added white noise, which raises its quiet-REM level to HMC's (the first 300
recordings; the same nights as recorded were flagged at 34% by Montreal, 83% by SINBAR and
12% by the RAI, T12). Each copy was processed exactly like the original cohorts.

**Figure 3. Sensitivity of the verdicts to the operational definition of background.**
Every night re-scored with the background of the relative criteria set to the minimum or
the 5th (default), 10th, 25th or 50th percentile of 1-s REM RMS amplitude, or the 5th
percentile of 1-s N2/N3 amplitude. (A, B) Share of nights flagged positive by the Montreal
and SINBAR criteria, by group. (C) Separation of CAP RBD from CAP patients recorded on the
same system (area under the ROC curve) for the continuous tonic and phasic measures; the
AASM tonic criterion keeps its NREM reference throughout and is not shown.

**Figure 4. Published and re-derived cut-offs against each group's distribution.**
(A) Montreal phasic activity (% of 2-s mini-epochs; the phasic criterion alone) and (B)
SINBAR "any" activity (% of 3-s mini-epochs), one point per night. Dashed line: published cut-off; solid line: cut-off
re-derived for automated scoring by maximising Youden's index for CAP RBD against CAP
patients recorded on the same system. Beneath each group: share of nights flagged by the
published and by the re-derived cut-off.

**Figure 5. Positive calls by a night's own quiet-REM level.**
Share of nights flagged positive, by tertile of the quiet-REM level within (A) MGH and (B)
HMC. A lower quiet-REM level did not make a night more likely to be flagged by the relative
criteria; the RAI, built on absolute amplitude, flagged nights with a higher level more
often.
