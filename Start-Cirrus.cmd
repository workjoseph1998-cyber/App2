@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup-Cirrus.cmd first.
  pause
  exit /b 1
)
echo.
echo  CIRRUS EXPERIENCE 2.0
 echo  Keep this window open. Press Ctrl+C to stop this application.
set CIRRUS_OPEN_BROWSER=1
".venv\Scripts\python.exe" run.py
if errorlevel 1 echo Startup failed. Check the message above; no other application was stopped.
pause
