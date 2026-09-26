# Abstract (draft, structured, ~250 words)

**Study Objectives:** Automated quantification of REM sleep without atonia (RWA) could find
people with prodromal synucleinopathy in routine polysomnograms. We asked whether published
RWA cut-offs, applied automatically, transfer across recording sites, and why they might not.

**Methods:** We implemented the Montreal, SINBAR (chin), AASM and REM Atonia Index criteria
in one open pipeline and applied them to 1,177 polysomnograms from three open databases:
CAP (22 patients with RBD, 51 other patients on the same system), a Dutch (HMC, n=147) and a
US (MGH, n=925) clinical cohort. We re-created recordings in software, changing storage
format, amplitude and noise floor one at a time; a pre-specified noise ladder then measured
how verdicts, including RBD sensitivity, follow the noise floor, and a second pre-specified
analysis tested floor-corrected criteria that subtract each recording's noise instead of
multiplying it.

**Results:** The Montreal and SINBAR cut-offs identified 91% and 95% of RBD patients but
flagged 29% and 76% of MGH patients against 9% and 25% of HMC patients. MGH's storage format
and lower amplitude did not explain the gap, nor did sleep apnoea, age or cardiac artefact.
Raising MGH's chin EMG noise floor to HMC's lowered positivity on the same nights from 34% to
10% (Montreal) and 83% to 36% (SINBAR); along the noise ladder MGH's curve passed through
HMC's point (8.9% vs 8.8%), and HMC's system was twice as noisy on EEG as well. At an
HMC-like floor, Montreal sensitivity for RBD fell from 90% to 57%. With the noise removed,
the sites recorded muscle activity at the same size. Floor-corrected criteria were
unaffected by added noise (0 of 280 MGH nights changed; RBD sensitivity unchanged) and
closed the site gap (Montreal +20.5 to +1.6 points; SINBAR +51.0 to +2.4), keeping SINBAR's
sensitivity at 95%; a floor-corrected SINBAR cut-off re-derived on CAP flagged 13% of MGH and
14% of HMC patients with 86% leave-one-out sensitivity. At 2% prevalence, positive
predictive values of the published criteria were 2-17%, depending on the site.

**Conclusions:** Background-relative RWA criteria are, in effect, measured against the
recording's noise floor: quieter systems flag more patients and noisier ones miss RBD.
Subtracting the floor makes the criteria portable; RWA thresholds should be reported with
the noise floor and reference on which they were set.
