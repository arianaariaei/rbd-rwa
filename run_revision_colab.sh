#!/bin/sh
# The revision analyses (paper/preregistration_revision.md) on a fresh Colab runtime,
# reusing the packs and scores already on Drive. Run from the code directory, e.g. in
# Colab's terminal:
#   cd /content/rbd-rwa && setsid nohup sh run_revision_colab.sh > /content/revision.log 2>&1 < /dev/null &
# PART=1: re-analyses, the noise arms and the visual-scoring excerpts (about 4 h);
# PART=2: the RBDtector checks (about 4 h, RBDtector's own environment). Without PART,
# both in turn. The injection experiment has its own runner (run_inject_colab.sh).
PART=${PART:-all}
D=/content/drive/MyDrive/rbd-rwa
export RBD_DURABLE_DIR=/content/durable PYTHONUNBUFFERED=1
R=$RBD_DURABLE_DIR/results
mkdir -p "$R" "$D/results"
for f in ladder_scores.csv floor_ladder_scores.csv floor_scores.csv external_scores.csv \
         rbdtector_scores.csv rbdtector_scores_systems.csv; do
  if [ -f "$D/results/$f" ] && [ ! -f "$R/$f" ]; then cp "$D/results/$f" "$R/"; fi
done
if [ "$PART" != 2 ]; then
  python run_revision.py && cp "$R"/revision_* "$D/results/"
  python run_noise_arms.py --library --mirror "$D"
  python run_noise_arms.py --cohort chal18 --mirror "$D"
  python run_noise_arms.py --cohort cap --mirror "$D"
  python run_noise_arms.py --report && cp "$R"/noise_arms_* "$D/results/"
  if [ ! -f "$D/visual_study_KEY/key.csv" ]; then
    pip -q install pyedflib
    python run_visual_package.py --out "$D/visual_study"
  fi
fi
if [ "$PART" != 1 ]; then
  E=/content/rbdt_env
  if [ ! -x "$E/bin/python" ]; then
    pip -q install uv
    uv venv -q -p 3.9 "$E"
    uv pip install -q -p "$E/bin/python" "numpy~=1.21.2" "pandas~=1.3.3" "scipy~=1.7.1" \
      "openpyxl~=3.0.8" "pyEDFlib~=0.1.22" "wfdb~=3.4.0"
  fi
  for part in verify mgh boas; do
    $E/bin/python run_rbdtector_checks.py --part $part --mirror "$D/results"
  done
  $E/bin/python run_rbdtector_checks.py --report && cp "$R"/rbdtector_checks* "$D/results/"
fi
echo REVISION_DONE
