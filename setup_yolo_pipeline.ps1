# YOLO Dataset Preparation and Training Pipeline
# Windows PowerShell compatible

Write-Host "=== YOLO Dataset Pipeline ===" -ForegroundColor Cyan

# Step 1: Split dataset (90/10)
Write-Host "`n[1/4] Splitting dataset..." -ForegroundColor Yellow
python .\src\vision\tools\split_yolo_export.py
if ($LASTEXITCODE -ne 0) { 
    Write-Host "✗ Dataset split failed" -ForegroundColor Red
    exit 1 
}

# Step 2: Create Python 3.12 venv for YOLO
Write-Host "`n[2/4] Creating .venv_yolo..." -ForegroundColor Yellow
if (Test-Path .venv_yolo) {
    Write-Host "  .venv_yolo already exists, skipping creation" -ForegroundColor Gray
} else {
    python -m venv .venv_yolo
    if ($LASTEXITCODE -ne 0) { 
        Write-Host "✗ venv creation failed" -ForegroundColor Red
        exit 1 
    }
}

# Step 3: Install ultralytics
Write-Host "`n[3/4] Installing ultralytics..." -ForegroundColor Yellow
& .\.venv_yolo\Scripts\python.exe -m pip install --upgrade pip -q
& .\.venv_yolo\Scripts\python.exe -m pip install ultralytics -q
if ($LASTEXITCODE -ne 0) { 
    Write-Host "✗ ultralytics installation failed" -ForegroundColor Red
    exit 1 
}

# Step 4: Show next steps
Write-Host "`n[4/4] Setup complete!" -ForegroundColor Green
Write-Host "`nTraining command:" -ForegroundColor Cyan
Write-Host "  .\.venv_yolo\Scripts\python.exe -m ultralytics train model=yolov8n.pt data=data\vision\yolo_115\data.yaml imgsz=960 epochs=60 batch=4 project=data\vision\yolo_runs name=train_v1" -ForegroundColor White

Write-Host "`nPrediction command (with debug images):" -ForegroundColor Cyan
Write-Host "  .\.venv_yolo\Scripts\python.exe -m ultralytics predict model=data\vision\yolo_runs\train_v1\weights\best.pt source=data\vision\videos\bgsub_test.mp4 save=True project=data\vision\yolo_runs name=predict_v1 imgsz=960 conf=0.25" -ForegroundColor White

Write-Host "`nTo activate YOLO venv:" -ForegroundColor Cyan
Write-Host "  .\.venv_yolo\Scripts\Activate.ps1" -ForegroundColor White
