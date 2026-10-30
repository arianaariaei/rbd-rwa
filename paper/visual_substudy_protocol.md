# Does visual scoring of REM sleep without atonia depend on the recording's noise floor?

*Protocol of a blinded visual-scoring substudy. Written 2026-10-27 to be registered on OSF
(osf.io, "OSF Preregistration" template) before any excerpt is scored. Status: not registered,
no scoring done.*

## Background

In an automated pipeline, the background-relative RWA criteria (Montreal, SINBAR) flagged far
more patients on recording systems with a low noise floor, and adding noise to the same nights
lowered RWA percentages (the noise ladder). The published criteria are visual. A visual
scorer judges "twice the background" by eye at a chosen display gain, which may impose an
implicit absolute detection limit that an automated relative rule lacks. Whether visual
scoring shares the noise-floor dependence is therefore unknown.

## Questions and hypotheses

- **H1 (agreement).** How closely do automated SINBAR chin scores (published and
  floor-corrected) agree with visual scores of the same REM epochs? Measured by ICC(2,1)
  (absolute agreement) and Bland-Altman bias and limits; no directional hypothesis.
- **H2 (primary).** Adding band-limited noise that raises a night's quiet-REM level to 1.5 µV
  lowers the visually scored SINBAR "any" percentage (one-sided Wilcoxon signed-rank test over
  nights, alpha 0.05).
- **H3.** The visual change is a fraction of the automated published change; we estimate that
  fraction (mean visual change / mean automated change, bootstrap 95% CI). A fraction near 1
  means visual scoring shares the mechanism fully; near 0, that visual scoring is protected by
  an implicit absolute limit.

## Design

- **Nights.** 30 nights drawn with a fixed seed (20261027): 10 patients with RBD (CAP Sleep
  Database, main recording system), 10 clinical PSGs from MGH (PhysioNet Challenge 2018) and 10
  from HMC (Haaglanden Medisch Centrum). All openly licensed.
- **Eligibility (amended 27 Oct 2026, before registration and before any scoring).** Each
  group's nights are taken in a seeded random order, and a night is used only if it has a stretch
  of 20 consecutive REM epochs and a quiet-REM level below 1.2 uV as recorded; the first 10
  eligible nights per group are used and the skipped ones are listed with the reason. Reason: the
  first draw included an MGH night whose longest REM period was 6 epochs and whose level was
  already 1.5 uV, so its two copies were identical; such pairs cannot show an effect of noise and
  cost scoring time.
- **Excerpts.** From each night, the first stretch of 20 consecutive REM epochs with 4 epochs of
  context on each side; chin EMG, a central EEG channel and
  the ECG; the original stage scoring as annotations.
- **Two copies per night.** As recorded, and with band-limited white noise (10-100 Hz) added to
  the chin EMG at the level that raises the night's quiet-REM level (5th percentile of 1-s REM
  RMS) to 1.5 µV, computed on the whole night.
- **Blinding.** The 60 excerpts are numbered in random order (seed 20261028). The scorer receives
  no information on cohort, diagnosis or copy. The key is held by the organizer and opened only
  after the scoring sheets are returned.
- **Scoring.** One experienced scorer (registered polysomnographic technologist or
  somnologist), SINBAR chin rules: "any" activity per 3-s mini-epoch (at least 0.1 s, at least
  twice the background) and tonic activity per 30-s epoch; artifacts marked and excluded;
  scorer's usual display settings, recorded. A second scorer on all excerpts, if available,
  gives inter-rater agreement (secondary).
- **Automated scores** of the same epochs (our pipeline, whole-night background) are computed
  when the excerpts are made and stored with the key.

## Analysis (`run_visual_analysis.py`, written before scoring)

H1: ICC(2,1) and Bland-Altman on the 30 excerpts as recorded, for "any" and tonic, against the
automated published and floor-corrected scores. H2: per night, visual "any" % (noisy copy) minus
(as recorded); one-sided Wilcoxon; mean with bootstrap 95% CI; by cohort (descriptive). H3: the
ratio of mean changes with a bootstrap CI over nights. Excerpts with more than 50% of
mini-epochs marked as artifact are excluded (reported).

## Sample size

On the same nights, the automated published "any" percentage fell by about 20 points at this
noise level (SD of the per-night change about 15 points). Thirty pairs give more than 95% power
(one-sided alpha 0.05) to detect a visual change half that size (10 points). The design is
limited by scoring time (60 excerpts of 20 epochs, about 20 hours), not by power.

## Ethics

Secondary analysis of de-identified, openly licensed recordings; no contact with participants.

## What the result will change in the paper

H2 not rejected and H3 near 0: the mechanism is specific to automated implementations, and the
paper is framed accordingly. H2 rejected with H3 clearly above 0: visual scoring shares part of
the mechanism, and the recommendation to report the noise floor applies to visual scoring too.
