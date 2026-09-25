"""Minimal EDF/EDF+ reader that returns each channel at its NATIVE rate.

Why not MNE: `mne.io.read_raw_edf` resamples every channel to the highest rate
in the file. CAP stores chin EMG at 256-512 Hz but leg EMG at 128 Hz, so the
leg channels silently came back upsampled to 512 Hz. Reading the samples
directly keeps each channel's true rate, reads only the channels asked for,
and needs nothing beyond numpy - which matters on hosted notebooks where
installing packages is not always possible.

Values are returned in microvolts when the header's physical dimension is a
voltage. Some files carry no unit at all (raw converter counts); those are
returned unscaled and flagged, because an absolute amplitude threshold means
nothing for them.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_TO_UV = {"uv": 1.0, "µv": 1.0, "mv": 1e3, "v": 1e6, "nv": 1e-3}


@dataclass
class Channel:
    index: int
    label: str
    dim: str
    fs: float
    n_per_record: int
    gain: float          # physical units per digital unit
    offset: float        # physical value at digital zero
    prefilter: str
    transducer: str

    @property
    def uv_scale(self):
        """Factor from physical units to microvolts, or None if not a voltage."""
        return _TO_UV.get(self.dim.strip().lower().replace("μ", "µ"))


@dataclass
class EdfHeader:
    path: Path
    n_records: int
    record_s: float
    header_bytes: int
    start_date: str
    start_time: str
    channels: list

    @property
    def duration_s(self):
        return self.n_records * self.record_s

    def find(self, label):
        for c in self.channels:
            if c.label == label:
                return c
        raise KeyError(label)


def read_header(path) -> EdfHeader:
    path = Path(path)
    with open(path, "rb") as f:
        h = f.read(256)
        ns = int(h[252:256])
        s = f.read(256 * ns)

    def fields(width, start):
        return [s[start + i * width: start + (i + 1) * width]
                .decode("latin-1").strip() for i in range(ns)], start + width * ns

    labels, o = fields(16, 0)
    trans, o = fields(80, o)
    dims, o = fields(8, o)
    pmin, o = fields(8, o)
    pmax, o = fields(8, o)
    dmin, o = fields(8, o)
    dmax, o = fields(8, o)
    pref, o = fields(80, o)
    nsamp, o = fields(8, o)

    header_bytes = int(h[184:192])
    n_records = int(h[236:244])
    record_s = float(h[244:252])
    per_rec = [int(x) for x in nsamp]
    # Records actually present. The header may say "-1" (unknown), or claim
    # more records than a truncated file holds; trust the file size.
    on_disk = (path.stat().st_size - header_bytes) // (2 * sum(per_rec))
    n_records = on_disk if n_records < 0 else min(n_records, on_disk)

    chans = []
    for i in range(ns):
        p0, p1, d0, d1 = (float(pmin[i]), float(pmax[i]),
                          float(dmin[i]), float(dmax[i]))
        gain = (p1 - p0) / (d1 - d0) if d1 != d0 else 1.0
        chans.append(Channel(
            index=i, label=labels[i], dim=dims[i],
            fs=per_rec[i] / record_s if record_s > 0 else float("nan"),
            n_per_record=per_rec[i], gain=gain, offset=p0 - gain * d0,
            prefilter=pref[i], transducer=trans[i]))
    return EdfHeader(path, n_records, record_s, header_bytes,
                     h[168:176].decode("ascii", "ignore").strip(),
                     h[176:184].decode("ascii", "ignore").strip(), chans)


def read_channel(hdr: EdfHeader, channel):
    """
    One channel as float64 at its native rate, in microvolts when the unit is
    a voltage. `channel` is a Channel, an index, or a label (first match).
    Returns (signal, fs, unit_known).
    """
    if isinstance(channel, Channel):
        ch = channel
    elif isinstance(channel, int):
        ch = hdr.channels[channel]
    else:
        ch = hdr.find(channel)
    per_rec = [c.n_per_record for c in hdr.channels]
    rec_len = sum(per_rec)
    start = sum(per_rec[:ch.index])
    raw = np.memmap(hdr.path, dtype="<i2", mode="r", offset=hdr.header_bytes,
                    shape=(hdr.n_records, rec_len))
    x = np.asarray(raw[:, start:start + ch.n_per_record], dtype=np.float64).ravel()
    del raw
    x = x * ch.gain + ch.offset
    k = ch.uv_scale
    if k is not None:
        x *= k
    return x, ch.fs, k is not None
