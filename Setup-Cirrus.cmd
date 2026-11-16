@echo off
setlocal
cd /d "%~dp0"
echo.
echo  CIRRUS EXPERIENCE 2.0 - SETUP
 echo  -----------------------------
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :pythonerror
)
".venv\Scripts\python.exe" -m pip install -r requirements.lock
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" scripts\first_run.py
if errorlevel 1 goto :failed
echo.
echo  Ready. Double-click Start-Cirrus.cmd to open your workspace.
pause
exit /b 0
:pythonerror
echo  Python 3.12 is required. Install Python 3.12 x64, then run setup again.
goto :failed
:failed
echo.
echo  Setup did not complete. Copy the error above for support.
pause
exit /b 1
