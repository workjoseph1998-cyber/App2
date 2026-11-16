@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No local Cirrus virtual environment. Nothing was stopped.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\stop.py
pause
