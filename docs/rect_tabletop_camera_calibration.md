# Rect tabletop camera calibration

This calibration maps the current camera's **Rect tabletop plane** to AISI World
coordinates in centimetres (`0..500` on X and Y). It is independent of, and
must not be confused with, protected TouchDesigner/projector calibration.

## Physical procedure

Keep the camera, capture resolution, `--camera-rotate`, and crop fixed. Measure
the actual Rect tabletop height and use the established physical AISI `(0,0)`,
`+X`, and `+Y` convention.

Place one ArUco marker exactly at the Rect tabletop centre. Move that table to
8–12 accurately measured marker-centre positions distributed across the room;
capture one processed image per position. A marker centre maps to its measured
`world_cm` value. It is only a table-centre reference when the marker was truly
centred. Multiple known markers in a capture are also supported.

Use `--save-live-frame-processed` to save an image after rotation and crop.

## Manifest and command

```json
{
  "schema_version": 1,
  "coordinate_system": "aisi_world_cm",
  "calibration_plane": "rect_tabletop",
  "plane_height_cm": 74.0,
  "aruco_dictionary": "DICT_4X4_50",
  "preprocessing": {"camera_rotate": 0, "crop": null},
  "captures": [
    {"image": "captures/p01.png", "points": [{"marker_id": 7, "world_cm": [20, 20]}]}
  ]
}
```

```powershell
python -m src.vision.tools.calibrate_camera_world `
  --manifest data/vision/calibration/rect_tabletop_manifest.json `
  --output data/vision/calibration/rect_tabletop_current.json `
  --report data/vision/calibration/rect_tabletop_current_report.json `
  --debug-dir data/vision/calibration/debug
```

Activate the result with `run_vision_pipeline.py --calibration <profile>`.
The report includes fit RMSE, maximum error, per-point error, and leave-one-out
error. Systematic edge/radial errors indicate that a planar homography may be
insufficient; do not silently compensate by changing projector calibration.

The profile is physically accurate only for table poses on the measured tabletop
plane. Chair/person values retain pipeline compatibility but are labelled as a
tabletop-plane approximation because they originate at different heights.

## Current-room live start

The current physical-room setup is intentionally an explicit launcher rather
than a changed global default. From the repository root, start it with:

```powershell
.\scripts\run_current_room_rect_vision.ps1
```

It uses these checked-in/local assets explicitly:

- tables: `models/vision/rect_obb_v1.pt` (the table-only Rect OBB model);
- chairs and persons: `yolov8s.pt` through the existing generic YOLO path;
- camera: index `0`, requested `1920x1080`, `camera_rotate=0`, no crop;
- world calibration:
  `data/vision/calibration/rect_tabletop_v1/calibration.json`.

The launcher requires `.venv_yolo\Scripts\python.exe` and verifies all three
model/calibration files before it opens the camera. It does not use the absent,
legacy `runs/detect/train/weights/best_fixed.pt`. Use `-DryRun` to print the
fully resolved command without opening the camera, `-NoDisplay` for headless
operation, and `-Device cpu` if CUDA is unavailable.

The selected calibration profile declares the `rect_tabletop` plane at `74 cm`;
verify this remains the measured tabletop height before a study session. Its
stored nine-point fit reports RMSE `1.33 cm` and maximum in-fit error `2.05 cm`.
Those figures apply to Rect tabletop poses only. Chair/person coordinates still
use the same homography for interface compatibility and must not be interpreted
as floor-accurate measurements.
