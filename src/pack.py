"""Compact per-recording storage: full detail for REM, summaries for the rest.

RWA is measured in REM sleep. Everything else a method needs from the rest of
the night is a background level, which 1-second summaries of N2/N3 provide.
Keeping 20 ms resolution for REM epochs only shrinks a night from ~15 MB to
~2 MB, which is what makes a thousand-night cohort fit in Google Drive.

A pack holds, for chin EMG rows ROWS (all heartbeat-cleaned unless named
otherwise):
    rem        (n_rows, n_rem_epochs, bins_per_epoch) float16
    rem_legs   (n_legs, n_rem_epochs, bins_per_epoch) float16   (RMS)
    rem_epochs (n_rem_epochs,) int32  - epoch numbers in the night
    nrem_1s    (n_rows, n_seconds) float16 - 1 s RMS (rms rows) or mean
               (mav rows) over N2/N3
    hypnogram  (n_epochs,) int8       - the whole night, for context
    epoch_flags {name: (n_epochs,) int8} - e.g. respiratory event, arousal
    meta       json
"""
import json

import numpy as np

REM_CODE = 4
NREM_CODES = (2, 3)
ROWS = ("rms", "mav", "rms_h", "mav_h", "rms_with_ecg")
F16_MAX = 65000.0


def _one_second(env, env_fs, how):
    n = len(env) // env_fs
    blocks = env[: n * env_fs].reshape(n, env_fs)
    return blocks.mean(axis=1) if how == "mean" else np.sqrt((blocks ** 2).mean(axis=1))


def build_pack(chin, legs, hypnogram, env_fs, epoch_sec, meta, epoch_flags=None):
    """
    chin: dict row -> full-night envelope (float32), for the rows in ROWS that
    exist. legs: list of full-night RMS envelopes. Returns a pack dict.
    """
    per = int(round(env_fs * epoch_sec))
    n_bins = min(len(v) for v in chin.values())
    n_ep = min(len(hypnogram), n_bins // per)
    hyp = np.asarray(hypnogram[:n_ep], dtype=np.int8)
    # the standard rows first, then any others (e.g. noise-ladder copies)
    rows = [r for r in ROWS if r in chin] + [r for r in chin if r not in ROWS]

    rem_ep = np.flatnonzero(hyp == REM_CODE).astype(np.int32)
    idx = rem_ep[:, None] * per + np.arange(per)[None, :]
    rem = np.stack([chin[r][idx] for r in rows]) if len(rem_ep) \
        else np.zeros((len(rows), 0, per), np.float32)
    rem_legs = np.stack([l[idx] for l in legs]) if (legs and len(rem_ep)) \
        else np.zeros((len(legs or []), len(rem_ep), per), np.float32)

    nrem_mask = np.isin(hyp, NREM_CODES).repeat(per)
    nrem_1s = []
    for r in rows:
        env = chin[r][: n_ep * per][nrem_mask]
        nrem_1s.append(_one_second(env, env_fs, "mean" if r.startswith("mav") else "rms"))
    nrem_1s = np.stack(nrem_1s) if nrem_1s else np.zeros((0, 0), np.float32)

    meta = dict(meta, rows=rows, env_fs=env_fs, epoch_sec=epoch_sec,
                n_rem_epochs=int(len(rem_ep)), n_epochs=int(n_ep))
    return {"rem": rem, "rem_legs": rem_legs, "rem_epochs": rem_ep,
            "nrem_1s": nrem_1s, "hypnogram": hyp,
            "epoch_flags": {k: np.asarray(v[:n_ep], np.int8)
                            for k, v in (epoch_flags or {}).items()},
            "meta": meta}


def save_pack(path, pack):
    f16 = lambda a: np.minimum(np.nan_to_num(a, nan=0.0), F16_MAX).astype(np.float16)
    extra = {f"flag_{k}": v for k, v in pack["epoch_flags"].items()}
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, rem=f16(pack["rem"]), rem_legs=f16(pack["rem_legs"]),
                        rem_epochs=pack["rem_epochs"], nrem_1s=f16(pack["nrem_1s"]),
                        hypnogram=pack["hypnogram"], meta=json.dumps(pack["meta"]),
                        **extra)
    tmp.replace(path)
    return path


def load_pack(path):
    z = np.load(path, allow_pickle=False)
    return {"rem": z["rem"].astype(np.float32), "rem_legs": z["rem_legs"].astype(np.float32),
            "rem_epochs": z["rem_epochs"], "nrem_1s": z["nrem_1s"].astype(np.float32),
            "hypnogram": z["hypnogram"],
            "epoch_flags": {k[5:]: z[k] for k in z.files if k.startswith("flag_")},
            "meta": json.loads(str(z["meta"]))}


def pack_from_full(d):
    """Convert a full-night derived file (see extract.load_derived) to a pack."""
    meta = d["meta"]
    chin = {r: d[f"chin_{r}"] for r in ROWS if f"chin_{r}" in d}
    legs = [row for row in d["legs"]] if len(d["legs"]) else []
    m = {k: v for k, v in meta.items() if k not in ("env_fs", "epoch_sec")}
    m["unit_known"] = bool(meta.get("chin_info", {}).get("unit_known", True))
    return build_pack(chin, legs, d["hypnogram"], meta["env_fs"], meta["epoch_sec"], m)
