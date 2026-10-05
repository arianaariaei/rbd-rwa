#!/bin/sh
# The injection experiment (paper/preregistration_injection.md) on a fresh Colab
# runtime. Every night's scores are copied to Drive as they are made, so a restart
# continues where it stopped. Run from the code directory, e.g. in Colab's terminal:
#   cd /content/rbd-rwa && setsid nohup sh run_inject_colab.sh > /content/inject.log 2>&1 < /dev/null &
# About 20 s of computing per night on Colab's 2-core runtime, plus the downloads
# (the Dreem sets come from Zenodo at a few MB/s). To split the work over two
# runtimes: PART=2 (the Dreem sets) on one, PART=1 (everything else, then the
# analysis once part 2 is on Drive) on the other; both need Drive.
PART=${PART:-all}
D=/content/drive/MyDrive/rbd-rwa
export RBD_DURABLE_DIR=/content/durable PYTHONUNBUFFERED=1
R=$RBD_DURABLE_DIR/results
F=$RBD_DURABLE_DIR/figures
mkdir -p "$R" "$F" "$D/results" "$D/figures" "$D/inject"
# the noise-ladder scores of the earlier run (criterion B2)
if [ -f "$D/results/ladder_scores.csv" ] && [ ! -f "$R/ladder_scores.csv" ]; then
  cp "$D/results/ladder_scores.csv" "$R/"
fi
I="python run_inject.py --workers 3 --mirror $D/inject"
$I --donors
if [ "$PART" != 2 ]; then
  $I --cohort cap
  $I --cohort hmc
  $I --cohort boas
  $I --cohort chal18 --every 3
fi
if [ "$PART" != 1 ]; then
  $I --cohort dodo
  $I --cohort dodh
fi
if [ "$PART" = 2 ]; then touch "$D/inject/part2.done"; echo PART2_DONE; exit 0; fi
if [ "$PART" = 1 ]; then
  while [ ! -f "$D/inject/part2.done" ]; do sleep 60; done
  $I --cohort dodo          # nothing left to compute: restores part 2's scores from Drive
  $I --cohort dodh
fi
# white-noise predictions on this runtime (the same seeds as the frozen file in paper/)
if [ ! -f "$R/inject_whitenoise_a50.csv" ]; then python sim_injection.py 2; fi
python run_inject_report.py
cp "$R"/inject_* "$D/results/"
cp "$F"/fig11_* "$D/figures/" 2>/dev/null
echo INJECT_DONE
