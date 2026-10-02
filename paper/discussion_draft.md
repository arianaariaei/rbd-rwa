# Discussion (draft)

## Principal findings

Applied through one automated pipeline to 1,177 openly available polysomnograms, the
published RWA cut-offs recognized clinical RBD - the Montreal and SINBAR criteria flagged
91% and 95% of CAP's RBD patients - but also flagged a large, and strongly site-dependent,
share of patients in whom RBD was not suspected: 29% (Montreal) and 76% (SINBAR) of MGH
patients against 9% and 25% of HMC patients, with CAP's patients with other sleep
disorders behaving like MGH. The methods disagreed on most nights where false positives
were common (70% of MGH nights). In a screening setting these rates imply positive
predictive values of 3-11% at an RBD prevalence of 2%.

The difference between the hospitals was reproduced by one property of the recording, the
noise floor of the chin EMG. Adding noise to MGH recordings until their quiet-REM level
matched HMC's lowered MGH's positivity to HMC's, every change in the same direction; along
a pre-specified dose-response, MGH's curve passed through HMC's own point; and HMC's
system was noisier on an EEG channel as well. The same mechanism works against
sensitivity: at an HMC-like noise floor, the Montreal criteria missed about four in ten of
the RBD patients they caught on CAP's quieter system. Once the noise was subtracted, the
three systems recorded muscle activity at the same size, and floor-corrected versions of
the criteria, specified in advance, no longer depended on the noise floor and gave the same
answer at both hospitals.

The effect is large in the units Parkinson's disease research uses. On the same RBD
nights, HMC's noise floor lowered tonic RWA by two-thirds of the difference that predicted
later Parkinson's disease, and RBDtector, the open-source scorer built for this field,
inherited the dependence when run unchanged; floor correction removed it from both, with
one exception among the pre-specified tests, in patients without RBD.

## Why the same criteria give different answers at different sites

The Montreal, SINBAR and AASM criteria judge muscle activity against a background: activity
counts when it exceeds a multiple of the quietest EMG of the night. In a well-atonic REM
period that quietest EMG is largely the noise of the electrodes and amplifier, so the
thresholds are, in effect, multiples of the recording system's noise floor. A quieter
system lowers them and lets the small twitches that occur in everyone's REM sleep count as
RWA; a noisier one raises them and hides part of a patient's abnormal activity.

Four lines of evidence support this reading. First, the storage format and the amplitude of
the signal did not matter: scaling HMC's signals to MGH's much lower level, or storing them
as MGH does (200 Hz, 1-uV steps), left the relative criteria unchanged. Second, raising the
noise floor did: adding noise to 300 MGH recordings changed 65 nights under the Montreal
criteria and 131 under SINBAR, all from positive to negative. Third, the effect followed a
dose-response on which MGH and HMC fell on the same curve - read at HMC's quiet-REM level,
MGH would be flagged at 8.9% (Montreal; HMC 8.8%) and 29% (SINBAR; HMC 25%). Fourth, the
difference is a property of the recording system, not of the chin alone: HMC's central EEG
had a 40-90 Hz floor twice MGH's, and in HMC the quietest NREM and REM chin levels were
indistinguishable (ratio 1.08), the signature of a floor set by noise rather than by
muscle, which MGH's recordings acquired when noise was added.

The account is not complete. After harmonizing both cohorts to the same floor, a SINBAR gap
of 5.5 points remained (from 58), just above the threshold we had fixed in advance, and REM
periods' first and last epochs carried about 4 of the 20 Montreal points - both consistent
with smaller contributions from what the open datasets do not document: electrode type and
placement, amplifier filters, scoring conventions and the patients' medication.
Serotonergic antidepressants, common in sleep-clinic populations, increase REM chin tone in
people without RBD [McCarter 2015; Ahdab 2026], and narcolepsy, part of CAP's patient
group, is itself associated with RWA [Dauvilliers 2013].

Within a single cohort the relationship runs the other way - nights with a higher quiet-REM
level were flagged slightly more often by the Montreal criteria - because there the level
also carries genuine muscle tone: CAP's RBD patients had higher quiet-REM levels than other
patients recorded on the same system. Across sites the floor is set by the equipment,
within a site by the patient.

## Both kinds of error, and the debate about local cut-offs

Because the thresholds follow the floor, a single published cut-off produces a different
operating point on every recording system: false positives on quiet systems, missed RBD on
noisy ones. This offers a testable explanation for recent reports that optimal thresholds
differ between centers. In Japanese patients with isolated RBD, the optimal SINBAR-type
threshold was 11.3% rather than 27.2%, and a fifth of clinically definite patients fell
below the Western cut-off; the difference was attributed to ethnic differences in EMG
activity [Sakuma 2025]. A noisier recording system would produce exactly this pattern -
lower activity percentages in patients and a lower optimal threshold - and our ladder
shows how steeply: sensitivity under the Montreal criteria fell from 90% to 57% between
floors of 0.9 and 1.5 uV. Automated chin cut-offs also differed between a laboratory
polysomnograph and a home device (6.5% vs 15.0%) [Levendowski 2025], while an open-source
algorithm validated at a new center with the full SINBAR montage arrived at a threshold
close to the original (33.0% vs 32%) [Joza 2025]. Whether such differences reflect
populations or equipment cannot be decided unless studies report the floor against which
their thresholds were measured.

## On systems not used to find the effect

The external cohorts turned the mechanism into a prediction about people who should not be
flagged at all. On the quietest recording system in the study, BOAS's Micromed (floor
0.37 uV), the published SINBAR chin criterion flagged 91% of healthy volunteers from the
general population, and the Montreal criteria 41% - exactly what a threshold set at twice a
very low noise floor predicts, and not an artifact of the heartbeat that system could not
remove. A second healthy cohort, on a different and somewhat noisier system, was flagged at
84% and 20%. Floor correction brought the two healthy cohorts together (a 21-point
difference under the Montreal criteria became 3 points) and, across all six groups without
RBD, removed the dependence of positivity on the floor of the recording system (Spearman rho
-0.83 published, +0.43 corrected), leaving healthy volunteers below patients, as they
should be. The mechanism also predicted numbers, not only directions: DOD-O's sleep-clinic
patients at Stanford, on a system not used before, were flagged within 10 points of what
MGH's noise ladder predicted for their floor. Four of the twelve checks were narrowly
missed - the healthy cohorts' lower muscle tone (0.65 times MGH's, against the 0.67 we had
set) and 11-12% of healthy nights above the re-derived SINBAR-FC cut-off (against 10%) -
and these belong in the paper as they are: the re-derived cut-off is about 88% specific in
healthy adults, not 90%. Together, three new systems reproduced the central claim, that the
published criteria measure the recording system as much as the patient, more strikingly
than the cohorts in which it was found: nine in ten healthy volunteers on a quiet system
would meet the published SINBAR chin criterion for RBD.

## Background is an undocumented free parameter

Visual scorers judge background EMG by eye; an automated method must turn it into a
number, and published descriptions do not say which. Across plausible choices the share of
MGH patients flagged by the Montreal criteria ranged from 13% to 47%, and by SINBAR from 45%
to 91% - a larger effect than age, sex or sleep apnea. Low references (the minimum, or the
5th or 10th percentile of REM amplitude) separated RBD from other patients best, and
references near the median collapsed the separation, because the median of an RBD
patient's REM EMG already contains the excess being measured. The references that work best
are also those closest to the noise floor, so the definition and the recording system act
together.

## What to do about it

We tested two remedies, each with criteria fixed in advance. Harmonizing every recording to
a common, higher noise floor made MGH and HMC agree under the published cut-offs, but only
by discarding sensitivity (Montreal 90% to 57%); re-deriving cut-offs on the harmonized data
to recover it pushed them so low (1.5-14%) that the two hospitals diverged again. Adding
noise throws information away; the second remedy removes noise instead.

The floor-corrected rules ask, on every recording, for the muscle activity the published
rule asks for on a system with a 1-uV background: the night's own noise is subtracted in
power rather than multiplied. Nothing else about the criteria changes, and the correction
needs nothing but the recording itself. It worked on both counts that matter. On the same
nights, raising the noise floor to HMC's no longer changed the verdict (Montreal-FC: none of
280 MGH nights changed; RBD sensitivity unchanged), and between hospitals the gap closed
(Montreal +20.5 to +1.6 points; SINBAR +51.0 to +2.4). The correction is legitimate only
if sites record muscle activity on the same scale, and they did: with the noise removed,
MGH, HMC and CAP had the same N2/N3 and REM chin levels to within 10%. What differed between
the hospitals was noise, and once it was subtracted the hospitals agreed.

Two qualifications follow from the pre-specified criteria. First, Montreal-FC at the primary
reference kept 81% sensitivity, below the 85% we had required; the reference background
sets the operating point (B = 0.75 uV kept 95% sensitivity with a 4.5-point gap), so a lower
reference may suit the Montreal criteria, but that choice was made after seeing the data and
needs confirmation elsewhere. Second, correcting the floor does not make a cut-off specific.
At the published chin cut-off of 18.2%, SINBAR-FC still flagged 45% of patients - now at
both hospitals. A cut-off re-derived for automated SINBAR-FC scoring (49% of mini-epochs)
flagged 13% and 14% of MGH and HMC patients with 86% leave-one-out sensitivity: the first
threshold in this study that transferred between hospitals, although it rests on 21 RBD
patients from one center and should be validated before use.

Why do visually derived cut-offs over-call when applied automatically, even after
correction? Our automated values in patients without RBD were three to five times those of
Frauscher's visually scored controls. A visual scorer reads chin EMG at a fixed display gain,
at which twitches of one or two microvolts are barely visible; visual scoring therefore
carries an implicit absolute detection limit that an automated relative rule lacks. The
floor-corrected rule restores an explicit one. This explanation is a hypothesis; it could be
tested by scoring the same nights visually at several display gains.

Floor correction also explains why the choice of reference matters as it does. For a rule
with multiplier k, noise-invariance on a system with background b requires
sqrt((b/0.91)^2 + (k^2 - 1) B^2) >= 1.5 b, that is B >= 0.59 b for SINBAR's k = 2. At HMC's
upper-quartile floor (1.8 uV) this means B >= 1.05 uV: a SINBAR-FC rule with a smaller
reference cannot be read the same way on HMC's system, which is what we saw at B = 0.5 uV
(site gap +25 points). The reference must be at least about 0.6 times the noisiest floor
among the systems to be compared, and a system's floor therefore limits the smallest RWA it
can detect in the same way as it does for any other measurement.

The correction has limits of its own. Its constants were set on simulated white noise at
200-512 Hz; on CAP's old 128-Hz system, where healthy volunteers had floors of 2.5-3.7 uV,
it turned three of them positive that the published Montreal rule had not. Below the AASM
minimum of 200 Hz, and above a floor of about 1.7 times the reference (1.7 uV for
B = 1.0 uV), small activity cannot be separated from noise reliably, and floor-corrected
scores should not be read. Real noise is also not perfectly white or stationary.

What the data support in practice is a short calibration report with every RWA measure and
every proposed cut-off: the chin EMG's quiet-REM level (its noise) and its net N2/N3 level
(its gain), both computable from any recording in seconds, together with the floor-corrected
reference used. The RAI, which subtracts a moving-minimum noise estimate, was also stable
across sites (MGH 9%, HMC 7%) and nearly immune to added noise but, like any absolute
measure, depends on gain.

## What this means for Parkinson's disease research

Parkinson's disease research uses the amount of RWA, not only its presence: to estimate
who will convert [Postuma 2010], to follow progression [Iranzo 2009], to define isolated
RWA as a possible earlier stage [Ferri 2026; Dodet 2024], and, in multi-center prodromal
cohorts, to pool patients recorded on different systems. Our results suggest that in each
of these uses the recording system is a hidden variable, and in the first two one of the
same size as the effects studied. On the same RBD nights, the difference in noise floor between two real hospital
systems moved the published tonic percentage by two-thirds of the baseline difference
that predicted Parkinson's disease, and by four and a half years of its reported
progression. In multi-center cohorts, part of the between-patient variation in RWA may
therefore reflect where a patient was recorded; adjusting for center absorbs this only if
each center's floor is stable and unrelated to outcome. In longitudinal studies, a change
of amplifier or electrodes during follow-up could appear as progression or as regression:
a rise of 0.6 uV in the floor lowered tonic RWA as much as four and a half years of the
reported progression would raise it. We could not measure
this in people with Parkinson's disease, because no such recordings are openly available,
but nothing in the mechanism is specific to the patients we had: it is a property of the
measurement.

RBDtector, the open-source scorer developed for this field, inherits the dependence,
because its baseline is, in effect, the noise floor (1.14 times ours). Its verdicts in
established RBD were robust, since those patients lie far above its cut-off, but its
continuous percentages were not, and in people without RBD its verdict largely followed
the recording system: 89% of healthy volunteers on the quietest system, 20% of patients on
the noisiest. Replacing its baseline with the floor-corrected one, a change that leaves
the rest of the program untouched, kept its percentages in RBD within a point at a noisier
floor and closed a 45-point gap between hospitals. It did not fully hold for patients
without RBD in the noisier half of the correction's range, where 6 of 51 nights turned
positive at HMC's floor. Noise alone explains little of this: in simulated noise, the corrected
RBDtector counted activity in only 0.4% of REM mini-epochs at that floor, about a seventh of
the rise. More likely, noise lifted small muscle activity just below the threshold over it
more often than it pushed larger activity under it. Small activity is far more common in
REM without RBD than large, and RBDtector judges 30-ms chunks of about eight samples, over
which the RMS of noise varies far more than over the 1-s windows our own rules use; we did
not test this explanation. Correcting a detector this fine may require allowing for the
spread of the noise as well as its mean. For RBDtector's users, the practical points are to
report each recording's floor with its output and not to expect its chin cut-off to
transfer between systems unchanged.

For isolated RWA, the definition matters more than for RBD. DREAMER's RAI-based definition
was the most stable we tested: it labeled 8-17% of nights without RBD on every system and
hardly moved with added noise, consistent with the RAI's own subtraction of a noise
estimate. The relative criteria would have labeled between 9% and 96% of comparable people
depending on the system, a range wide enough to decide by itself how common an "earlier
stage" appears. Because the RAI depends on gain, multi-center studies of isolated RWA
should still report the floor and net NREM tone that the floor check provides.

For recruitment into prevention trials the numbers are sobering but usable. At an RBD
prevalence of 2% among people aged 50 or over, the published SINBAR chin rule would
require about 39 sleep studies to be reviewed per patient with RBD found, RBDtector about
37, and the best rule we tested, the SINBAR-FC cut-off re-derived on CAP, about 8.
Automated RWA scoring of routine polysomnograms is therefore better used as a pre-filter
for clinical and video review than as a case-finding test, and its yield will depend on the
recording system unless the floor is taken into account. The same caution applies where a
polysomnogram showing RWA carries diagnostic weight, as an indicative biomarker of dementia
with Lewy bodies [McKeith 2017].

None of this needs new data. Each recording's floor can be measured in seconds (the floor
check is provided as a tool); thresholds can be set against it rather than in multiples of
it; and multi-center and longitudinal analyses can check that floors do not differ between
the groups compared or change during follow-up.

## Clinical covariates

Sleep apnea raised the odds of a positive call by about 20% per 10 events per hour,
consistent with the known mimicry of RBD by severe obstructive sleep apnea [Iranzo 2005];
the effect was carried entirely by REM epochs containing respiratory events or arousals and
disappeared when those epochs were excluded, which lowered MGH's positivity only modestly
(Montreal 28% to 22%). Age was not associated with a Montreal or RAI call and only weakly
and inversely with a SINBAR call (odds ratio 0.89 per decade), although RWA has been
reported to increase with age [Feemster 2019]; our population was clinical, not community.

## Strengths and limitations

Only openly licensed data and public code were used, so every number can be regenerated;
three sites on two continents and four methods were compared; explanations were tested by
simulation rather than assumed, and the main simulation and its decision criteria were
fixed before it was run. Our automated scoring reproduced published values in RBD (SINBAR
"any" 73% vs 67% [Frauscher 2012]).

The limitations are substantial. The only open recordings of RBD are CAP's: 22 patients
with clinical RBD from one Italian center, so sensitivity estimates are imprecise and come
from a single, quiet recording system. These patients had established RBD, whose diagnosis
itself rests on polysomnographic RWA; sensitivity is therefore optimistic for the milder,
prodromal cases a screening program would seek, and the positive predictive values we
report are upper bounds. They were also older (71 years) than most patients recorded on the
same system (mostly epilepsy patients around 30 years), so discrimination within CAP is
flattered by age; against same-system patients aged 50 or over, discrimination held
(AUC 0.81-0.88) but patients without RBD were flagged more often (Montreal 44% against 29%).
Scorers may leave the most active REM epochs of RBD patients unscored as REM, which would
dilute RWA in exactly the nights that define sensitivity. RBD status is unknown in MGH and HMC; at a prevalence
of about 1-2% [Haba-Rubio 2018] most, but not all, positive calls there are false. Only chin
EMG was analyzed; SINBAR's recommended montage adds the flexor digitorum superficialis, and
the AASM rules consider limb muscles, which may improve specificity. Automated scoring does
not reproduce a human scorer who discards artifacts, and our results concern automated
implementations of the criteria. Human scorers also judge background relative to what they
see, so the mechanism is likely to apply to visual scoring, but we did not test that. The
ladder adds white, stationary noise; it can raise a floor but not lower one, and real noise
is colored and varies through the night. Finally, the databases do not document
medication, electrode montage or amplifier settings.

The Parkinson's analyses have limitations of their own. No recordings of people with
Parkinson's disease are openly available, so the effects were measured in isolated RBD,
in patients with other sleep disorders and in healthy adults, and compared with
benchmarks from cohorts recorded on other equipment; the comparison concerns scale, and
does not suggest those findings are artifacts. RBDtector was run on chin EMG alone,
without the arousal, snoring and artifact annotations its published cut-off assumes, which
may raise its absolute percentages but cannot explain changes on the same nights. Its
MGH estimates rest on a random 100 of the 925 nights. The one missed prediction was
examined only in simulated noise, after the result was known, and the explanation offered
for it remains untested.

## Conclusion

Published RWA cut-offs do not transfer to automated scoring across recording sites: the
same criteria flagged 9% of patients at one hospital and 29% at another. The difference is
not explained by amplitude, storage format, sleep apnea or age; it follows the noise floor
of the recording, against which the relative criteria are, in effect, measured. The same
mechanism makes noisier systems miss RBD. Subtracting each recording's own noise floor, a
correction that needs nothing but the recording, removed both effects in a pre-specified
test. Before automated RWA quantification is used to find people with prodromal
synucleinopathy in routine polysomnograms, or pooled across the centers of multi-site
cohorts, thresholds should be defined against the noise floor rather than in multiples of
it, and reported with the floor and reference on which they were set. The same applies
when the amount of RWA is used to predict or follow Parkinson's disease: on the same
nights, the recording system alone moved it by two-thirds of the difference that
predicted the disease.

<!-- References: see references.md (verified 2026-09-26). -->
