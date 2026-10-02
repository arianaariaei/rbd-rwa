# Methods (draft)

*Working title:* Measured against the noise floor: why published cut-offs for REM sleep
without atonia do not transfer across recording sites - an open multi-cohort analysis

## 2.1 Data sources

All recordings come from openly licensed databases that require no application,
credential or data-use agreement (Table 1).

| Cohort | Source | Nights | Population | Chin EMG | License |
|---|---|---|---|---|---|
| CAP | CAP Sleep Database, PhysioNet (Terzano et al. 2001) | 108 | 22 clinical RBD, 16 healthy, 40 NFLE, 10 PLM, 9 insomnia, 5 narcolepsy, 4 SDB, 2 bruxism (Parma, Italy) | 100-512 Hz, several systems | ODC-By 1.0 |
| HMC | Haaglanden Medisch Centrum sleep staging database v1.1, PhysioNet | 151 | Patients referred for PSG for mixed sleep complaints (The Netherlands) | 256 Hz | CC BY 4.0 |
| MGH | PhysioNet/CinC Challenge 2018 training set | 994 | Patients evaluated at the Massachusetts General Hospital sleep laboratory (USA) | 200 Hz, 1 uV resolution | ODC-By 1.0 |

CAP is the only openly available source of polysomnograms from patients with RBD and
supplies the positive class. Its healthy volunteers were recorded on several systems
that differ from the one used for the RBD patients (chin EMG sampled at 100-200 Hz in
most of them; three recordings stored as raw converter counts without physical units;
one without chin EMG). Because amplitude-based measures are sensitive to acquisition
hardware, RBD patients were compared primarily with the other CAP patients recorded on
the same system (512 Hz, microvolts; "same-system patients"), and the healthy group is
reported separately. HMC and MGH provide large clinical reference populations in which
RBD is not labeled; given its prevalence in sleep-clinic populations, nearly all
positive calls in these cohorts are expected to be false positives.

This is a retrospective analysis of pre-existing open databases. CAP does not state the
criteria by which RBD was diagnosed; because a clinical diagnosis of RBD itself requires
polysomnographic evidence of RWA, and CAP's patients had established disease, sensitivity
estimates are subject to incorporation and spectrum bias and are best read as upper bounds
for a screening population. Ages and sexes of CAP subjects were taken from the database's
spreadsheet (gender-age.xlsx); MGH provides age and sex per record; HMC publishes only group
summaries.

## 2.2 Signal processing

Recordings were streamed from PhysioNet's open-data mirror, processed in the cloud and
discarded; only derived envelopes were kept. Each channel was read at its native
sampling rate (EDF/EDF+ via a direct reader; WFDB for MGH), avoiding the implicit
resampling of general-purpose readers that up-sampled 128 Hz leg EMG to 512 Hz.

Chin EMG was band-pass filtered (4th-order Butterworth, zero-phase) between 10 Hz and
100 Hz, or Nyquist minus 5 Hz where the sampling rate did not allow 100 Hz, with notch
filters at the local mains frequency and its harmonics (50 Hz CAP and HMC, 60 Hz MGH).
Cardiac contamination was removed by detecting R-peaks on the ECG channel (5-20 Hz
band-pass, adaptive threshold, refractory period 0.3 s) and subtracting a median
heartbeat template, estimated in 5-minute blocks from -100 to +150 ms around each
R-peak, from the filtered chin signal. The effect was quantified as the ratio of the
median chin amplitude at the R-peak to that 300-500 ms before it (heartbeat-locked
ratio; 1.0 = no artifact).

The filtered signal was reduced to RMS and mean-rectified amplitude in bins of exactly
20 ms. To allow amplitude comparisons across recordings made with different
bandwidths, the same envelopes were also computed in a common 10-45 Hz band available
to every recording ("harmonized band").

## 2.3 Sleep stages and events

Sleep stages were taken from each database's expert scoring in 30-s epochs, aligned to
the signal start (wall-clock annotations in CAP, recording-onset offsets in HMC,
sample indices in MGH). In MGH, epochs overlapping an annotated respiratory event
(apnea, hypopnea) or arousal were flagged. Nights with less than 10 minutes of REM
sleep were excluded from all analyses.

## 2.4 RWA quantification

Four published approaches were implemented on the same REM epochs (Table 2).

| | Montreal | SINBAR (mentalis) | AASM | REM Atonia Index |
|---|---|---|---|---|
| Source | Montplaisir et al. 2010 | Frauscher et al. 2012 | AASM Manual | Ferri et al. 2008, 2010 |
| Tonic | 20-s epochs, >50% above 2x background or >10 uV | 30-s epochs, same criterion | 30-s epoch, >=50% above minimum NREM amplitude | - |
| Phasic | 2-s mini-epochs with 0.1-15 s bursts >4x background | 3-s mini-epochs with 0.1-5 s bursts >2x background | 3-s mini-epochs with 0.1-5 s bursts >=4x background; epoch phasic if >=5 of 10 | - |
| Other | - | "any" activity in 3-s mini-epochs | - | 1-s mean rectified amplitude, moving-minimum (60 s) noise correction |
| Cut-off | tonic >=30% or phasic >=15% | any >=18.2% | none published | RAI <0.8 |

The visual methods define activity relative to "background" EMG, which human scorers
judge by eye. Here background was operationalized as the 5th percentile of 1-s RMS
amplitudes within REM (NREM for the AASM tonic criterion); the sensitivity of results
to this choice is examined in Section 2.6. We refer to this per-night value as the
night's quiet-REM level. Where physical units were unavailable, the absolute (uV)
criteria were not applied.

## 2.5 Statistical analysis

For each method and group we report the share of nights classified positive by the
published cut-off with 95% Wilson intervals: sensitivity in CAP RBD, false-positive
rate elsewhere. Discrimination of the continuous scores was summarized by the area
under the ROC curve for RBD versus same-system patients. Agreement between methods was
assessed with Cohen's kappa. In MGH, the association of age, sex and apnea-hypopnea
index with a positive call was estimated by logistic regression, and the effect of
excluding event-flagged REM epochs was assessed on paired calls. Positive predictive
values for screening were computed from the sensitivity in CAP RBD and the specificity
in the pooled external cohorts across RBD prevalences of 1-10%.

To ask whether automated scoring needs its own cut-offs, each continuous score was
given a new cut-off maximizing Youden's index for CAP RBD versus same-system patients,
and the share of MGH and HMC nights above it was recorded. Because this re-uses the
22 RBD patients, the cut-offs were validated by leave-one-out cross-validation (the
cut-off re-derived without the held-out night) and their uncertainty by 2,000 bootstrap
re-derivations, resampling RBD patients and same-system patients separately; for each
bootstrap cut-off the external false-positive shares were recomputed, giving
percentile intervals.

To ask whether a night's own quiet-REM level shapes its verdict, nights were split into
tertiles of that level within each external cohort, and in MGH its association with a
positive call was estimated by logistic regression on log2 of the level (odds ratio per
halving), adjusted for age, sex and apnea-hypopnea index.

## 2.6 Sensitivity analyses

*Background definition.* All nights were re-scored with the background of the relative
criteria set to the minimum, or the 5th (default), 10th, 25th or 50th percentile, of
1-s REM RMS, or the 5th percentile of 1-s N2/N3 RMS; the AASM tonic criterion kept its
NREM definition throughout.

*Recording hardware.* MGH stores chin EMG at 200 Hz in steps of 1 uV (WFDB gain
1 unit/uV), while HMC stores it at 256 Hz in steps of 0.024 uV (16 bits over
+/-800 uV). To isolate what that storage
format can do on its own, every HMC recording was passed through the pipeline again
after its chin EMG had been (i) quantized to 1-uV steps, and (ii) additionally
resampled to 200 Hz (polyphase filtering). Because the median quiet-REM level is lower
in MGH (0.59 uV) than in HMC (1.52 uV), both were repeated after first scaling the HMC
signal by 0.39, which places it where MGH sits relative to the quantization step; the
scaled signal without quantization served as that comparison's reference. Each copy of
HMC was processed exactly like the original cohorts.

*Noise floor.* The reverse manipulation tested whether the lower quiet-REM level of MGH
could itself produce its higher positivity: white Gaussian noise (standard deviation
1.5 uV, seeded by record name) was added to the chin EMG of the first 300 MGH recordings
in the database's record list, which raises the expected quiet-REM level from 0.59 uV
to about 1.5 uV, HMC's median. Each noisy recording was compared with the same night as
recorded (paired difference with a 95% Wald interval; exact McNemar test).

*Noise ladder (pre-specified).* To turn this single comparison into a dose-response, and
to measure what the noise floor does to sensitivity, CAP (every recording with a chin EMG
in physical units), HMC (all) and the same 300 MGH recordings were streamed once more.
Because band-pass filtering and heartbeat subtraction are linear, each night's chin EMG and
one track of unit white noise (seeded by record name) were filtered once, and noisy copies
were formed by adding the filtered noise scaled to an in-band RMS of 0.5, 1.0, 1.5, 2.0
and 3.0 uV - the same noise draw at every level (common random numbers). Two further copies
were *harmonized*: the added noise was chosen, by iteration, to bring the night's
quiet-REM level to 1.5 and to 2.0 uV (within 1%); nights already above a target were left
unchanged. Every copy was scored with every method. The criteria for interpreting this
analysis - including when the noise floor would be judged to account for the site
difference, and when harmonization would be judged a working remedy - were written down
and committed to the repository before it was run (Supplement S1).

*Independent estimate of system noise.* In the same pass, the 40-90 Hz floor (5th
percentile of 1-s RMS) of a central EEG channel (C4 or C3 against the contralateral
mastoid) was measured in N2/N3 and in REM, as an estimate of each recording system's own
noise obtained from a channel other than the chin.

*Floor signature.* For every night, the ratio of the quietest N2/N3 chin level to the
quietest REM chin level (5th percentiles of 1-s RMS) was computed. Where the floor is set
by muscle tone, NREM tone rises above REM atonia (ratio > 1); where it is set by the
recording's own noise, the two are indistinguishable (ratio near 1).

*Transitional epochs.* Because laboratories differ most in how they place the boundaries
of REM periods, all nights were re-scored without the first and last epoch of every REM
period.

*Age.* CAP reports each subject's age in a separate spreadsheet. Because the RBD patients
were older (71 +/- 6 years) than most same-system patients (mostly NFLE, 30 +/- 11 years),
discrimination and false-positive rates were recomputed against same-system patients aged
50 or over.

## 2.7 Floor-corrected criteria (pre-specified)

A relative rule counts activity above k times the background b. When b is set by noise,
this requires muscle activity of about sqrt(k^2 - 1) b (in RMS terms), so the muscle activity
a criterion asks for scales with the noise floor of the recording system. We therefore
tested a floor-corrected (FC) version of each rule, in which activity counts above

T = max( sqrt(n^2 + (k^2 - 1) B^2), g b ),  with n = b / 0.91,

where b is the night's background as before, n the noise RMS that b implies (for
band-limited white noise the 5th percentile of 1-s RMS values is 0.91 of the RMS, in
simulation at 200, 256 and 512 Hz), B a reference background and g = 1.5 a guard against
counting noise (on simulated white noise, 0.1-s runs above 1.5 b occurred in 0.4-0.7% of
3-s mini-epochs and never made an epoch tonic). The muscle activity required is thus fixed at
what the published rule requires on a system whose background is B; at b = B the FC rule is
within 3% of the published one, below B it becomes an absolute threshold, and above B the
noise is subtracted in power instead of multiplied. Epoch and mini-epoch lengths, burst
durations, the 10-uV tonic alternative and the published percentage cut-offs were
unchanged; FC rules were applied only to recordings in physical units. B = 1.0 uV was fixed
in advance as the primary reference (between the quiet systems' 0.5-0.9 uV and HMC's
1.5 uV); 0.5, 0.75, 1.25, 1.5 and 2.0 uV, and a "clamp" variant without subtraction
(threshold k max(b, B)), were secondary. The rule, its parameters and five decision
criteria - invariance of MGH positivity and of RBD sensitivity along the noise ladder, MGH-HMC
agreement as recorded, RBD sensitivity of at least 85%, and no increase in CAP patients'
positivity - were committed to the repository with the analysis code before any FC result
for MGH, HMC or the CAP patients existed (Supplement S2). Cut-offs were also re-derived under
FC (Youden's index on CAP, leave-one-out and bootstrap, as in Section 2.5) and called
portable if MGH and HMC positivity differed by at most 5 points with leave-one-out
sensitivity of at least 80%.

*Scale of muscle activity.* Because FC thresholds are in microvolts, they assume that sites
record muscle activity on a comparable scale. For every night we computed the median of
1-s RMS in N2/N3 and the median and 95th percentile in REM, each with the noise power
(b / 0.91)^2 subtracted, and compared the medians between cohorts; a ratio within 0.67-1.5
was fixed in advance as comparable.

## 2.8 External cohorts (pre-specified)

To test the findings on recording systems not used to obtain them, three further
request-free cohorts were processed with the unchanged pipeline after the predictions had
been committed (Supplement S3): BOAS (OpenNeuro ds005555, CC0; 128 nights of 100 adults
recruited from the general population without psychotropic medication or severe disease;
Micromed SD plus, bipolar chin EMG at 256 Hz; consensus AASM stages of three scorers),
DOD-O (Dreem Open Datasets, Zenodo 15900394, MIT license; 55 patients with suspected
sleep-disordered breathing at the Stanford Sleep Medicine Center; Somnomedics Somno HD) and
DOD-H (same release; 25 healthy volunteers, French Armed Forces Biomedical Research Institute;
Compumedics Siesta); both Dreem sets provide chin EMG and ECG at 250 Hz and consensus stages of
five scorers. BOAS has no ECG channel; heartbeats were searched for on the chin EMG itself
with the same detector and plausibility test, and removed only where they passed it. For
BOAS, each participant's first recording was analyzed (all 128 nights as a sensitivity
analysis). Six predictions were fixed in advance: comparable muscle scale (net N2/N3 level
within 0.67-1.5 times MGH's), at least 30% of healthy nights flagged by the published SINBAR
criterion on systems with a floor below 1 uV, agreement between healthy cohorts once the
floor is subtracted, a negative rank correlation between cohort floor and published SINBAR
positivity that weakens under floor correction, specificity of the SINBAR-FC cut-off
re-derived on CAP (<= 10% of healthy and <= 20% of DOD-O nights flagged), and DOD-O's
published positivity within 10 points of MGH's noise-ladder curve at DOD-O's floor.

## 2.9 Reproducibility

All code (Python; NumPy, SciPy, pandas, wfdb) is openly available and runs end-to-end
from a single Google Colab notebook that downloads the public data, so every number in
this paper can be regenerated without local installation.
