"""Build the self-contained Colab notebook from the source tree.

The notebook carries its own copy of every source file (written out with
%%writefile), so running it needs nothing but a Google account: no git clone,
no copying code to Drive. Re-run this script after changing any source file.

    python tools/build_notebook.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "RBD_RWA_Colab.ipynb"
CODE_DIR = "/content/rbd-rwa"
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
        md("""
# REM sleep without atonia: CAP extraction and scoring

Runs entirely in the cloud. Each recording is streamed from PhysioNet's open
mirror into this machine's temporary disk, reduced to a small EMG-envelope file
that is saved to **Google Drive** (`MyDrive/rbd-rwa`), and the raw file is
deleted. Progress is recorded after every recording, so if the session
disconnects just run all cells again and it continues where it stopped.

Run order: **Runtime -> Run all**.
"""),
        code("""
from google.colab import drive
drive.mount('/content/drive')
"""),
        code(f"""
!mkdir -p {CODE_DIR}/src
%cd {CODE_DIR}
"""),
    ]
    for rel in FILES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        cells.append(code(f"%%writefile {CODE_DIR}/{rel}\n{src}"))
    cells += [
        code(f"""
import os
assert os.path.isdir('/content/drive/MyDrive'), 'Google Drive is not mounted - run the first cell'
!cd {CODE_DIR} && python -c "from src import config; config.describe()"
"""),
        md("## 1. Extract every CAP recording (about 40 GB streamed, a few hundred MB kept)"),
        code(f"!cd {CODE_DIR} && python run_extract.py"),
        md("## 2. Score every recording with every RWA method"),
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
