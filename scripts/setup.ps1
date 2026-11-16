$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
if (!(Test-Path '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
}
& '.venv\Scripts\python.exe' -m pip install -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& '.venv\Scripts\python.exe' -c 'from cirrus import create_app; create_app(); print("Database initialized; additive schema applied.")'
if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed.' }
Write-Host 'Setup complete. Create the initial administrator with .venv\Scripts\python.exe -m flask --app cirrus:create_app init-admin'
