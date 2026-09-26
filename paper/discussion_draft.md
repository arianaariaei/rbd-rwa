# Discussion (draft)

## Principal findings

Applied through one automated pipeline to 1,177 openly available polysomnograms, the
published RWA cut-offs recognised clinical RBD - the Montreal and SINBAR criteria
flagged 91% and 95% of CAP's RBD patients - but also flagged a large, and strongly
site-dependent, share of patients in whom RBD was not suspected: 29% (Montreal) and 76%
(SINBAR) of MGH patients against 9% and 25% of HMC patients, with CAP's patients with
other sleep disorders behaving like MGH (Montreal 22-60%, SINBAR 67-100% by diagnosis).
The methods disagreed with each other on most nights where the false-positive burden
was high (70% of MGH nights); agreement was lowest between SINBAR and the RAI, the only
index built on absolute amplitude (kappa 0.04 in MGH). In a screening setting, these
false-positive rates translate into positive predictive values of 3-11% at an RBD
prevalence of 2%. The between-site difference was reproduced by a single property of
the recording, its noise floor: adding noise to MGH's chin EMG until its quiet-REM level
matched HMC's lowered MGH's positivity to HMC's.

## Why the same criteria give different answers at different sites

The Montreal, SINBAR and AASM criteria judge muscle activity against a background: an
activity counts when it exceeds a multiple of the quietest EMG of the night. In a
well-atonic REM period that quietest EMG is mostly not muscle but the noise of the
electrodes and amplifier, so the thresholds are, in effect, multiples of the recording
system's noise floor. A quieter system lowers the thresholds and lets smaller muscle
twitches - which occur in everyone's REM sleep - count as RWA. Our simulations isolate
this. Scaling HMC's signals to MGH's much lower level left the verdicts unchanged, as it
should, because signal and noise scale together; storing them as MGH does - 200 Hz and
1-uV steps, a step larger than the quiet-REM level itself - did not raise positivity,
at HMC's amplitude or at MGH's. But adding noise to MGH recordings, which raises the
floor without adding muscle activity, removed two-thirds of MGH's Montreal positives
and more than half of its SINBAR positives, every change in the direction of HMC, and
brought the agreement between methods to HMC's level. The MGH chin EMG is 2.6 times
quieter than HMC's; that alone is enough to account for most of the difference between
the two hospitals.

Within a single cohort the relationship runs the other way - nights with a higher
quiet-REM level were flagged slightly more often by the Montreal criteria - because
there the level also carries genuine muscle tone: CAP's RBD patients had a higher
quiet-REM level than other patients recorded on the same system. The two observations
are compatible: across sites the floor is set by the equipment, within a site by the
patient.

The gap was robust to everything else we could vary or measure: every definition of
background, the removal of REM epochs containing respiratory events or arousals, the
severity of sleep apnoea (MGH patients with an apnoea-hypopnoea index below 5 were still
flagged at 21-24% by the Montreal criteria), age, and residual cardiac artefact. The
simulation shows that a noise-floor difference of the size observed is sufficient to
explain the gap; it cannot exclude contributions from what the open datasets do not
document - electrode type and placement, amplifier filters, how scorers placed REM
boundaries, and the patients' medication. Serotonergic antidepressants, common in
sleep-clinic populations, increase REM chin tone in people without RBD [McCarter 2015],
and narcolepsy, which accounts for part of CAP's positive calls, is itself associated
with RWA [Dauvilliers 2013]. The practical consequence is the same whatever the mix: a
cut-off validated in one laboratory cannot be assumed to mean the same thing in another,
and the noise floor of the chin EMG - easily measured in every recording - should be
reported alongside any RWA measure and taken into account by its thresholds.

## Background is an undocumented free parameter

Visual scorers judge "background" EMG by eye; an automated method must turn it into a
number, and published descriptions do not say which. Across plausible choices - the
minimum, or a low to middle percentile of REM amplitude, or a percentile of NREM
amplitude - the share of MGH patients flagged by the Montreal criteria ranged from 13%
to 47%, and by SINBAR from 45% to 91%: a larger effect than age, sex or sleep apnoea.
Low references (the minimum, or the 5th or 10th percentile of REM amplitude) separated
RBD from other patients best, and references near the median collapsed the separation,
because the median of an RBD patient's REM EMG already contains the excess activity being
measured. The low references that work best are also the ones closest to the recording's
noise floor, so the choice of definition and the recording system act together.
Automated implementations should state their background definition explicitly, and
studies comparing methods should report sensitivity to it.

## Invariance: no method is robust to both gain and noise

The simulations expose a complementary weakness. The relative criteria divide by the
night's quiet level: they were unaffected by scaling the signal but moved strongly when
noise was added. The RAI subtracts a moving minimum before binning absolute amplitudes:
added noise barely changed it (MGH 12% to 10%), but scaling the signal to MGH's level
halved its positive calls in HMC (7% to 3%). A criterion that removes the noise floor
before comparing activity with a relative reference - for instance by estimating the
noise from the recording itself and subtracting it, as the RAI does, before dividing -
would in principle be invariant to both, and is a natural next step.

## Clinical covariates

Sleep apnoea raised the odds of a positive call by about 20% per 10 events per hour,
consistent with the known mimicry of RBD by severe obstructive sleep apnoea [Iranzo
2005]; the effect was carried entirely by REM epochs containing respiratory events or
arousals, and disappeared when those epochs were excluded. Excluding them lowered the
MGH positivity only modestly (Montreal 28% to 22%), so event contamination explains a
small part of the false-positive burden. Age was not associated with a Montreal or RAI
call, and only weakly and inversely with a SINBAR call (odds ratio 0.89 per decade),
although RWA has been reported to increase with age [Feemster 2019]; the difference may
reflect our clinical, rather than community, population.

## Cut-offs for automated scoring

Re-deriving each cut-off for automated scoring (Youden's index, RBD against patients
recorded on the same system) raised the thresholds of the relative criteria - SINBAR
"any" activity from 18.2% to 62.9%, Montreal phasic activity from 15% to 27.7% - and
reduced the external false-positive share sharply (SINBAR: MGH 76% to 10%, HMC 25% to
1%) while leave-one-out cross-validation retained 81-95% sensitivity. For the RAI the
re-derived cut-off moved the other way, trading specificity for sensitivity. These
cut-offs are not ready for use: they rest on 21 RBD patients from one centre, their
bootstrap intervals are wide, and the RBD patients' sensitivity was measured at the
same site that supplied the reference patients. They show, however, that the
published thresholds are poorly matched to automated scoring, and that recalibration on
local data is likely to be necessary before automated RWA quantification is used to
screen.

## Strengths and limitations

The analysis uses only openly licensed data and publicly available code, so every
number can be regenerated; it spans three sites on two continents and four methods, and
it tests explanations for between-site differences directly by simulation rather than
by assumption. The limitations are substantial. The only open recordings of RBD come
from CAP: 22 patients with clinical RBD at one Italian centre, in a database published
in 2001, so sensitivity estimates are imprecise and may not transfer. RBD status is unknown in MGH
and HMC; given a prevalence of about 1-2% [Haba-Rubio 2018], most - but not all -
positive calls there are false. Only chin EMG was analysed; SINBAR's recommended montage
includes the flexor digitorum superficialis, and the AASM rules also consider limb
muscles, which may improve specificity. Automated scoring does not reproduce the
judgement of a human scorer who discards artefacts, and our results describe automated
implementations of the criteria, not the criteria as scored visually. The noise we added
was white and stationary, whereas real electrode and amplifier noise is coloured and
varies through the night; the simulation shows that a noise-floor difference of the
observed size is sufficient to explain the site difference, not that it is its only
cause. Finally, the datasets do not document medication, electrode montage or amplifier
settings.

## Conclusion

Published RWA cut-offs do not transfer to automated scoring across recording sites: the
same criteria flagged 9% of patients at one hospital and 29% at another. The difference
is not explained by amplitude, storage format, sleep apnoea or age, but is reproduced by
the noise floor of the chin EMG, against which the relative criteria are, in effect,
measured - a quieter recording system flags more patients. Before automated RWA
quantification is used to find people with prodromal synucleinopathy in routine
polysomnograms, its thresholds need to account for the noise floor, and be calibrated
and reported for each site and implementation.

<!-- References to verify:
McCarter SJ et al. Sleep 2015;38:907-917 (antidepressants increase REM chin tone)
Dauvilliers Y, Jennum P, Plazzi G. Sleep Med 2013;14:775-781 (RBD/RWA in narcolepsy)
Iranzo A, Santamaria J. Sleep 2005;28:203-206 (OSA mimicking RBD)
Haba-Rubio J et al. Sleep 2018;41(2):zsx197 (RBD prevalence, HypnoLaus)
Feemster JC et al. Sleep 2019 (normative RSWA; age effect)
Cesari M et al. Sleep 2022;45(3):zsab257 (IRBDSG v-PSG guidelines)
-->
