<!-- Snapshot of the Claude Doc, exported 2026-10-04 (figures are submitted as separate files; see Figure legends). -->

## Title page

**Title:** The recording system's noise floor drives automated scoring of REM sleep without atonia: four pre-specified analyses of 1,354 open polysomnograms

**Authors:** Ariana Ariaei¹ \[add co-authors and supervisor as agreed\]

¹ \[Department, University, City, Country\]

**Corresponding author:** \[name, postal address, email\]

**Article type:** Original Article

**Target journal:** SLEEP (Oxford University Press), formatted to its [instructions for original articles](https://academic.oup.com/sleep/pages/General_Instructions): structured abstract of at most 250 words, Statement of Significance of at most 120 words, 3-10 keywords, no running title, data availability and disclosure statements, and AI use disclosed in the Methods or Acknowledgements and in the cover letter. Alternatives with a matching scope: Sleep Medicine, Journal of Sleep Research, Clinical Neurophysiology.

**Counts:** main text about 6,800 words (Introduction to Conclusions; tables, legends and references excluded); abstract 248 words; Statement of Significance 119 words; 38 references; 4 tables; 6 figures; Supplementary material with 12 tables and 5 figures.

## Statement of Significance

Automated scoring of REM sleep without atonia (RWA) could find people at risk of Parkinson's disease in routine sleep studies and pool patients across centers. In four pre-specified analyses of open recordings, we show that the published criteria measure chin activity against a multiple of the recording system's noise floor. Consequently, the Montreal criteria flagged 9% of patients at one hospital and 29% at another, SINBAR flagged 91% of healthy volunteers on quiet equipment, and tonic RWA on the same nights shifted by two-thirds of the difference that predicted Parkinson's disease. Subtracting each recording's noise floor removed these effects. Thresholds should be set against, and reported with, the noise floor; confirming this in Parkinson's disease is the next step.

## Abstract

**Study Objectives:** Automated scoring of REM sleep without atonia (RWA) could find prodromal synucleinopathy in routine polysomnograms. We asked whether published RWA cut-offs transfer across recording systems, and what this means for Parkinson's disease research.

**Methods:** Montreal, SINBAR (chin), AASM and REM Atonia Index criteria were applied by one open pipeline to 1,177 polysomnograms from three open databases (CAP, including 22 RBD patients; HMC, n=147; MGH, n=925). Four analyses were pre-specified: a noise ladder; floor-corrected criteria, subtracting each recording's noise rather than multiplying it; three further systems (177 nights); and effects on continuous RWA and the open-source RBDtector.

**Results:** Published cut-offs flagged 29% (Montreal) and 76% (SINBAR) of MGH patients but 9% and 25% at HMC. Format, amplitude, apnea and age did not explain the gap; raising MGH's noise floor to HMC's reproduced it, and noisier floors cost RBD sensitivity (Montreal 90% to 57%). Floor-corrected criteria resisted added noise, closed the gap (Montreal +20.5 to +1.6 points; SINBAR +51.0 to +2.4) and kept SINBAR sensitivity at 95%. On quiet new systems, published SINBAR flagged 91% and 84% of healthy volunteers; floor-corrected, 35% and 32%. Raising RBD nights to HMC's floor lowered tonic RWA by 21 points, two-thirds of the difference that predicted Parkinson's disease (floor-corrected: 1 point); RBDtector flagged 89% of the quietest system's healthy volunteers.

**Conclusions:** Background-relative RWA criteria measure the recording's noise floor as much as the patient, enough to confound Parkinson's disease research. Thresholds should be defined against the noise floor, not in multiples of it, and reported with it.

**Keywords:** REM sleep behavior disorder; REM sleep without atonia; polysomnography; electromyography; automated scoring; noise floor; multi-center studies; Parkinson's disease; prodromal synucleinopathy; reproducibility

## Introduction

Isolated REM sleep behavior disorder (RBD) is the strongest known prodromal marker of the alpha-synucleinopathies: in an international multicenter cohort of 1,280 patients, 73.5% developed Parkinson's disease, dementia with Lewy bodies or multiple system atrophy within 12 years \[1\]. People with RBD are therefore the natural population for disease-modifying prevention trials, and there is growing interest in finding them at scale, for example by screening polysomnograms recorded for other reasons \[2\].

The diagnosis rests on REM sleep without atonia (RWA), the loss of the normal muscle atonia of REM sleep, documented by video-polysomnography \[3\]. RWA is quantified from chin and, in some schemes, limb electromyography (EMG), and several scoring methods with diagnostic cut-offs exist: the Montreal method \[4\], the SINBAR method \[5\], the scoring rules of the American Academy of Sleep Medicine (AASM) \[6\] and the REM Atonia Index (RAI) \[7,8\]. Each was developed in one or a few centers, largely by visual scoring, and the visual methods define muscle activity relative to a "background" EMG level that the scorer judges by eye. Automated implementations now make these methods applicable to thousands of recordings \[9-11\], and normative values in adults without RBD have been reported from a single center \[12\].

Before automated RWA scores are compared across sites, a question must be answered that single-center validation cannot: does a published cut-off mean the same thing on every recording system? There are signs that it does not. Visually and automatically derived thresholds differ \[13\]; optimal thresholds in Japanese patients were less than half the Western ones \[14,15\]; and automated cut-offs differed between laboratory and home recordings \[16\]. Meanwhile, multi-center prodromal cohorts pool RWA measured in different laboratories \[17,18\]. The candidate explanations (population, ethnicity, scoring practice, equipment) have not been separated, because no study has compared the criteria across recording systems on shared data.

The question matters beyond diagnosis. Parkinson's disease research uses the amount of RWA as a continuous marker: baseline tonic chin RWA was 31.9 percentage points higher in RBD patients who later developed Parkinson's disease than in those who remained disease-free \[19\]; it rose by about 4.8 points per year in isolated RBD \[20\]; RWA without RBD is followed as a possible earlier stage \[18\] and separates subgroups of early Parkinson's disease \[21\]; and polysomnographic RWA is an indicative biomarker of dementia with Lewy bodies \[22\]. Each use assumes that an RWA percentage means the same on every recording system.

Here we applied four published methods, through one open and fully automated pipeline, to openly available polysomnograms from three databases: CAP, which holds the only open recordings of patients with RBD; a Dutch clinical cohort (HMC); and a US clinical cohort (MGH). The published cut-offs flagged very different shares of patients at the two hospitals, and re-making recordings in software traced the difference to one property of the recording system, its noise floor. Four analyses were then fixed in advance and committed to the project repository before they were run: a noise ladder that adds noise to the same nights in steps; floor-corrected versions of the criteria that subtract each recording's noise instead of multiplying it; a test on three recording systems not used to find the effect; and the consequences for Parkinson's disease research, including the open-source scorer RBDtector \[10,11\] run unchanged. Every dataset is public and all code will be released with the paper, so every number can be regenerated.

## Methods

### Study design and cohorts

This retrospective study analyzed pre-existing, openly licensed polysomnography (PSG) databases that require no application or data-use agreement (Table 1). All recordings were de-identified by their providers, and the study involved no contact with participants. It is reported following STARD 2015 \[23\] (Supplementary Table S12).

CAP (CAP Sleep Database \[24\], distributed by PhysioNet \[25\]) supplied the positive class: 22 patients with clinically diagnosed RBD recorded in Parma, Italy. Twenty-one of them, and 51 patients with other sleep disorders (nocturnal frontal lobe epilepsy, periodic limb movements, insomnia, narcolepsy), were recorded on the database's main system (chin EMG at 512 Hz in microvolts). These "same-system patients" are the primary comparison group, because a comparison across systems would confound disease with equipment. CAP's 15 healthy volunteers were recorded on several other systems and are reported separately. Two clinical cohorts supplied reference populations in which RBD is not labeled: HMC (Haaglanden Medisch Centrum sleep staging database, version 1.1; 151 PSGs of patients referred with a range of sleep complaints, the Netherlands \[26,27\]) and MGH (training set of the PhysioNet/Computing in Cardiology Challenge 2018; 994 PSGs from the Massachusetts General Hospital sleep laboratory, USA \[28\]). Three further cohorts were used only for the pre-specified external test.

CAP does not state how RBD was diagnosed. Because a clinical diagnosis of RBD requires polysomnographic RWA and these patients had established disease, sensitivity estimates are subject to incorporation and spectrum bias and are upper bounds for a screening population. Ages and sexes came from CAP's spreadsheet and from MGH's records; HMC publishes only group summaries.

### Signal processing

Recordings were streamed from the public repositories, processed in the cloud and discarded; only derived envelopes were kept. Each signal was read at its native sampling rate. The chin EMG was band-pass filtered between 10 and 100 Hz (fourth-order zero-phase Butterworth; upper edge 5 Hz below Nyquist where lower), with notch filters at the local mains frequency and its harmonics. Cardiac artifact was removed by subtracting a median heartbeat template (-100 to +150 ms around ECG R-peaks, re-estimated in 5-min blocks); its removal was checked with a heartbeat-locked amplitude ratio (1.0 = no artifact). The filtered signal was reduced to root-mean-square (RMS) and mean-rectified amplitude in 20-ms bins, from which all criteria were computed.

### Sleep stages, events and inclusion

Sleep stages came from each database's expert scoring in 30-s epochs (Rechtschaffen and Kales in CAP, AASM elsewhere). In MGH, REM epochs overlapping a scored respiratory event or arousal were flagged for a sensitivity analysis. Nights with less than 10 min of REM sleep were excluded. Of 1,253 recordings, one had no chin EMG, three HMC recordings had been withdrawn by the providers for erroneous signals, and 72 had less than 10 min of REM sleep, leaving 1,177 nights: CAP 105, MGH 925 and HMC 147 (participant flow in Supplementary Figure S1).

### RWA criteria and the noise floor

Four published methods were implemented on the same REM epochs (Table 2): the Montreal criteria (tonic activity in at least 30% of 20-s epochs or phasic activity in at least 15% of 2-s mini-epochs \[4\]); the SINBAR chin criterion ("any" activity in at least 18.2% of 3-s mini-epochs \[5\]); the AASM rules, for which no cut-off is published \[6\]; and the RAI (below 0.8 \[7,8\]). Absolute criteria (the 10-µV tonic alternative and the RAI) were applied only to recordings stored in physical units.

The visual methods count activity above a multiple k of the background EMG (k = 2 for tonic and SINBAR activity, k = 4 for Montreal phasic bursts). We operationalized the background as the 5th percentile of 1-s RMS amplitudes in REM sleep and call it the night's quiet-REM level, b. In a night with intact atonia the quietest seconds of chin EMG contain little muscle activity, so b is set mainly by the noise of the electrodes and amplifier; we therefore also call b the recording's noise floor. Five alternative definitions of background were examined in a sensitivity analysis (Supplementary Table S5).

### Re-recording in software and other mechanism checks (exploratory)

To isolate which property of a recording drives its verdicts, every HMC recording was re-made in MGH's storage format: quantized to MGH's 1-µV steps, and additionally resampled to 200 Hz. Both were repeated after first scaling HMC by 0.39, which places it at MGH's median quiet-REM level relative to the storage step. In the reverse direction, white Gaussian noise (SD 1.5 µV, seeded by record name) was added to the chin EMG of the first 300 MGH records, raising their expected quiet-REM level to HMC's. Each copy was processed exactly like the original cohorts and compared with the same nights as recorded.

As evidence of system noise from a channel other than the chin, we measured the 40-90 Hz floor (5th percentile of 1-s RMS) of a central EEG derivation in N2/N3. As a signature of a floor set by noise rather than muscle, we computed the ratio of the quietest N2/N3 to the quietest REM chin level, which approaches 1 when noise sets both. Further exploratory analyses (definition of background; removal of transitional REM epochs and of epochs with respiratory events or arousals; age; residual heartbeat) are described in Supplementary Section S2.

### Pre-specified analysis 1: the noise ladder

All CAP recordings in physical units, all HMC recordings and the same 300 MGH records were streamed again. Noise was added to each night's chin EMG in band, after the same filtering, at 0.5, 1.0, 1.5, 2.0 and 3.0 µV RMS, using one seeded noise track per night scaled to each level. Two further copies were harmonized: the added noise was chosen, per night, to raise the quiet-REM level to 1.5 µV (HMC's median) or 2.0 µV. Six interpretation criteria were committed to the repository before the ladder was run (commit 6d3cc6b; Supplementary Section S3). The 300 MGH records were slightly quieter than the rest of MGH (median 0.56 vs 0.61 µV), so ladder percentages for MGH run a few points high; paired same-night comparisons are unaffected.

### Pre-specified analysis 2: floor-corrected criteria

If the background is noise of RMS n, a rule "activity above k times b" demands muscle activity of only about √(k² − 1)·b on top of it, so the muscle activity a criterion demands scales with the recording system's noise floor. In the floor-corrected (FC) version of each rule, activity counts above

```latex
T = \max\left(\sqrt{n^{2} + (k^{2}-1)\,B^{2}},\; g\,b\right), \qquad n = b / 0.91
```

where n is the noise RMS implied by b (for band-limited white noise the 5th percentile of 1-s RMS values is 0.91 times the RMS, in simulation at 200, 256 and 512 Hz), B is a reference background and g = 1.5 is a guard against counting noise (in simulated noise, 0.1-s runs above 1.5 b occurred in 0.4-0.7% of 3-s mini-epochs). The rule demands of every recording the muscle activity that the published rule demands on a system whose background is B. At b = B it is within 3% of the published rule; below B it becomes an absolute threshold; above B the noise is subtracted in power instead of multiplied. Everything else, including the published percentage cut-offs, was unchanged.

B = 1.0 µV was fixed in advance as the primary reference; B from 0.5 to 2.0 µV and a "clamp" without subtraction (k·max(b, B)) were secondary. FC rules require physical units, a sampling rate of at least 200 Hz and a floor of at most B/0.59 (1.7 µV for B = 1.0 µV), above which the guard binds. The rule, its parameters and five decision criteria were committed with the analysis code before any FC result existed for MGH, HMC or the CAP patients (commit 20b9ec2; Supplementary Section S4). Because FC thresholds are partly absolute, they assume that sites record muscle activity at a comparable scale (gain). We checked this with each night's median 1-s RMS in N2/N3 and in REM after removing the noise in power (√(RMS² − n²); "net" levels); cohort ratios within 0.67-1.5 were fixed in advance as comparable.

### Pre-specified analysis 3: recording systems not used so far

Three request-free cohorts on three further recording systems were processed with the unchanged pipeline after six predictions had been committed and before any of their EMG was read (commit 48053f3; Supplementary Section S5): BOAS (100 adults from the general population without psychotropic medication; Micromed SD plus; each participant's first night \[29\]) and, from the Dreem Open Datasets \[30\], DOD-O (55 patients with suspected sleep-disordered breathing, Stanford, USA; Somnomedics Somno HD) and DOD-H (25 healthy volunteers, France; Compumedics Siesta). BOAS has no ECG channel, so heartbeats were sought on the chin EMG itself and removed only where detection passed a plausibility test.

### Pre-specified analysis 4: Parkinson's disease research and RBDtector

A fourth plan (commit 1e7acf0; Supplementary Section S6) expressed the recording system's effect in the units Parkinson's disease research uses. For the 21 CAP RBD and 51 same-system nights, the per-night change in Montreal tonic and phasic and SINBAR "any" percentages from the night as recorded to its ladder copy at HMC's quiet-REM level (1.5 µV) was compared with two benchmarks: the 31.9-point difference in baseline tonic RWA between RBD patients who later developed Parkinson's disease and those who remained disease-free (72.9% vs 41.0%) \[19\], and the rise of about 4.8 points per year in isolated RBD (30% to 54% over a mean 5 years) \[20\].

RBDtector (commit 7c9c73d \[10\]), an open-source scorer developed on patients with Parkinson's disease and RBD and validated at a second center \[11\], was run unchanged through its own controller, in the software environment its requirements specify. It counts chin activity where the RMS of 30-ms chunks exceeds twice a baseline, the lowest 30-s RMS window of each REM period; a night was positive when chin "any" activity reached 23.5%, RBDtector's own chin-only cut-off \[10\]. It was run on the CAP ladder (as recorded; +0.5, +1.0 and +2.0 µV; and at a quiet-REM level of 1.5 µV) and, as recorded, on 100 randomly drawn MGH nights, all HMC nights and the BOAS nights. In a floor-corrected variant, its baseline was replaced by T/2, with T = max(√(n² + 3B²), 1.5n), n = baseline/0.976 (the simulated ratio of its baseline to the noise RMS) and B = 1.0 µV; nothing else changed. Ten outcomes were predicted.

Descriptive analyses covered isolated RWA by DREAMER's definition (RAI below 0.85 \[18\]); the yield of screening for prevention-trial recruitment per 1,000 PSGs of people aged 50 or over, at RBD prevalences of 1%, 2% and 5%, with sensitivity from CAP RBD, false-positive rates from MGH patients aged 50 or over and a 12-year conversion rate of 73.5% \[1\]; and a per-system floor check (the floor, the share of nights within the FC rule's range, the net N2/N3 level as a gain check, and the muscle activity the published threshold demands). The floor check is also provided as a tool for any EDF recording. After one prediction failed, RBDtector was additionally run on simulated noise alone (exploratory).

### Statistical analysis

Shares flagged positive are given with 95% Wilson intervals. For CAP RBD they are sensitivities; for groups without RBD they are false-positive rates, which in clinical cohorts are upper bounds because undiagnosed RBD is possible. Discrimination between CAP RBD and same-system patients was summarized by the area under the ROC curve (AUC), and agreement between methods by Cohen's kappa. In MGH, associations of age, sex and the apnea-hypopnea index (AHI) with a positive call were estimated by logistic regression. Paired comparisons of the same nights used exact McNemar tests with Wald intervals for the difference; mean per-night changes used bootstrap intervals (2,000 resamples). Cut-offs re-derived for automated scoring maximized Youden's index for CAP RBD versus same-system patients and were assessed by leave-one-out cross-validation and 2,000 bootstrap re-derivations. Rank correlations are Spearman's. Positive predictive values combined sensitivity from CAP RBD with false-positive rates from the clinical cohorts. No adjustment was made for multiple comparisons: pre-specified criteria were judged on point estimates as fixed in advance, and the remaining analyses are descriptive or exploratory.

Each analysis is labeled as pre-specified, with the commit that fixed it, or exploratory, and every pre-specified criterion is reported as met or not met whatever the result. Analyses used Python 3 with NumPy, SciPy, pandas, statsmodels, wfdb, pyEDFlib and matplotlib.

### Reproducibility

The pipeline runs end-to-end from a single Google Colab notebook that streams the public data, so every number in this paper can be regenerated without local installation. The four analysis plans, the code that ran them and their commit history are in the project repository (see Data Availability).

## Results

### The same criteria give different answers at different hospitals

Table 1 describes the 1,177 development nights and the 177 external nights. MGH patients were 55 years old on average (67% men); CAP's RBD patients were 71 (86% men).

Of the 21 RBD patients recorded on CAP's main system, the published Montreal and SINBAR cut-offs flagged 19 and 20 (90% \[95% CI 71-97\] and 95% \[77-99\]) and the RAI 12 (57% \[37-76\]) (Figure 1; Table 3). The same cut-offs flagged many patients without RBD, at rates that depended on the hospital more than on the method: the Montreal criteria flagged 29% \[27-32\] of MGH and 9% \[5-15\] of HMC patients, SINBAR 76% \[73-79\] and 25% \[19-33\], and the RAI 9% \[7-11\] and 7% \[4-13\]. CAP's same-system patients were flagged at 33% (Montreal) and 75% (SINBAR) (Supplementary Table S1). Where positive calls were common the methods disagreed: on 70% of MGH nights (Cohen's kappa 0.04-0.34) against 22% of HMC nights (Supplementary Table S2). At an RBD prevalence of 2%, the positive predictive value of the Montreal criteria would be 6% with MGH's false-positive rate and 17% with HMC's; for SINBAR, 2% and 7%.

### Neither storage format, amplitude, apnea, age nor heartbeat explains the difference

The quiet-REM level differed 2.6-fold between the hospitals: 0.59 µV \[IQR 0.47-0.77\] in MGH, below the 1-µV step in which MGH stores the signal, and 1.52 µV \[1.23-1.79\] in HMC (Figure 2A). Re-making HMC in MGH's storage format did not reproduce MGH's positivity (Figure 2B; Supplementary Table S4). Quantized to 1-µV steps and resampled to 200 Hz, HMC was flagged at 9% (Montreal), 22% (SINBAR) and 7% (RAI). Scaling HMC to MGH's quiet-REM level left the relative criteria unchanged (Montreal 8%, SINBAR 25%), because every threshold is a multiple of the night's own level, and lowered the RAI from 7% to 3%, as expected for an index built on absolute amplitude; quantizing the scaled signal changed little (8%, 20% and 3%).

Clinical covariates explained little (Supplementary Table S3). In MGH, each additional 10 apnea-hypopnea events per hour raised the odds of a positive call by 16-21% (Montreal odds ratio 1.16 \[1.05-1.28\]), but the gradient disappeared when REM epochs containing a scored respiratory event or arousal were excluded, and in event-free REM MGH patients without sleep apnea (AHI below 5) were still flagged at 21% (Montreal) and 65% (SINBAR). Age was not associated with a Montreal or RAI call. After template subtraction the heartbeat-locked ratio fell to 1.08 in MGH and 1.01 in HMC, and MGH nights with more residual artifact were not flagged more often by the Montreal or RAI criteria (SINBAR: 75%, 70% and 84% across tertiles of residual artifact). The operational definition of background mattered more than any covariate, moving MGH positivity from 13% to 47% (Montreal) and from 45% to 91% (SINBAR), but MGH stayed above HMC under every definition (Supplementary Figure S2).

### A higher noise floor turns MGH into HMC

Adding noise reproduced the difference. On the 277 MGH nights with at least 10 min of REM sleep, raising the quiet-REM level from 0.56 to 1.37 µV (HMC 1.52 µV) lowered the share flagged by the Montreal criteria from 34% to 10% (-23.5 percentage points \[-28.5 to -18.5\]; 65 nights changed, all from positive to negative; McNemar p = 5 × 10⁻²⁰) and by SINBAR from 83% to 36% (-47.3 \[-53.2 to -41.4\]; 131 nights changed, all from positive to negative), close to HMC's 9% and 25% (Figure 2B). The RAI, which subtracts its own noise estimate, barely moved (12% to 10%). The noisy nights also took on HMC's floor signature: the ratio of the quietest NREM to the quietest REM chin level fell from 1.20 to 1.08, HMC's value. The difference between the systems was not confined to the chin: the 40-90 Hz floor of a central EEG channel was 0.46 µV \[0.41-0.82\] in HMC, twice MGH's 0.23 µV \[0.22-0.25\] (CAP 0.16 µV). Within a cohort the relationship differed, because there a night's quiet-REM level also carries genuine muscle tone: in MGH, nights with a lower level were flagged less often by the Montreal criteria (odds ratio 0.64 per halving \[0.55-0.75\]; Supplementary Figure S4).

### The noise ladder: a dose-response, and missed RBD (pre-specified)

As noise was added in steps to the same nights, the share flagged fell steadily in every group without RBD (Figure 3; Supplementary Table S7): in MGH from 34% to 6% (Montreal) and from 83% to 13% (SINBAR) as the quiet-REM level rose from 0.56 to 2.84 µV. Read at HMC's own level, MGH's curve gave 8.9% under the Montreal criteria (HMC 8.8%) and 29.2% under SINBAR (HMC 25.2%). Harmonized to a quiet-REM level of 2.0 µV, MGH and HMC differed by 0.8 points under the Montreal criteria (25.1 as recorded on these nights) and by 5.5 under SINBAR (57.9), just above the 5-point criterion. The same mechanism cost sensitivity: CAP's RBD patients were flagged by the Montreal criteria on 90% of nights as recorded (0.86 µV), 57% at an HMC-like 1.5 µV and 19% at 3.0 µV, while SINBAR held at 95% up to 1.7 µV. Harmonizing every recording to a common floor and re-deriving the cut-offs did not give portable cut-offs, and removing the first and last epoch of each REM period narrowed the Montreal gap by 4 of its 20 points (Table 4; Supplementary Figure S5).

### Floor-corrected criteria remove the dependence on noise (pre-specified)

With the noise removed, the hospitals recorded muscle activity at the same size: the median net N2/N3 level was 1.60 µV in MGH, 1.70 µV in HMC and 1.61 µV in CAP's same-system patients (net REM medians 0.44, 0.45 and 0.39 µV), although their quiet-REM levels differed 2.6-fold. The sites differed in noise, not in gain.

The floor-corrected rules (B = 1.0 µV) removed the dependence on noise (Figure 4A-B). On the same MGH ladder nights, raising the floor to HMC's left Montreal-FC positivity unchanged (21.3%; no night changed; published 33.9% to 11.9%) and moved SINBAR-FC from 48.7% to 50.5% (published 83.0% to 33.2%). CAP RBD sensitivity did not change (Montreal-FC 81%, SINBAR-FC 95%), whereas the published Montreal criteria fell from 90% to 57%. As recorded, floor correction closed the site gap (Figure 4C; Table 3): Montreal-FC flagged 18% \[16-21\] of MGH and 16% \[11-23\] of HMC patients (difference +1.6 points, against +20.5 published), and SINBAR-FC 45% \[42-48\] and 43% \[35-51\] (+2.4, against +51.0). Subtraction mattered: a clamp that only kept the background from falling below 1.0 µV left gaps of +7.5 and +15.2 points. SINBAR-FC met all five pre-specified criteria; Montreal-FC met four, its sensitivity (81%, 17 of 21) falling short of the required 85%. From B = 1.0 to 2.0 µV, both rules stayed within 2 points along the ladder and within 6 points between sites, while sensitivity and false-positive rates fell together (Supplementary Table S8).

Floor correction did not make the published SINBAR chin cut-off specific: it flagged about 45% of patients at both hospitals. Re-derived on CAP, however, the SINBAR-FC cut-off (49.1% of mini-epochs) transferred: it flagged 13% \[10-17\] of MGH and 14% \[11-20\] of HMC patients with 86% leave-one-out sensitivity, whereas the cut-off re-derived on the published SINBAR measure flagged 10% and 1% (Supplementary Table S6). Within CAP, where RBD patients and controls share one system, floor correction changed discrimination little (AUC 0.83-0.85 against 0.84-0.85).

### Recording systems not used to find the effect (pre-specified)

On the quietest system in the study, BOAS's (median floor 0.37 µV), the published criteria flagged most healthy volunteers from the general population: SINBAR 91% \[84-95\] and Montreal 41% \[32-51\] (96% and 58% of those aged 50 or over) (Figure 5; Table 3). This was not heartbeat artifact: in the 80 BOAS nights whose REM envelope was no more periodic at the heart rate than MGH's after removal, positivity was the same (SINBAR 92%, Montreal 44%). DOD-H's healthy volunteers, on a system with a floor of 0.56 µV, were flagged at 84% \[65-94\] and 20% \[9-39\]. Floor-corrected, BOAS positivity fell to 35% \[27-45\] (SINBAR) and 15% \[9-24\] (Montreal), and DOD-H's to 32% \[17-52\] and 12% \[4-30\]; between the two healthy cohorts, the published Montreal criteria differed by 21.4 points and SINBAR by 6.9, the floor-corrected rules by 3.2 and 3.4. DOD-O's sleep-clinic patients fell where MGH's noise ladder predicted for their floor (0.82 µV), although neither the patients nor the system had been used to draw it: Montreal 30% \[20-44\] against 21% predicted, SINBAR 59% \[45-71\] against 62%.

Across the six groups without RBD, published positivity fell with the cohort's floor (Spearman ρ -0.83 for SINBAR, -0.77 for Montreal); under floor correction the relation reversed weakly (+0.43, +0.31), leaving the population rather than the system to order the groups, with healthy volunteers at 32-35% and patients at 43-51% under SINBAR-FC. Eight of the twelve pre-specified checks were met. The four misses were narrow: the healthy cohorts' net N2/N3 tone was 0.65 and 0.66 times MGH's (at least 0.67 required), and the SINBAR-FC cut-off re-derived on CAP flagged 11% \[6-19\] of BOAS and 12% \[4-30\] of DOD-H nights (at most 10% required) (Table 4).

### Consequences for Parkinson's disease research (pre-specified)

On the same 21 RBD nights, raising the quiet-REM level from 0.86 to 1.5 µV lowered published Montreal tonic RWA by 21.4 points \[13.2-29.7\], from 53.3% to 31.8% (Figure 6A). That is two-thirds of the 31.9-point baseline difference that separated RBD patients who later developed Parkinson's disease from those who remained disease-free, and the rise reported over 4.5 years of isolated RBD. Phasic activity fell by 14.3 points and SINBAR "any" activity by 20.7. Floor-corrected, the same measures moved by about one point (Montreal tonic -1.1 \[-1.7 to -0.5\]; Supplementary Table S9).

RBDtector behaved in the same way when run unchanged. Its baseline was 1.14 times our quiet-REM floor (median), and its chin "any" percentage agreed with our SINBAR measure (Spearman ρ 0.79, 418 nights). On the RBD nights its tonic percentage fell by 12.1 points \[7.3-17.0\] at 1.5 µV (38% of the Parkinson's difference) and, with the floor-corrected baseline, did not change (+0.1 \[-0.9 to +1.3\]). Its verdict on RBD held either way (20 of 21 nights flagged), because those nights lay far above its 23.5% cut-off, but on people without RBD it followed the recording system (Figure 6B-C). Published, it flagged 78% of CAP's same-system patients as recorded and 25% at 1.5 µV, 89% \[81-94\] of healthy BOAS volunteers, and 65% \[55-74\] of MGH and 20% \[15-28\] of HMC patients (difference +44.6 points); across the 397 nights without RBD, the higher a night's floor, the lower its "any" percentage (ρ -0.52 \[-0.59 to -0.43\]). With the floor-corrected baseline, MGH and HMC were flagged at 55% and 56% (-0.8 points) and BOAS at 34%, and RBD sensitivity stayed at 95%. Nine of the ten predictions were met. The exception: floor-corrected RBDtector flagged 49.0% of CAP's same-system patients at 1.5 µV against 37.3% as recorded (+11.8 points \[2.9-20.6\]; 6 nights turned positive, none negative), where at most 5 points had been allowed. In an exploratory check on simulated noise alone, floor-corrected RBDtector counted activity in only 0.4% of REM mini-epochs at that floor, about a seventh of the underlying 2.9-point rise in "any" activity.

Isolated RWA by DREAMER's definition (RAI below 0.85) was the most stable label: it applied to 8-17% of nights without RBD in every cohort (12% of MGH patients aged 50 or over) and hardly moved with added noise (MGH 15% to 13%), whereas the relative criteria labeled between 9% and 96% of comparable people depending on the recording system (Supplementary Table S10). Per 1,000 PSGs of people aged 50 or over at an RBD prevalence of 2%, the published SINBAR chin criterion would flag 752 people to find 19 with RBD (positive predictive value 2.5%), RBDtector 696 (2.7%) and the published Montreal criteria 308 (5.9%); the re-derived SINBAR-FC cut-off would flag 129 to find 17 (13.3%), of whom about 13 would be expected to develop a synucleinopathy within 12 years (Supplementary Table S11). The floor check summarizes the source of these differences in one number per system: to count as RWA under a threshold of twice the floor, muscle activity had to reach 0.61 µV on BOAS's system and 2.54 µV on HMC's, against 1.73 µV on every system under floor correction.

## Discussion

Applied through one automated pipeline to openly available polysomnograms, the published RWA cut-offs recognized clinical RBD but flagged a large and strongly site-dependent share of people without RBD: 29% and 76% of MGH patients (Montreal, SINBAR) against 9% and 25% of HMC patients, and up to 91% of healthy volunteers on the quietest system. Four lines of evidence traced the difference to one property of the recording system, its noise floor. A correction fixed in advance, which subtracts each recording's noise instead of multiplying it, removed the dependence on noise, closed the gap between hospitals and held on three systems not used to develop it. The effect is large in the units Parkinson's disease research uses: on the same RBD nights, HMC's floor lowered tonic RWA by two-thirds of the difference that predicted later Parkinson's disease, and RBDtector, the open-source scorer built for this field, inherited the dependence.

### Why background-relative criteria measure the noise floor

The Montreal, SINBAR and AASM criteria count muscle activity that exceeds a multiple of the quietest EMG of the night. In a well-atonic REM period the quietest EMG is largely the noise of the electrodes and amplifier, so the thresholds are, in effect, multiples of the recording system's noise floor. A quieter system lowers them and lets the small twitches that occur in everyone's REM sleep count as RWA; a noisier one raises them and hides part of a patient's abnormal activity.

The evidence for this reading is experimental rather than correlational. Storage format and amplitude did not matter. Raising the noise floor of the same nights changed verdicts only from positive to negative, along a dose-response on which MGH and HMC fell on the same curve. The noisier system was noisier on an EEG channel too, and its chin floor had the signature of noise, with indistinguishable NREM and REM floors, which MGH's recordings acquired when noise was added. Because the same nights were compared, differences in population cannot explain these changes; we therefore regard the noise ladder, rather than the comparison between hospitals, as the primary evidence.

The account is not complete. After harmonization a SINBAR gap of 5.5 points remained, and the first and last epochs of REM periods carried about 4 of the 20 Montreal points, both consistent with smaller contributions from what open datasets do not document: electrode type and placement, amplifier filters, scoring conventions and medication. Serotonergic antidepressants increase REM chin tone in people without RBD \[31,32\], narcolepsy, part of CAP's patient group, is itself associated with RWA \[33\], and severe obstructive sleep apnea can mimic RBD \[34\], which fits the apnea gradient we saw only in REM epochs containing events. Within a cohort the relation runs the other way, because there the floor also carries genuine muscle tone: across sites the floor is set by the equipment, within a site by the patient.

### Relation to previous work

Because the thresholds follow the floor, a single published cut-off yields a different operating point on every recording system: false positives on quiet systems and missed RBD on noisy ones. This offers a testable, non-ethnic explanation for reports that optimal thresholds differ between centers. In Japanese patients with isolated RBD the optimal SINBAR-type threshold was 11.3% rather than 27.2% \[14,15\]; a noisier recording system would produce exactly this pattern of lower activity percentages and a lower optimal threshold. Automated chin cut-offs also differed between a laboratory and a home device (6.5% vs 15.0%) \[16\], whereas RBDtector, validated at a second center with the full SINBAR montage, arrived at a threshold close to the original \[11\]. Whether such differences reflect populations or equipment cannot be decided unless studies report the floor against which their thresholds were measured. Comparisons of computerized methods on one dataset \[9\] and single-center normative values \[12\] could not reveal the effect, because within one system the floor varies little.

Our automated values in people without RBD were three to five times those of visually scored controls \[5\]. One explanation, which we did not test, is that a visual scorer reads chin EMG at a fixed display gain at which twitches of one or two microvolts are barely visible, so visual scoring carries an implicit absolute detection limit that an automated relative rule lacks. Scoring the same nights visually at several display gains would test it.

### A remedy that subtracts the noise

Harmonizing every recording to a common, higher floor made the hospitals agree only by discarding sensitivity, and re-deriving cut-offs on harmonized data to recover it reopened the gap. Floor correction removes noise instead of adding it: it asks every recording for the muscle activity the published rule asks for on a system with a 1-µV background. It held on the counts that matter (no MGH night changed at HMC's floor under Montreal-FC, RBD sensitivity was unchanged, the hospitals agreed, and three new systems behaved as predicted), and it is legitimate because the sites recorded muscle activity at the same scale once the noise was removed.

Three qualifications follow. First, Montreal-FC at the primary reference kept 81% sensitivity, below the 85% required; the reference sets the operating point, and a lower reference may suit the Montreal criteria, but that choice was made after seeing the data and needs confirmation. Second, floor correction does not make a cut-off specific: at the published 18.2%, SINBAR-FC flagged about 45% of patients, now at both hospitals. A cut-off re-derived for automated scoring (49.1%) was the first threshold in this study to transfer between hospitals, but it rests on 21 RBD patients from one center and flagged 11-12% of healthy volunteers. Third, the correction has limits of its own: its constants were set on simulated white noise at 200-512 Hz, it turned three healthy nights positive on CAP's 128-Hz system, it should not be read below 200 Hz or above a floor of about 1.7 µV (for B = 1.0 µV), and real noise is neither perfectly white nor stationary. The RAI, which subtracts a moving-minimum noise estimate, was also stable across sites and nearly immune to added noise but, like any absolute measure, depends on gain. Other automated tools \[35,36\] can be checked the same way, by scoring the same nights with added noise, and spectral detection of muscle potentials \[37\] offers a route that does not depend on amplitude thresholds.

Two numbers, computable from any recording in seconds, would make RWA results comparable between laboratories: the chin EMG's quiet-REM level (its noise) and its net N2/N3 level (its gain). We provide a tool that reports both for any recording, together with the muscle activity each threshold demands on that system.

### What this means for Parkinson's disease research

Parkinson's disease research uses the amount of RWA, not only its presence: to estimate who will convert \[19\], to follow progression \[20\], to define isolated RWA as a possible earlier stage \[18,21\], and to pool patients recorded on different systems in multi-center prodromal cohorts \[17,18\]. In each of these uses the recording system is a hidden variable, and in the first two one of the same size as the effects studied. In multi-center cohorts, part of the variation in RWA between patients may reflect where they were recorded; adjusting for center removes this only if each center's floor is stable and unrelated to outcome. In longitudinal studies, a change of amplifier or electrodes during follow-up could appear as progression or as regression: a rise of 0.6 µV in the floor lowered tonic RWA as much as four and a half years of reported progression would raise it. We could not measure this in people with Parkinson's disease, for whom no recordings are openly available, but nothing in the mechanism is specific to the patients we studied.

RBDtector inherits the dependence because its baseline is, in effect, the noise floor. Its verdicts in established RBD were robust, but its continuous percentages were not, and in people without RBD its verdict largely followed the recording system. A floor-corrected baseline kept its percentages in RBD within a point at a noisier floor and closed a 45-point gap between hospitals, but it did not fully hold for patients without RBD near the top of the correction's range. Noise alone explained little of this. More likely, noise lifted small muscle activity just below the threshold over it more often than it pushed larger activity under it, an effect magnified by RBDtector's 30-ms resolution, over which the RMS of noise varies far more than over the 1-s windows of our rules. We did not test this explanation; a detector this fine may need a correction that allows for the spread of noise as well as its mean.

For isolated RWA, DREAMER's RAI-based definition was the most stable we tested, whereas relative definitions would let the recording system decide how common an "earlier stage" appears. For recruitment into prevention trials, automated scoring of routine polysomnograms is better used as a pre-filter for clinical and video review than as a case-finding test: even the best rule we tested required about eight studies to be reviewed per patient found at 2% prevalence, and the published SINBAR chin rule about 39. The same caution applies where a polysomnogram showing RWA carries diagnostic weight, as an indicative biomarker of dementia with Lewy bodies \[22\].

### Strengths and limitations

Only openly licensed data were used and the code will be released with the paper, so every number can be regenerated. Six recording systems in five countries were compared with four scoring approaches; explanations were tested by manipulating recordings rather than assumed; and four analyses with 38 checks were fixed in advance and reported whatever their outcome. Our automated scoring reproduced published values in RBD (SINBAR "any" 73% against 67% \[5\]).

The limitations are substantial. The only open recordings of RBD are CAP's: 22 patients with established RBD from one center, so sensitivity estimates are imprecise, optimistic for the milder prodromal cases a screening program would seek, and subject to incorporation bias; positive predictive values are therefore upper bounds. The RBD patients were older than most same-system patients; discrimination held against patients aged 50 or over (AUC 0.81-0.88), but those patients were flagged more often. RBD status is unknown in the clinical cohorts, where at a prevalence of about 1-2% \[38\] most, but not all, positive calls are false; the same-night ladder does not depend on this assumption. Only chin EMG was analyzed, whereas SINBAR's recommended montage adds the flexor digitorum superficialis and limb muscles may improve specificity. Automated scoring did not reproduce a human scorer who discards movement, snoring and electrode artifacts, and scorers may leave the most active REM epochs of RBD patients unscored as REM. Visual scoring may share the mechanism, but we did not test it. The ladder adds white, stationary noise; it can raise a floor but not lower one. Comparisons with published Parkinson's benchmarks concern scale and do not imply that those findings are artifacts. RBDtector was run without the arousal and artifact annotations its published cut-off assumes, which may raise its absolute percentages but cannot explain changes on the same nights. Finally, the databases do not document medication, electrode montage or amplifier settings.

## Conclusions

Published RWA cut-offs do not transfer to automated scoring across recording systems: the same criteria flagged 9% of patients at one hospital and 29% at another, and most healthy volunteers on quiet equipment. The difference follows the noise floor of the recording, against which background-relative criteria are, in effect, measured. The same mechanism makes noisier systems miss RBD and moves continuous RWA by amounts on the scale of the disease signals Parkinson's disease research relies on. Subtracting each recording's noise floor, a correction that needs nothing but the recording itself, removed these effects in pre-specified tests. Before automated RWA scoring is used to find prodromal synucleinopathy in routine polysomnograms, or pooled across centers and years, thresholds should be defined against the noise floor rather than in multiples of it, and reported with it.

## Declarations

**Data availability.** All recordings are openly available without application: the CAP Sleep Database ([PhysioNet](https://physionet.org/content/capslpdb/1.0.0/)), the HMC sleep staging database version 1.1 (PhysioNet, doi:10.13026/t79q-fr32), the PhysioNet/Computing in Cardiology Challenge 2018 training set ([PhysioNet](https://physionet.org/content/challenge-2018/1.0.0/)), the BOAS dataset (OpenNeuro ds005555, doi:10.18112/openneuro.ds005555.v1.1.3) and the Dreem Open Datasets (Zenodo record 15900394). The analysis code, the Colab notebook that runs it end to end, the four analysis plans with their commit history, and the derived per-night scores will be deposited in a public repository with a persistent identifier on submission: \[repository URL and Zenodo DOI to be added\].

**Pre-specification.** The noise ladder (commit 6d3cc6b, 26 September 2026), the floor-corrected criteria (20b9ec2, 26 September 2026), the external test (48053f3, 27 September 2026) and the Parkinson's analyses (1e7acf0, 2 October 2026) were committed to the project's version-controlled repository before they were run. They were not registered in an external registry.

**Ethics.** Secondary analysis of de-identified, publicly available data; no participant was contacted and no ethics approval was required \[confirm with your institution's requirements\].

**Funding.** \[State all funding with grant numbers, or "This work received no specific funding."\]

**Disclosure statement.** Financial disclosure: \[none\]. Non-financial disclosure: \[none\]. Preprint: \[none, or the preprint server and DOI\].

**Author contributions.** \[CRediT roles, for example: Conceptualization, Methodology, Software, Formal analysis, Writing - original draft: A.A.; Supervision, Writing - review and editing: (supervisor).\]

**Acknowledgements.** We thank the providers of the CAP, HMC, PhysioNet/Computing in Cardiology Challenge 2018, BOAS and Dreem Open Datasets for making their recordings openly available, and the authors of RBDtector for releasing their software as open source.

**Use of AI tools.** \[Required by SLEEP in the Methods or Acknowledgements and in the cover letter. Suggested wording, to be confirmed by the authors: "A generative AI assistant was used to help write and debug the analysis code, run the cloud analyses, and draft and edit the manuscript. The authors reviewed and verified all code, results and text and take full responsibility for the content."\]

## References

Metadata of every entry checked against Europe PMC, Crossref, DataCite or the publisher's page (October 2026).

1. Postuma RB, Iranzo A, Hu M, et al. Risk and predictors of dementia and parkinsonism in idiopathic REM sleep behaviour disorder: a multicentre study. Brain. 2019;142(3):744-759. doi:10.1093/brain/awz030
2. Cesari M, Brink-Kjaer A, During E, et al. Isolated REM sleep behaviour disorder - is screening possible? J Sleep Res. 2025;34(5):e70109. doi:10.1111/jsr.70109
3. Cesari M, Heidbreder A, St Louis EK, et al. Video-polysomnography procedures for diagnosis of rapid eye movement sleep behavior disorder (RBD) and the identification of its prodromal stages: guidelines from the International RBD Study Group. Sleep. 2022;45(3):zsab257. doi:10.1093/sleep/zsab257
4. Montplaisir J, Gagnon JF, Fantini ML, et al. Polysomnographic diagnosis of idiopathic REM sleep behavior disorder. Mov Disord. 2010;25(13):2044-2051. doi:10.1002/mds.23257
5. Frauscher B, Iranzo A, Gaig C, et al. Normative EMG values during REM sleep for the diagnosis of REM sleep behavior disorder. Sleep. 2012;35(6):835-847. doi:10.5665/sleep.1886
6. Troester MM, Quan SF, Berry RB, et al.; for the American Academy of Sleep Medicine. The AASM Manual for the Scoring of Sleep and Associated Events: Rules, Terminology and Technical Specifications. Version 3. Darien, IL: American Academy of Sleep Medicine; 2023.
7. Ferri R, Manconi M, Plazzi G, et al. A quantitative statistical analysis of the submentalis muscle EMG amplitude during sleep in normal controls and patients with REM sleep behavior disorder. J Sleep Res. 2008;17(1):89-100. doi:10.1111/j.1365-2869.2008.00631.x
8. Ferri R, Rundo F, Manconi M, et al. Improved computation of the atonia index in normal controls and patients with REM sleep behavior disorder. Sleep Med. 2010;11(9):947-949. doi:10.1016/j.sleep.2010.06.003
9. Cesari M, Christensen JAE, Kempfner L, et al. Comparison of computerized methods for rapid eye movement sleep without atonia detection. Sleep. 2018;41(10):zsy133. doi:10.1093/sleep/zsy133
10. Röthenbacher A, Cesari M, Doppler CEJ, et al. RBDtector: an open-source software to detect REM sleep without atonia according to visual scoring criteria. Sci Rep. 2022;12(1):20886. doi:10.1038/s41598-022-25163-9
11. Joza S, Pelletier A, Gagnon JF, et al. Validation of RBDtector: an open-source automated software for scoring REM sleep without atonia. J Sleep Res. 2025;34(6):e70037. doi:10.1111/jsr.70037
12. Feemster JC, Jung Y, Timm PC, et al. Normative and isolated rapid eye movement sleep without atonia in adults without REM sleep behavior disorder. Sleep. 2019;42(10):zsz124. doi:10.1093/sleep/zsz124
13. Leclair-Visonneau L, Feemster JC, Bibi N, et al. Contemporary diagnostic visual and automated polysomnographic REM sleep without atonia thresholds in isolated REM sleep behavior disorder. J Clin Sleep Med. 2024;20(2):279-291. doi:10.5664/jcsm.10862
14. Sakuma T, Kanai Y, Takei Y, Kimura M, Inoue Y. Diagnostic quantitative thresholds for rapid eye movement sleep without atonia in Japanese patients with isolated rapid eye movement sleep behavior disorder. Sleep. 2025;48(11):zsaf178. doi:10.1093/sleep/zsaf178
15. Mihashi I, Takei Y, Kawana F, et al. REM sleep without atonia thresholds are associated with reduced cardiac MIBG uptake but not with DAT-SPECT binding in probable REM sleep behavior. Sleep Med. 2026;147:109132. doi:10.1016/j.sleep.2026.109132
16. Levendowski DJ, Chahine LM, Lewis SJG, et al. Validation of automated detection of REM sleep without atonia using in-laboratory and in-home recordings. J Clin Sleep Med. 2025;21(3):583-592. doi:10.5664/jcsm.11488
17. Lim MM, Neilson LE, Elliott JE, et al. The North American Prodromal Synucleinopathy study: protocol for a multi-site, longitudinal, observational study of idiopathic/isolated rapid eye movement sleep behavior disorder. Sleep Adv. 2026;7(1):zpag007. doi:10.1093/sleepadvances/zpag007
18. Ferri R, Puligheddu M, Figorilli M, et al. Protocol for the DREAMER study: design and methodological framework of a multicenter trial-ready cohort of individuals with isolated REM sleep without atonia. PLoS One. 2026;21(6):e0350467. doi:10.1371/journal.pone.0350467
19. Postuma RB, Gagnon JF, Rompré S, Montplaisir JY. Severity of REM atonia loss in idiopathic REM sleep behavior disorder predicts Parkinson disease. Neurology. 2010;74(3):239-244. doi:10.1212/WNL.0b013e3181ca0166
20. Iranzo A, Ratti PL, Casanova-Molla J, Serradell M, Vilaseca I, Santamaría J. Excessive muscle activity increases over time in idiopathic REM sleep behavior disorder. Sleep. 2009;32(9):1149-1153. doi:10.1093/sleep/32.9.1149
21. Dodet P, Houot M, Leu-Semenescu S, et al. Isolated REM sleep without atonia is not equivalent to REM sleep behavior disorder in early-stage Parkinson's disease. Mov Disord. 2024;39(7):1190-1202. doi:10.1002/mds.29813
22. McKeith IG, Boeve BF, Dickson DW, et al. Diagnosis and management of dementia with Lewy bodies: fourth consensus report of the DLB Consortium. Neurology. 2017;89(1):88-100. doi:10.1212/WNL.0000000000004058
23. Bossuyt PM, Reitsma JB, Bruns DE, et al. STARD 2015: an updated list of essential items for reporting diagnostic accuracy studies. BMJ. 2015;351:h5527. doi:10.1136/bmj.h5527
24. Terzano MG, Parrino L, Smerieri A, et al. Atlas, rules, and recording techniques for the scoring of cyclic alternating pattern (CAP) in human sleep. Sleep Med. 2001;2(6):537-553. doi:10.1016/s1389-9457(01)00149-6
25. Goldberger AL, Amaral LAN, Glass L, et al. PhysioBank, PhysioToolkit, and PhysioNet: components of a new research resource for complex physiologic signals. Circulation. 2000;101(23):e215-e220. doi:10.1161/01.CIR.101.23.e215
26. Alvarez-Estevez D, Rijsman RM. Inter-database validation of a deep learning approach for automatic sleep scoring. PLoS One. 2021;16(8):e0256111. doi:10.1371/journal.pone.0256111
27. Alvarez-Estevez D, Rijsman RM. Haaglanden Medisch Centrum sleep staging database (version 1.1) \[dataset\]. PhysioNet; 2022. doi:10.13026/t79q-fr32
28. Ghassemi MM, Moody BE, Lehman LH, et al. You snooze, you win: the PhysioNet/Computing in Cardiology Challenge 2018. Comput Cardiol. 2018;45. doi:10.22489/CinC.2018.049
29. López-Larraz E, Sierra-Torralba M, Clemente S, et al. The Bitbrain Open Access Sleep (BOAS) dataset \[dataset\]. Version 1.1.3. OpenNeuro; 2026. doi:10.18112/openneuro.ds005555.v1.1.3
30. Guillot A, Sauvet F, During EH, Thorey V. Dreem Open Datasets: multi-scored sleep datasets to compare human and automated sleep staging. IEEE Trans Neural Syst Rehabil Eng. 2020;28(9):1955-1965. doi:10.1109/TNSRE.2020.3011181
31. McCarter SJ, St Louis EK, Sandness DJ, et al. Antidepressants increase REM sleep muscle tone in patients with and without REM sleep behavior disorder. Sleep. 2015;38(6):907-917. doi:10.5665/sleep.4738
32. Ahdab JE, Rodriguez CL, Grigg-Damberger M, et al. Antidepressant medications have differential effects on REM sleep without atonia quantified by chin and upper extremity EMG. J Clin Sleep Med. 2026;22(1):109. doi:10.1007/s44470-026-00127-2
33. Dauvilliers Y, Jennum P, Plazzi G. Rapid eye movement sleep behavior disorder and rapid eye movement sleep without atonia in narcolepsy. Sleep Med. 2013;14(8):775-781. doi:10.1016/j.sleep.2012.10.006
34. Iranzo A, Santamaría J. Severe obstructive sleep apnea/hypopnea mimicking REM sleep behavior disorder. Sleep. 2005;28(2):203-206. doi:10.1093/sleep/28.2.203
35. Papakonstantinou A, Klemming J, Haberecht M, et al. Ikelos-RWA. Validation of an automatic tool to quantify REM sleep without atonia. Clin EEG Neurosci. 2024;55(6):657-664. doi:10.1177/15500594231175320
36. Possti D, Oz S, Gerston A, et al. Semi automatic quantification of REM sleep without atonia in natural sleep environment. NPJ Digit Med. 2024;7(1):341. doi:10.1038/s41746-024-01354-8
37. Modarres MH, Elliott JE, Weymann KB, et al. Validation of visually identified muscle potentials during human sleep using high frequency/low frequency spectral power ratios. Sensors (Basel). 2021;22(1):55. doi:10.3390/s22010055
38. Haba-Rubio J, Frauscher B, Marques-Vidal P, et al. Prevalence and determinants of rapid eye movement sleep behavior disorder in the general population. Sleep. 2018;41(2):zsx197. doi:10.1093/sleep/zsx197

## Tables

**Table 1. Cohorts and recording systems.** Nights with at least 10 min of REM sleep. Quiet-REM level: 5th percentile of 1-s RMS chin EMG in REM (the noise floor). Net N2/N3 level: median 1-s RMS in N2/N3 with the noise removed in power (a gain check).

| Group | Nights | Population, place | Age, years | Men, % | System, chin sampling rate | REM, min (median) | Quiet-REM level, µV, median \[IQR\] | Net N2/N3 level, µV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP RBD | 21 (22) | Clinical RBD; Parma, Italy | 71 ± 7 | 86 | CAP main system, 512 Hz | 72 | 0.86 \[0.61-1.24\] | 2.91 |
| CAP same-system patients | 51 | NFLE 30, PLM 9, insomnia 7, narcolepsy 5; Parma | 30 ± 9 (n = 35); 59 ± 6 (n = 16) | - | CAP main system, 512 Hz | 89 | 0.48 \[0.44-0.69\] | 1.61 |
| CAP healthy | 15 | Healthy volunteers; Parma | 32 | - | Several systems, 100-512 Hz | 108 | 1.32 \[0.49-2.38\] | - |
| MGH | 925 | Clinical PSG; Boston, USA | 55 | 67 | 200 Hz, stored in 1-µV steps | 60 | 0.59 \[0.47-0.77\] | 1.60 |
| HMC | 147 | Clinical PSG; The Hague, Netherlands | 54 (group) | 56 (group) | 256 Hz | 69 | 1.52 \[1.23-1.79\] | 1.70 |
| BOAS | 99 | Healthy, general population; Zaragoza, Spain | 38 (18-82) | - | Micromed SD plus, 256 Hz | 79 | 0.37 \[0.28-0.49\] | 1.04 |
| DOD-O | 53 | Suspected sleep-disordered breathing; Stanford, USA | - | - | Somnomedics Somno HD, 250 Hz | 73 | 0.82 \[0.76-0.92\] | 1.68 |
| DOD-H | 25 | Healthy volunteers; Bretigny-sur-Orge, France | 18-65 (range) | - | Compumedics Siesta, 250 Hz | 98 | 0.56 \[0.54-0.65\] | 1.05 |

CAP RBD: 22 patients, 21 recorded on CAP's main system and used in all same-system comparisons. Age: mean ± SD, or median (range). HMC publishes age and sex only as group summaries. BOAS: first night per participant. NFLE, nocturnal frontal lobe epilepsy; PLM, periodic limb movements.

**Table 2. RWA criteria as implemented.** b: the night's background, the 5th percentile of 1-s REM RMS (AASM tonic: minimum NREM amplitude).

|  | Montreal \[4\] | SINBAR, chin \[5\] | AASM \[6\] | REM Atonia Index \[7,8\] | RBDtector \[10\] |
| --- | --- | --- | --- | --- | --- |
| Tonic | 20-s epochs with activity above 2b (or 10 µV) for more than 50% | 30-s epochs, same rule | 30-s epochs, at least 50% above the minimum NREM amplitude | - | 30-s epochs more than 50% active |
| Phasic | 2-s mini-epochs with 0.1-15-s bursts above 4b | 3-s mini-epochs with 0.1-5-s bursts above 2b | 3-s mini-epochs with 0.1-5-s bursts of at least 4b | - | 3-s mini-epochs with active runs of at most 5 s |
| Other | - | "Any" (tonic or phasic) activity in 3-s mini-epochs | - | 1-s mean rectified amplitude after a 60-s moving-minimum noise correction | Activity: 30-ms chunks above 2 x baseline (lowest 30-s RMS window per REM period), at least 0.1 s; "any" in 3-s mini-epochs |
| Published cut-off | Tonic at least 30% or phasic at least 15% | Any at least 18.2% | None | Below 0.8 | Chin any at least 23.5% |
| Floor-corrected version | Thresholds kb replaced by T (k = 2 tonic, 4 phasic) | 2b replaced by T (k = 2) | Not tested | Not applicable (subtracts its own noise estimate) | Baseline replaced by T/2 (k = 2; n = baseline/0.976) |

T = max(√(n² + (k² − 1)B²), 1.5b), with n = b/0.91 the noise RMS implied by b and B = 1.0 µV (Methods). Published percentage cut-offs are unchanged under floor correction.

**Table 3. Share of nights flagged positive, % \[95% CI\], by cohort and rule, as recorded.** For CAP RBD the share is the sensitivity; for groups without RBD it is the false-positive rate (an upper bound in clinical cohorts).

| Group (nights) | Floor, µV | Montreal, published | Montreal-FC | SINBAR, published | SINBAR-FC | RAI below 0.8 | SINBAR-FC at least 49.1% | RBDtector, published | RBDtector-FC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP RBD (21) | 0.86 | 90.5 \[71-97\] | 81.0 \[60-92\] | 95.2 \[77-99\] | 95.2 \[77-99\] | 57.1 \[37-76\] | 85.7 \[65-95\] | 95.2 \[77-99\] | 95.2 \[77-99\] |
| CAP same-system patients (51) | 0.48 | 33.3 \[22-47\] | 21.6 \[12-35\] | 74.5 \[61-84\] | 45.1 \[32-59\] | 13.7 \[7-26\] | 19.6 \[11-32\] | 78.4 \[65-88\] | 37.3 \[25-51\] |
| MGH (925) | 0.59 | 29.4 \[27-32\] | 18.0 \[16-21\] | 76.2 \[73-79\] | 45.3 \[42-48\] | 8.9 \[7-11\] | 13.2 \[11-16\] | 65.0 \[55-74\] | 55.0 \[45-64\] |
| HMC (147) | 1.52 | 8.8 \[5-15\] | 16.3 \[11-23\] | 25.2 \[19-33\] | 42.9 \[35-51\] | 7.5 \[4-13\] | 14.3 \[10-21\] | 20.4 \[15-28\] | 55.8 \[48-64\] |
| BOAS, healthy (99) | 0.37 | 41.4 \[32-51\] | 15.2 \[9-24\] | 90.9 \[84-95\] | 35.4 \[27-45\] | 13.1 \[8-21\] | 11.1 \[6-19\] | 88.9 \[81-94\] | 34.3 \[26-44\] |
| DOD-O (53) | 0.82 | 30.2 \[20-44\] | 24.5 \[15-38\] | 58.5 \[45-71\] | 50.9 \[38-64\] | 7.5 \[3-18\] | 17.0 \[9-29\] | - | - |
| DOD-H, healthy (25) | 0.56 | 20.0 \[9-39\] | 12.0 \[4-30\] | 84.0 \[65-94\] | 32.0 \[17-52\] | 4.0 \[1-20\] | 12.0 \[4-30\] | - | - |

FC, floor-corrected (B = 1.0 µV). SINBAR-FC at least 49.1%: cut-off re-derived on CAP for automated scoring (Youden's index; leave-one-out sensitivity 86%). RBDtector was run on a random 100 MGH nights (floor 0.53 µV) and not on the Dreem cohorts. MGH - HMC difference: Montreal +20.5 points published, +1.6 floor-corrected; SINBAR +51.0 and +2.4; RBDtector +44.6 and -0.8.

**Table 4. Pre-specified analyses: every decision criterion and its outcome.**

| Analysis (commit, date) | Criterion fixed in advance | Result | Verdict |
| --- | --- | --- | --- |
| Noise ladder (6d3cc6b, 26 Sep 2026) | 1. Harmonized to 2.0 µV, MGH - HMC within 3 (Montreal) and 5 (SINBAR) points | +0.8; +5.5 | Met; narrowly not met |
|  | 2. MGH's ladder at HMC's level within 3 / 5 points of HMC | 8.9% vs 8.8%; 29.2% vs 25.2% | Met |
|  | 3. RBD sensitivity below 70% at 2.0 µV: noisier systems miss RBD | Montreal 57%; SINBAR 86% | Supported (Montreal) |
|  | 4. Harmonize, re-derive cut-offs: gap within 5 points, leave-one-out sensitivity at least 80% | Gaps +10 to +21; sensitivity 71-90% | Not met |
|  | 5. HMC / MGH EEG 40-90 Hz floor at least 1.5: system-wide noise | 1.98 | Met |
|  | 6. Dropping transitional REM epochs changes the Montreal gap by less than 3 points | 20 to 16 | Narrowly not met |
| Floor-corrected criteria (20b9ec2, 26 Sep 2026), Montreal-FC / SINBAR-FC | 1. MGH within 5 points at a 1.5-µV floor | 0.0 / +1.8 | Met / met |
|  | 2. RBD sensitivity within 10 points at a 1.5-µV floor | 0 / 0 | Met / met |
|  | 3. MGH - HMC as recorded within 5 / 10 points | +1.6 / +2.4 | Met / met |
|  | 4. RBD sensitivity at least 85% | 81% / 95% | Not met / met |
|  | 5. Same-system patients not flagged more than under the published rule | 22% vs 33% / 45% vs 75% | Met / met |
| External systems (48053f3, 27 Sep 2026) | E1. Net N2/N3 level within 0.67-1.5 times MGH's | BOAS 0.65; DOD-H 0.66; DOD-O 1.05 | Not met; not met; met |
|  | E2. Published SINBAR flags at least 30% of healthy nights on systems with a floor below 1 µV | BOAS 91%; DOD-H 84% | Met; met |
|  | E3. Difference between healthy cohorts at least halved under FC | Montreal 21.4 to 3.2; SINBAR 6.9 to 3.4 | Met; met |
|  | E4. Across groups without RBD, rank correlation of floor and published SINBAR positivity below 0 and weaker under FC | -0.83 to +0.43 | Met |
|  | E5. SINBAR-FC at least 49.1% flags at most 10% of healthy and 20% of DOD-O nights | BOAS 11%; DOD-H 12%; DOD-O 17% | Not met; not met; met |
|  | E6. DOD-O within 10 points of MGH's ladder at DOD-O's floor | Montreal +9.3; SINBAR -3.0 | Met |
| Parkinson's disease research (1e7acf0, 2 Oct 2026) | PD1a. Montreal tonic, published: mean change on RBD nights at most -10 points | -21.4 | Met |
|  | PD1b. Montreal tonic, FC: change within 3 points | -1.1 | Met |
|  | PD1c. RBDtector tonic, published: at most -10 points | -12.1 | Met |
|  | PD1d. RBDtector tonic, FC: within 3 points | +0.1 | Met |
|  | PD2a. RBDtector, same-system patients flagged: fall of at least 10 points | -52.9 | Met |
|  | PD2b. RBDtector-FC, same-system patients flagged: change within 5 points | +11.8 | Not met |
|  | PD2c. RBDtector-FC, RBD sensitivity: change within 10 points | 0 | Met |
|  | PD2d. RBDtector MGH - HMC at least 20 points, at most half under FC | +44.6 to -0.8 | Met |
|  | PD2e. RBDtector flags at least 50% of BOAS, at most half under FC | 88.9% to 34.3% | Met |
|  | PD2f. Rank correlation of floor and "any" below 0, weaker under FC | -0.52 to +0.31 | Met |

In total, 29 of 38 checks were met in full and one in part (ladder criterion 1). Changes are from the night as recorded to the copy at a 1.5-µV quiet-REM level unless stated.

## Figure legends

Figures are submitted as separate files, generated by the pipeline (Google Drive folder rbd-rwa/figures, PNG and PDF): Figure 1 = fig1\_positivity, Figure 2 = fig2\_level\_and\_hardware, Figure 3 = fig6\_noise\_ladder, Figure 4 = fig8\_floor\_corrected, Figure 5 = fig9\_external, Figure 6 = fig10\_parkinsons.

**Figure 1. Share of nights flagged positive by each method's published cut-off.** Percentage of nights classified positive, with 95% Wilson intervals, by the Montreal (tonic at least 30% of 20-s epochs or phasic at least 15% of 2-s mini-epochs), SINBAR (chin "any" activity in at least 18.2% of 3-s mini-epochs) and REM Atonia Index (below 0.8) criteria, applied by the same automated pipeline. CAP RBD: patients with RBD; CAP patients: CAP patients with other sleep disorders recorded on the same system as the RBD patients (512 Hz); CAP healthy: healthy volunteers recorded on other systems; MGH: Massachusetts General Hospital clinical cohort; HMC: Haaglanden Medisch Centrum clinical cohort. For CAP RBD the share is the sensitivity; for the other groups it is the false-positive rate if none of them has RBD.

**Figure 2. The quiet-REM level, and recordings re-made in software.** (A) Each night's quiet-REM level, the 5th percentile of 1-s RMS chin EMG amplitude during REM sleep and the reference against which the relative criteria judge activity, by group (log scale; boxes: median and interquartile range; whiskers: 1.5 times the IQR). Dashed line: the 1-µV step in which MGH stores chin EMG. (B) Share of nights flagged positive (95% Wilson intervals) in HMC as recorded; HMC quantized to 1-µV steps; HMC quantized and resampled to 200 Hz (MGH's storage format); HMC scaled by 0.39 to MGH's median quiet-REM level; the scaled signal in MGH's storage format; MGH as recorded; and MGH with 1.5 µV of added white noise, which raises its quiet-REM level to HMC's (the first 300 records; the same nights as recorded were flagged at 34% by Montreal, 83% by SINBAR and 12% by the RAI). Storage format and amplitude do not reproduce the difference between the hospitals; the noise floor does.

**Figure 3. The noise ladder (pre-specified): verdicts follow the recording's noise floor.** Share of nights flagged positive by each method's published cut-off as white noise is added to the chin EMG of the same nights (0.5, 1.0, 1.5, 2.0 and 3.0 µV in-band RMS), plotted against the group's median quiet-REM level (log scale). Filled circles: as recorded; open circles: noise added; stars: every night harmonized to a quiet-REM level of 2.0 µV. CAP RBD (n = 21) and CAP patients (n = 51) were recorded on CAP's main system; MGH: the first 300 Challenge 2018 records (280 with at least 10 min of REM); HMC: all nights. Read at HMC's own level (1.52 µV), MGH's curve reaches HMC's positivity (Montreal 8.9% vs 8.8%). The analysis and its decision criteria were committed before it was run.

**Figure 4. Floor-corrected criteria (pre-specified).** (A, B) Share of nights flagged by the published criteria (dotted) and the floor-corrected criteria (solid; reference background 1.0 µV) as white noise is added to the same nights, plotted against the median quiet-REM level: CAP RBD (red, n = 21), CAP patients on the same system (gray, n = 51), MGH (blue, n = 280) and HMC (purple, n = 147). Floor-corrected verdicts do not change until the floor exceeds about 2 µV, where small activity can no longer be told from noise. (C) As recorded: share flagged by the published (plain) and floor-corrected (hatched) Montreal and SINBAR criteria. Floor correction closes the MGH-HMC gap (Montreal +20.5 to +1.6 points; SINBAR +51.0 to +2.4).

**Figure 5. Recording systems not used to find the effect (pre-specified external test).** Share of nights flagged by the published (open symbols) and floor-corrected (filled; arrows from published to corrected) SINBAR (A) and Montreal (B) criteria, plotted against each cohort's median quiet-REM level. Circles: patients (CAP same-system patients, MGH, HMC, DOD-O); squares: healthy volunteers (BOAS, first night per participant; DOD-H); star: CAP RBD. On quiet systems the published criteria flag most healthy volunteers (SINBAR: BOAS 91%, DOD-H 84%); floor correction removes the dependence on the recording's floor and leaves the population to order the groups.

**Figure 6. What the noise floor means for Parkinson's disease research (pre-specified).** (A) Change in tonic chin RWA, in percentage points, on the same 21 CAP RBD nights when the quiet-REM level is raised from 0.86 µV as recorded to 1.5 µV (HMC's), mean with 95% bootstrap interval, under the published and floor-corrected Montreal criteria and RBDtector. Gray: the difference in baseline tonic RWA between RBD patients who later developed Parkinson's disease and those who remained disease-free \[19\], and the rise over a mean 5 years in isolated RBD \[20\]. (B) RBDtector, run unchanged: share of nights flagged (chin "any" at least 23.5%) as white noise is added to the same nights, plotted against the median quiet-REM level, with its published baseline (dotted) and the floor-corrected baseline (solid): CAP RBD (red, n = 21) and CAP patients on the same system (gray, n = 51). (C) RBDtector on the nights as recorded, by recording system: published (open) and floor-corrected (filled; arrows from published to corrected), against each cohort's median quiet-REM level: CAP RBD (star), CAP patients, MGH (random 100), HMC (n = 147) and BOAS (healthy volunteers, first nights, n = 99).

## Supplementary material

Submitted as a separate file: participant flow, every exploratory analysis, the four analysis plans with their full results, the Parkinson's analyses and deviations from the run plan, and the STARD 2015 checklist with 2 x 2 tables: Supplementary material
