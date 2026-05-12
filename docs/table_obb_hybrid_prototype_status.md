# Table-OBB Hybrid Status (Prototype)

## Scope
Current best-known table tracking setup for the table-OBB hybrid path on branch `vision/wip-dark-proposals`.

## Dataset
- `data/vision/dataset/video_crop_5fps_150_b`

## Reference Run Command (PowerShell)
```powershell
python -m src.vision.tools.run_vision_pipeline `
  --image-dir data\vision\dataset\video_crop_5fps_150_b `
  --out data\vision\out_hybrid_table_obb_150_b_continuity.jsonl `
  --auto-proposals yolo `
  --yolo-model runs\detect\train\weights\best_fixed.pt `
  --table-obb-model <TABLE_OBB_MODEL_PATH.pt> `
  --table-obb-conf 0.25 `
  --table-obb-iou 0.45 `
  --table-obb-max-det 4 `
  --table-protect-existing-tracks `
  --table-recover-lost-tracks `
  --table-lost-track-ttl 15 `
  --table-new-confirm-frames 2 `
  --overlay-style debug `
  --overlay-out-dir data\vision\overlays_video_crop_5fps_150_b_continuity `
  --overlay-every 1
```

## What Improved
- Table continuity is significantly better with continuity-first + lost-track recovery.
- Short occlusions during table movement are handled better (fewer unnecessary new IDs).
- Phantom-table frequency is strongly reduced.
- Final table overlay quality improved by preferring polygon geometry (`corners_px` -> `poly_px` -> `bbox_px`) in debug rendering.

## Remaining Error
- Rare residual failure: a phantom table can briefly substitute a real table track.
- Most visible in dense spatial layouts and occlusion-heavy table shifts.

## Why Acceptable for Current Prototype
- Core behavior is stable and usable for current prototype goals.
- Residual error is infrequent and short-lived compared to prior behavior.
- Current setup gives a good trade-off between robustness, simplicity, and minimal code complexity.

## Recommended Later Next Steps
- Add stricter table-only plausibility checks before accepting recovery/birth in ambiguous gaps.
- Strengthen recovery scoring under occlusion (history-aware matching, motion/shape consistency).
- Keep debug JSONL counters enabled in evaluation runs to quantify substitutions before further tuning.

## Preferred Live Stabilization (2026-03-23)
- Geometric center/angle smoothing was too invasive and degraded table geometry quality.
- `--table-angle-deadband-deg` gave visibly better stability with fewer angle flickers.
- Static-table hold further improved visual calm for resting tables.
- Short table drop-outs are now covered by render grace using last final geometry reuse.
- Best current live setup is `angle deadband + static-table hold`.
- Scope: this stabilizes final table render/output only; detection, tracking, birth/lost, and matching stay unchanged.

### Milestone Freeze (Table Path)
- Table path is frozen for the current milestone; no further core table optimization is planned now.
- Preferred live baseline in this freeze:
  - `--table-angle-deadband-deg 5`
  - `--table-static-hold-frames 3`
  - `--table-static-hold-center-px 8`
  - `--table-static-hold-angle-deg 4`
  - `--table-static-hold-area-frac 0.08`
  - `--table-render-grace-frames 3`
- Additional table ideas (for example tape markers on table edges) are explicitly deferred.

### Preferred Baseline Values (Live)
- `--table-angle-deadband-deg 5`
- `--table-static-hold-frames 3`
- `--table-static-hold-center-px 8`
- `--table-static-hold-angle-deg 4`
- `--table-static-hold-area-frac 0.08`
- `--table-render-grace-frames 3`
- Crop: `--crop-x 64 --crop-y 282 --crop-w 1000 --crop-h 1291`
- Rotation: `--camera-rotate 90 --display-rotate 90`

### Qualitative Baseline Assessment
- Live overlays are currently stable enough for demos with low visual jitter on resting tables.
- Table geometry remains faithful (no invasive geometric smoothing/reconstruction).
- Remaining imperfections are acceptable for the current prototype milestone.

### Recommended Live Command (PowerShell)
```powershell
python -m src.vision.tools.run_vision_pipeline `
  --camera 0 `
  --out data\vision\out_live_table_crop_final_preferred_2026-03-23.jsonl `
  --auto-proposals yolo `
  --yolo-model runs\detect\train\weights\best_fixed.pt `
  --table-obb-model runs\obb\table_obb_pilot_01_cpu\weights\best.pt `
  --table-obb-conf 0.15 `
  --table-obb-iou 0.45 `
  --table-obb-max-det 4 `
  --table-new-conf-create 0.20 `
  --table-new-min-bbox-area 12000 `
  --table-new-min-bbox-minside 80 `
  --table-new-confirm-frames 3 `
  --table-protect-existing-tracks `
  --table-recover-lost-tracks `
  --table-lost-track-ttl 50 `
  --table-birth-block-near-lost-dist 90 `
  --table-birth-block-near-lost-frames 8 `
  --table-render-grace-frames 3 `
  --conf-keep 0.08 `
  --table-angle-deadband-deg 5 `
  --table-static-hold-frames 3 `
  --table-static-hold-center-px 8 `
  --table-static-hold-angle-deg 4 `
  --table-static-hold-area-frac 0.08 `
  --overlay-style projector_on_frame `
  --show-table-ids `
  --camera-width 1920 `
  --camera-height 1080 `
  --camera-rotate 90 `
  --display-rotate 90 `
  --crop-x 64 `
  --crop-y 282 `
  --crop-w 1000 `
  --crop-h 1291
```

### Demo Startup Script
- `scripts/run_live_demo_tables.ps1` starts this exact preferred live baseline command.
