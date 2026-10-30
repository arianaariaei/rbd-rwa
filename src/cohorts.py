"""Open polysomnography cohorts, each reduced to the same compact pack.

Every cohort here is downloadable with no application and no credential:

  cap     CAP Sleep Database (PhysioNet, ODC-By). 22 RBD patients plus
          healthy sleepers and other sleep disorders. Italy, 50 Hz mains.
  chal18  PhysioNet/CinC Challenge 2018 training set (PhysioNet, ODC-By).
          994 clinical PSGs from Massachusetts General Hospital with sleep
          stages, respiratory events and arousals, age and sex. USA, 60 Hz.
  hmc     Haaglanden Medisch Centrum sleep staging database (PhysioNet,
          CC BY 4.0). 151 clinical PSGs. The Netherlands, 50 Hz.

External cohorts (paper/preregistration_external.md):

  boas    Bitbrain Open Access Sleep dataset (OpenNeuro ds005555, CC0). 128
          nights of 100 adults from the general population, Micromed SD plus,
          chin EMG at 256 Hz, no ECG. Spain, 50 Hz.
  dodh    Dreem Open Dataset, healthy (Zenodo 15900394, MIT). 25 healthy
          volunteers, Compumedics Siesta, 250 Hz. France, 50 Hz.
  dodo    Dreem Open Dataset, obstructive sleep apnea (same). 55 patients,
          Somnomedics Somno HD, 250 Hz. Stanford, USA, 60 Hz.

Added 2026-10-30 (paper/preregistration_anphy.md):

  anphy   ANPHY-Sleep (OSF r26fh). 28 healthy adults aged 20-44, Nihon Kohden
          JE-120, 1000 Hz; chin EMG units unverified. Montreal, Canada, 60 Hz.

A cohort adapter knows how to list records, fetch one record's files into
scratch, and read from them: chin EMG, ECG, leg EMG (if any), the hypnogram in
30 s epochs from the start of the signal, per-epoch event flags and any
demographics. `extract_pack` turns that into a pack (see pack.py).
"""
import csv
import io
import urllib.request
from pathlib import Path

import numpy as np

from .config import ENV_FS, HARMONIZED_BAND
from .ecg import r_peaks, plausible, artifact_ratio
from .extract import envelope
from .fetch import download_any
from .pack import build_pack

EPOCH_SEC = 30
PHYSIONET = ("https://physionet-open.s3.amazonaws.com/{db}/",
             "https://physionet.org/files/{db}/")


def _mirrors(db):
    return tuple(m.format(db=db) for m in PHYSIONET)


def _read_text(db, name):
    for base in _mirrors(db):
        try:
            return urllib.request.urlopen(base + name, timeout=60).read().decode("latin-1")
        except Exception:
            continue
    raise IOError(f"cannot fetch {db}/{name}")


EEG_PREFERRED = ("C4-M1", "C3-M2", "C4-A1", "C3-A2", "C4A1", "C3A2")


def _central_eeg(channels):
    """A central EEG channel of an EDF (C4 or C3, against a mastoid if possible)."""
    norm = lambda s: s.upper().replace(" ", "").replace("EEG", "")
    for want in EEG_PREFERRED:
        for c in channels:
            if norm(c.label) == want:
                return c
    return next((c for c in channels if norm(c.label).startswith(("C4", "C3"))), None)


# ══════════════════════════════════════════════════════════════════════════════
#  CAP (streamed like the other cohorts, for the noise ladder; the main CAP
#  pipeline goes through run_extract.py and is repacked by run_cohort.py)
# ══════════════════════════════════════════════════════════════════════════════

class CAP:
    name, mains = "cap", 50.0

    def records(self):
        from .fetch import cap_records
        return [r for group in cap_records().values() for r in group]

    def demographics(self):
        return {}

    def fetch(self, rec, scratch):
        from .fetch import fetch_cap
        edf, txt = fetch_cap(rec, scratch)
        return {"edf": edf, "txt": txt}

    def read(self, rec, files):
        from .cap import build_hypnogram
        from .ecg import find_ecg
        from .edf import read_header, read_channel
        from .extract import find_emg, read_source
        hdr = read_header(files["edf"])
        chin_src, _ = find_emg(hdr)
        if chin_src is None:
            raise ValueError(f"{rec}: no chin EMG among {[c.label for c in hdr.channels]}")
        chin, fs, unit_known, label, _ = read_source(hdr, chin_src)
        ecg_src = find_ecg(hdr)
        ecg, fs_e = read_source(hdr, ecg_src)[:2] if ecg_src is not None else (None, None)
        eeg_ch = _central_eeg(hdr.channels)
        eeg, fs_g = read_channel(hdr, eeg_ch)[:2] if eeg_ch else (None, None)
        hyp, _ = build_hypnogram(files["edf"], files["txt"], len(chin) / fs)
        return dict(chin=chin, fs=fs, unit_known=unit_known, chin_label=label,
                    ecg=ecg, fs_ecg=fs_e, legs=[], hypnogram=hyp, flags={}, extra={},
                    eeg=eeg, fs_eeg=fs_g, eeg_label=eeg_ch.label if eeg_ch else None)


# ══════════════════════════════════════════════════════════════════════════════
#  CHALLENGE 2018 (MGH)
# ══════════════════════════════════════════════════════════════════════════════

class Chal18:
    name, db, mains = "chal18", "challenge-2018/1.0.0", 60.0
    STAGES = {"W": 0, "N1": 1, "N2": 2, "N3": 3, "R": 4}

    def records(self):
        return [r.strip("/").split("/")[-1]
                for r in _read_text(self.db, "training/RECORDS").split()]

    def demographics(self):
        rows = csv.DictReader(io.StringIO(_read_text(self.db, "age-sex.csv")))
        return {r["Record"]: {"age": float(r["Age"]), "sex": r["Sex"]} for r in rows}

    def fetch(self, rec, scratch):
        out = {}
        for ext in ("hea", "mat", "arousal"):
            out[ext] = download_any(f"training/{rec}/{rec}.{ext}",
                                    Path(scratch) / f"{rec}.{ext}", _mirrors(self.db))
        return out

    def read(self, rec, files):
        import wfdb
        base = str(files["hea"])[:-4]
        names = wfdb.rdheader(base).sig_name
        eeg_name = next((n for n in ("C4-M1", "C3-M2") if n in names), None)
        sig = wfdb.rdrecord(base, channel_names=[n for n in ("Chin1-Chin2", "ECG", eeg_name)
                                                 if n in names])
        col = {n: i for i, n in enumerate(sig.sig_name)}

        def channel(name):                        # microvolts, and whether units are known
            if name not in col:
                return None, False
            unit = sig.units[col[name]].lower()
            return sig.p_signal[:, col[name]] * (1e3 if unit == "mv" else 1.0), \
                unit in ("uv", "mv")

        chin, unit_known = channel("Chin1-Chin2")
        ecg, _ = channel("ECG")
        eeg, _ = channel(eeg_name)
        fs = float(sig.fs)
        n_ep = int(len(chin) / fs // EPOCH_SEC)

        ann = wfdb.rdann(base, "arousal")
        hyp = np.full(n_ep, -1, np.int8)
        stage_marks = [(s, self.STAGES[n]) for s, n in zip(ann.sample, ann.aux_note)
                       if n in self.STAGES]
        for (s0, code), nxt in zip(stage_marks, stage_marks[1:] + [(len(chin), None)]):
            a = int(round(s0 / fs / EPOCH_SEC))
            b = int(round(nxt[0] / fs / EPOCH_SEC))
            hyp[a:min(b, n_ep)] = code

        flags = {"resp": np.zeros(n_ep, np.int8), "arousal": np.zeros(n_ep, np.int8)}
        events = {"resp": [], "arousal": []}      # (start, end) in seconds
        open_ev = {}
        for s, note in zip(ann.sample, ann.aux_note):
            if note.startswith("("):
                open_ev[note[1:]] = s
            elif note.endswith(")") and note[:-1] in open_ev:
                label, s0 = note[:-1], open_ev.pop(note[:-1])
                kind = "resp" if label.startswith("resp_") else \
                    "arousal" if label.startswith("arousal_") else None
                if kind:
                    events[kind].append((s0 / fs, s / fs))
                    a = int(s0 / fs // EPOCH_SEC)
                    b = int(s / fs // EPOCH_SEC)
                    flags[kind][a:min(b + 1, n_ep)] = 1
        n_resp = sum(1 for n in ann.aux_note if n.startswith("(resp_"))
        sleep_h = np.isin(hyp, (1, 2, 3, 4)).sum() * EPOCH_SEC / 3600.0
        extra = {"ahi": round(n_resp / sleep_h, 1) if sleep_h > 0 else None}
        return dict(chin=chin, fs=fs, unit_known=unit_known,
                    chin_label="Chin1-Chin2", ecg=ecg, fs_ecg=fs, legs=[],
                    hypnogram=hyp, flags=flags, extra=extra, events=events,
                    eeg=eeg, fs_eeg=fs, eeg_label=eeg_name)


# ══════════════════════════════════════════════════════════════════════════════
#  HAAGLANDEN MEDISCH CENTRUM
# ══════════════════════════════════════════════════════════════════════════════

class HMC:
    name, db, mains = "hmc", "hmc-sleep-staging/1.1", 50.0
    STAGES = {"W": 0, "N1": 1, "N2": 2, "N3": 3, "R": 4}
    # v1.1 lists 151 recordings: SN001-SN154 minus SN014, SN064 and SN135,
    # which the release notes withdrew for erroneous, unfixable signal data.

    def records(self):
        return [Path(x).stem for x in _read_text(self.db, "RECORDS").split()]

    def demographics(self):
        return {}                       # only group-level age/sex are published

    def fetch(self, rec, scratch):
        return {"edf": download_any(f"recordings/{rec}.edf", Path(scratch) / f"{rec}.edf",
                                    _mirrors(self.db)),
                "txt": download_any(f"recordings/{rec}_sleepscoring.txt",
                                    Path(scratch) / f"{rec}_sleepscoring.txt",
                                    _mirrors(self.db))}

    def read(self, rec, files):
        from .edf import read_header, read_channel
        hdr = read_header(files["edf"])
        chin_ch = next(c for c in hdr.channels if "CHIN" in c.label.upper())
        ecg_ch = next((c for c in hdr.channels if "ECG" in c.label.upper()), None)
        eeg_ch = _central_eeg(hdr.channels)
        chin, fs, unit_known = read_channel(hdr, chin_ch)
        ecg, fs_e = (read_channel(hdr, ecg_ch)[:2]) if ecg_ch else (None, None)
        eeg, fs_g = (read_channel(hdr, eeg_ch)[:2]) if eeg_ch else (None, None)
        n_ep = int(len(chin) / fs // EPOCH_SEC)
        hyp = np.full(n_ep, -1, np.int8)
        text = Path(files["txt"]).read_text(encoding="latin-1").splitlines()
        for line in text[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 5 or not parts[4].startswith("Sleep stage"):
                continue
            code = self.STAGES.get(parts[4].split()[-1])
            e = int(round(float(parts[2]) / EPOCH_SEC))
            if code is not None and 0 <= e < n_ep:
                hyp[e] = code
        return dict(chin=chin, fs=fs, unit_known=unit_known, chin_label=chin_ch.label,
                    ecg=ecg, fs_ecg=fs_e, legs=[], hypnogram=hyp, flags={}, extra={},
                    eeg=eeg, fs_eeg=fs_g, eeg_label=eeg_ch.label if eeg_ch else None)


class HMCDegraded(HMC):
    """
    HMC recordings re-acquired, in software, the way the MGH chin EMG was:
    optionally scaled by `gain`, resampled to `fs_out` and quantized to
    `lsb_uv` microvolt steps. MGH stores chin EMG at 200 Hz with 1 uV
    resolution, and its quiet-REM level (~0.6 uV) is below that step; HMC's is
    ~1.5 uV. Scaling HMC down to the MGH level first puts the signal where the
    step size can matter. Comparing HMC with its degraded copies isolates how
    much of a site difference that hardware alone can create.
    """
    def __init__(self, name, fs_out=None, lsb_uv=None, gain=None):
        self.name, self.fs_out, self.lsb_uv, self.gain = name, fs_out, lsb_uv, gain

    def read(self, rec, files):
        d = super().read(rec, files)
        x, fs = d["chin"], d["fs"]
        if self.gain:
            x = x * self.gain
        if self.fs_out and self.fs_out != fs:
            from fractions import Fraction
            from scipy.signal import resample_poly
            f = Fraction(int(self.fs_out), int(fs)).limit_denominator(1000)
            x = resample_poly(x, f.numerator, f.denominator)
            fs = float(self.fs_out)
        if self.lsb_uv:
            x = np.round(x / self.lsb_uv) * self.lsb_uv
        d.update(chin=x, fs=fs)
        return d


class Chal18Noisy(Chal18):
    """
    MGH recordings with white noise added to the chin EMG, the reverse test:
    MGH's quiet-REM level (~0.6 uV) raised to HMC's (~1.5 uV), as a noisier
    amplifier or higher electrode impedance would. The noise is seeded by
    record name, so reruns are identical.
    """
    def __init__(self, name, noise_uv):
        self.name, self.noise_uv = name, noise_uv

    def read(self, rec, files):
        import zlib
        d = super().read(rec, files)
        rng = np.random.default_rng(zlib.crc32(rec.encode()))
        d["chin"] = d["chin"] + rng.normal(0.0, self.noise_uv, len(d["chin"]))
        return d


# ══════════════════════════════════════════════════════════════════════════════
#  EXTERNAL COHORTS
# ══════════════════════════════════════════════════════════════════════════════

class BOAS:
    """
    Bitbrain Open Access Sleep dataset (OpenNeuro ds005555, CC0): adults from
    the general population, one or more nights each (participants.tsv 'pid'),
    Micromed SD plus PSG, bipolar chin EMG at 256 Hz, consensus AASM stages of
    three scorers in the events file (0 W, 1 N1, 2 N2, 3 N3, 4 REM; 8 and -2 =
    disconnection / artifact). There is no ECG channel: heartbeats are found
    on the chin EMG itself (see `_beats`).
    """
    name, mains = "boas", 50.0
    BASE = "https://s3.amazonaws.com/openneuro.org/ds005555/"

    def _participants(self):
        txt = urllib.request.urlopen(self.BASE + "participants.tsv", timeout=60).read().decode()
        return list(csv.DictReader(io.StringIO(txt), delimiter="\t"))

    def records(self):
        return [r["participant_id"] for r in self._participants()]

    def demographics(self):
        num = lambda v: float(v) if v not in (None, "", "n/a") else None
        return {r["participant_id"]: {"age": num(r.get("age")), "sex": r.get("sex"),
                                      "pid": r.get("pid")} for r in self._participants()}

    def fetch(self, rec, scratch):
        from .fetch import download
        stem = f"{rec}/eeg/{rec}_task-Sleep_acq-psg"
        return {"edf": download(self.BASE + stem + "_eeg.edf", Path(scratch) / f"{rec}.edf"),
                "tsv": download(self.BASE + stem + "_events.tsv", Path(scratch) / f"{rec}.tsv")}

    def read(self, rec, files):
        from .edf import read_header, read_channel
        hdr = read_header(files["edf"])
        chin_ch = next(c for c in hdr.channels if c.label.upper().endswith("EMG"))
        chin, fs, unit_known = read_channel(hdr, chin_ch)
        eeg_ch = next((c for c in hdr.channels if c.label.upper().endswith(("C4", "C3"))), None)
        eeg, fs_g = read_channel(hdr, eeg_ch)[:2] if eeg_ch else (None, None)
        n_ep = int(len(chin) / fs // EPOCH_SEC)
        hyp = np.full(n_ep, -1, np.int8)
        with open(files["tsv"], encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                e, code = int(round(float(r["onset"]) / EPOCH_SEC)), int(float(r["stage_hum"]))
                if 0 <= e < n_ep and code in (0, 1, 2, 3, 4):
                    hyp[e] = code
        return dict(chin=chin, fs=fs, unit_known=unit_known, chin_label=chin_ch.label,
                    ecg=None, fs_ecg=None, beats_from_chin=True, legs=[], hypnogram=hyp,
                    flags={}, extra={}, eeg=eeg, fs_eeg=fs_g,
                    eeg_label=eeg_ch.label if eeg_ch else None)


class _RangeReader:
    """Byte ranges of one URL, with retries (Zenodo serves ~1.6 MB/s per connection,
    so large members are fetched as many ranges in parallel)."""
    def __init__(self, url):
        self.url = url

    def get(self, a, b, tries=8):
        import time
        for i in range(tries):
            try:
                req = urllib.request.Request(self.url, headers={"Range": f"bytes={a}-{b - 1}"})
                data = urllib.request.urlopen(req, timeout=300).read()
                if len(data) == b - a:
                    return data
            except Exception:
                pass
            time.sleep(min(60, 3 * 2 ** i))
        raise IOError(f"range {a}-{b} of {self.url} failed")


class _RangeFile(io.RawIOBase):
    """A seekable file over HTTP ranges - enough for zipfile to read a central directory."""
    def __init__(self, url, block=1 << 16):
        self.r, self.pos, self.block = _RangeReader(url), 0, block
        head = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60)
        self.size = int(head.headers["Content-Length"])
        self.c0, self.c = -1, b""

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        n = self.size - self.pos if n is None or n < 0 else min(n, self.size - self.pos)
        if n <= 0:
            return b""
        a, b = self.pos, self.pos + n
        if not (self.c0 <= a and b <= self.c0 + len(self.c)):
            self.c0 = a
            self.c = self.r.get(a, min(self.size, a + max(n, self.block)))
        self.pos = b
        return self.c[a - self.c0: b - self.c0]


class DOD:
    """
    Dreem Open Datasets (Zenodo 15900394, MIT license): one h5 file per night
    inside a zip per dataset, with signals/eeg/*, signals/emg/* and ECG in uV at
    250 Hz and a consensus hypnogram of five scorers (-1 not scored, 0 W, 1 N1,
    2 N2, 3 N3, 4 REM). A record's member is fetched with parallel byte-range
    requests and inflated locally.
    """
    URL = "https://zenodo.org/records/15900394/files/{}.zip?download=1"
    UNSCORED = {"5d8e93a5-d26a-436d-bc2c-e9527dc92cbf"}   # no consensus (release notes)
    FS = 250.0

    def __init__(self, name, mains, threads=8, chunk=32 << 20):
        self.name, self.mains, self.threads, self.chunk = name, mains, threads, chunk
        self._members = None

    def members(self):
        if self._members is None:
            import zipfile
            z = zipfile.ZipFile(_RangeFile(self.URL.format(self.name)))
            self._members = {Path(i.filename).stem: i for i in z.infolist()
                             if i.filename.endswith(".h5") and "__MACOSX" not in i.filename
                             and i.file_size > 1e6}
        return self._members

    def records(self):
        return sorted(r for r in self.members() if r not in self.UNSCORED)

    def demographics(self):
        return {}

    def fetch(self, rec, scratch):
        import struct
        import zlib
        from concurrent.futures import ThreadPoolExecutor
        info = self.members()[rec]
        rr = _RangeReader(self.URL.format(self.name))
        head = rr.get(info.header_offset, info.header_offset + 30)
        n, m = struct.unpack("<HH", head[26:30])
        start = info.header_offset + 30 + n + m
        parts = [(a, min(a + self.chunk, start + info.compress_size))
                 for a in range(start, start + info.compress_size, self.chunk)]
        out = Path(scratch) / f"{rec}.h5"
        inflate = zlib.decompressobj(-15) if info.compress_type == 8 else None
        with ThreadPoolExecutor(self.threads) as ex, open(out, "wb") as f:
            for i in range(0, len(parts), self.threads):          # in order, bounded memory
                for data in ex.map(lambda p: rr.get(*p), parts[i: i + self.threads]):
                    f.write(inflate.decompress(data) if inflate else data)
            if inflate:
                f.write(inflate.flush())
        if out.stat().st_size != info.file_size:
            raise IOError(f"{rec}: inflated {out.stat().st_size} of {info.file_size} bytes")
        return {"h5": out}

    def read(self, rec, files):
        import h5py
        is_ecg = lambda k: "ECG" in k.upper() or "EKG" in k.upper()
        with h5py.File(files["h5"], "r") as h:
            sig = h["signals"]
            keys = [k for k in sig["emg"].keys() if not is_ecg(k)]
            emg_name = next((k for k in keys if any(t in k.upper() for t in
                                                    ("CHIN", "EMG", "MENT", "SUBM"))), keys[0])
            chin = np.asarray(sig["emg"][emg_name][:], dtype=np.float64)
            ecg = None
            for group in sig.values():
                if isinstance(group, h5py.Group):
                    for k in group.keys():
                        if is_ecg(k):
                            ecg = np.asarray(group[k][:], dtype=np.float64)
            eeg_name = next((k for k in ("C3_M2", "C4_M1") if k in sig["eeg"]), None)
            eeg = np.asarray(sig["eeg"][eeg_name][:], dtype=np.float64) if eeg_name else None
            stages = np.asarray(h["hypnogram"][:])
        n_ep = int(len(chin) / self.FS // EPOCH_SEC)
        hyp = np.full(n_ep, -1, np.int8)
        k = min(n_ep, len(stages))
        hyp[:k] = np.where(np.isin(stages[:k], (0, 1, 2, 3, 4)), stages[:k], -1)
        return dict(chin=chin, fs=self.FS, unit_known=True, chin_label=f"emg/{emg_name}",
                    ecg=ecg, fs_ecg=self.FS if ecg is not None else None, legs=[],
                    hypnogram=hyp, flags={}, extra={}, eeg=eeg, fs_eeg=self.FS,
                    eeg_label=eeg_name)


class ANPHY:
    """
    ANPHY-Sleep (OSF r26fh, Wei et al., Sci Data 2024): healthy adults aged 20-44,
    one night each (28 released; EPCTL08 is not on OSF), Montreal Neurological
    Institute, Nihon Kohden JE-120 at 1000 Hz. One zip per subject holding the EDF
    (94 signals) and a stage file ("stage<TAB>start s<TAB>duration s"; W N1 N2 N3 R,
    "L" marks lights). Chin EMG = ChEMG1 - ChEMG2, ECG = ECG1 - ECG2. The
    polygraphic channels carry the unit "?"; they count as microvolts only if `uv`
    is set, which follows the unit check of paper/preregistration_anphy.md.
    """
    name, mains = "anphy", 60.0
    API = "https://api.osf.io/v2/nodes/r26fh/files/osfstorage/?page%5Bsize%5D=100"
    SUBJECTS = "https://osf.io/download/trmbu/"
    STAGE = {"W": 0, "N1": 1, "N2": 2, "N3": 3, "R": 4}

    def __init__(self, uv=False):
        self.uv, self._zips = uv, None

    def _list(self):
        if self._zips is None:
            import json
            zips, url = {}, self.API
            while url:
                j = json.loads(urllib.request.urlopen(url, timeout=60).read().decode())
                for d in j["data"]:
                    n = d["attributes"]["name"]
                    if n.startswith("EPCTL") and n.endswith(".zip"):
                        zips[n[:7]] = d["links"]["download"]
                url = j["links"].get("next")
            self._zips = zips
        return self._zips

    def records(self):
        return sorted(self._list())

    def demographics(self):
        txt = urllib.request.urlopen(self.SUBJECTS, timeout=60).read().decode("utf-8-sig")
        return {r["Subjects ID"].strip(): {"age": float(r["Age"]), "sex": r["Sex"].strip()}
                for r in csv.DictReader(io.StringIO(txt))}

    def fetch(self, rec, scratch):
        import shutil
        import zipfile
        from .fetch import download
        scratch = Path(scratch)
        z = download(self._list()[rec], scratch / f"{rec}.zip")
        out = {}
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                kind = n.lower().rsplit(".", 1)[-1]
                if kind in ("edf", "txt") and kind not in out:
                    out[kind] = scratch / f"{rec}.{kind}"
                    with zf.open(n) as src, open(out[kind], "wb") as dst:
                        shutil.copyfileobj(src, dst, 1 << 24)
        z.unlink()
        return out

    def read(self, rec, files):
        from .edf import read_header, read_channel
        hdr = read_header(files["edf"])
        chin1, fs, _ = read_channel(hdr, "ChEMG1")
        chin = chin1 - read_channel(hdr, "ChEMG2")[0]
        ecg1, fs_e, _ = read_channel(hdr, "ECG1")
        ecg = ecg1 - read_channel(hdr, "ECG2")[0]
        eeg_ch = _central_eeg(hdr.channels)        # C4 in most nights; not in all
        eeg, fs_g = read_channel(hdr, eeg_ch)[:2] if eeg_ch else (None, None)
        n_ep = int(len(chin) / fs // EPOCH_SEC)
        hyp = np.full(n_ep, -1, np.int8)
        with open(files["txt"], encoding="latin-1") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3 or parts[0] not in self.STAGE:
                    continue
                e0 = int(round(float(parts[1]) / EPOCH_SEC))
                for e in range(e0, e0 + max(1, int(round(float(parts[2]) / EPOCH_SEC)))):
                    if 0 <= e < n_ep:
                        hyp[e] = self.STAGE[parts[0]]
        return dict(chin=chin, fs=fs, unit_known=self.uv, chin_label="ChEMG1-ChEMG2",
                    ecg=ecg, fs_ecg=fs_e, legs=[], hypnogram=hyp, flags={}, extra={},
                    eeg=eeg, fs_eeg=fs_g, eeg_label=eeg_ch.label if eeg_ch else None)


# 0.39 = median quiet-REM level MGH / HMC (0.59 / 1.52 uV). 1.5 uV of white noise
# at 200 Hz leaves ~1.4 uV in the 10-95 Hz band: sqrt(0.59^2 + 1.4^2) ~ 1.52 uV.
COHORTS = {"chal18": Chal18(), "hmc": HMC(),
           "hmc_q1uv": HMCDegraded("hmc_q1uv", lsb_uv=1.0),
           "hmc_mgh": HMCDegraded("hmc_mgh", fs_out=200, lsb_uv=1.0),
           "hmc_low": HMCDegraded("hmc_low", gain=0.39),
           "hmc_low_mgh": HMCDegraded("hmc_low_mgh", fs_out=200, lsb_uv=1.0, gain=0.39),
           "chal18_noise": Chal18Noisy("chal18_noise", noise_uv=1.5),
           "cap": CAP(),
           "boas": BOAS(), "dodh": DOD("dodh", mains=50.0), "dodo": DOD("dodo", mains=60.0),
           # units unverified (preregistration_anphy.md, unit check): not microvolts
           "anphy": ANPHY(uv=False)}


# ══════════════════════════════════════════════════════════════════════════════
#  COMMON: raw signals -> pack
# ══════════════════════════════════════════════════════════════════════════════

def _beats(d):
    """R-peak times (s) from the record's ECG, or none if they do not look real.
    Records without ECG may ask for the chin EMG itself to be searched for the
    heartbeat it carries (same detector, same plausibility test)."""
    if d.get("ecg") is not None:
        sig, fs = d["ecg"], d["fs_ecg"]
    elif d.get("beats_from_chin"):
        sig, fs = d["chin"], d["fs"]
    else:
        return np.empty(0)
    beats = r_peaks(sig, fs)
    return beats if plausible(beats, len(sig) / fs) else np.empty(0)


def extract_pack(cohort, rec, d, demo=None):
    """Envelopes, heartbeat removal and packing for one record's signals."""
    beats = _beats(d)
    x, fs, mains = d["chin"], d["fs"], cohort.mains
    rms, mav, band = envelope(x, fs, mains=mains, beats_s=beats)
    rms_h, mav_h, band_h = envelope(x, fs, band=HARMONIZED_BAND, mains=mains, beats_s=beats)
    rms_raw, _, _ = envelope(x, fs, mains=mains)
    legs = [envelope(l, fs_l, mains=mains)[0] for l, fs_l in d.get("legs", [])]
    meta = {
        "record": rec, "cohort": cohort.name, "chin_channel": d["chin_label"],
        "chin_fs": fs, "band": list(band), "band_harmonized": list(band_h),
        "unit_known": bool(d["unit_known"]), "mains_notch": mains,
        "ecg": {"beats": int(len(beats)),
                "artifact_ratio_before": round(artifact_ratio(rms_raw, ENV_FS, beats), 3),
                "artifact_ratio_after": round(artifact_ratio(rms, ENV_FS, beats), 3)},
        "duration_s": round(len(x) / fs, 1),
        **(demo or {}), **d.get("extra", {}),
    }
    chin = {"rms": rms, "mav": mav, "rms_h": rms_h, "mav_h": mav_h, "rms_with_ecg": rms_raw}
    return build_pack(chin, legs, d["hypnogram"], ENV_FS, EPOCH_SEC, meta, d.get("flags"))


# ══════════════════════════════════════════════════════════════════════════════
#  THE NOISE LADDER: the same night at several noise floors
# ══════════════════════════════════════════════════════════════════════════════

LADDER_UV = (0.5, 1.0, 1.5, 2.0, 3.0)   # in-band RMS of the added noise, uV
TARGETS_UV = (1.5, 2.0)                 # quiet-REM level after harmonization, uV
EEG_BAND = (40.0, 90.0)                 # where EEG is mostly the system's own noise


def quiet_level(rms, hypnogram, env_fs=ENV_FS):
    """5th percentile of 1 s RMS over REM: the background the relative
    criteria are multiples of ('p5_rem' in rwa.py)."""
    from .rwa import mini_epoch_rms
    per = int(round(env_fs * EPOCH_SEC))
    hyp = np.asarray(hypnogram)[: len(rms) // per]
    rem = np.flatnonzero(hyp == 4)
    if len(rem) == 0:
        return float("nan")
    r, _ = mini_epoch_rms(rms[(rem[:, None] * per + np.arange(per)[None, :]).reshape(-1)],
                          env_fs, 1.0)
    return float(np.percentile(r, 5)) if len(r) >= 10 else float("nan")


def eeg_floor(eeg, fs, hypnogram, mains, band=EEG_BAND):
    """The 40-90 Hz floor (5th percentile of 1 s RMS) of an EEG channel in N2/N3
    and in REM: an estimate of the recording system's own noise, measured on a
    channel other than the chin."""
    from .extract import bandpass, bin_envelope
    if eeg is None or not fs or fs / 2.0 - 5.0 < band[0] + 10.0:
        return {}
    x, (lo, hi) = bandpass(eeg, fs, band, mains)
    sec, _ = bin_envelope(x, fs, env_fs=1)
    n = min(len(sec), len(hypnogram) * EPOCH_SEC)
    stage = np.repeat(np.asarray(hypnogram), EPOCH_SEC)[:n]
    out = {"band": [lo, hi]}
    for name, codes in (("nrem", (2, 3)), ("rem", (4,))):
        v = sec[:n][np.isin(stage, codes)]
        out[f"floor_{name}_uv"] = round(float(np.percentile(v, 5)), 4) if len(v) >= 60 else None
    return out


def extract_ladder_pack(cohort, rec, d, demo=None):
    """
    The night's chin EMG as recorded (native band, heartbeat removed) and with
    white noise added in band: at each LADDER_UV level, and at the level that
    raises its quiet-REM level to each TARGETS_UV. Filtering and heartbeat
    removal are linear, so the signal and one unit-RMS noise track (seeded by
    record name) are filtered once and every copy is their sum - the same noise
    draw scaled, i.e. common random numbers across levels.
    """
    import zlib
    from .ecg import subtract_heartbeat
    from .extract import bandpass, bin_envelope
    beats = _beats(d)
    x, fs, mains, hyp = d["chin"], d["fs"], cohort.mains, d["hypnogram"]
    xf, band = bandpass(x, fs, mains=mains)
    if len(beats):
        xf = subtract_heartbeat(xf, fs, beats)
    rms, mav = bin_envelope(xf, fs)
    chin = {"rms": rms, "mav": mav}
    level = quiet_level(rms, hyp)
    ladder = {}
    if d["unit_known"] and np.isfinite(level):
        rng = np.random.default_rng(zlib.crc32(rec.encode()))
        nf, _ = bandpass(rng.normal(0.0, 1.0, len(x)), fs, mains=mains)
        edge = int(5 * fs)
        nf /= np.sqrt(np.mean(nf[edge:-edge] ** 2))
        for u in LADDER_UV:
            r, m = bin_envelope(xf + u * nf, fs)
            chin[f"rms_n{round(u * 100):03d}"], chin[f"mav_n{round(u * 100):03d}"] = r, m
            ladder[f"n{round(u * 100):03d}"] = {"added_uv": u, "level_uv": round(quiet_level(r, hyp), 3)}
        for t in TARGETS_UV:
            # The 5th percentile catches seconds where the noise itself dips, so
            # sqrt(t^2 - level^2) undershoots; rescale until within 1% of t.
            s, r, m, got = float(np.sqrt(max(t * t - level * level, 0.0))), rms, mav, level
            for _ in range(4):
                if s <= 0 or abs(got - t) <= 0.01 * t:
                    break
                r, m = bin_envelope(xf + s * nf, fs)
                got = quiet_level(r, hyp)
                if abs(got - t) > 0.01 * t:
                    s *= np.sqrt((t * t - level * level) / max(got * got - level * level, 1e-9))
            chin[f"rms_h{round(t * 100):03d}"], chin[f"mav_h{round(t * 100):03d}"] = r, m
            ladder[f"h{round(t * 100):03d}"] = {"added_uv": round(s, 3), "level_uv": round(got, 3)}
        del nf
    meta = {
        "record": rec, "cohort": cohort.name, "chin_channel": d["chin_label"],
        "chin_fs": fs, "band": list(band), "unit_known": bool(d["unit_known"]),
        "mains_notch": mains, "duration_s": round(len(x) / fs, 1),
        "level_uv": round(level, 4) if np.isfinite(level) else None, "ladder": ladder,
        "ecg": {"beats": int(len(beats))},
        "eeg": dict(eeg_floor(d.get("eeg"), d.get("fs_eeg"), hyp, mains),
                    channel=d.get("eeg_label")),
        **(demo or {}), **d.get("extra", {}),
    }
    return build_pack(chin, [], hyp, ENV_FS, EPOCH_SEC, meta, d.get("flags"))
