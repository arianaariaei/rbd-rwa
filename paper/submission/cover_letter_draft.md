⟦Date⟧

Editor-in-Chief, SLEEP

Dear Editor,

We submit the Original Article "The recording system's noise floor biases automated scoring of REM sleep without atonia across sites" for consideration in SLEEP.

Automated scoring of REM sleep without atonia (RWA) is moving from single-center validation to multi-center use: screening routine polysomnograms for isolated RBD, pooling prodromal cohorts and following patients over years. We show that automated implementations of the background-relative criteria (Montreal, SINBAR chin, and the open-source RBDtector) judge chin activity against a multiple of each recording's own noise floor. On 1,354 openly available polysomnograms from six recording systems, the same rules flagged 29% of patients at one hospital and 9% at another and most healthy volunteers on quiet equipment. Adding noise to the same nights reproduced the difference, and muscle activity of known size added to nights from every system was detected only above an amplitude proportional to the system's floor. On the same RBD nights, a noisier floor lowered tonic RWA by two-thirds of the difference that predicted Parkinson's disease in a landmark cohort. A correction that subtracts each recording's noise removes most of the dependence, at the price of a dependence on gain, which we quantify.

We think the work fits SLEEP because it concerns the measurement on which the diagnosis of RBD and much prodromal Parkinson's research rest, and its recommendation is simple: report automated RWA results together with the recording's noise floor and gain. We have framed every claim as a property of automated implementations; whether visual scoring shares the mechanism is the subject of a registered, blinded substudy (⟦OSF link⟧).

All data are openly licensed (CAP, HMC and Challenge 2018 on PhysioNet; BOAS on OpenNeuro; Dreem Open Datasets on Zenodo). The code, a Colab notebook that regenerates every number, the analysis plans with their commit history (each committed before its analysis was run) and the per-night scores are public (https://github.com/arianaariaei/rbd-rwa; analysis plans archived on Zenodo, doi:10.5281/zenodo.23697366).

Use of AI: a generative AI assistant (Claude, Anthropic) was used to write and debug analysis code, run the cloud analyses, and draft and edit the manuscript. The authors checked all code, results and text and take full responsibility for the content. This is also stated in the Acknowledgements.

The manuscript has not been published or submitted elsewhere, and no preprint has been posted. The authors declare no conflicts of interest. ⟦Suggested reviewers, if wanted, and any reviewers to exclude.⟧

Yours sincerely,

⟦Corresponding author, affiliation, email⟧
