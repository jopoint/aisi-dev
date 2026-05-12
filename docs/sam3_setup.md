# SAM3 setup on Windows

This guide sets up a reproducible Python environment for SAM3 on Windows and provides a minimal test that runs text-prompt segmentation for "chair" and saves an OpenCV overlay.

## 1) Python venv

```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel setuptools
```

## 2) PyTorch + CUDA (if GPU is available)

Check GPU and CUDA driver first:

```powershell
nvidia-smi
```

Install a CUDA-enabled PyTorch build that matches your driver. Use the official PyTorch install selector and copy the command it provides.

Examples (replace with the command from the PyTorch website):

```powershell
# Example: CUDA build
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Example: CPU-only
python -m pip install torch torchvision torchaudio
```

## 3) Install SAM3 repo dependencies

Clone the official SAM3 repository (see the official README for the correct URL) and install it in editable mode:

```powershell
git clone <SAM3_REPO_URL>
cd sam3
python -m pip install -e .
```

If the repo ships extra requirements files, install them as documented in the repo README.

## 4) Download model weights

Download the SAM3 checkpoint(s) from the official sources referenced by the repository (README) or from the official HuggingFace model card. Place the files in a known folder, for example:

```
<sam3_repo>\checkpoints\
```

## 5) Minimal test: text prompt "chair" and OpenCV overlay

Create a test script in the repo root, for example `sam3_min_test.py`. The import paths and model creation match the official SAM3 API in the repo. If the names differ, adjust them according to the README.

```python
import cv2
import numpy as np

# Adjust these imports to the official SAM3 API
from sam3 import sam3_model_registry, Sam3Predictor  # noqa: F401

# Paths
image_path = "data/vision/test_frames/sample.jpg"
checkpoint_path = "checkpoints/sam3_model.pt"

# Load image
image_bgr = cv2.imread(image_path)
if image_bgr is None:
    raise RuntimeError(f"Could not load image: {image_path}")
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

# Build model (adjust keys and args to repo docs)
model = sam3_model_registry["vit_h"](checkpoint=checkpoint_path)
predictor = Sam3Predictor(model)

# Run text-prompt segmentation (adjust method name if needed)
# Expect a binary mask in the same resolution as the input
mask = predictor.predict_text(image_rgb, text="chair")

# Create overlay (OpenCV only)
mask = (mask > 0).astype(np.uint8)
color = np.array([0, 255, 0], dtype=np.uint8)

overlay = image_bgr.copy()
overlay[mask == 1] = color

alpha = 0.5
out = cv2.addWeighted(overlay, alpha, image_bgr, 1.0 - alpha, 0)

out_path = "data/vision/debug/sam3_chair_overlay.png"
cv2.imwrite(out_path, out)
print(f"Saved overlay to {out_path}")
```

### Run the test

```powershell
python sam3_min_test.py
```

If the repo uses a different API, update the import names, model registry key, and text-prompt call to match the official README. The OpenCV overlay code will remain the same.

## 6) Using the SAM3Segmenter wrapper

Once SAM2/SAM3 is installed, use the wrapper class:

```python
import cv2
from src.vision.detection.sam3_segmenter import SAM3Segmenter

# Initialize segmenter
segmenter = SAM3Segmenter(
    model_config_path="configs/sam2/sam2_hiera_l.yaml",  # adjust to your config
    checkpoint_path="checkpoints/sam2_hiera_large.pt",   # adjust to your checkpoint
    device="cuda"  # or "cpu"
)

# Load image
frame = cv2.imread("data/vision/test_frames/sample.jpg")

# Segment with text prompts
results = segmenter.segment_image(
    frame,
    prompts=["table", "chair"],
    debug_dir="data/vision/debug"  # optional: saves overlay PNGs
)

# Process results
for prompt, masks in results.items():
    print(f"Prompt '{prompt}': found {len(masks)} instances")
    for i, mask_dict in enumerate(masks):
        print(f"  Instance {i}: score={mask_dict['score']:.3f}, bbox={mask_dict['bbox_px']}")
```

**Note:** SAM2 doesn't natively support text prompts. For text-based segmentation, integrate Grounding-DINO or CLIP to convert text→bounding boxes, then pass those boxes to SAM2. The `SAM3Segmenter` class provides a placeholder `_predict_with_text` method that needs to be implemented based on your chosen text→box pipeline.

## 7) Running the complete vision pipeline

The `src/vision/pipeline.py` module integrates SAM3 segmentation, geometric post-processing, homography projection, and JSONL output:

```powershell
# Process video file
python -m src.vision.tools.run_vision_pipeline \
  --video data/video.mp4 \
  --out data/vision_output.jsonl \
  --sam-config configs/sam2/sam2_hiera_l.yaml \
  --sam-checkpoint checkpoints/sam2_hiera_large.pt \
  --homography data/homography.json \
  --debug-dir data/vision/debug

# Live camera stream
python -m src.vision.tools.run_vision_pipeline \
  --camera 0 \
  --out data/vision_live.jsonl \
  --sam-config configs/sam2/sam2_hiera_l.yaml \
  --sam-checkpoint checkpoints/sam2_hiera_large.pt \
  --device cuda
```

### Pipeline stages

1. **SAM3 Segmentation**: Detects tables and chairs using text prompts
2. **Geometric Fitting**: 
   - Tables → minimum-area rectangle (center, yaw, corners)
   - Chairs → enclosing circle (center, radius)
3. **Area Filtering**: Configurable min/max area per class
4. **Homography Projection**: Maps pixel coordinates to floor coordinates (meters)
5. **JSONL Output**: Writes `FrameEvent` objects with detected furniture entities

### Output format

Each line in the JSONL file is a `FrameEvent`:

```json
{
  "timestamp_iso": "2026-03-03T10:30:45.123456",
  "frame_id": 42,
  "furniture": [
    {
      "id": "table_0",
      "kind": "table",
      "pose": {"x": 2.5, "y": 3.1, "theta": 0.785},
      "confidence": 0.95
    },
    {
      "id": "chair_0",
      "kind": "chair",
      "pose": {"x": 1.2, "y": 2.8, "theta": null},
      "confidence": 0.87
    }
  ],
  "people": [],
  "world": {"homography_applied": true}
}
```
