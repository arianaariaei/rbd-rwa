# Pre-specified analysis: external cohorts (written 2026-09-27, before any of their EMG was read)

Committed before any chin EMG of the cohorts below has been processed. Only metadata were
read beforehand (licences, channel lists, sampling rates, units, stage coding, and the
structure of one DOD-H file). The rules, code paths and parameters are those already fixed
(published criteria as implemented; floor-corrected criteria of
preregistration_floor_corrected.md with B = 1.0 uV, guard 1.5, n = b / 0.91).

## Why

The noise floor explained the site difference between MGH and HMC and a floor-corrected
rule removed it (results_floor_2026-09-26.md). Both were shown on the cohorts in which they
were found. This analysis asks whether they hold on recording systems not used so far.

## Cohorts (request-free)

| cohort | source, licence | population | system | chin EMG |
|---|---|---|---|---|
| BOAS | OpenNeuro ds005555, CC0 | 128 nights, 100 adults from the general population (no psychotropic drugs, no severe disease), Zaragoza, Spain | Micromed SD plus | bipolar, 256 Hz, uV; no ECG channel |
| DOD-O | Dreem Open Datasets, Zenodo 15900394, MIT | 55 patients with suspected sleep-disordered breathing, Stanford Sleep Medicine Center, USA (the record without consensus scoring is excluded) | Somnomedics Somno HD | 1 EMG derivation, 250 Hz, uV; ECG |
| DOD-H | same | 25 healthy volunteers aged 18-65, IRBA, Bretigny-sur-Orge, France | Compumedics Siesta | 1 EMG, 250 Hz, uV; ECG |

DOD-O is primary; DOD-H is processed after it if Zenodo's throughput allows (about
1.6 MB/s per connection; the two sets are 32 and 25 GB). Predictions involving DOD-H are
evaluated only if it is processed. Mains: 60 Hz for DOD-O, 50 Hz for DOD-H and BOAS.

Optional, only if time allows: DREAMS subjects (20 healthy) and patients (27), Zenodo
2650142 (CC BY-NC-ND 3.0), Brainnet/Medatec system, 200 Hz.

Inclusion as before: chin EMG in physical units sampled at >= 200 Hz, expert or consensus
sleep stages in 30-s epochs, >= 10 min of REM. BOAS has several nights for some
participants: the primary analysis uses each participant's first recording (lowest
recording number); all nights are a sensitivity analysis.

Processing is unchanged: 10-100 Hz band-pass, notch at the local mains, heartbeat subtraction from R-peaks on the ECG channel where there is one. BOAS
has no ECG: R-peaks are detected on the chin EMG itself with the same detector and the same
plausibility test (35-130 beats/min, > 90% regular intervals); where they are not plausible
no heartbeat is removed, and the number of such nights is reported.

## Measures per night

Quiet-REM level (floor), floor signature, net N2/N3 and REM levels (noise removed), and the
positive calls of the published Montreal, SINBAR and RAI criteria, of Montreal-FC and
SINBAR-FC (B = 1.0 uV), and of SINBAR-FC at the cut-off re-derived on CAP (49.1%).

## Predictions

E1. **Scale.** Each new cohort's median net N2/N3 level is within 0.67-1.5 times MGH's
    (1.60 uV). If not, floor-corrected comparisons with that cohort are flagged as confounded
    by gain.
E2. **Quiet systems flag healthy people.** In every healthy cohort whose median floor is
    below 1.0 uV, the published SINBAR criterion flags at least 30% of nights.
E3. **Healthy cohorts agree once the floor is subtracted.** If the healthy cohorts' median
    floors differ by a factor of at least 1.5, published SINBAR positivity is higher in the
    quieter cohort, and the difference between them is at least halved under SINBAR-FC
    (likewise for Montreal if its published difference is >= 5 points).
E4. **Across all groups without RBD** recorded at >= 200 Hz in physical units (CAP
    same-system patients, MGH, HMC, BOAS, DOD-H, DOD-O, and DREAMS if added), the Spearman
    correlation between median floor and published SINBAR positivity is negative, and its
    absolute value is smaller under SINBAR-FC.
E5. **The portable cut-off stays specific.** The SINBAR-FC cut-off re-derived on CAP (49.1%)
    flags <= 10% of nights in each healthy cohort and <= 20% in DOD-O.
E6. **Out-of-sample dose-response.** DOD-O's published Montreal and SINBAR positivity lie
    within 10 points of MGH's noise-ladder curve interpolated at DOD-O's median floor (not
    applicable if that floor is outside the ladder's range, 0.56-2.84 uV).

Everything else (floor signature, age strata, all-night BOAS, the RAI) is descriptive.
