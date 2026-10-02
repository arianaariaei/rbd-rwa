#!/bin/sh
# The Parkinson's analyses (paper/preregistration_parkinsons.md) on a fresh Colab
# runtime, reusing the scores already on Drive; everything new is copied back to
# Drive as it is made. Run from the code directory, e.g. in Colab's terminal:
#   cd /content/rbd-rwa && setsid nohup sh run_parkinsons_colab.sh > /content/pd.log 2>&1 < /dev/null &
# RBDtector needs about 75 s per night and step (both rules) on Colab's 2-core
# runtime, so the work can be split over two runtimes: PART=1 (the CAP ladder, then
# the analysis once part 2 is on Drive) and PART=2 (MGH, HMC and BOAS).
set -e
PART=${PART:-all}
D=/content/drive/MyDrive/rbd-rwa
export RBD_DURABLE_DIR=/content/durable PYTHONUNBUFFERED=1
R=$RBD_DURABLE_DIR/results
F=$RBD_DURABLE_DIR/figures
mkdir -p "$R" "$F" "$D/results" "$D/figures"
for f in external_scores.csv floor_ladder_scores.csv floor_scores.csv ladder_scores.csv; do
  if [ -f "$D/results/$f" ] && [ ! -f "$R/$f" ]; then cp "$D/results/$f" "$R/"; fi
done
O=rbdtector_scores.csv
if [ "$PART" = 2 ]; then O=rbdtector_scores_systems.csv; fi
if [ -f "$D/results/$O" ] && [ ! -f "$R/$O" ]; then cp "$D/results/$O" "$R/"; fi
# RBDtector runs in the environment its requirements.txt specifies (2021 versions;
# pandas 2 removed DataFrame.append, which its output writer uses)
E=/content/rbdt_env
if [ ! -x "$E/bin/python" ]; then
  pip -q install uv
  uv venv -q -p 3.9 "$E"
  uv pip install -q -p "$E/bin/python" "numpy~=1.21.2" "pandas~=1.3.3" "scipy~=1.7.1" \
    "openpyxl~=3.0.8" "pyEDFlib~=0.1.22" "wfdb~=3.4.0"
fi
RB="$E/bin/python run_rbdtector.py --out $O --mirror $D/results"
if [ "$PART" != 2 ]; then
  $RB --cohort cap
  # exploratory, added after PD2b was missed: RBDtector on noise alone (~10 minutes)
  if [ ! -f "$R/rbdtector_noise.csv" ]; then $E/bin/python run_rbdtector_noise.py; fi
  cp "$R/rbdtector_noise.csv" "$D/results/"
fi
if [ "$PART" != 1 ]; then
  $RB --cohort chal18 --sample 100
  $RB --cohort hmc
  $RB --cohort boas
fi
if [ "$PART" = 2 ]; then touch "$D/results/rbdtector_part2.done"; echo PART2_DONE; exit 0; fi
if [ "$PART" = 1 ]; then
  while [ ! -f "$D/results/rbdtector_part2.done" ]; do sleep 60; done
  cp "$D/results/rbdtector_scores_systems.csv" "$R/"
fi
python run_parkinsons.py
python run_ladder.py --from-csv
cp "$R"/parkinsons_* "$R"/ladder_report.md "$D/results/"
cp "$F"/fig10_* "$F"/fig6_* "$F"/fig7_* "$D/figures/"
echo PD_DONE
