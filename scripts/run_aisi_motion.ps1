[CmdletBinding()]
param(
    [ValidateSet('Start', 'Status', 'ReplaceController')][string]$Action = 'Status',
    [switch]$OutputsOff,
    [switch]$DryRun
)
# Bestehende Kamera-/Study-/Tracking-Konfiguration erhalten. Keine TD-Mutationen.
$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
$VisionPython = Join-Path $RepositoryRoot '.venv_yolo\Scripts\python.exe'
$env:PYTHONPATH = "$RepositoryRoot;$RepositoryRoot\src"
$Processes = @(Get-CimInstance Win32_Process)

function Get-OwnedRoots([string]$Module, [string]$Executable = $Python) {
    @($Processes | Where-Object {
        $_.ExecutablePath -eq $Executable -and
        $_.CommandLine -match ('(?<!\S)-m\s+' + [regex]::Escape($Module) + '(?=\s|$)')
    })
}

function Start-ServiceProcess([string]$Name, [string[]]$Arguments) {
    Write-Host "$Name starten: $Python $($Arguments -join ' ')"
    if ($DryRun) { return }
    $LogRoot = Join-Path $RepositoryRoot 'data\aisi\debug\motion_runtime'
    New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
    Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $RepositoryRoot `
        -WindowStyle Hidden -RedirectStandardOutput "$LogRoot\${Name}_${Stamp}.out.log" `
        -RedirectStandardError "$LogRoot\${Name}_${Stamp}.err.log" | Out-Null
}

$Services = @(
    @{Name='Kamera'; Module='src.vision.tools.run_vision_pipeline'; Exe=$VisionPython},
    @{Name='Scene'; Module='aisi.app.vision_live_to_aisi_scene'; Exe=$Python},
    @{Name='Study'; Module='aisi.app.study_control'; Exe=$Python},
    @{Name='LegacyOSC'; Module='aisi.app.sim_scene_to_osc'; Exe=$Python},
    @{Name='UI'; Module='aisi.app.learning_format_server'; Exe=$Python},
    @{Name='AlterMotionController'; Module='aisi.app.motion_live_control'; Exe=$Python}
)
foreach ($Service in $Services) {
    $Roots = @(Get-OwnedRoots $Service.Module $Service.Exe)
    Write-Host "$($Service.Name): $($Roots.Count) Prozessketten; Root-PIDs: $($Roots.ProcessId -join ', ')"
    if ($Roots.Count -gt 1) { throw "Mehrere $($Service.Name)-Prozessketten. Erst manuell klären; nichts gestartet." }
}
if ($Action -eq 'Status') {
    try {
        Invoke-RestMethod 'http://127.0.0.1:8080/motion-status' -TimeoutSec 2 | ConvertTo-Json -Depth 5
    } catch { Write-Host 'Motion-Webstatus nicht erreichbar; Prozessstatus allein beweist keine aktuellen Kameraframes.' }
    return
}

$Ui = @(Get-OwnedRoots 'aisi.app.learning_format_server')
$Old = @(Get-OwnedRoots 'aisi.app.motion_live_control')
$AlreadyCombined = $Ui.Count -eq 1 -and $Ui[0].CommandLine -match '(?<!\S)--motion(?=\s|$)'
if (@(Get-OwnedRoots 'aisi.app.motion_preview_sim').Count) {
    throw 'Motion-Simulator läuft. Erst gezielt beenden; gemeinsame OSC-Namespace nicht doppelt senden.'
}
if ($Action -eq 'ReplaceController') {
    if (-not $OutputsOff) { throw 'Zuerst TD Enablemotion, Sourceapproved und Simulationtest ausschalten; dann -OutputsOff angeben.' }
    foreach ($RootProcess in @($Ui) + @($Old)) {
        # Nur eindeutig diesem Repository zugeordnete venv-Kette einschließlich Python-Kind.
        $Children = @($Processes | Where-Object { $_.ParentProcessId -eq $RootProcess.ProcessId -and $_.Name -ne 'conhost.exe' })
        foreach ($Child in $Children) {
            $RootArgs = $RootProcess.CommandLine -replace '^"[^"]+"\s*', ''
            $ChildArgs = $Child.CommandLine -replace '^"[^"]+"\s*', ''
            if ($Child.Name -notmatch '^python(w)?\.exe$' -or $ChildArgs -ne $RootArgs) {
                throw "Unbekannter Kindprozess $($Child.ProcessId); Wechsel abgebrochen."
            }
        }
    }
    foreach ($RootProcess in @($Ui) + @($Old)) {
        $Children = @($Processes | Where-Object { $_.ParentProcessId -eq $RootProcess.ProcessId -and $_.Name -match '^python(w)?\.exe$' })
        Write-Host "Eigenen Controller ersetzen: $($RootProcess.ProcessId)"
        if (-not $DryRun) {
            foreach ($Child in $Children) { Stop-Process -Id $Child.ProcessId -ErrorAction SilentlyContinue }
            Stop-Process -Id $RootProcess.ProcessId -ErrorAction SilentlyContinue
        }
    }
    $AlreadyCombined = $false
    $Ui = @()
    $Old = @()
}
if ($Old.Count -or ($Ui.Count -and -not $AlreadyCombined)) {
    throw 'Alter UI-/Motion-Pfad läuft. TD-Ausgänge ausschalten und ReplaceController -OutputsOff verwenden.'
}
if (-not $AlreadyCombined -and -not $OutputsOff) {
    $AutomaticOff = $false
    try {
        $TdStatus = Get-Content -LiteralPath (Join-Path $RepositoryRoot 'data\aisi\state\motion_td_approval.json') -Raw | ConvertFrom-Json
        $Age = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0 - [double]$TdStatus.updated_at
        $AutomaticOff = $Age -ge 0 -and $Age -le 3 -and $TdStatus.automatic -eq $true -and `
            $TdStatus.enabled -eq $true -and $TdStatus.output_flags.Count -eq 2 -and `
            $TdStatus.output_flags[0] -eq $false -and $TdStatus.output_flags[1] -eq $false
    } catch { $AutomaticOff = $false }
    if (-not $AutomaticOff) {
        throw 'Neue Motion-Sitzung: TD-Arbeitsdatei mit Auto-Freigabe öffnen und Play starten; alternativ Ausgänge manuell aus und Start -OutputsOff.'
    }
}

if (-not @(Get-OwnedRoots 'src.vision.tools.run_vision_pipeline' $VisionPython).Count) {
    Write-Host 'Kamera mit bestehendem Labor-Launcher starten.'
    if (-not $DryRun) {
        Start-Process powershell.exe -ArgumentList @('-NoProfile','-File',"`"$PSScriptRoot\run_current_room_rect_vision.ps1`"") `
            -WorkingDirectory $RepositoryRoot -WindowStyle Hidden | Out-Null
    }
}
if (-not @(Get-OwnedRoots 'aisi.app.vision_live_to_aisi_scene').Count) {
    Start-ServiceProcess 'scene' @('-u','-m','aisi.app.vision_live_to_aisi_scene','--input','data/vision/live/current_room_rect.jsonl','--output','data/aisi/scenes/live/vision_live_scene.json','--poll-seconds','0.01')
}
if (-not @(Get-OwnedRoots 'aisi.app.study_control').Count) {
    Start-ServiceProcess 'study' @('-u','-m','aisi.app.study_control','--mode','2')
}
if (-not @(Get-OwnedRoots 'aisi.app.sim_scene_to_osc').Count) {
    Start-ServiceProcess 'legacy_osc' @('-u','-m','aisi.app.sim_scene_to_osc','--scene','data/aisi/scenes/live/vision_live_scene.json','--study-active-binding','data/aisi/state/study_active_track.json','--study-table-tracks-binding','data/aisi/state/study_table_tracks.json','--require-fresh-live-scene','--host','127.0.0.1','--port','9000','--interval','0.05')
}
if (-not $AlreadyCombined) {
    Start-ServiceProcess 'motion_ui' @('-u','-m','aisi.app.learning_format_server','--motion','--send')
}
Write-Host 'UI: http://127.0.0.1:8080 — Status nach einigen Sekunden separat abrufen. Keine TD-Freigabe gesetzt.'
