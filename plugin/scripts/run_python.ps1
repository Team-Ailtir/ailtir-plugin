$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $env:CLAUDE_PLUGIN_ROOT) {
    $env:CLAUDE_PLUGIN_ROOT = Split-Path -Parent $scriptDir
}

if ($args.Count -lt 1) {
    Write-Error "usage: run_python.ps1 <script.py> [args...]"
    exit 2
}

$candidates = @(
    @("python3"),
    @("python"),
    @("py", "-3")
)

foreach ($candidate in $candidates) {
    $command = $candidate[0]
    $prefixArgs = @()
    if ($candidate.Count -gt 1) {
        $prefixArgs = $candidate[1..($candidate.Count - 1)]
    }

    try {
        & $command @prefixArgs @args
        exit $LASTEXITCODE
    } catch {
        continue
    }
}

Write-Error "Python 3 was not found. Install Python 3 and ensure python3, python, or py is on PATH."
exit 127
