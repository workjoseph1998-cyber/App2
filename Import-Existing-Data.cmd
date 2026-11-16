@echo off
setlocal
cd /d "%~dp0"
echo.
echo  CIRRUS EXPERIENCE 2.0 - IMPORT EXISTING PULSE DATA
 echo  Stop the old Pulse app first. Run this BEFORE Setup-Cirrus.cmd.
py -3.12 scripts\upgrade.py
if errorlevel 1 echo Import did not complete. Your original data has not been changed.
pause
