# AISI Project State – May 2026

## Synthetic Baseline Status

**Groupwork Overlap Fix (Completed)**
- Pair-aware geometry with fixed 74cm seam spacing (70cm table depth + 4cm gap) implemented.
- Deterministic pair-normal repair path: overlap detected → increase internal pair distance along normal only (not generic push).
- Generation notes include pair metadata (center, normal, gap_cm) for downstream parsing.
- Regression validation: `random_4tables | groupwork` scenario → 0 overlaps, 0 clearance violations, 0 ROI violations.
- Applicable to 2-table groupwork pairs; larger clusters unchanged.

**Test Format Support**
- Layouts synthesized for `input`, `groupwork`, `discussion` formats.
- Scene feature metrics computed; projection payloads generated.
- Layout proposal → hard constraint repair pipeline operational.

## Real Snapshot Integration Status

**Vision Schema Support (In Progress)**
- Existing schema: summary.json with nested table structure → **working**.
- New schema: `furniture` top-level with `kind: "table"` and `pose: {x, y, theta}` → **implemented and validated**.
  - Theta (radians) → rot_deg (degrees) conversion working.
  - Schema detection and reporting enabled.

**Converter Infrastructure (Complete)**
- CLI: `src/aisi/app/convert_vision_snapshot_to_aisi.py`
  - Input: JSON/JSONL with flexible field mapping (id, x, y, rot_deg tolerant).
  - Output: AISI scene format with ROI bounds and table list.
  - Optional ROI coordinate mapping for furniture_pose: `x_out = (x / source_width) * roi_width`.
  - Deployment: `.venv` compatible, tested on summary.json and furniture test fixtures.

**Video Preprocessing (Complete)**
- CLI: `src/vision/tools/extract_video_testset_rotated_crop.py`
  - Input: MP4/AVI video, frame sampling by FPS, start/end time window.
  - Transforms: rotate (0°/90°/180°/270°) → crop (x, y, w, h) → JPEG sequence.
  - Output: numbered frames (frame_000000.jpg …) for downstream CV processing.
  - Validation: crop bounds checked against rotated frame dimensions.
  - Tested: extracted 51 frames from real video with rotate=90°, crop=1000×1291.

**Real Snapshot Workflow (Defined)**
- Document: `docs/video_to_aisi_snapshot_workflow.md`
  - Steps: video → segment → frames → CV → snapshot → AISI export → test.
  - Test cases defined: clean, messy, leichte Occlusion.
  - Decision rules: consistency across frames, plausibility heuristics.

## Good Real Cases

Three test scenarios planned for real snapshot validation:
1. **Clean**: Clear view, minimal background noise, good reference baseline.
2. **Messy**: More clutter, but tables still detectable and recognized.
3. **Leichte Occlusion**: One table partially obscured, but recognizable.

Each case targets same camera position/lighting as deployment scenario. Snapshot selection by highest table detection stability and fewest false positives.

## Current Bottlenecks

1. **Real CV Execution**:
   - Video frames extracted; converter ready; CV pipeline (YOLO + OBB) not yet run on new frames.
   - Blocking: Need actual `run_vision_pipeline` output (JSONL with furniture detections) for real frames.

2. **Dataset Matching**:
   - Old working dataset: 1277×1015 px.
   - New source video: 1920×1080 px.
   - After rotate 90° CCW → 1080×1920 px.
   - Crop space available: 1080×~859 px (to maintain aspect ratio).
   - Exact pixel matching requires optional resize; coordinate mapping enables fair comparison without resize.

3. **Schema Validation**:
   - furniture_pose schema tested on synthetic fixture; real CV output format not yet confirmed.
   - Assumption: real furniture detections will follow pose format; fallback to summary schema if needed.

## Next Sensible Steps

**Phase 1: Real Snapshot Acquisition (This Week)**
1. Extract frames from 3 video segments (clean, messy, occlusion) using `extract_video_testset_rotated_crop.py`.
2. Run full CV pipeline (`run_vision_pipeline`) on extracted frames → JSONL output.
3. Convert best snapshot per scenario using `convert_vision_snapshot_to_aisi.py` with coordinate mapping.
4. Record snapshot selection rationale in `docs/real_snapshot_test_log.md`.

**Phase 2: Real vs. Synthetic Comparison (Next Week)**
1. Run AISI layout synthesis on each real snapshot with all three formats (input/groupwork/discussion).
2. Compare movement cost, rotation cost, fit score against synthetic baseline.
3. Log results in test protocol.
4. Decision point: ≥3/3 scenarios viable → fixate CV→AISI interface; <3/3 → debug per error class.

**Phase 3: Stabilization (Following Week)**
1. If real snapshots pass: merge groupwork overlap fix + converter + preprocessing tools to main.
2. Establish snapshot caching strategy for regression testing.
3. Document field-by-field schema validation for production CV output.

**Known Assumptions**
- Real camera FOV and table geometry match training data assumptions.
- Furniture pose format will be consistent across video frames.
- Coordinate mapping (source → ROI) sufficient without actual pixel→cm calibration.

## Recommended Test Command Sequence

```powershell
# 1. Extract frames from video (example: clean scenario)
$env:PYTHONPATH='src'
python -m src.vision.tools.extract_video_testset_rotated_crop `
  --video "C:\path\to\video.mp4" `
  --out "data\vision\aisi_snapshot_test\clean_scenario" `
  --fps 5 `
  --start-sec 0 `
  --end-sec 20 `
  --rotate 270 `
  --crop 0 300 1080 859

# 2. Run CV pipeline (use existing config; output to JSONL)
python -m src.vision.tools.run_vision_pipeline `
  --video "data\vision\aisi_snapshot_test\clean_scenario\frame_000000.jpg" `
  --out "data\vision\aisi_snapshot_test\clean_scenario_detections.jsonl" `
  --auto-proposals yolo `
  --yolo-model "runs\detect\train\weights\best_fixed.pt" `
  [... other model/param configs ...]

# 3. Convert best frame snapshot to AISI scene
python -m src.aisi.app.convert_vision_snapshot_to_aisi `
  --input "data\vision\aisi_snapshot_test\clean_scenario_detections.jsonl" `
  --output "data\aisi\out\real_clean_scene.json" `
  --source-width 1080 `
  --source-height 859 `
  --roi-width 500 `
  --roi-height 500

# 4. Run AISI layout test (existing test framework)
python -m src.aisi.app.run_layout_synthesis_test `
  --scene "data\aisi\out\real_clean_scene.json" `
  --formats "input groupwork discussion" `
  --outdir "data\aisi\out\real_clean_results"
```
