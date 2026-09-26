# Discussion (draft)

## Principal findings

Applied through one automated pipeline to 1,177 openly available polysomnograms, the
published RWA cut-offs recognised clinical RBD - the Montreal and SINBAR criteria flagged
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
the RBD patients they caught on CAP's quieter system.

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

The account is not complete. After harmonising both cohorts to the same floor, a SINBAR gap
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
differ between centres. In Japanese patients with isolated RBD, the optimal SINBAR-type
threshold was 11.3% rather than 27.2%, and a fifth of clinically definite patients fell
below the Western cut-off; the difference was attributed to ethnic differences in EMG
activity [Sakuma 2025]. A noisier recording system would produce exactly this pattern -
lower activity percentages in patients and a lower optimal threshold - and our ladder
shows how steeply: sensitivity under the Montreal criteria fell from 90% to 57% between
floors of 0.9 and 1.5 uV. Automated chin cut-offs also differed between a laboratory
polysomnograph and a home device (6.5% vs 15.0%) [Levendowski 2025], while an open-source
algorithm validated at a new centre with the full SINBAR montage arrived at a threshold
close to the original (33.0% vs 32%) [Joza 2025]. Whether such differences reflect
populations or equipment cannot be decided unless studies report the floor against which
their thresholds were measured.

## Background is an undocumented free parameter

Visual scorers judge background EMG by eye; an automated method must turn it into a
number, and published descriptions do not say which. Across plausible choices the share of
MGH patients flagged by the Montreal criteria ranged from 13% to 47%, and by SINBAR from 45%
to 91% - a larger effect than age, sex or sleep apnoea. Low references (the minimum, or the
5th or 10th percentile of REM amplitude) separated RBD from other patients best, and
references near the median collapsed the separation, because the median of an RBD
patient's REM EMG already contains the excess being measured. The references that work best
are also those closest to the noise floor, so the definition and the recording system act
together.

## What to do about it

We tested one obvious remedy and it failed our pre-specified criterion. Harmonising every
recording to a common, higher noise floor made MGH and HMC agree under the published
cut-offs, but only by discarding sensitivity (Montreal 90% to 57%); re-deriving cut-offs on
the harmonised data to recover it pushed them so low (1.5-14%) that the two hospitals
diverged again. Re-deriving cut-offs without harmonisation reduced external false
positives substantially, but those cut-offs rest on 21 patients from one centre and were
imprecise. None of these is a portable threshold.

What the data do support is reporting. The chin EMG's quiet-REM level (in uV) and its floor
signature can be computed from any recording in seconds, and should accompany every RWA
measure and every proposed cut-off, so that thresholds can be compared, pooled or
recalibrated across systems. Methods may also be designed to be less sensitive to the
floor. The RAI, which subtracts a moving-minimum noise estimate, was the most stable across
sites (MGH 9%, HMC 7%) and nearly immune to added noise, but depends on gain: scaling the
signal to MGH's level halved its positive calls in HMC. The relative criteria have the
opposite weakness. A measure that subtracts the noise floor before comparing activity with
a relative reference would in principle be invariant to both, and is a natural next step.

## Clinical covariates

Sleep apnoea raised the odds of a positive call by about 20% per 10 events per hour,
consistent with the known mimicry of RBD by severe obstructive sleep apnoea [Iranzo 2005];
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
with clinical RBD from one Italian centre, so sensitivity estimates are imprecise and come
from a single, quiet recording system. RBD status is unknown in MGH and HMC; at a prevalence
of about 1-2% [Haba-Rubio 2018] most, but not all, positive calls there are false. Only chin
EMG was analysed; SINBAR's recommended montage adds the flexor digitorum superficialis, and
the AASM rules consider limb muscles, which may improve specificity. Automated scoring does
not reproduce a human scorer who discards artefacts, and our results concern automated
implementations of the criteria. Human scorers also judge background relative to what they
see, so the mechanism is likely to apply to visual scoring, but we did not test that. The
ladder adds white, stationary noise; it can raise a floor but not lower one, and real noise
is coloured and varies through the night. Finally, the databases do not document
medication, electrode montage or amplifier settings.

## Conclusion

Published RWA cut-offs do not transfer to automated scoring across recording sites: the
same criteria flagged 9% of patients at one hospital and 29% at another. The difference is
not explained by amplitude, storage format, sleep apnoea or age; it follows the noise floor
of the recording, against which the relative criteria are, in effect, measured. The same
mechanism makes noisier systems miss RBD. Before automated RWA quantification is used to
find people with prodromal synucleinopathy in routine polysomnograms, every threshold should
be reported together with the noise floor it was set on, and methods should be made robust
to it.

<!-- References: see references.md (verified 2026-09-26). -->
