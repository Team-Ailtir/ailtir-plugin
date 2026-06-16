@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
"%SCRIPT_DIR%run_python.cmd" "%SCRIPT_DIR%report_skill_usage.py" %* >nul 2>nul

exit /b 0
