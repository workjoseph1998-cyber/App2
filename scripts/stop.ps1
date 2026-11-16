$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$Data = if ($env:CIRRUS_DATA_DIR) { $env:CIRRUS_DATA_DIR } else { Join-Path $Root 'data' }
$PidFile = Join-Path $Data 'cirrus.pid'
if (!(Test-Path $PidFile)) { Write-Host 'No Cirrus PID file. No process was stopped.'; exit 0 }
$CirrusProcessId = [int](Get-Content $PidFile -Raw)
$Proc = Get-CimInstance Win32_Process -Filter "ProcessId = $CirrusProcessId"
if (!$Proc) { Remove-Item $PidFile; Write-Host 'Stale PID removed. No process stopped.'; exit 0 }
$ExpectedRunner = Join-Path $Root 'run.py'
$ExpectedPython = Join-Path $Root '.venv\Scripts\python.exe'
if (!$Proc.CommandLine -or !$Proc.CommandLine.Contains('"' + $ExpectedRunner + '"') -or $Proc.ExecutablePath -ne $ExpectedPython) {
    throw 'PID identity mismatch. Refusing to stop an unrelated process.'
}
Stop-Process -Id $CirrusProcessId -ErrorAction Stop
Wait-Process -Id $CirrusProcessId -ErrorAction SilentlyContinue
Remove-Item $PidFile -ErrorAction SilentlyContinue
Write-Host 'Only this Cirrus instance was stopped.'
