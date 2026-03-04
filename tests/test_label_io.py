from __future__ import annotations
import tempfile
from pathlib import Path
from src.aisi_sensing.core.logging import read_jsonl, write_jsonl

def test_label_io_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'labels.jsonl'
        rows = [
            {"frame_id": 1, "human_layout": "circle", "timestamp_iso": "t1", "note": None},
            {"frame_id": 2, "human_layout": "group_islands", "timestamp_iso": "t2", "note": None},
        ]
        write_jsonl(p, rows)
        loaded = read_jsonl(p)
        assert len(loaded) == 2
        assert loaded[0]["human_layout"] == "circle"
        # Update: clear label for frame 1
        rows2 = [
            {"frame_id": 2, "human_layout": "group_islands", "timestamp_iso": "t2", "note": None},
        ]
        write_jsonl(p, rows2)
        loaded2 = read_jsonl(p)
        assert len(loaded2) == 1
        assert loaded2[0]["frame_id"] == 2
