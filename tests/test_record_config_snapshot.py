import tempfile
from pathlib import Path
import json
import shutil
from src.aisi_sensing.apps.run_record import main as run_record_main

def test_config_snapshotting(monkeypatch):
    # Prepare dummy config files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        lab = tmp / "lab.yaml"
        classes = tmp / "classes.yaml"
        lab.write_text("room: testlab\nsize: [6,4]\n", encoding="utf-8")
        classes.write_text("person: {color: red}\n", encoding="utf-8")
        outdir = tmp / "sessions"
        # Patch sys.argv
        monkeypatch.setattr("sys.argv", [
            "run_record.py",
            "--out-dir", str(outdir),
            "--lab-config", str(lab),
            "--classes-config", str(classes),
            "--num-frames", "2",
            "--source", "dummy"
        ])
        run_record_main()
        # Find session folder
        session_folders = list(outdir.iterdir())
        assert session_folders, "No session folder created"
        session = session_folders[0]
        # Check snapshot files
        assert (session / "lab.yaml").exists(), "lab.yaml snapshot missing"
        assert (session / "classes.yaml").exists(), "classes.yaml snapshot missing"
        # Check meta.json
        meta = json.loads((session / "meta.json").read_text(encoding="utf-8"))
        assert "lab_config_snapshot_path" in meta
        assert "classes_config_snapshot_path" in meta
        assert meta["lab_config_snapshot"]["room"] == "testlab"
        assert meta["classes_config_snapshot"]["person"]["color"] == "red"
