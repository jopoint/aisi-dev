from __future__ import annotations
import tempfile
from pathlib import Path
import json
from src.aisi_sensing.apps.run_record import main as record_main
from src.aisi_sensing.core.logging import iter_jsonl
from src.aisi_sensing.core.types import FrameEvent
from src.aisi_sensing.inference.layout_classifier import classify as classify_layout

def test_dummy_layout_phases(monkeypatch):
    # Record a dummy session with 120 frames to a temp out dir
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "sessions"
        # Use example configs
        lab_cfg = Path("configs/lab.example.yaml").resolve()
        classes_cfg = Path("configs/classes.example.yaml").resolve()
        monkeypatch.setattr("sys.argv", [
            "run_record.py",
            "--out-dir", str(out),
            "--source", "dummy",
            "--num-frames", "120",
            "--lab-config", str(lab_cfg),
            "--classes-config", str(classes_cfg),
            "--seed", "123",
        ])
        record_main()
        # Find the created session
        sessions = sorted(out.iterdir())
        assert sessions, "No session created"
        session = sessions[0]
        # Load frames
        frames = [FrameEvent.from_dict(d) for d in iter_jsonl(session / "events.jsonl")]
        assert len(frames) == 120
        # Classify
        import yaml
        with open(classes_cfg, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        labels = []
        for f_ev in frames:
            labels.append(classify_layout(f_ev, cfg)["label"])
        # Check 4 phases of 30 frames each
        target = ["presentation_front", "group_islands", "circle", "seminar_rows"]
        phase_len = 30
        for pi, name in enumerate(target):
            seg = labels[pi*phase_len:(pi+1)*phase_len]
            n_intended = seg.count(name)
            n_unknown = seg.count("unknown")
            assert (
                n_intended >= 20 or ((n_intended + n_unknown) >= 26 and n_intended >= n_unknown)
            ), f"Phase {name} insufficient: intended={n_intended}, unknown={n_unknown}"
