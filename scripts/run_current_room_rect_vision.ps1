[CmdletBinding()]
param(
    [int]$CameraIndex = 0,
    [string]$OutputPath = "data/vision/live/current_room_rect.jsonl",
    [ValidateSet("cuda", "cpu")]
    [string]$Device = "cuda",
    [string]$TablePoseLatencyDebugJsonl,
    [switch]$NoDisplay,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# This launcher is deliberately explicit: it is for the current physical room
# and does not change the generic run_vision_pipeline.py defaults.
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot ".venv_yolo\Scripts\python.exe"
$TableObbModel = Join-Path $RepositoryRoot "models\vision\rect_obb_v1.pt"
$GenericYoloModel = Join-Path $RepositoryRoot "yolov8s.pt"
$CalibrationProfile = Join-Path $RepositoryRoot "data\vision\calibration\rect_tabletop_v1\calibration.json"

foreach ($RequiredPath in @($Python, $TableObbModel, $GenericYoloModel, $CalibrationProfile)) {
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Required current-room vision file is missing: $RequiredPath"
    }
}

$PipelineArgs = @(
    "-m", "src.vision.tools.run_vision_pipeline",
    "--camera", "$CameraIndex",
    "--camera-width", "1920",
    "--camera-height", "1080",
    "--camera-rotate", "0",
    "--auto-proposals", "yolo",
    "--yolo-model", $GenericYoloModel,
    "--table-obb-model", $TableObbModel,
    "--calibration", $CalibrationProfile,
    "--device", $Device,
    "--show-table-ids",
    "--table-bbox-smoothing-alpha", "1.0",
    "--table-center-smoothing-alpha", "1.0",
    "--table-yaw-smoothing-alpha", "0.7",
    "--adaptive-table-smoothing",
    "--adaptive-table-stationary-center-delta-px", "1.5",
    "--adaptive-table-stationary-yaw-delta-deg", "0.5",
    "--adaptive-table-stationary-frames", "5",
    "--adaptive-table-moving-center-delta-px", "3.0",
    "--adaptive-table-moving-yaw-delta-deg", "1.5",
    "--flush-every", "1",
    "--out", $OutputPath
)

if ($NoDisplay) {
    $PipelineArgs += "--no-display"
}
if (-not [string]::IsNullOrWhiteSpace($TablePoseLatencyDebugJsonl)) {
    $PipelineArgs += "--table-pose-latency-debug-jsonl", $TablePoseLatencyDebugJsonl
}

Write-Host "Current-room Rect-table vision configuration:"
Write-Host "  tables:  $TableObbModel"
Write-Host "  chairs/persons: $GenericYoloModel"
Write-Host "  calibration: $CalibrationProfile"
Write-Host "  camera: index=$CameraIndex, 1920x1080, rotate=0, crop=none"
if (-not [string]::IsNullOrWhiteSpace($TablePoseLatencyDebugJsonl)) {
    Write-Host "  table pose latency debug: $TablePoseLatencyDebugJsonl"
}

if ($DryRun) {
    Write-Host "Dry run; command not started:"
    Write-Host ("  " + $Python + " " + ($PipelineArgs -join " "))
    exit 0
}

Push-Location $RepositoryRoot
try {
    $env:PYTHONPATH = if ($env:PYTHONPATH) { "$RepositoryRoot;$env:PYTHONPATH" } else { $RepositoryRoot }
    & $Python @PipelineArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
