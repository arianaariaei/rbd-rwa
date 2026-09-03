"""Resumable downloads. PhysioNet's TLS drops connections mid-transfer, so
every request retries and partial files resume with an HTTP Range header."""
import time
import urllib.request
from pathlib import Path

CAP_BASE = "https://physionet.org/files/capslpdb/1.0.0/"


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
    if total and dest.exists() and dest.stat().st_size == total:
        return dest
    for i in range(tries):
        have = dest.stat().st_size if dest.exists() else 0
        if total and have == total:
            return dest
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
    if total and got != total:
        raise IOError(f"{dest.name}: got {got} of {total} bytes")
    return dest


def cap_records():
    """All CAP record names, grouped by cohort prefix."""
    txt = urllib.request.urlopen(CAP_BASE + "RECORDS", timeout=45).read().decode()
    recs = [r.replace(".edf", "") for r in txt.split()]
    groups = {}
    for r in recs:
        key = "".join(c for c in r if not c.isdigit())
        groups.setdefault(key, []).append(r)
    return groups


def fetch_cap(record, scratch: Path):
    """Download one CAP recording (.edf + .txt) into scratch."""
    edf = download(CAP_BASE + record + ".edf", Path(scratch) / f"{record}.edf")
    ann = download(CAP_BASE + record + ".txt", Path(scratch) / f"{record}.txt")
    return edf, ann
