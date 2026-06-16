$ErrorActionPreference = "SilentlyContinue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "report_skill_usage.py"

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

    & $command @prefixArgs $scriptPath @args
    if ($LASTEXITCODE -eq 0) {
        exit 0
    }
}

exit 0
