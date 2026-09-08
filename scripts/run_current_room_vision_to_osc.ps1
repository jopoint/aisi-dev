[CmdletBinding()]
param(
    [switch]$NoDisplay,
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
        throw "Required current-room live component is missing: $RequiredPath"
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
$AdapterCommand = "& '$AisiPython' -m aisi.app.vision_live_to_aisi_scene --input '$VisionInput' --output '$VisionScene'"
$OscCommand = "& '$AisiPython' -m aisi.app.sim_scene_to_osc --scene '$VisionScene' --host 127.0.0.1 --port 9000"

Write-Host "Current-room Vision -> AISI Scene -> OSC mode"
Write-Host "  Vision FrameEvents: $VisionInput"
Write-Host "  Dedicated scene:    $VisionScene"
Write-Host "  OSC target:         127.0.0.1:9000"
Write-Host "  This mode does not use or overwrite the Room Editor live_scene.json."

if ($DryRun) {
    Write-Host "Dry run; no processes started:"
    Write-Host "  $VisionCommand"
    Write-Host "  $AdapterCommand"
    Write-Host "  $OscCommand"
    exit 0
}

Start-AisiWindow -Title 'AISI Current-Room Vision' -Command $VisionCommand
Start-AisiWindow -Title 'AISI Vision to Scene Adapter' -Command $AdapterCommand
Start-AisiWindow -Title 'AISI Scene to OSC (Vision)' -Command $OscCommand

Write-Host "Started current-room vision, adapter, and OSC sender in separate PowerShell windows."
Write-Host "Do not also start scripts/run_sim_pipeline.ps1: it starts a second OSC sender for the Room Editor."
