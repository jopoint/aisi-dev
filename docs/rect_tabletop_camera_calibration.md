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

### Table-pose latency diagnostics

The live path can append one compact JSON object for each active `table_00`
frame without changing tracking or the normal FrameEvent output:

```powershell
.\scripts\run_current_room_rect_vision.ps1 `
  -TablePoseLatencyDebugJsonl data\vision\debug\table_00_pose_latency.jsonl
```

Read the live log with:

```powershell
Get-Content data\vision\debug\table_00_pose_latency.jsonl -Wait
```

Each line contains the raw OBB center/yaw, EMA-bbox center, center-smoothed
position, and the emitted calibrated world `x/y` and table `theta`, all for the
same `frame_id`.

## Current-room Vision to AISI/OSC live mode

For the calibrated live path into the existing AISI Scene-to-OSC sender, use:

```powershell
.\scripts\run_current_room_vision_to_osc.ps1
```

It starts three separate processes: the current-room Rect OBB vision launcher,
the FrameEvent-to-scene adapter, and `aisi.app.sim_scene_to_osc` on OSC port
9000. The adapter reads `data/vision/live/current_room_rect.jsonl` and writes
the dedicated scene `data/aisi/scenes/live/vision_live_scene.json`. This avoids
overwriting the Room Editor's
`data/aisi/scenes/simulated/live_scene.json`; do not start
`run_sim_pipeline.ps1` at the same time because it would start a second OSC
sender for the same TouchDesigner port.

Only `furniture[].kind == "table"` entries are forwarded. For each valid
table, the adapter preserves its stable vision track ID, copies calibrated AISI
world `x`/`y` directly to `x_cm`/`y_cm`, converts `theta` from radians to the
existing `rotation_deg` scene unit, and emits canonical `rect` dimensions
`160 x 80 cm`. It adds no coordinate transform. Chairs and persons are emitted
as empty lists in this explicit tables-only mode.

Table order is fixed by the first valid appearance of a vision track ID (new
simultaneous IDs are ordered by ID), so ordinary detection-order jitter cannot
change the Scene/OSC index. A missing table retains its last pose for 15 valid
FrameEvents, then is removed and the existing `/table/count` lifecycle channel
removes its TouchDesigner instance. The existing count-only OSC contract has
no inactive-slot address: after a permanent removal, later active entries are
necessarily compacted. If the entire FrameEvent stream stops for two seconds,
the adapter publishes an empty table list. These values are intentional,
deterministic defaults; change them only through the adapter CLI when
validating a different tracking cadence.

For a safe offline conversion of the last completed FrameEvent, use:

```powershell
python -m aisi.app.vision_live_to_aisi_scene --once
```

All scene writes are atomic. The resulting file is compatible with the existing
scene loader and OSC sender, but TouchDesigner/physical-room correctness still
requires a live validation.

## Tracking-only projection validation

For an isolated one-Rect-table validation path, use:

```powershell
.\scripts\run_current_room_tracking_only.ps1
```

The OSC sender runs with `--tracking-only`. It accepts exactly one scene table
with `type=rect`, emits it at OSC index `0` (`table_00` in the current Vision
tracker), emits `/table/count = 1`, and bypasses `compute_target_layout(...)`
entirely. Source x/y/rotation are sent unchanged in the existing source
channels. The existing target channels remain present for compatibility, but
mirror the source pose exactly; this yields a zero motion vector and no
generated target pose. Persons and chairs are suppressed.

Tracking-only Rect rotation is unwrapped at the OSC boundary modulo 180 degrees,
because a 160 x 80 Rect footprint is geometrically unchanged by a half turn.
For example, scene rotations `88, 89, 270, 271` become the continuous source
sequence `88, 89, 90, 91` before the existing TouchDesigner sign inversion.
The mirrored target rotation uses that same unwrapped value. The continuity
state is reset when the accepted table disappears or when the sender restarts;
regular layout mode is unchanged.

The active manual TouchDesigner project is not represented authoritatively in
this repository, so it is not modified here. In the active graph, configure a
temporary tracking-only output route that renders only the existing source
contours: the source inner contour to TABLETOP and the source outer footprint
to FLOOR. Disable/bypass target-contour and motion-line geometry in that route;
do not alter any calibration, homography, projector, mask, or blend node. The
source expressions must read `table/0/source_x`, `table/0/source_y`, and
`table/0/source_rot` from `null_osc_raw (Null CHOP)`; do not use the mirrored
target channels for the tracking contour.
