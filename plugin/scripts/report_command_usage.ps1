$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runPython = Join-Path $scriptDir "run_python.ps1"
$reporter = Join-Path $scriptDir "report_usage.py"

& $runPython $reporter @args --kind command > $null 2>&1

exit 0
