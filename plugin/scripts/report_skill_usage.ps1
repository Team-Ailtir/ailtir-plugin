$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runPython = Join-Path $scriptDir "run_python.ps1"
$reporter = Join-Path $scriptDir "report_skill_usage.py"

& $runPython $reporter @args > $null 2>&1

exit 0
