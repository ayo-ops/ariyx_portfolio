param(
    [int]$Target = 30,
    [int]$MaxDays = 0,
    [int]$MaxCandidates = 240,
    [switch]$SyncSheets = $true
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$RunnerPy = Join-Path $ProjectRoot "run_daily.py"
$LogDir = Join-Path $ProjectRoot "data\logs"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "scheduled_run_$Timestamp.log"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment Python not found at $PythonExe"
    exit 1
}

$ArgsList = @(
    "`"$RunnerPy`"",
    "--target", $Target,
    "--max-days", $MaxDays,
    "--max-candidates", $MaxCandidates
)

if ($SyncSheets) {
    $ArgsList += "--sync-sheets"
}

Write-Output "[$(Get-Date -Format o)] Starting Ariyx Daily Lead Pipeline -> Target=$Target SyncSheets=$SyncSheets" | Tee-Object -FilePath $LogFile
Push-Location $ProjectRoot
try {
    & $PythonExe @ArgsList *>&1 | Tee-Object -FilePath $LogFile -Append
    $ExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

Write-Output "[$(Get-Date -Format o)] Finished with exit code $ExitCode" | Tee-Object -FilePath $LogFile -Append
exit $ExitCode
