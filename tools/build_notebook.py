"""Build the self-contained Colab notebook from the source tree.

The notebook carries its own copy of every source file (written out with
%%writefile), so running it needs nothing but a Google account: no git clone,
no copying code to Drive. Re-run this script after changing any source file.

Work happens on the Colab machine's own disk (/content/durable), which is fast
and needs no permissions; results are copied to Google Drive only in the last
step, and copied back at the start of a later session to resume.

    python tools/build_notebook.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "RBD_RWA_CAP.ipynb"
CODE_DIR = "/content/rbd-rwa"
WORK_DIR = "/content/durable"
DRIVE_DIR = "/content/drive/MyDrive/rbd-rwa"
FILES = ["src/__init__.py", "src/config.py", "src/edf.py", "src/fetch.py",
         "src/cap.py", "src/extract.py", "src/rwa.py",
         "run_extract.py", "run_score.py"]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.strip("\n")}


def main():
    cells = [
        md(f"""
# REM sleep without atonia: CAP extraction and scoring

Runs entirely in the cloud. Each of CAP's 108 recordings is streamed from
PhysioNet's open mirror (about 40 GB in total) onto this Colab machine,
reduced to a small EMG-envelope file, and the raw file is deleted.

* Steps 1-2 work on the Colab machine's own disk and need no permissions.
* Step 3 copies the results to Google Drive (`MyDrive/rbd-rwa`) so they
  survive the session. It asks for permission to access Drive.
* In a later session, run step 0 first to bring earlier results back, and
  extraction continues where it stopped.
"""),
        code(f"""
import os
os.environ['RBD_DURABLE_DIR'] = '{WORK_DIR}'
!mkdir -p {CODE_DIR}/src {WORK_DIR}
%cd {CODE_DIR}
"""),
    ]
    for rel in FILES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        cells.append(code(f"%%writefile {CODE_DIR}/{rel}\n{src}"))
    cells += [
        md("## 0. (Later sessions only) Restore earlier results from Google Drive"),
        code(f"""
from google.colab import drive
drive.mount('/content/drive')
!mkdir -p {DRIVE_DIR} && rsync -a {DRIVE_DIR}/ {WORK_DIR}/ && du -sh {WORK_DIR}
"""),
        md("## 1. Extract every CAP recording"),
        code(f"!cd {CODE_DIR} && python run_extract.py"),
        md("## 2. Score every recording with every RWA method"),
        code(f"!cd {CODE_DIR} && python run_score.py"),
        md("## 3. Save results to Google Drive"),
        code(f"""
from google.colab import drive
drive.mount('/content/drive')
!mkdir -p {DRIVE_DIR} && rsync -a {WORK_DIR}/ {DRIVE_DIR}/ && du -sh {DRIVE_DIR}
"""),
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
