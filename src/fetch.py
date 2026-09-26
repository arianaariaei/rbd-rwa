"""Resumable downloads. PhysioNet's TLS drops connections mid-transfer, so
every request retries and partial files resume with an HTTP Range header.

Open PhysioNet databases are mirrored byte-for-byte on AWS Open Data
(s3://physionet-open), which is far faster from cloud notebooks than
physionet.org, so the mirror is tried first and PhysioNet is the fallback."""
import time
import urllib.request
from pathlib import Path

CAP_MIRRORS = (
    "https://physionet-open.s3.amazonaws.com/capslpdb/1.0.0/",
    "https://physionet.org/files/capslpdb/1.0.0/",
)
CAP_BASE = CAP_MIRRORS[-1]


def remote_size(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            return int(urllib.request.urlopen(req, timeout=45)
                       .headers.get("Content-Length", 0))
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(3)


def download(url, dest: Path, tries=10, quiet=False):
    """Fetch `url` to `dest`, resuming if a partial file is already there."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = remote_size(url)
    if total is None:
        raise IOError(f"cannot reach {url}")
    if dest.exists() and dest.stat().st_size == total:
        return dest
    for i in range(tries):
        have = dest.stat().st_size if dest.exists() else 0
        if have == total:
            return dest
        if have > total:                          # stale file from another source
            dest.unlink()
            have = 0
        try:
            headers = {"Range": f"bytes={have}-"} if have else {}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "ab") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
        except Exception as e:
            if not quiet:
                print(f"    {dest.name}: {type(e).__name__}, resuming "
                      f"({dest.stat().st_size / 1e6 if dest.exists() else 0:.0f} MB)")
            time.sleep(3)
    got = dest.stat().st_size if dest.exists() else 0
    if got != total:
        raise IOError(f"{dest.name}: got {got} of {total} bytes")
    return dest


def download_any(name, dest: Path, mirrors=CAP_MIRRORS):
    """Try each mirror in turn; the first one that completes wins."""
    last = None
    for base in mirrors:
        try:
            return download(base + name, dest, quiet=True)
        except Exception as e:
            last = e
    raise IOError(f"{name}: all mirrors failed ({last})")


def cap_records():
    """All CAP record names, grouped by cohort prefix."""
    txt = None
    for base in CAP_MIRRORS:
        try:
            txt = urllib.request.urlopen(base + "RECORDS", timeout=45).read().decode()
            break
        except Exception:
            continue
    if txt is None:
        raise IOError("cannot fetch the CAP RECORDS list from any mirror")
    recs = [r.replace(".edf", "") for r in txt.split()]
    groups = {}
    for r in recs:
        key = "".join(c for c in r if not c.isdigit())
        groups.setdefault(key, []).append(r)
    return groups


def cap_demographics():
    """
    Age and sex of every CAP subject, from the database's gender-age.xlsx,
    keyed by record name. The sheet has no header and two typos ("SBD" for
    sdb, "RDB11" for rbd11). Read with the standard library, so no Excel
    package is needed. Returns {} if no mirror answers.
    """
    import io
    import zipfile
    import xml.etree.ElementTree as ET
    raw = None
    for base in CAP_MIRRORS:
        try:
            raw = urllib.request.urlopen(base + "gender-age.xlsx", timeout=60).read()
            break
        except Exception:
            continue
    if raw is None:
        return {}
    z = zipfile.ZipFile(io.BytesIO(raw))
    m = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    shared = ["".join(t.text or "" for t in si.iter(m + "t"))
              for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(m + "si")]
    out = {}
    for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(m + "row"):
        vals = []
        for c in row.iter(m + "c"):
            v = c.find(m + "v")
            vals.append(shared[int(v.text)] if c.get("t") == "s"
                        else (v.text if v is not None else ""))
        if len(vals) < 3:
            continue
        rec = vals[0].strip().lower().replace("sbd", "sdb").replace("rdb", "rbd")
        try:
            out[rec] = {"sex": vals[1].strip().upper()[:1], "age": float(vals[2])}
        except ValueError:
            continue
    return out


def fetch_cap(record, scratch: Path):
    """Download one CAP recording (.edf + .txt) into scratch."""
    edf = download_any(record + ".edf", Path(scratch) / f"{record}.edf")
    ann = download_any(record + ".txt", Path(scratch) / f"{record}.txt")
    return edf, ann
