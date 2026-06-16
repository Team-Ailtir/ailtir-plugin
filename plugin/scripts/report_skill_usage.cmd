@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%report_skill_usage.py"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%SCRIPT_PATH%" %*
  if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%SCRIPT_PATH%" %*
  if not errorlevel 1 exit /b 0
)

where python3 >nul 2>nul
if not errorlevel 1 (
  python3 "%SCRIPT_PATH%" %*
)

exit /b 0
