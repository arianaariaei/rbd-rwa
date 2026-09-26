# Abstract (draft, structured, ~250 words)

**Study Objectives:** Automated quantification of REM sleep without atonia (RWA) could
find people with prodromal synucleinopathy in routine polysomnograms. We asked whether
published RWA cut-offs, applied automatically, transfer across recording sites, and why
they might not.

**Methods:** We implemented the Montreal, SINBAR (chin), AASM and REM Atonia Index (RAI)
criteria in one open pipeline and applied them to 1,177 polysomnograms from three open
databases: CAP (22 patients with RBD, 51 other patients recorded on the same system, 15
healthy), a Dutch (HMC, n=147) and a US (MGH, n=925) clinical cohort. We re-created
recordings in software - changing storage format, amplitude and noise floor one at a
time - varied the operational definition of background activity, and stratified by
sleep apnoea, age and cardiac artefact.

**Results:** The Montreal and SINBAR cut-offs identified 91% and 95% of RBD patients,
but flagged 29% and 76% of MGH patients against 9% and 25% of HMC patients; the methods
disagreed on 70% of MGH nights. MGH's storage format (200 Hz, 1-uV steps) and its 2.6-fold
lower chin EMG amplitude did not explain the gap, nor did sleep apnoea, age or cardiac
artefact. Adding noise to MGH recordings until their quiet-REM level matched HMC's lowered
positivity on the same nights from 34% to 10% (Montreal) and from 83% to 36% (SINBAR).
The operational definition of background moved MGH positivity between 13% and 47%. At 2%
prevalence, positive predictive values were 3-11%. Cut-offs re-derived for automated
scoring cut the external false positives of the Montreal and SINBAR measures to 1-13%
with 86-90% cross-validated sensitivity, but were imprecise.

**Conclusions:** Relative RWA criteria are, in effect, measured against the chin EMG noise
floor, so a quieter recording system flags more patients. Automated RWA screening needs
thresholds that account for the noise floor, calibrated and reported for each site.
