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
from typing import Iterable, Dict, Any, Generator

def write_jsonl(path: Path, iterable_of_dicts: Iterable[Dict[str, Any]]) -> None:
    """Write an iterable of dicts to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for d in iterable_of_dicts:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')

def iter_jsonl(path: Path) -> Generator[Dict[str, Any], None, None]:
    """Yield dicts from a JSONL file."""
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
