"""Build the self-contained Colab notebook from the source tree.

The notebook carries its own copy of every source file (written out with
%%writefile), so running it needs nothing but a Google account: no git clone,
no copying code to Drive. Re-run this script after changing any source file.

Results go straight to Google Drive (MyDrive/rbd-rwa): each night is reduced
to a 1-2 MB pack, so even a thousand nights fit, and a disconnected session
loses nothing - re-running continues where it stopped.

    python tools/build_notebook.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "RBD_RWA.ipynb"
CODE_DIR = "/content/rbd-rwa"
DRIVE_DIR = "/content/drive/MyDrive/rbd-rwa"
FILES = ["src/__init__.py", "src/config.py", "src/edf.py", "src/ecg.py", "src/fetch.py",
         "src/cap.py", "src/extract.py", "src/pack.py", "src/cohorts.py", "src/rwa.py",
         "run_extract.py", "run_cohort.py", "run_score.py"]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.strip("\n")}


def main():
    cells = [
        md("""
# REM sleep without atonia across open sleep cohorts

Everything runs in the cloud; nothing is downloaded to your computer. Every
dataset used here is open (no application, no credential):

| cohort | what | licence |
|---|---|---|
| CAP | 22 RBD patients + healthy sleepers + other sleep disorders (Italy) | ODC-By |
| HMC | 148 clinical PSGs, Haaglanden Medisch Centrum (Netherlands) | CC BY 4.0 |
| Challenge 2018 | 994 clinical PSGs, Massachusetts General Hospital (USA) | ODC-By |

Each night is streamed from PhysioNet's open mirror, reduced to a 1-2 MB file
in Google Drive (`MyDrive/rbd-rwa/packs`), and the raw file is deleted.
Progress is recorded after every night, so if the session disconnects just
run the cells again and it continues where it stopped.

Run order: **Runtime -> Run all** (the first cell asks for access to Drive).
"""),
        code(f"""
from google.colab import drive
drive.mount('/content/drive')
import os
os.environ['RBD_DURABLE_DIR'] = '{DRIVE_DIR}'
!pip -q install wfdb
!mkdir -p {CODE_DIR}/src {DRIVE_DIR}
%cd {CODE_DIR}
"""),
    ]
    for rel in FILES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        cells.append(code(f"%%writefile {CODE_DIR}/{rel}\n{src}"))
    cells += [
        md("""
## 1. CAP: repack the already-extracted nights
(If `MyDrive/rbd-rwa/derived` is empty, first run `!python run_extract.py`.)
"""),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort cap"),
        md("## 2. HMC: 148 nights (about 15 GB streamed, ~10 minutes)"),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort hmc --workers 3"),
        md("## 3. Challenge 2018: 994 nights (about 130 GB streamed, roughly an hour)"),
        code(f"!cd {CODE_DIR} && python run_cohort.py --cohort chal18 --workers 3"),
        md("## 4. Score every night with every method"),
        code(f"!cd {CODE_DIR} && python run_score.py"),
    ]
    nb = {"cells": cells,
          "metadata": {"colab": {"provenance": []},
                       "kernelspec": {"name": "python3", "display_name": "Python 3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({len(cells)} cells, {OUT.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
