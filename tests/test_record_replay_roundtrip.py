"""Test for record→replay roundtrip using dummy mode and JSONL sessions."""
import tempfile
from pathlib import Path
from src.aisi_sensing.core.types import FrameEvent
from src.aisi_sensing.core.logging import write_jsonl, iter_jsonl

def test_record_replay_roundtrip():
    # Dummy generator: 10 frames, 2 layouts cycling
    num_frames = 10
    layouts = ["presentation_front", "group_islands"]
    frames = []
    for i in range(num_frames):
        layout = layouts[i % len(layouts)]
        ev = FrameEvent(
            timestamp_iso=f"2026-03-02T15:38:{i:02d}Z",
            frame_id=i,
            furniture=[],
            people=[],
            world={"layout": layout},
        )
        frames.append(ev)
    with tempfile.TemporaryDirectory() as tmpdir:
        session = Path(tmpdir) / "session1"
        session.mkdir(parents=True, exist_ok=True)
        events_path = session / "events.jsonl"
        write_jsonl(events_path, (f.to_dict() for f in frames))
        # Read back
        loaded = [FrameEvent.from_dict(d) for d in iter_jsonl(events_path)]
        assert len(loaded) == num_frames
        for f in loaded:
            assert hasattr(f, "timestamp_iso")
            assert hasattr(f, "frame_id")
            assert hasattr(f, "furniture")
            assert hasattr(f, "people")
            assert hasattr(f, "world")
            assert f.world["layout"] in layouts
