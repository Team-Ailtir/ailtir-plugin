@echo off
setlocal

if "%~1"=="" (
  echo usage: run_python.cmd ^<script.py^> [args...] 1>&2
  exit /b 2
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 %*
  exit /b %errorlevel%
)

where python >nul 2>nul
if not errorlevel 1 (
  python %*
  exit /b %errorlevel%
)

where python3 >nul 2>nul
if not errorlevel 1 (
  python3 %*
  exit /b %errorlevel%
)

echo Python 3 was not found. Install Python 3 and ensure python3, python, or py is on PATH. 1>&2
exit /b 127
