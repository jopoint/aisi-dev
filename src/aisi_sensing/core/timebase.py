from __future__ import annotations

import datetime as _dt
from typing import Iterator


def now_iso() -> str:
    """Return current UTC time in ISO8601 format with 'Z'."""
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def frame_counter(start: int = 0) -> Iterator[int]:
    """A simple frame counter generator."""
    i = start
    while True:
        yield i
        i += 1
