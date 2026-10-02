#!/bin/sh
# The Parkinson's analyses (paper/preregistration_parkinsons.md) on a fresh Colab
# runtime, reusing the scores already on Drive; everything new is copied back to
# Drive as it is made. Run from the code directory, e.g. in Colab's terminal:
#   cd /content/rbd-rwa && setsid nohup sh run_parkinsons_colab.sh > /content/pd.log 2>&1 < /dev/null &
set -e
D=/content/drive/MyDrive/rbd-rwa
export RBD_DURABLE_DIR=/content/durable PYTHONUNBUFFERED=1
R=$RBD_DURABLE_DIR/results
F=$RBD_DURABLE_DIR/figures
mkdir -p "$R" "$F" "$D/results" "$D/figures"
for f in external_scores.csv floor_ladder_scores.csv floor_scores.csv ladder_scores.csv rbdtector_scores.csv; do
  if [ -f "$D/results/$f" ] && [ ! -f "$R/$f" ]; then cp "$D/results/$f" "$R/"; fi
done
python run_rbdtector.py --cohort cap --mirror "$D/results"
python run_rbdtector.py --cohort chal18 --sample 100 --mirror "$D/results"
python run_rbdtector.py --cohort hmc --mirror "$D/results"
python run_rbdtector.py --cohort boas --mirror "$D/results"
python run_parkinsons.py
python run_ladder.py --from-csv
cp "$R"/parkinsons_* "$R"/ladder_report.md "$D/results/"
cp "$F"/fig10_* "$F"/fig6_* "$F"/fig7_* "$D/figures/"
echo PD_DONE
