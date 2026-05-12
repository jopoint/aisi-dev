# YOLO Training Pipeline - Quick Reference

## Step-by-Step Commands (PowerShell)

### 1. Split Dataset (90/10, seed=42)
```powershell
python .\src\vision\tools\split_yolo_export.py
```
- Input: `data/vision/yolo_export_115/{images,labels}`
- Output: `data/vision/yolo_115/{images,labels}/{train,val}` + `data.yaml`

### 2. Create YOLO Virtual Environment
```powershell
python -m venv .venv_yolo
.\.venv_yolo\Scripts\Activate.ps1
```

### 2b. Create Vision Env for Combined YOLO + SAM
Use `.venv_vision` when running the combined YOLO proposer + SAM table refinement pipeline.

```powershell
.\scripts\setup_venv_vision.ps1
.\.venv_vision\Scripts\Activate.ps1
```

This environment includes `ultralytics`, `torch`/`torchvision` CPU wheels, and `sam2`.

### 3. Install Ultralytics
```powershell
python -m pip install --upgrade pip
pip install ultralytics
```

### 4. Train YOLOv8n
```powershell
python -m ultralytics train model=yolov8n.pt data=data\vision\yolo_115\data.yaml imgsz=960 epochs=60 batch=4 project=data\vision\yolo_runs name=train_v1
```

**Parameters:**
- `model=yolov8n.pt` - YOLOv8 nano (auto-downloads)
- `data=...` - Path to data.yaml with classes: table/chair/person
- `imgsz=960` - Input image size (960×960)
- `epochs=60` - Training epochs
- `batch=4` - Batch size
- `project=...` - Output directory for runs
- `name=train_v1` - Run name

**Output:**
- Weights: `data/vision/yolo_runs/train_v1/weights/best.pt`
- Logs: `data/vision/yolo_runs/train_v1/`

### 5. Predict with Debug Images
```powershell
python -m ultralytics predict model=data\vision\yolo_runs\train_v1\weights\best.pt source=data\vision\videos\bgsub_test.mp4 save=True project=data\vision\yolo_runs name=predict_v1 imgsz=960 conf=0.25
```

**Parameters:**
- `model=...` - Path to trained weights
- `source=...` - Video or image path
- `save=True` - Save annotated images/videos
- `conf=0.25` - Confidence threshold
- `imgsz=960` - Inference image size

**Output:**
- Annotated results: `data/vision/yolo_runs/predict_v1/`

---

## One-Command Setup (Automated)
```powershell
.\setup_yolo_pipeline.ps1
```
Runs all setup steps automatically (split + venv + install).

---

## data.yaml Structure
Generated automatically by `split_yolo_export.py`:
```yaml
path: C:\dev\Promotion_Prototypen\AISI\data\vision\yolo_115
train: images/train
val: images/val
nc: 3
names: ['table', 'chair', 'person']
```

---

## Directory Structure
```
data/vision/
├── yolo_export_115/         # Input (original export)
│   ├── images/              # Source images
│   └── labels/              # Source labels (YOLO format)
├── yolo_115/                # Output (split dataset)
│   ├── data.yaml            # Dataset config
│   ├── images/
│   │   ├── train/           # 90% training images
│   │   └── val/             # 10% validation images
│   └── labels/
│       ├── train/           # Training labels
│       └── val/             # Validation labels
└── yolo_runs/               # Training outputs
    ├── train_v1/            # Training run
    │   └── weights/
    │       └── best.pt      # Best model checkpoint
    └── predict_v1/          # Prediction results
        └── [annotated outputs]
```

---

## Training Tips
- Monitor training: TensorBoard logs saved in run directory
- Reduce `batch=2` if VRAM issues occur
- Increase `epochs=100` for better convergence
- Use `device=0` to specify GPU (default: auto-detect)
- Resume training: `resume=data\vision\yolo_runs\train_v1\weights\last.pt`
