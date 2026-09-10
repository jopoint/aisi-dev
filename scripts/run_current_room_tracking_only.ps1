[CmdletBinding()]
param(
    [switch]$NoDisplay,
    [string]$TableObbDebugJsonl,
    [string]$TablePoseLatencyDebugJsonl,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$VisionLauncher = Join-Path $PSScriptRoot "run_current_room_rect_vision.ps1"
$AisiPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$VisionInput = Join-Path $RepositoryRoot "data\vision\live\current_room_rect.jsonl"
$VisionScene = Join-Path $RepositoryRoot "data\aisi\scenes\live\vision_live_scene.json"

foreach ($RequiredPath in @($VisionLauncher, $AisiPython)) {
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Required tracking-only component is missing: $RequiredPath"
    }
}

function Start-AisiWindow {
    param(
        [Parameter(Mandatory = $true)] [string]$Title,
        [Parameter(Mandatory = $true)] [string]$Command
    )

    $WindowCommand = @"
Set-Location '$RepositoryRoot'
`$host.UI.RawUI.WindowTitle = '$Title'
`$env:PYTHONPATH = 'src'
$Command
"@
    Start-Process powershell.exe -ArgumentList @(
        '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $WindowCommand
    ) -WindowStyle Normal -WorkingDirectory $RepositoryRoot -PassThru | Out-Null
}

$VisionCommand = "& '$VisionLauncher'"
if ($NoDisplay) {
    $VisionCommand += " -NoDisplay"
}
if (-not [string]::IsNullOrWhiteSpace($TableObbDebugJsonl)) {
    $VisionCommand += " -TableObbDebugJsonl '$TableObbDebugJsonl'"
}
if (-not [string]::IsNullOrWhiteSpace($TablePoseLatencyDebugJsonl)) {
    $VisionCommand += " -TablePoseLatencyDebugJsonl '$TablePoseLatencyDebugJsonl'"
}
$AdapterCommand = "& '$AisiPython' -m aisi.app.vision_live_to_aisi_scene --input '$VisionInput' --output '$VisionScene' --poll-seconds 0.01"
$OscCommand = "& '$AisiPython' -m aisi.app.sim_scene_to_osc --scene '$VisionScene' --tracking-only --tracking-table-id table_00 --host 127.0.0.1 --port 9000 --interval 0.01"

Write-Host "Current-room tracking-only mode: Rect table table_00 -> OSC 9000"
Write-Host "  Vision FrameEvents: $VisionInput"
Write-Host "  Dedicated scene:    $VisionScene"
Write-Host "  No layout synthesis, people, chairs, or generated target pose."
Write-Host "  Target OSC compatibility values equal source, so motion vectors are zero."
if (-not [string]::IsNullOrWhiteSpace($TableObbDebugJsonl)) {
    Write-Host "  Table association debug: $TableObbDebugJsonl"
}
if (-not [string]::IsNullOrWhiteSpace($TablePoseLatencyDebugJsonl)) {
    Write-Host "  Table pose debug:        $TablePoseLatencyDebugJsonl"
}

if ($DryRun) {
    Write-Host "Dry run; no processes started:"
    Write-Host "  $VisionCommand"
    Write-Host "  $AdapterCommand"
    Write-Host "  $OscCommand"
    exit 0
}

Start-AisiWindow -Title 'AISI Current-Room Vision' -Command $VisionCommand
Start-AisiWindow -Title 'AISI Vision to Scene Adapter' -Command $AdapterCommand
Start-AisiWindow -Title 'AISI Tracking-Only Scene to OSC' -Command $OscCommand

Write-Host "Started vision, scene adapter, and tracking-only OSC sender."
Write-Host "Do not also start scripts/run_sim_pipeline.ps1; it would start a second OSC sender on port 9000."
