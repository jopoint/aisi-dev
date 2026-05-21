Set-Location 'C:\dev\Promotion_Prototypen\AISI'

function Start-AisiWindow {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,

        [Parameter(Mandatory = $true)]
        [string]$PythonCommand
    )

    $windowScript = @"
Set-Location 'C:\dev\Promotion_Prototypen\AISI'
`$host.UI.RawUI.WindowTitle = '$Title'
`$env:PYTHONPATH = 'src'

if (Test-Path '.\.venv\Scripts\Activate.ps1') {
    try {
        . '.\.venv\Scripts\Activate.ps1'
    }
    catch {
        Write-Host 'Warning: virtual environment activation failed, continuing with python from PATH.'
    }
}

python $PythonCommand
"@

    Start-Process powershell.exe -ArgumentList @(
        '-NoExit',
        '-ExecutionPolicy', 'Bypass',
        '-Command', $windowScript
    ) -WindowStyle Normal -WorkingDirectory 'C:\dev\Promotion_Prototypen\AISI' -PassThru | Out-Null
}

# Start the three simulation components in separate PowerShell windows.
Start-AisiWindow -Title 'AISI Sim Room Editor' -PythonCommand '-m aisi.app.sim_room_editor'
Start-AisiWindow -Title 'AISI Learning Format Server' -PythonCommand '-m aisi.app.learning_format_server --port 8080'
Start-AisiWindow -Title 'AISI Sim Scene to OSC' -PythonCommand '-m aisi.app.sim_scene_to_osc --host 127.0.0.1 --port 9000'

Write-Host 'Sim pipeline started.'
Write-Host 'Open browser: http://127.0.0.1:8080'
Write-Host 'TouchDesigner OSC port: 9000'
