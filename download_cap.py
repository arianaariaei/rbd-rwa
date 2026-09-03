"""Download a subset of the CAP Sleep Database (PhysioNet, open access).

Resumable: re-running skips files already complete, and partial files are
resumed with an HTTP Range request. PhysioNet's TLS drops connections
intermittently, so every request is retried.
"""
import sys, time, urllib.request
from pathlib import Path

BASE = "https://physionet.org/files/capslpdb/1.0.0/"
OUT  = Path(__file__).resolve().parent / "data" / "raw"


def remote_size(name, tries=5):
    for i in range(tries):
        try:
            r = urllib.request.Request(BASE + name, method="HEAD")
            return int(urllib.request.urlopen(r, timeout=45).headers.get("Content-Length", 0))
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(3)


def fetch(name, tries=8):
    dest = OUT / name
    total = remote_size(name)
    if total and dest.exists() and dest.stat().st_size == total:
        print(f"  {name:<14} already complete ({total/1e6:.0f} MB)")
        return True
    for i in range(tries):
        have = dest.stat().st_size if dest.exists() else 0
        if total and have == total:
            return True
        try:
            headers = {"Range": f"bytes={have}-"} if have else {}
            req = urllib.request.Request(BASE + name, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "ab") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            got = dest.stat().st_size
            if total is None or got == total:
                print(f"  {name:<14} OK ({got/1e6:.0f} MB)")
                return True
            print(f"  {name:<14} short ({got/1e6:.0f}/{total/1e6:.0f} MB), resuming")
        except Exception as e:
            print(f"  {name:<14} attempt {i+1}: {type(e).__name__}, resuming")
            time.sleep(3)
    print(f"  {name:<14} FAILED")
    return False


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    subjects = sys.argv[1:] or ["rbd1", "rbd2", "rbd3", "rbd4", "n1", "n2", "n3", "n5"]
    print(f"Downloading {len(subjects)} subjects to {OUT}\n")
    ok = 0
    for s in subjects:
        a = fetch(s + ".edf")
        b = fetch(s + ".txt")     # hypnogram + CAP event annotations
        ok += a and b
    used = sum(p.stat().st_size for p in OUT.glob("*"))
    print(f"\n{ok}/{len(subjects)} subjects complete, {used/1e9:.2f} GB on disk")
