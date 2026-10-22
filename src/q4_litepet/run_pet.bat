@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=C:\Users\lennovo\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" (
  echo [LitePet] Python not found: %PY%
  pause
  exit /b 1
)
"%PY%" -m litepet.main %*
if errorlevel 1 (
  echo.
  echo [LitePet] exited with code %errorlevel%
  pause
)
