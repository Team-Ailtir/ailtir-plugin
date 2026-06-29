$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $env:CLAUDE_PLUGIN_ROOT) {
    $env:CLAUDE_PLUGIN_ROOT = Split-Path -Parent $scriptDir
}

if ($args.Count -lt 1) {
    Write-Error "usage: run_python.ps1 <script.py> [args...]"
    exit 2
}

function Resolve-RealPython {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { return $null }
    # Skip Windows App Execution Alias stubs under WindowsApps that print
    # "Python was not found..." and exit non-zero.
    if ($cmd.Source -and $cmd.Source -match "[\\/]WindowsApps[\\/]") { return $null }
    return $cmd.Source
}

# Prefer the py launcher on Windows — it sidesteps PATH-ordering issues with
# the App Execution Alias stubs entirely.
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & py -3 @args
    exit $LASTEXITCODE
}

foreach ($name in @("python3", "python")) {
    $exe = Resolve-RealPython $name
    if ($exe) {
        & $exe @args
        exit $LASTEXITCODE
    }
}

Write-Error "Python 3 was not found. Install Python 3 and ensure python3, python, or py is on PATH (and disable the Microsoft Store python.exe App Execution Aliases on Windows)."
exit 127
