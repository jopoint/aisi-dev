from __future__ import annotations

import logging
from typing import Optional


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger with a concise format."""
    logger = logging.getLogger(name if name else "aisi_sensing")
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


import json
from pathlib import Path
from typing import Iterable, Dict, Any, Generator, List

def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    """Write dict rows to a JSONL file (overwrite).

    Accepts any iterable of dicts (e.g., list[dict]).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for d in rows:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')

def iter_jsonl(path: Path) -> Generator[Dict[str, Any], None, None]:
    """Yield dicts from a JSONL file."""
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read an entire JSONL file into a list of dicts."""
    return list(iter_jsonl(path))
