# Data requests: RBD and Parkinson's recordings from other centers

Prepared 2026-10-27. Excluded as agreed: NSRR (including NAPS) and the BDSP / Challenge 2026
data (CITI course). Nothing here has been sent; every letter is a draft for you (and ideally
your supervisor) to check, sign and send. Email addresses are not given where they could not
be confirmed: take them from the institutional page listed.

## Two ways to ask

1. **Run it locally (preferred).** The center runs `run_site.py` on its own computer and
   shares only one row of numbers per night (noise floor, gain check, RWA percentages and
   verdicts, under the published and floor-corrected rules, optionally also at a 1.5-µV
   floor). No recording leaves the center, so most centers need no data-use agreement, only
   their own permission to compute aggregate statistics. This is what the reviewer called the
   best fix for the one-center limitation.
2. **Data transfer** under the center's data-use agreement. Slower (ethics approval at your
   university is usually required first) and only worth it where (1) is refused.

What to ask for: at least 20 nights of patients with video-PSG-confirmed RBD (isolated or with
Parkinson's disease), and as many controls recorded on the same system; ideally also
Parkinson's disease without RBD. Chin EMG in microvolts at 200 Hz or more, with the 30-s
stages.

## Candidates

| Center (contact) | What they hold | Why it matters most | Route |
|---|---|---|---|
| **Bonn / Cologne** (PD Dr. Michael Sommerauer, University Hospital Bonn, Dept. of Parkinson, Sleep and Movement Disorders, Venusberg-Campus 1, 53127 Bonn; [page](https://www.medfak.uni-bonn.de/en/research/research-funding/accent/accent-fellows/michael-sommerauer)) | RBDtector development cohort: 21 PD with RBD, 16 PD without RBD, 81 iRBD, 56 controls (SOMNOscreen plus, 256 Hz); Cologne-Bonn cohort | Parkinson's patients with and without RBD on one system; RBDtector's authors (likely reviewers) | Letter A |
| **Aarhus** (Prof. Per Borghammer, Dr. Jesper Strøm, Aarhus University Hospital) | PACE: with CBC, 112 PD, 138 iRBD, 89 controls ([arXiv 2602.09793](https://arxiv.org/abs/2602.09793v1)) | Large PD and iRBD cohort, a second system | Letter A |
| **Copenhagen, Danish Center for Sleep Medicine** (Prof. Poul Jennum, Rigshospitalet) | DCSM clinical PSGs: 81 PD, 36 iRBD, 87 sleep-clinic controls | Clinical recordings like MGH and HMC, with PD and iRBD | Letter A |
| **Montreal, CARSM** (Prof. Ronald Postuma, Prof. Jean-François Gagnon, McGill / CIUSSS-NÎM) | RBDtector validation: 118 iRBD, 37 controls ([J Sleep Res 2025](https://doi.org/10.1111/jsr.70037)); the Montreal criteria were developed there | The floor of the system on which the Montreal thresholds were set | Letter A, plus the floor-check-only request (Letter B) |
| **Innsbruck** (Prof. Birgit Högl, Prof. Ambra Stefani, Medical University of Innsbruck, Sleep Disorders Unit) | SINBAR cohorts: iRBD, PD with RBD, controls | The SINBAR thresholds were set there | Letter A or B |
| **Tokyo** (Dr. Takashi Sakuma, Prof. Yuichi Inoue; Japan Somnology Center) | The Japanese iRBD cohort of Sakuma et al., Sleep 2025 | Directly tests whether equipment explains the lower Japanese thresholds (review M3) | Letter B (floor check only) |
| **Eindhoven / Kempenhaeghe** (Dr. Merel van Gilst, Prof. Sebastiaan Overeem; Eindhoven University of Technology and Kempenhaeghe Center for Sleep Medicine) | 485 clinical PSGs including 30 with RBD, used for single-channel chin-EMG atonia detection ([Van Gorp et al., J Parkinsons Dis 2026](https://doi.org/10.1177/1877718X261468531)) | A clinical cohort with RBD on a third system; the group works on automated chin-EMG scoring | Letter A |
| **Oxford Parkinson's Disease Centre** (Dr Michele Hu, University of Oxford) | Discovery cohort: about 300 patients with PSG-diagnosed RBD from three sleep clinics, Parkinson's disease and controls, followed longitudinally | The largest RBD collection found; several clinics means several recording systems | Letter A, or the OPDC's own data-access application |
| **Montreal Archive of Sleep Studies (MASS)**, CEAMS ([MASS page](http://www.ceams-carsm.ca/en/MASS)) | 200 laboratory PSGs of healthy adults (cohort 1, 18-76 years), with chin EMG | Same institution as the Montreal criteria; a new system for the floor analyses | Email request to the MASS team with a project description and proof of local research-ethics approval or exemption; then a license and download from Borealis |

## Letter A - run the open pipeline on your recordings

> Subject: Request: running an open RWA pipeline on your RBD/PD recordings (no data transfer)
>
> Dear Dr. [name],
>
> I am [name], [position] at [university], working with [supervisor]. We have studied
> automated scoring of REM sleep without atonia on openly licensed polysomnograms (CAP, HMC,
> MGH, BOAS, Dreem; 1,354 nights). Background-relative criteria (Montreal, SINBAR chin, and
> RBDtector's default rule) turned out to depend strongly on the recording system's noise
> floor: on the same nights, raising the floor from 0.86 to 1.5 µV lowered tonic RWA in RBD by
> 21 points, and the published cut-offs flagged 9% of patients at one hospital and 29% at
> another. A floor-corrected version of the rules removed most of this in pre-specified tests.
>
> The only open RBD recordings are 22 CAP patients from one center, and there are no open
> recordings of people with Parkinson's disease. We would be very grateful if your group could
> run our open pipeline on [iRBD / PD with and without RBD / control] recordings at your
> center. It is one command (`python run_site.py manifest.csv --ladder`), runs on a laptop,
> and writes only one row of numbers per night (noise floor, RWA percentages and verdicts);
> no recording or identifier leaves your center. We would analyse the shared numbers with
> you, and your contribution would of course be recognized by co-authorship.
>
> The code, the analysis plans (committed before each analysis was run) and the manuscript
> draft are available at [repository link]. I would be happy to adapt the script to your file
> formats or to meet online.
>
> With kind regards,
> [name, affiliation, email]

## Letter B - the floor check only (a few nights, a few minutes)

> Subject: Could you measure the EMG noise floor of your PSG system?
>
> Dear Dr. [name],
>
> [first paragraph as in Letter A]. Your [Montreal / SINBAR / Japanese] thresholds were derived
> on [system]. We would like to know that system's chin EMG noise floor, which needs nothing
> but a few ordinary nights: `python check_floor.py night.edf stages.txt` reports the quiet-REM
> level (in µV), a gain check and what each threshold means in microvolts on that system. The
> numbers from 5-10 nights of patients without RBD would let us state, rather than guess,
> whether equipment contributes to differences between published thresholds.
>
> [closing as in Letter A]

## Letter C - to RBDtector's authors (review M9; courtesy and check)

> Dear Dr. Sommerauer, dear Ms. Röthenbacher,
>
> Thank you for releasing RBDtector as open source. In a study of automated RWA scoring across
> open polysomnography databases we ran RBDtector (commit 7c9c73d) on about 400 nights through
> its own controller. To make it fast enough for cloud runs we vectorized one function
> (`find_rem_blocks`) and trimmed each input to the REM stretch; on 12 nights we verified that
> the output is identical to the program as released [result to be added]. We also tested a
> variant that replaces the baseline by a noise-corrected threshold. Before submitting the
> manuscript we would like to make sure we represent RBDtector correctly, and would welcome
> your comments on the attached description and results. [Optionally: Letter A.]

## Letter D - invitation to a sleep-medicine co-author (review C1, M11)

> Dear Dr. [name],
>
> [one paragraph summary as in Letter A]. Reviewers will rightly ask whether visual scoring
> shares the dependence on the recording's noise floor that we found for automated scoring.
> We have prepared a small blinded substudy (protocol attached, to be registered on OSF before
> scoring): 60 REM excerpts from 30 nights, each night once as recorded and once with added
> noise, scored with the SINBAR chin rules (about 20 hours of scoring). Would you, or a
> registered polysomnographic technologist in your team, be willing to do the scoring and join
> the paper as a co-author? We would also value your clinical review of the manuscript.
