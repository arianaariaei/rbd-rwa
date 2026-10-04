<!-- Snapshot of the Claude Doc, exported 2026-10-04; the diagrams and charts are in the Doc and in Research_proposal_2026-10-04.docx. -->

# Research proposal: comparable REM-sleep muscle scoring across sleep labs

Oct 4, 2026 · @Ariana

## Summary

**In one sentence:** software that scores muscle activity during dreaming (REM) sleep gives different answers on different hospitals' equipment, mainly because it compares the muscle signal with the recording's own electrical noise; we measured this on 1,354 openly available sleep recordings, explained why it happens, and fixed it with a rule that subtracts the noise instead of multiplying it.

**Why it matters.** During REM sleep the body is normally paralyzed. People who act out their dreams have REM sleep behavior disorder (RBD), and about three in four of them develop Parkinson's disease or a related brain disease within 12 years. The loss of paralysis, called REM sleep without atonia (RWA), is measured from a small muscle sensor on the chin. Researchers want computers to measure it automatically in thousands of routine sleep recordings, to find people at risk early and to follow how the disease develops.

**What we found.**

- The same published rules flagged 9% of patients at one hospital and 29% at another, and 91% of healthy volunteers recorded on the quietest equipment.
- The cause is how the rules are built: muscle activity counts only if it exceeds a multiple (2 or 4 times) of the quietest part of the signal, and on a normal night that quietest part is mostly noise from the electrodes and amplifier. Quiet equipment means a low bar and many false alarms; noisy equipment means a high bar and missed disease.
- Adding noise in software to the same recordings reproduced the difference between the hospitals. That is a controlled experiment, not a correlation.
- A floor-corrected rule, which subtracts the noise mathematically, removed the effect, closed the gap between hospitals, and held on three types of equipment it had never seen.
- For Parkinson's research: on the same patients' recordings, changing only the noise level shifted the measured RWA by two-thirds of the difference that predicted Parkinson's disease in a published study. RBDtector, the open-source scorer used in this field, has the same problem.

**How.** Everything ran in Google Colab on public data, with no applications or data-use agreements. Four analyses were written down and committed to git before they were run, so their results could not be tuned afterwards; 29 of their 38 checks passed fully and one partly, and the failures are reported.

**What comes next.** Submit the paper (target journal: SLEEP), release the code, and repeat the test in people with Parkinson's disease, whose recordings are not openly available.

## Background for computer scientists

**A sleep study is a multichannel time series.** A polysomnogram (PSG) records a person overnight with many sensors at once: brain waves (EEG), eye movements (EOG), muscle activity (EMG, mainly from the chin), the heart (ECG), breathing and oxygen. Each channel is a stream of voltage samples, typically 200-512 per second, stored in a format such as EDF. A night is about 8 hours, so one chin channel alone holds 6-15 million numbers.

**Sleep is labeled in 30-second windows.** A trained technician (or an algorithm) assigns every 30-s "epoch" a stage: wake, N1, N2, N3 (light to deep non-REM sleep) or REM (rapid-eye-movement sleep, when most vivid dreaming happens). The sequence of labels is the hypnogram. In this project the stage labels are given; we use them to know which parts of the night are REM.

**In REM sleep the body is switched off.** The brain actively paralyzes most muscles during REM sleep, probably so that we do not act out our dreams. On the chin EMG this shows up as an almost flat line: the muscle signal falls to the level of the recording's own electrical noise. That paralysis is called atonia.

**When the switch fails.** In REM sleep behavior disorder (RBD), the paralysis fails and people punch, kick or shout while dreaming. On the EMG, REM sleep then contains bursts and stretches of muscle activity: REM sleep without atonia (RWA). RBD matters far beyond the bedroom: it is an early sign of the alpha-synucleinopathies, a family of brain diseases in which a protein (alpha-synuclein) clumps in nerve cells. They include Parkinson's disease, dementia with Lewy bodies and multiple system atrophy. In a cohort of 1,280 people with RBD, 73.5% developed one of them within 12 years. This makes people with RBD the natural group for trials of drugs that might prevent Parkinson's disease, and it makes RWA a candidate signal for finding them early.

**How RWA is scored.** Clinicians count how much of REM sleep contains muscle activity. Two kinds are distinguished: tonic activity (sustained tension over most of an epoch) and phasic activity (short twitches lasting 0.1 to a few seconds). Each published method chops REM sleep into windows, marks each window active or not, and reports the percentage of active windows; a night above a cut-off counts as RWA. The key design choice, central to this project, is how "active" is decided. The visual methods compare the signal with the night's own background: a window is active if its amplitude exceeds 2 or 4 times the quietest EMG of that night. Think of it as an anomaly detector whose threshold is a multiple of each sensor's baseline.

| Method | What counts as active | Window | Published cut-off for a positive night |
| --- | --- | --- | --- |
| Montreal | Tonic: above 2 x background for more than half of a 20-s epoch; phasic: bursts above 4 x background | 20-s epochs, 2-s mini-epochs | Tonic at least 30% or phasic at least 15% |
| SINBAR (chin) | "Any" activity above 2 x background | 3-s mini-epochs | At least 18.2% |
| AASM | Tonic: above the minimum NREM amplitude; phasic: bursts at least 4 x background | 30-s epochs, 3-s mini-epochs | None published |
| REM Atonia Index (RAI) | Share of 1-s windows with amplitude at most 1 microvolt after a noise correction (1 = fully atonic) | 1-s windows | Below 0.8 |
| RBDtector (open-source software) | 30-ms chunks above 2 x the night's lowest 30-s level, lasting at least 0.1 s | 3-s mini-epochs, 30-s epochs | Chin "any" at least 23.5% |

**Why automate.** Visual scoring of RWA is slow, window by window through every REM period, and needs trained experts. Automated versions of these rules make it possible to score thousands of recordings, for screening, for pooling multi-center cohorts, and for tracking change over years. That raises the question this project answers: when software applies the same rule on different hospitals' equipment, does it measure the same thing?

## Problem statement and motivation

**The problem: a threshold that moves with the equipment.** The published RWA cut-offs were set in one or a few hospitals, mostly by humans scoring visually. When software applies them, "background" must become a number. A natural choice is the quietest few seconds of REM sleep. But in a healthy REM period the muscle is silent, so those quietest seconds contain mostly the electrical noise of the electrodes and amplifier: the recording's noise floor. A rule "active = above 2 x background" then really means "above 2 x this machine's noise".

An analogy: imagine an anomaly detector that flags any event above twice the level of the quietest events it has seen. On a very quiet sensor the bar drops and ordinary fluctuations are flagged (false positives). On a noisy sensor the bar rises and real anomalies are missed (false negatives). The detector's verdict then describes the sensor as much as the events.

**Signs that this happens.** Hospitals report different optimal RWA thresholds: in Japanese patients the best SINBAR-type threshold was 11.3% instead of the Western 27.2%, and automated cut-offs differed between laboratory and home devices (6.5% vs 15.0%). These differences were attributed to ethnicity or populations; equipment was never tested as an explanation.

**Why it matters.**

1. **Screening.** If routine sleep studies are screened automatically for RBD, false alarms decide whether the approach is usable. A rule that flags most people on quiet equipment is useless there.
2. **Multi-center studies.** Prodromal Parkinson's cohorts pool patients from several hospitals (9 centers in the North American NAPS study, 4 in Italy's DREAMER). If each hospital's equipment shifts RWA, part of what looks like patient differences is equipment.
3. **Following patients over years.** Studies track RWA over time as a marker of progression. An amplifier or electrode change in the middle of a study could look like disease progression or improvement.
4. **Parkinson's disease research.** The amount of RWA predicts who develops Parkinson's disease: tonic RWA was 31.9 percentage points higher at baseline in RBD patients who later developed Parkinson's disease than in those who did not, and it rises by about 4.8 points per year. If equipment can shift RWA by tens of points, these markers are confounded.

**The gap.** No study had compared the scoring rules across recording systems on shared data, or tested the noise explanation with a controlled experiment. That needs data from several hospitals, which is usually locked behind data-use agreements, and a pipeline that applies every rule identically. This project builds both from openly available recordings only.

## Research questions and hypotheses

The project asks six questions. The first two were explored openly; the last four were pre-registered: the hypotheses and their pass/fail criteria were written down and committed to git before the analysis was run, much as one writes test cases before the code they test. Each commit is time-stamped and its hash depends on everything before it, so the criteria could not be tuned to the results without rewriting history; because local history can be rewritten, publishing the repository (or archiving it with a DOI) is what lets others verify the order.

| # | Question | Hypothesis | Status |
| --- | --- | --- | --- |
| RQ1 | Do the published cut-offs, applied by software, give the same answers in different hospitals? | No: positivity will differ between sites with similar patients | Exploratory |
| RQ2 | If not, which property of the recording causes the difference? | The noise floor, not storage format, signal amplitude, sleep apnea or age | Exploratory, tested by experiment |
| RQ3 | Is there a dose-response, and do noisier systems miss RBD? | Adding noise step by step lowers positivity smoothly; one hospital's curve passes through the other's point; RBD sensitivity drops | Pre-registered: noise ladder, 6 criteria (commit 6d3cc6b) |
| RQ4 | Can a rule that subtracts the noise make the criteria portable? | A floor-corrected rule is unaffected by added noise, makes the hospitals agree and keeps at least 85% sensitivity | Pre-registered: 5 criteria per rule (commit 20b9ec2) |
| RQ5 | Do the mechanism and the fix hold on equipment never used to develop them? | On quiet systems the published rules flag many healthy people; the fixed rule does not; a new clinic falls on the predicted curve | Pre-registered: 6 predictions (commit 48053f3) |
| RQ6 | How large is the equipment effect in the units Parkinson's research uses, and does the open-source tool RBDtector share it? | Noise alone shifts tonic RWA by at least 10 points; RBDtector behaves the same; the fix removes both | Pre-registered: 10 predictions (commit 1e7acf0) |

Three further outputs are descriptive, with no pass/fail criteria: how many people each rule would label as having "isolated RWA" (an earlier stage than RBD); how many sleep studies a screening program would have to review per RBD patient found; and a per-system "floor check" that tells any lab how noisy its equipment is and whether the fixed rule applies to it.

## Related work and what is new

| Line of work | Key studies | What they did | What they left open |
| --- | --- | --- | --- |
| Scoring methods and cut-offs | Montplaisir 2010 (Montreal); Frauscher 2012 (SINBAR); AASM manual; Ferri 2008 and 2010 (RAI) | Defined the rules and cut-offs on one or a few centers, mostly by visual scoring | Whether the cut-offs hold on other equipment |
| Automated scoring | Cesari 2018 (comparison of computer methods); Rothenbacher 2022 and Joza 2025 (RBDtector); Papakonstantinou 2024 (Ikelos-RWA); Possti 2024 (home recordings) | Implemented and validated the rules in software | Validated within one dataset or one center at a time |
| Normal values | Feemster 2019 | RWA in adults without RBD at one center | One recording system |
| Thresholds that differ by site | Sakuma 2025 and Mihashi 2026 (Japan: 11.3% vs 27.2%); Levendowski 2025 (lab vs home: 6.5% vs 15.0%); Leclair-Visonneau 2024 (visual vs automated) | Found different optimal thresholds | Attributed the differences to populations or devices without a mechanism |
| Multi-center prodromal cohorts | Lim 2026 (NAPS, 9 centers); Ferri 2026 (DREAMER, 4 centers) | Pool RWA across hospitals | Assume RWA is comparable across equipment |
| RWA as a Parkinson's marker | Postuma 2010 (conversion); Iranzo 2009 (progression); Dodet 2024 (subtypes); McKeith 2017 (dementia with Lewy bodies) | Used the amount of RWA as a continuous marker | Assume the measurement is equipment-independent |

A literature search in Europe PMC (September 2026: "REM sleep without atonia" with noise, background EMG, automated, multicenter, equipment) found no study that relates background-relative RWA thresholds to the recording system's noise floor.

**What is new here.**

1. The first comparison of the published criteria across several recording systems on shared data, with every rule implemented identically in one open pipeline.
2. A controlled experiment that identifies the cause: re-making recordings in software changes one property at a time (storage format, amplitude, noise), and only the noise reproduces the difference between hospitals.
3. A pre-registered fix, the floor-corrected rule, validated on three recording systems that played no part in developing it.
4. The effect expressed in the units Parkinson's research uses, and a test of the field's open-source tool, RBDtector, run unchanged.
5. A fully reproducible, cloud-only pipeline on request-free data, and a floor-check tool that any lab can run on its own recordings.

## Data

All six datasets are public and request-free: anyone can download them without an application, a credential or a data-use agreement. 1,354 nights were analyzed out of 1,462 recordings (the paper's Supplementary Figure S1 shows each exclusion).

| Dataset | Who was recorded | Recordings (analyzed) | Equipment, chin EMG | Source and license | Role |
| --- | --- | --- | --- | --- | --- |
| CAP Sleep Database | 22 patients with RBD, patients with epilepsy, limb movements, insomnia, narcolepsy, and healthy volunteers; Parma, Italy | 108 (105) | Mostly one system at 512 Hz; healthy volunteers on several others | PhysioNet, ODC-By; about 40 GB | The only open recordings of RBD: the positive class |
| MGH (PhysioNet Challenge 2018) | Sleep-clinic patients, Massachusetts General Hospital, USA | 994 (925) | 200 Hz, stored in 1-microvolt steps | PhysioNet, ODC-By; about 130 GB | Large clinical reference with age, sex and breathing events |
| HMC | Sleep-clinic patients, Haaglanden Medisch Centrum, the Netherlands | 151 (147) | 256 Hz | PhysioNet, CC BY 4.0; about 15 GB | Second clinical reference, on a noisier system |
| BOAS | Healthy adults from the general population, no psychotropic drugs; Spain | 128 nights of 100 people (99 first nights) | Micromed SD plus, 256 Hz; no ECG channel | OpenNeuro ds005555, CC0 | External test: healthy, quietest system |
| Dreem DOD-O | Patients with suspected sleep apnea, Stanford, USA | 56 (53) | Somnomedics Somno HD, 250 Hz | Zenodo 15900394, MIT license; about 32 GB | External test: sleep-clinic patients |
| Dreem DOD-H | Healthy volunteers, France | 25 (25) | Compumedics Siesta, 250 Hz | Same release; about 25 GB | External test: healthy, second system |

**Labels.** Every dataset provides expert sleep stages per 30-s epoch. Only CAP says who has RBD; in the clinical cohorts RBD is not labeled, so a positive call there is a false positive unless the person has undiagnosed RBD (about 1-2% of adults), which makes those rates upper bounds. The three external cohorts were added only after their predictions had been committed.

**Why only request-free data.** This was a decision for the project: anyone must be able to rerun every number. It also reflects what happened when restricted data were tried: the National Sleep Research Resource denied access, and the PhysioNet Challenge 2026 data required a research-ethics training certificate whose registration step repeatedly failed. Datasets checked and set aside: MASS, the full Human Sleep Project and PPMI (controlled access); the RBDtector cohorts and other Parkinson's sleep cohorts (on request only); DREAMS (non-commercial, no-derivatives license); ISRUC (diagnosis labels unavailable). No openly available sleep recordings of people with Parkinson's disease exist; open Parkinson's datasets contain only awake EEG.

**What is kept.** Raw recordings are large (up to 134 MB a night), so each night is streamed from the public server into the cloud, reduced to a compact "pack" of 1-2 MB (the REM chin envelope at 50 values per second plus NREM summaries), and the raw file is deleted. The packs, not the raw data, are what every analysis reads.

## System design

&#91;embedded content: System design · from public servers to results\]

The notebook built from the repository carries all the code. Each night is streamed from its public server, cleaned and reduced to a compact pack, and only packs and results are kept, on Google Drive, so a session that disconnects resumes where it stopped. RBDtector runs in its own pinned Python environment inside the same cloud machine.

## Methods

### Signal processing, step by step

1. **Read** each night at its native sampling rate (EDF files via a direct reader, WFDB for MGH, HDF5 for the Dreem sets), avoiding libraries that silently resample.
2. **Band-pass filter** the chin EMG between 10 and 100 Hz (a fourth-order Butterworth filter run forwards and backwards, so it does not shift the signal in time). Muscle activity lives in this band; slow drift and very high-frequency hiss do not.
3. **Notch filter** the mains frequency (50 Hz in Europe, 60 Hz in the USA) and its harmonics: power lines leak a pure tone into every recording.
4. **Remove the heartbeat.** Each heartbeat leaks a small electrical spike into the chin channel. R-peaks are found on the ECG, the average shape of the spike is estimated every 5 minutes (a median template from -100 to +150 ms around each beat) and subtracted at every beat.
5. **Compute the envelope:** the root-mean-square (RMS) amplitude in 20-ms bins, 50 numbers per second instead of 200-512 raw samples. Every rule is computed from this envelope.
6. **Pack** the REM envelope, NREM summaries and stage labels into a 1-2 MB file per night.

### The scoring rules as algorithms

Each published rule becomes a short, deterministic function of the envelope and the stage labels. SINBAR's chin rule, for example:

```python
b = percentile(rms_1s[REM], 5)            # the night's quiet-REM level
for window in three_second_windows(REM):
    active[window] = longest_run(rms_20ms[window] > 2 * b) >= 0.1   # seconds
any_pct = 100 * mean(active)
positive = any_pct >= 18.2                # published cut-off
```

Montreal uses 2-s and 20-s windows and a 4 x b threshold for twitches; the AASM rules use 3-s and 30-s windows; the RAI counts 1-s windows whose amplitude, after subtracting a 60-s moving minimum, is at most 1 microvolt. RBDtector, an existing open-source program, was not reimplemented: it was run unchanged.

### The noise-floor idea

Independent signals add in power: if muscle activity of RMS a sits on noise of RMS n, the recording shows the square root of (a squared + n squared). A rule "active above k x b", with b set by noise, is therefore met only when the muscle activity reaches about the square root of (k squared - 1) times b. For SINBAR (k = 2) that is 1.73 x b: 1.0 microvolt of muscle activity on MGH's equipment (b = 0.59) but 2.6 microvolts on HMC's (b = 1.52). The same rule asks two and a half times more of a patient's muscles in one hospital than in the other.

### The floor-corrected rule

The fix asks every recording for the same amount of muscle activity: what the published rule asks for on a reference system whose background is B. The noise is subtracted in power instead of multiplied:

```latex
T = \max\left(\sqrt{n^{2} + (k^{2}-1)\,B^{2}},\; 1.5\,b\right), \qquad n = b / 0.91
```

- n is the noise RMS implied by the quiet-REM level b: for white noise, the 5th percentile of 1-s RMS values is 0.91 times the true RMS (found by simulation at 200, 256 and 512 Hz).
- B = 1.0 microvolt was fixed in advance. At b = B the rule matches the published one within 3%; on quieter systems it becomes an absolute threshold; on noisier ones the noise is subtracted.
- The guard 1.5 x b stops noise alone from crossing the threshold (in simulated noise, runs above 1.5 x b occurred in under 1% of windows).
- Nothing else changes: same windows, same published percentage cut-offs.
- It applies only where it can work: sampling at 200 Hz or more and a floor of at most 1.7 microvolts. Above that, small muscle activity can no longer be told apart from noise by any rule.

## Experiments

### 1. Re-recording in software: an ablation study on the equipment

MGH and HMC differ in many ways (patients, staff, equipment, file format), so comparing them directly cannot say which difference matters. Instead, recordings were re-made in software with one property changed at a time, like an ablation study:

- **Storage format.** MGH stores the chin signal in steps of 1 microvolt at 200 Hz; HMC in steps of 0.024 microvolts at 256 Hz. HMC was re-saved in MGH's format.
- **Amplitude.** HMC was scaled down by 0.39 to MGH's signal level, alone and combined with MGH's format.
- **Noise.** In the reverse direction, white noise (1.5 microvolts) was added to 300 MGH nights, which lifts their quiet-REM level to HMC's.

Each copy went through the identical pipeline and was compared with the same nights as recorded. If storage or amplitude were the cause, those copies would change their verdicts; if noise were the cause, only the noisy copy would.

### 2-5. Four pre-registered experiments

| Experiment | What was done | What would count as success (fixed in advance) |
| --- | --- | --- |
| Noise ladder | The same nights (CAP, all HMC, 300 MGH) with noise added in five steps (0.5-3.0 microvolts), plus copies "harmonized" to a common floor of 1.5 or 2.0 microvolts. Each night uses one seeded noise track scaled to each level, so the steps differ only in amount. | Hospitals agree once floors match; MGH's curve passes through HMC's point; RBD sensitivity falls with noise; the EEG channel shows the same noise difference; and two checks on remedies and scoring conventions |
| Floor-corrected rule | Montreal and SINBAR rewritten with the floor-corrected threshold, scored on every night and every ladder step | Unchanged by added noise (patients and RBD), MGH and HMC agree, RBD sensitivity at least 85%, no extra false positives on a quiet system |
| External test | Three new cohorts on three new systems (BOAS, DOD-O, DOD-H), processed with the frozen pipeline | Quiet systems flag at least 30% of healthy people under the published rule; the fixed rule halves differences; positivity follows the floor under the published rule but not under the fixed one; a new clinic lands within 10 points of the predicted curve |
| Parkinson's research | Change in tonic RWA on the same RBD nights at HMC's noise level, compared with published disease effects; RBDtector run unchanged on 1,412 night-and-condition combinations, with and without a floor-corrected baseline | Published rules shift tonic RWA by at least 10 points; the fix keeps it within 3; RBDtector shows the same pattern |

**Running third-party software faithfully.** RBDtector (released in 2022) depends on old library versions: pandas 2 removed a function it calls. It was therefore run in its own pinned environment (Python 3.9, NumPy 1.21, pandas 1.3, SciPy 1.7), created by a script. Two optimizations cut a run from 81 to 35 seconds (a vectorized lookup replacing a Python loop over every REM sample, and trimming each night to its REM stretch while keeping clock times so that RBDtector's 30-ms, 3-s and 30-s grids fell where they would); on a test night the outputs were identical to the last digit before and after.

### 6. Exploratory checks

Several questions were explored without pre-set criteria and are labeled as exploratory: how the definition of "background" changes verdicts (six definitions); whether sleep apnea, age, sex or leftover heartbeat explain positive calls; whether the first and last epochs of REM periods matter; whether cut-offs re-derived for automated scoring transfer between hospitals; and, after one pre-registered prediction failed, whether RBDtector counts pure simulated noise as muscle activity.

## Statistics explained simply

| Tool | The question it answers | In machine-learning terms |
| --- | --- | --- |
| Sensitivity, false-positive rate | What share of people with RBD are flagged? What share of people without RBD are flagged anyway? | Recall on the positive class; false-positive rate on the negative class |
| 95% Wilson interval | Within what range the true rate probably lies, given the sample size | An error bar; Wilson's version stays sensible for small samples and rates near 0% or 100% |
| AUC (area under the ROC curve) | If we pick one RBD night and one non-RBD night at random, how often does the score rank the RBD night higher? | The usual ROC-AUC of a classifier score |
| Cohen's kappa | Do two methods agree more than chance would make them? | Agreement between two classifiers, corrected for chance |
| Logistic regression | Does age, sex or sleep apnea change the odds of a positive call? | A linear model of the log-odds, used for explanation, not prediction |
| Paired comparison and McNemar test | On the same nights, did adding noise flip verdicts, and in which direction? | Comparing two models on the same test set by counting the cases each gets right and the other wrong |
| Bootstrap | How uncertain is an estimate? Resample the nights with replacement 2,000 times and see how much it moves | The standard bootstrap confidence interval |
| Youden's index and leave-one-out | Which cut-off best separates RBD from other patients, and how well would it do on a night it never saw? | Threshold tuning, then leave-one-out cross-validation to avoid an optimistic estimate |
| Spearman's rho | Do two quantities rise and fall together, in rank? | A rank correlation, robust to outliers |
| Positive predictive value | If a screening rule flags someone, how likely is it that they truly have RBD? | Precision, which depends on how rare the condition is |

**Why rare conditions make screening hard (Bayes' rule).** Precision depends on prevalence:

```latex
PPV = \frac{\text{sensitivity} \times p}{\text{sensitivity} \times p + \text{false-positive rate} \times (1 - p)}
```

With p = 2% of people aged 50 or over having RBD, a rule with 95% sensitivity and a 75% false-positive rate (the published SINBAR rule) flags 752 of every 1,000 people to find 19 cases: a precision of 2.5%.

**Many tests, one discipline.** The project computes many numbers, so some would look significant by chance. Two safeguards were used: the decisive analyses had their pass criteria fixed in advance, judged on the estimate itself rather than on p-values; and everything else is labeled exploratory or descriptive, so a reader knows which results confirm a prediction and which generate new ones.

## Results so far

The same published rules gave very different answers in different hospitals, the difference followed the equipment's noise, and subtracting the noise removed it.

- **Hospitals disagree.** The Montreal rule flagged 29% of MGH patients and 9% of HMC patients; SINBAR flagged 76% and 25%. The methods also disagreed with each other on 70% of MGH nights.
- **Not format, amplitude, apnea or age.** HMC re-saved in MGH's storage format, or scaled to MGH's signal level, kept HMC's verdicts. Sleep apnea and age explained little.
- **Noise reproduces the difference.** Adding noise to 277 MGH nights lowered Montreal positivity from 34% to 10% and SINBAR from 83% to 36%, close to HMC's 9% and 25%; every changed night went from positive to negative. HMC's EEG channel was also twice as noisy as MGH's.
- **The fix works.** Floor-corrected rules closed the gap between hospitals (Montreal +20.5 to +1.6 points; SINBAR +51.0 to +2.4) and kept SINBAR's sensitivity at 95%. A cut-off re-derived for automated scoring (49.1%) flagged 13% of MGH and 14% of HMC patients with 86% sensitivity.

&#91;embedded content: Paper, Table 3 · SINBAR chin rule, six groups without RBD, nights as recorded\]

On quiet equipment the published rule flags most people, healthy or not, and its verdicts fall as the noise floor rises (rank correlation -0.83). Floor-corrected, the groups no longer follow the equipment: healthy volunteers sit lowest and clinic patients higher, as they should.

&#91;embedded content: Paper, Supplementary Tables S7 and S8 · Montreal criteria, noise ladder\]

The noise ladder is the controlled experiment: the nights stay the same and only the noise changes. Under the published rule, false positives fall as noise rises, and so does the detection of real RBD (a system as noisy as HMC's would miss about four in ten RBD patients that CAP's quieter system catches). The floor-corrected rule stays flat until the noise floor passes about 2 microvolts, where no rule can tell small muscle activity from noise.

&#91;embedded content: Paper, Supplementary Table S9 · 21 CAP RBD nights; benchmarks from Postuma 2010 and Iranzo 2009\]

For Parkinson's research this is the key picture: a difference in equipment noise between two real hospitals moved the published tonic measure by two-thirds of the difference that separated future Parkinson's patients from people who stayed healthy, and by as much as four and a half years of typical progression. RBDtector moved by about a third of that difference. With the floor-corrected baseline neither moved meaningfully. RBDtector's verdict on the RBD nights themselves held throughout (20 of 21 flagged), because those patients lie far above its cut-off; in people without RBD its verdict followed the equipment, which the floor correction largely removed.

**Screening.** Per 1,000 sleep studies of people aged 50 or over, with 2% of them having RBD, the published SINBAR rule would flag 752 people to find 19 cases (2.5% precision); the best rule tested, the re-derived floor-corrected cut-off, would flag 129 to find 17 (13.3%).

**Pre-registered checks.**

| Analysis plan | Checks | Met | Not met |
| --- | --- | --- | --- |
| Noise ladder | 6 | 3, and 1 in part | 2 (harmonizing then re-deriving cut-offs; a check on REM-period edges, narrowly) |
| Floor-corrected rule | 10 (5 per rule) | 9 | 1 (Montreal version: 81% sensitivity, 85% required) |
| External systems | 12 | 8 | 4 narrow misses (healthy cohorts' muscle scale; specificity of the re-derived cut-off) |
| Parkinson's research | 10 | 9 | 1 (floor-corrected RBDtector on patients without RBD at high noise) |
| Total | 38 | 29, and 1 in part | 8 |

## Interpretation, limitations and threats to validity

**What the results mean.** The published RWA rules partly measure the recording equipment, because their thresholds are multiples of the equipment's noise. The evidence is causal rather than correlational: on the same nights, adding noise changed verdicts in one direction only, along a smooth dose-response, and reproduced the difference between two real hospitals. Subtracting the noise instead of multiplying it makes the rules portable, as long as the recording is good enough (200 Hz or more, floor at most 1.7 microvolts). Within one hospital the relation runs the other way, because there a higher quiet level often reflects genuine muscle tone (RBD patients have more of it), not noise.

| Threat | What could be wrong | How it was handled, or what remains |
| --- | --- | --- |
| Internal validity | Something other than noise drives the hospital difference | Same-night experiments rule out patient differences; format and amplitude were tested and failed to reproduce it. A small part remains unexplained (5.5 points for SINBAR), probably electrodes, filters, scoring habits or medication, which the databases do not document |
| Construct validity | The software may not score RWA the way a human expert would | The automated scores reproduce published RBD values (SINBAR "any" 73% vs 67%), but no human scoring of these nights exists; only the chin was used (SINBAR also recommends arm muscles); movement and snoring artifacts are not removed as a human would |
| Reference standard | CAP's RBD diagnoses themselves rely on RWA, and the patients had established disease | Sensitivity is optimistic for the milder, early cases a screening program would look for; predictive values are upper bounds |
| External validity | One small RBD cohort from one center; no Parkinson's patients | 22 RBD patients give wide intervals; the Parkinson's findings concern the measurement, compared with published benchmarks, and need confirming in patients with Parkinson's disease, whose recordings are not openly available |
| Simulated noise | Real equipment noise is not perfectly white or constant | The ladder used white, stationary noise and can only raise a floor, not lower it; three real new systems behaved as predicted |
| Statistical conclusions | Many comparisons; small samples | Pass/fail criteria fixed in advance; exploratory results labeled; a re-derived cut-off (49.1%) rests on 21 patients and needs external validation |
| Limits of the fix | The floor-corrected rule is not a cure-all | It does not make a lenient cut-off specific (about 45% of patients flagged at the published SINBAR cut-off, now at both hospitals); it failed one prediction when applied inside RBDtector, which scores 30-ms pieces where noise varies much more; it should not be used on recordings below 200 Hz |

## Software engineering and reproducibility

**Design rules.** Everything runs in Google Colab, so nothing depends on the author's laptop (whose disk and connection could not hold 200+ GB of recordings). Raw data are disposable and derived data are precious: raw nights live only in the cloud machine's scratch disk, while the 1-2 MB packs and all results are mirrored to Google Drive. Every long step is resumable: a manifest records finished nights, so a disconnected session continues where it stopped.

**Repository layout** (Python; 43 commits from 3 September to 2 October 2026).

| Part | Files | Job |
| --- | --- | --- |
| Input and storage | src/config.py, src/fetch.py, src/edf.py, src/cap.py, src/cohorts.py, src/pack.py | Paths that work in Colab and locally; resumable downloads; an EDF reader at native sampling rates; one adapter per dataset; software re-recordings and the noise ladder; compact per-night packs |
| Signal processing | src/extract.py, src/ecg.py | Filtering, envelopes, heartbeat detection and subtraction |
| Scoring | src/rwa.py, src/rbdtector.py, src/floorcheck.py | The four published rules and their floor-corrected versions; a bridge that runs RBDtector unchanged; the floor check |
| Analyses | run\_cohort.py, run\_score.py, run\_report.py, run\_sensitivity.py, run\_ladder.py, run\_floor.py, run\_external.py, run\_rbdtector.py, run\_rbdtector\_noise.py, run\_parkinsons.py | One script per analysis; each writes a report, a CSV of scores and its figures |
| Packaging | tools/build\_notebook.py, notebooks/RBD\_RWA.ipynb, run\_parkinsons\_colab.sh, check\_floor.py | Builds a self-contained notebook (54 cells; the code travels inside it); one-command runner for the Parkinson's analyses; a command-line floor check for any EDF |
| Paper | paper/ | Drafts, four pre-registrations, result records, audit, STARD checklist |

**How to reproduce.** Open notebooks/RBD\_RWA.ipynb in Colab and choose Runtime, then Run all. The first cell asks for Google Drive access (an OAuth prompt only the account owner can answer). Each dataset is streamed and packed, then every analysis runs in order. Fixed seeds make the random parts repeat exactly: noise tracks are seeded by record name, the MGH sample for RBDtector by seed 0. RBDtector is pinned to its published commit (7c9c73d) and its own library versions.

**Engineering problems solved along the way.**

- **Volume.** MGH alone is about 130 GB. Streaming each night, packing it and deleting it kept disk use small; parallel workers and parallel byte-range downloads (for slow Zenodo archives) kept the runtime to hours.
- **Timing bugs.** An early version assumed 50 envelope bins per second when a 512-Hz signal gave 51.2, so the sleep stages drifted about 11 minutes by the end of a night and corrupted the first results; the fix and a native-rate EDF reader came before any reported analysis.
- **Colab limits.** A runtime lives at most 12 hours. The Parkinson's runs (1,412 RBDtector runs) were split across two runtimes; one ran out of memory when a second job started beside it and was resumed without losing a night, because scores are written only when a night is complete.
- **Legacy dependencies.** RBDtector needs 2021-era libraries, so it runs in its own virtual environment, with one documented compatibility shim for a renamed field in the EDF library.
- **Faithful speed-ups.** Every optimization of third-party code was checked by comparing outputs before and after on a test night: identical to the last digit.

## Project history

The project began as a university course project (course 4042) on deep-learning sleep staging from rodent EEG; the dataset turned out to contain mice, not rats. Several article ideas from that work were checked and dropped: some had just been published by others, and some tested negative here (EEG-muscle coupling sat at the noise floor; a cross-lab "convention versus signal" decomposition did not replicate). That work is parked. The current project, measuring REM sleep without atonia, started on 3 September 2026.

| Date (2026) | What happened | What it changed |
| --- | --- | --- |
| 4 Oct | Manuscript assembled for the journal SLEEP | Ready for review by co-authors |
| 2 Oct | Parkinson's analyses pre-registered (commit 1e7acf0) and run: 1,412 RBDtector runs on two cloud machines | 9 of 10 predictions met; one failure explained in part by an extra check |
| 27 Sep | External test pre-registered (48053f3) before any new recording was read; three new systems processed | 8 of 12 predictions met; four narrow misses reported |
| 26 Sep | Floor-corrected rule pre-registered (20b9ec2) and tested | SINBAR version passed all 5 criteria, Montreal version 4 of 5 |
| 26 Sep | Self-audit: ages were available but unused; three recordings without physical units were being scored as microvolts | Age-matched comparisons added; units bug fixed and rerun |
| 26 Sep | Noise ladder pre-registered (6d3cc6b) and run | Dose-response confirmed; noisier systems miss RBD |
| 26 Sep | MGH and HMC added; the same rules gave 29% vs 9%; software re-recordings pointed to the noise floor | The project's central question |
| 26 Sep | CAP's healthy volunteers turned out to be recorded on different equipment from its RBD patients | RBD compared only with patients on the same system |
| 25 Sep | NSRR denied access; Challenge 2026 data needed a certificate whose registration kept failing | Request-free data only |
| 25 Sep | A timing bug was found: 512-Hz signals gave 51.2 envelope bins per second, not 50, so sleep stages drifted about 11 minutes by morning | An early "relative thresholds fail" result was withdrawn; native-rate reading added |
| 3 Sep | RWA project started: cloud-first pipeline, four scoring methods | First results on CAP |

**Lessons that shaped the method.**

- Search the literature before investing: a head-to-head comparison of computerized RWA methods on one dataset had already been published (Cesari 2018), so the project moved to comparing hospitals and finding a mechanism.
- Compare like with like: CAP's healthy controls differ from its RBD patients in equipment as well as health, which would have inflated any "RBD detector".
- Check the clock: an alignment error between signal and labels can manufacture a finding.
- Write the pass criteria down before running the test, and report the misses.

## Work plan, risks and mitigations

**Done.** Data pipeline for six open cohorts; all four pre-registered analyses and the exploratory checks; the floor-check tool; the manuscript and its supplement, assembled for the journal SLEEP.

**Remaining, in order.**

1. Supervisor and co-author review of the manuscript; complete the title page, funding, disclosures and the AI-use statement the journal requires.
2. Publish the code repository with a permanent identifier (for example a Zenodo DOI), so that anyone can verify that the analysis plans predate the results.
3. Optionally add a figure that shows the mechanism on real traces: the same night as recorded and with added noise, with both thresholds drawn.
4. Submit to SLEEP and answer the reviewers.
5. Follow-up studies (outside the request-free scope): repeat the key tests in people with Parkinson's disease, whose sleep recordings are available only on request; test a correction that accounts for how much noise fluctuates, for fine-resolution detectors such as RBDtector; and score the same nights visually at several display gains to test whether human scoring shares the mechanism.

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Reviewers doubt that the analysis plans came first, because the repository is private | High until published | Publish the repository and archive it with a DOI before submission |
| Reviewers ask for data from people with Parkinson's disease | High | State the limitation plainly; request access to existing Parkinson's sleep cohorts for a follow-up |
| The RBD sample (22 patients, one center) is called too small | Medium | Report every estimate with its interval; the central experiments compare the same nights and do not depend on it |
| The floor-corrected rule fails on other detectors | Medium | Its valid range is stated; the RBDtector result is reported as a failed prediction with an exploratory explanation |
| Journal length limits | Low (SLEEP sets none) | Main text about 6,800 words; detail moved to the supplement |
| Journal policy on AI assistance | Certain to apply | Disclose AI use in the Methods or Acknowledgements and the cover letter, as SLEEP requires |
| Colab or dataset hosts change | Low | The notebook is self-contained and resumable; derived packs and results are kept on Drive |

## Ethics, data governance and research integrity

- **Participants.** All recordings were collected by others with their own ethical approval and released de-identified. This project contacted no one and made no attempt to re-identify anyone; as a secondary analysis of public data it is not expected to need new ethics approval, which should be confirmed with the university.
- **Licenses.** The data come under open licenses (ODC-By, CC BY 4.0, CC0, MIT). The attribution licenses require citing the datasets, which the paper does. Raw recordings are not redistributed; only derived summaries and results are kept.
- **Pre-registration.** The four decisive analyses had their hypotheses and pass/fail criteria committed to version control before they were run. Every criterion is reported as met or not met, including the misses.
- **Self-audit.** A reviewer-style audit of the code and drafts found two real problems (unused age data, and recordings without physical units scored as if they had them); both were fixed and everything was rerun before the later analyses.
- **Reporting standard.** The paper follows STARD 2015, the checklist for diagnostic accuracy studies, including a participant flow diagram and 2 x 2 tables.
- **Use of AI tools.** AI assistance was used in this project; the target journal requires this to be disclosed in the paper and the cover letter, and the authors decide the wording.
- **Not a medical device.** The findings concern how RWA is measured across equipment. Nothing here diagnoses or predicts anything for an individual, and the floor check is a research tool.

## Expected impact and future work

**For sleep laboratories.** Two numbers, computable from any recording in seconds, make RWA results comparable: the quiet-REM level (how noisy the equipment is) and the net N2/N3 level (how strongly it records muscle). The floor-check tool reports both, says whether the floor-corrected rule applies, and states how much muscle activity each published threshold demands on that equipment. Reporting these with every RWA result would let readers judge whether thresholds from another lab apply.

**For Parkinson's disease research.**

- Multi-center cohorts should check that recording floors do not differ between the groups they compare; adjusting for "center" helps only if each center's equipment is stable.
- Long-term studies should check whether equipment changed during follow-up: a rise of 0.6 microvolts in the floor lowered tonic RWA by as much as four and a half years of reported progression would raise it.
- Users of RBDtector should report each recording's floor and not expect its chin cut-off to transfer between systems.
- For "isolated RWA" studies, the REM Atonia Index definition (as in DREAMER) was the most stable across equipment.
- For recruiting people with RBD into prevention trials, automated scoring of routine sleep studies works best as a pre-filter for expert and video review, not as a diagnosis: even the best rule needed about eight studies reviewed per person found at 2% prevalence.

**For developers of scoring software.** The noise ladder is a reusable test: score the same nights with noise added in steps, and a robust method should not change its verdicts until the noise truly hides the muscle signal.

**Future work.** Validate in people with Parkinson's disease; extend floor correction to fine-resolution detectors by accounting for how much noise fluctuates over short windows; test whether visual scoring shares the mechanism by scoring the same nights at several display gains; add limb muscles, as SINBAR's full montage does; and re-derive cut-offs for automated scoring on a larger, multi-center RBD sample.

## Glossary

| Term | Meaning |
| --- | --- |
| AASM | American Academy of Sleep Medicine; publishes the standard sleep-scoring manual |
| Alpha-synucleinopathy | A family of brain diseases in which the protein alpha-synuclein clumps in nerve cells: Parkinson's disease, dementia with Lewy bodies, multiple system atrophy |
| Atonia | The normal muscle paralysis of REM sleep |
| AUC | Area under the ROC curve: how well a score ranks positives above negatives (0.5 = chance, 1 = perfect) |
| Background | The reference level a scoring rule compares muscle activity against; here the night's quiet-REM level |
| Band-pass and notch filters | Filters that keep a frequency range (10-100 Hz for muscle) and remove one frequency (mains hum at 50 or 60 Hz) |
| Bootstrap | Estimating uncertainty by resampling the data with replacement many times |
| DLB | Dementia with Lewy bodies |
| ECG, EEG, EMG, EOG | Recordings of the heart, brain, muscles and eyes |
| EDF | European Data Format, the standard file format for sleep recordings |
| Envelope (RMS) | The signal's amplitude over short windows: the square root of the mean of the squared samples |
| Epoch, mini-epoch | A 30-s scoring window; shorter windows (2-3 s) used to count twitches |
| Floor-corrected rule | This project's fix: demand the same muscle activity on every system by subtracting the noise in power |
| Hypnogram | The sequence of sleep stages through the night |
| Isolated RWA | REM sleep without atonia in someone without dream-enactment behavior; studied as a possible earlier stage |
| Leave-one-out cross-validation | Testing a choice (such as a cut-off) on each case after re-making the choice without it |
| Montreal, SINBAR | Two published methods for scoring RWA, named after the groups that developed them |
| Net N2/N3 level | Muscle level in deep sleep with the noise removed; a check of how strongly the equipment records muscle (gain) |
| Noise floor | The level of electrical noise in a recording, set by electrodes and amplifier |
| Noise ladder | Adding noise to the same recordings in steps to measure its effect |
| Phasic, tonic | Short muscle twitches versus sustained muscle tension |
| Positive predictive value (PPV) | The share of people flagged by a test who truly have the condition (precision) |
| Pre-registration | Writing down hypotheses and pass criteria before running the analysis |
| Prodromal | An early stage before the main symptoms of a disease appear |
| PSG | Polysomnography: an overnight recording of many body signals |
| Quiet-REM level | The 5th percentile of 1-s RMS chin amplitude during REM sleep; on a normal night, mostly noise |
| RAI | REM Atonia Index: the share of 1-s windows with near-zero muscle activity |
| RBD | REM sleep behavior disorder: acting out dreams because atonia fails |
| RBDtector | An open-source program that scores RWA automatically |
| REM, NREM (N1-N3) | Rapid-eye-movement sleep (dreaming, atonia) and the stages of non-REM sleep (light to deep) |
| RWA | REM sleep without atonia: muscle activity during REM sleep |
| Sensitivity, specificity | The share of true cases a test detects, and the share of non-cases it correctly clears |
| STARD | The reporting checklist for diagnostic accuracy studies |
| Wilson interval | A confidence interval for a proportion that behaves well with small samples |
| Youden's index | Sensitivity + specificity - 1; the cut-off that maximizes it balances the two |

## Key references

The full, verified list of 38 references is in the manuscript.

1. Postuma RB, et al. Risk and predictors of dementia and parkinsonism in idiopathic REM sleep behaviour disorder: a multicentre study. Brain. 2019;142:744-759. [doi:10.1093/brain/awz030](https://doi.org/10.1093/brain/awz030)
2. Montplaisir J, et al. Polysomnographic diagnosis of idiopathic REM sleep behavior disorder. Mov Disord. 2010;25:2044-2051. [doi:10.1002/mds.23257](https://doi.org/10.1002/mds.23257)
3. Frauscher B, et al. Normative EMG values during REM sleep for the diagnosis of REM sleep behavior disorder. Sleep. 2012;35:835-847. [doi:10.5665/sleep.1886](https://doi.org/10.5665/sleep.1886)
4. Ferri R, et al. Improved computation of the atonia index in normal controls and patients with REM sleep behavior disorder. Sleep Med. 2010;11:947-949. [doi:10.1016/j.sleep.2010.06.003](https://doi.org/10.1016/j.sleep.2010.06.003)
5. Cesari M, et al. Comparison of computerized methods for rapid eye movement sleep without atonia detection. Sleep. 2018;41:zsy133. [doi:10.1093/sleep/zsy133](https://doi.org/10.1093/sleep/zsy133)
6. Rothenbacher A, et al. RBDtector: an open-source software to detect REM sleep without atonia according to visual scoring criteria. Sci Rep. 2022;12:20886. [doi:10.1038/s41598-022-25163-9](https://doi.org/10.1038/s41598-022-25163-9)
7. Joza S, et al. Validation of RBDtector. J Sleep Res. 2025;34:e70037. [doi:10.1111/jsr.70037](https://doi.org/10.1111/jsr.70037)
8. Feemster JC, et al. Normative and isolated rapid eye movement sleep without atonia in adults without REM sleep behavior disorder. Sleep. 2019;42:zsz124. [doi:10.1093/sleep/zsz124](https://doi.org/10.1093/sleep/zsz124)
9. Sakuma T, et al. Diagnostic quantitative thresholds for REM sleep without atonia in Japanese patients with isolated RBD. Sleep. 2025;48:zsaf178. [doi:10.1093/sleep/zsaf178](https://doi.org/10.1093/sleep/zsaf178)
10. Postuma RB, et al. Severity of REM atonia loss in idiopathic REM sleep behavior disorder predicts Parkinson disease. Neurology. 2010;74:239-244. [doi:10.1212/WNL.0b013e3181ca0166](https://doi.org/10.1212/WNL.0b013e3181ca0166)
11. Iranzo A, et al. Excessive muscle activity increases over time in idiopathic REM sleep behavior disorder. Sleep. 2009;32:1149-1153. [doi:10.1093/sleep/32.9.1149](https://doi.org/10.1093/sleep/32.9.1149)
12. Ferri R, et al. Protocol for the DREAMER study. PLoS One. 2026;21:e0350467. [doi:10.1371/journal.pone.0350467](https://doi.org/10.1371/journal.pone.0350467)
13. Bossuyt PM, et al. STARD 2015. BMJ. 2015;351:h5527. [doi:10.1136/bmj.h5527](https://doi.org/10.1136/bmj.h5527)
14. Datasets: CAP Sleep Database ([PhysioNet](https://physionet.org/content/capslpdb/1.0.0/)); HMC sleep staging v1.1 ([doi:10.13026/t79q-fr32](https://doi.org/10.13026/t79q-fr32)); PhysioNet/CinC Challenge 2018 ([PhysioNet](https://physionet.org/content/challenge-2018/1.0.0/)); BOAS ([doi:10.18112/openneuro.ds005555.v1.1.3](https://doi.org/10.18112/openneuro.ds005555.v1.1.3)); Dreem Open Datasets (Guillot A, et al. IEEE Trans Neural Syst Rehabil Eng. 2020;28:1955-1965, [doi:10.1109/TNSRE.2020.3011181](https://doi.org/10.1109/TNSRE.2020.3011181)).
