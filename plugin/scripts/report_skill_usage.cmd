@echo off
setlocal

"%~dp0run_python.cmd" "%~dp0report_usage.py" %* >nul 2>nul

exit /b 0
