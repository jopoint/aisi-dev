# AISI Sensing Prototype

A sensing-first research prototype to detect and interpret live-changing relational configurations in a lab area. Tracks furniture (tables, chairs, screens/partitions) via ArUco markers and people (stub initially) from a top-down camera, derives layout and social constellations, and supports record/replay for debugging.

## Features
- Marker-based furniture tracking (ArUco / OpenCV)
- Modular people detection (stub: from JSON, simple clicks, or blobs)
- Stable FrameEvent contract separating sensing from inference
- Record and replay sessions (JSONL)
- Rule-based layout and social inference with debug info
- Visual debugging overlays and floorplan renderer

## Setup

### 1) Create and activate a virtual environment
```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
```

### 2) Install dependencies
```bash
pip install opencv-python numpy pyyaml matplotlib
# Optional (recommended for ArUco marker detection):
pip install opencv-contrib-python
```

### 3) Configuration
Copy the example configs and adjust as needed:
- configs/camera.example.yaml
- configs/lab.example.yaml
- configs/classes.example.yaml

### 4) Run replay demo (no camera needed)
```bash
python -m src.aisi_sensing.apps.run_replay --events src/aisi_sensing/contracts/examples/frame_event.example.json
```

A window will display a top-down view with overlays and print classification results to the console. Close the window or press any key in the figure window to exit.

## Calibration (Homography) — Placeholder Steps
1. Print/place a calibration marker grid or use known reference points on the floor.
2. Capture a still image from the top-down camera.
3. Manually identify pixel coordinates and their corresponding world coordinates.
4. Compute a homography `H` (e.g., using OpenCV `findHomography`).
5. Save `H` into `configs/lab.yaml` (replace the placeholder identity matrix).

## FrameEvent Contract
See schema at: src/aisi_sensing/contracts/frame_event_schema.json

A FrameEvent contains:
- timestamp_iso: ISO 8601 timestamp of frame capture
- frame_id: monotonically increasing frame counter
- furniture: list of DetectedEntity (tables, chairs, screens, partitions)
- people: list of DetectedEntity (persons, possibly from stub)
- world: dict for additional metadata (e.g., homography id, bounds)

Each DetectedEntity has:
- id: stable string id (e.g., marker id or tracked id)
- kind: one of [table, chair, screen, partition, person]
- pose: Pose2D with x,y (meters or pixels depending on stage), theta (optional)
- confidence: optional float [0,1]

Downstream modules expect world-space meters if homography is configured; otherwise pixel units are acceptable for replay/debugging.

## Live and Record
- Live: src/aisi_sensing/apps/run_live.py (camera → sensing → tracking → features → inference → overlays)
- Record: src/aisi_sensing/apps/run_record.py (write JSONL + optional video to data/sessions/<session_id>)
- Replay: src/aisi_sensing/apps/run_replay.py (load events.jsonl or example JSON)
- Export: src/aisi_sensing/apps/run_export.py (summaries to data/exports)

## Notes
- Prefer clarity and debuggability over sophistication; start rule-based.
- People detection is intentionally modular and can remain a stub at first.
- For ArUco detection, ensure `opencv-contrib-python` is installed.
