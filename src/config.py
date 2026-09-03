"""Paths that work identically on Colab, locally, or anywhere else.

The guiding rule: RAW recordings are disposable, DERIVED data is precious.
Raw PSG is hundreds of MB per night and lives in scratch (Colab's ephemeral
disk); the extracted envelope + hypnogram is a few MB and lives in a durable
directory (Google Drive), so a disconnected session never loses real work.
"""
import os
from pathlib import Path


def _first_existing(*candidates):
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    return None


ON_COLAB = "COLAB_GPU" in os.environ or Path("/content").exists()

# Durable storage: Drive on Colab, the project folder otherwise.
DRIVE = _first_existing(
    os.environ.get("RBD_DRIVE_DIR"),
    "/content/drive/MyDrive",
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DURABLE = Path(os.environ.get("RBD_DURABLE_DIR",
                              (DRIVE / "rbd-rwa") if DRIVE else PROJECT_ROOT / "data"))

# Scratch: fast, large, and wiped when the session ends. Raw EDFs only.
SCRATCH = Path(os.environ.get("RBD_SCRATCH_DIR",
                              "/content/scratch" if ON_COLAB else PROJECT_ROOT / "data" / "raw"))

DERIVED   = DURABLE / "derived"      # one compact .npz per recording
MANIFESTS = DURABLE / "manifests"    # progress records, so a restart resumes
FIGURES   = DURABLE / "figures"
RESULTS   = DURABLE / "results"

for d in (DERIVED, MANIFESTS, FIGURES, RESULTS, SCRATCH):
    d.mkdir(parents=True, exist_ok=True)

# Envelope sampling rate. Phasic RWA bursts are >= 0.1 s, so 50 Hz (20 ms bins)
# gives 5 samples across the shortest event a method needs to see, while being
# ~100x smaller than the raw signal.
ENV_FS = 50

# EMG band. 10 Hz high-pass removes movement/drift and ECG baseline; 100 Hz is
# the conventional upper edge, lowered automatically when Nyquist forbids it.
EMG_BAND = (10.0, 100.0)


def describe():
    print(f"on Colab : {ON_COLAB}")
    print(f"durable  : {DURABLE}   (derived data, survives disconnects)")
    print(f"scratch  : {SCRATCH}   (raw EDFs, disposable)")
