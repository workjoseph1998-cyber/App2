$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { throw 'Run scripts\setup.ps1 first.' }
# This check never terminates or changes the other application's listener.
& $Python -c 'from run import check_port; check_port()'
if ($LASTEXITCODE -ne 0) { throw 'Port 8000 is occupied. Startup refused.' }
$Data = if ($env:CIRRUS_DATA_DIR) { $env:CIRRUS_DATA_DIR } else { Join-Path $Root 'data' }
New-Item -ItemType Directory -Force -Path (Join-Path $Data 'logs') | Out-Null
$Runner = Join-Path $Root 'run.py'
$p = Start-Process -FilePath $Python -ArgumentList @('"' + $Runner + '"') -WorkingDirectory $Root -RedirectStandardOutput (Join-Path $Data 'logs\stdout.log') -RedirectStandardError (Join-Path $Data 'logs\stderr.log') -PassThru
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    $p.Refresh()
    if ($p.HasExited) { throw 'Startup failed. Inspect this application data\logs\stderr.log.' }
    try {
        $Prefix = if ($env:CIRRUS_URL_PREFIX) { $env:CIRRUS_URL_PREFIX.TrimEnd('/') } else { '' }
        $r = Invoke-WebRequest -Uri ('http://127.0.0.1:8000' + $Prefix + '/login') -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200 -and $r.Content.Contains('Cirrus')) {
            Write-Host "Cirrus started (PID $($p.Id)). IIS can now use the existing port 8000 endpoint."
            exit 0
        }
    } catch { }
}
throw 'Readiness check timed out. Inspect logs; use stop.ps1 to stop only this instance.'
