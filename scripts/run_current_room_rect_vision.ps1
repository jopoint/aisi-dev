[CmdletBinding()]
param(
    [int]$CameraIndex = 0,
    [string]$OutputPath = "data/vision/live/current_room_rect.jsonl",
    [ValidateSet("cuda", "cpu")]
    [string]$Device = "cuda",
    [ValidateSet("none", "gaussian5", "levels")]
    [string]$TableObbPreprocess = "levels",
    [ValidateRange(1, 255)]
    [int]$TableObbLevelsWhitePoint = 200,
    [switch]$NoTableTombstoneReactivation,
    [switch]$TableObbDebugJsonl,
    [string]$TablePoseLatencyDebugJsonl,
    [string]$HardExampleCaptureDir = "data/vision/debug/hard_examples",
    [ValidateRange(1, 1000)]
    [int]$HardExampleBurstFrames = 1,
    [switch]$PerfLog,
    [ValidateSet("direct", "latest")]
    [string]$CameraCaptureMode = "latest",
    [switch]$NoDisplay,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# This launcher is deliberately explicit: it is for the current physical room
# and does not change the generic run_vision_pipeline.py defaults.
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot ".venv_yolo\Scripts\python.exe"
$TableObbModel = Join-Path $RepositoryRoot "models\vision\rect_obb_v2.pt"
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
    "--camera-capture-mode", $CameraCaptureMode,
    "--auto-proposals", "yolo",
    "--yolo-model", $GenericYoloModel,
    "--table-obb-model", $TableObbModel,
    "--table-obb-preprocess", $TableObbPreprocess,
    "--table-obb-levels-white-point", "$TableObbLevelsWhitePoint",
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
    "--table-new-confirm-frames", "2",
    "--hard-example-capture-dir", $HardExampleCaptureDir,
    "--hard-example-burst-frames", "$HardExampleBurstFrames",
    "--flush-every", "1",
    "--out", $OutputPath
)

if (-not $NoTableTombstoneReactivation) {
    $PipelineArgs += @(
        "--table-tombstone-reactivation",
        "--table-tombstone-max-age-seconds", "10",
        "--table-tombstone-max-distance-cm", "35",
        "--table-tombstone-max-rotation-deg", "15"
    )
}

if ($NoDisplay) {
    $PipelineArgs += "--no-display"
}
if ($PerfLog) {
    $PipelineArgs += "--perf-log"
}
if (-not [string]::IsNullOrWhiteSpace($TablePoseLatencyDebugJsonl)) {
    $PipelineArgs += "--table-pose-latency-debug-jsonl", $TablePoseLatencyDebugJsonl
}
if ($TableObbDebugJsonl) {
    $TableObbDebugPath = Join-Path $RepositoryRoot "data\vision\debug\current_room_table_obb_association.jsonl"
    $PipelineArgs += "--table-obb-debug-jsonl", $TableObbDebugPath
}
if ($PerfLog) {
    Write-Host "  performance logging: enabled (~2 s aggregates)"
}

Write-Host "Current-room Rect-table vision configuration:"
Write-Host "  tables:  $TableObbModel"
$TableObbPreprocessDisplay = if ($TableObbPreprocess -eq "levels") { "levels (white_point=$TableObbLevelsWhitePoint)" } else { $TableObbPreprocess }
Write-Host "  table OBB preprocessing: $TableObbPreprocessDisplay"
Write-Host "  chairs/persons: $GenericYoloModel"
Write-Host "  calibration: $CalibrationProfile"
Write-Host "  camera: index=$CameraIndex, 1920x1080, rotate=0, crop=none"
Write-Host "  Camera capture mode: $CameraCaptureMode"
Write-Host "  hard-example capture: press c -> $HardExampleCaptureDir (burst=$HardExampleBurstFrames)"
if (-not [string]::IsNullOrWhiteSpace($TablePoseLatencyDebugJsonl)) {
    Write-Host "  table pose latency debug: $TablePoseLatencyDebugJsonl"
}
if ($TableObbDebugJsonl) {
    Write-Host "  table OBB association debug: $TableObbDebugPath"
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
