@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
"%SCRIPT_DIR%run_python.cmd" "%SCRIPT_DIR%report_usage.py" %* --kind command >nul 2>nul

exit /b 0
