# Vision Pipeline - Image Directory Mode

## Overview

The vision pipeline now supports processing image directories in addition to video files and camera streams. This mode is useful for batch processing of pre-captured images.

## Usage

### Basic Usage

Process all images in a directory:

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/vision/test_frames \
  --out data/vision/out_frames.jsonl
```

### With Simulated FPS

Control timestamp intervals with `--fps-sim`:

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/vision/test_frames \
  --out data/vision/out_frames.jsonl \
  --fps-sim 10
```

This will simulate 10 FPS (100ms between frames) for timestamp calculation.

### With Initial Box Prompts

#### Interactive Box Selection

Select boxes interactively on the first image:

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/vision/test_frames \
  --out data/vision/out_frames.jsonl \
  --init-boxes
```

When `--init-boxes` is specified:
1. The first image is displayed
2. You can select multiple bounding boxes using cv2.selectROI
3. Press ENTER to add each box
4. Press ESC when done selecting boxes
5. These boxes are used as prompts for the first frame only

#### Predefined Box Prompts

Use predefined boxes from command line:

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/vision/test_frames \
  --out data/vision/out_frames.jsonl \
  --boxes-init "100,100,500,500;600,200,900,600"
```

Box format: `x1,y1,x2,y2` separated by semicolons for multiple boxes.

### With Debug Overlays

Save debug overlays for each frame:

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/vision/test_frames \
  --out data/vision/out_frames.jsonl \
  --debug-dir data/vision/debug_overlays
```

### Complete Example

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/vision/test_frames \
  --out data/vision/out_frames.jsonl \
  --fps-sim 10 \
  --init-boxes \
  --debug-dir data/vision/debug \
  --max-frames 50 \
  --homography data/vision/homography.json
```

## Features

### Image Loading

- Scans directory for `*.jpg` and `*.png` files
- Sorts files alphabetically by filename
- Treats each image as a sequential frame

### Timestamp Generation

- Base timestamp: System time when processing starts
- Frame timestamps: `base_time + (frame_index / fps_sim)`
- Default FPS: 10 (configurable via `--fps-sim`)

### Box Prompts (First Frame Only)

When using `--boxes-init` or `--init-boxes`:
- Boxes are only used for the **first frame**
- Subsequent frames use standard text prompts ["table", "chair"]
- Useful for tracking specific regions from frame 1

### Classification

When using box prompts, detected masks are classified as:
- **Table**: If area ≥ `--table-min-area` (default: 5000 px²)
- **Chair**: If area ≥ `--chair-min-area` (default: 2000 px²)

### Output Format

JSONL file with one FrameEvent per line:

```json
{
  "timestamp_iso": "2026-03-04T12:34:56.000Z",
  "frame_id": 0,
  "furniture": [
    {
      "id": "table_0",
      "kind": "table",
      "pose": {"x": 1.234, "y": 2.345, "theta": 0.123},
      "confidence": 0.95
    }
  ],
  "people": [],
  "world": {
    "homography_applied": true,
    "used_box_prompts": true
  }
}
```

## Limitations

- No matplotlib usage (pure OpenCV)
- Box prompts only supported for first frame
- Text prompts require Grounding-DINO integration (placeholder only)
- Box-based classification is heuristic (area-based)

## Comparison with Video/Camera Modes

| Feature | Video | Camera | Image Dir |
|---------|-------|--------|-----------|
| Input | Video file | Live stream | Image files |
| Timestamps | From video | Real-time | Simulated |
| Box prompts | N/A | N/A | ✅ Supported |
| Real-time display | ❌ | ✅ | ❌ |
| Max frames | ✅ | ❌ | ✅ |
| Debug overlays | ✅ | ✅ | ✅ |

## Examples

### Process frames from timelapse camera

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/timelapse/2026-03-04 \
  --out data/vision/timelapse_analysis.jsonl \
  --fps-sim 0.1
```

### Track specific furniture pieces

```bash
# Select furniture regions interactively on first frame
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/meeting_room \
  --out data/vision/meeting_furniture.jsonl \
  --init-boxes \
  --debug-dir data/vision/debug
```

### Batch process with homography

```bash
python -m src.vision.tools.run_vision_pipeline \
  --image-dir data/lab_frames \
  --out data/vision/lab_analysis.jsonl \
  --homography data/calibration/lab_homography.json \
  --fps-sim 15
```
