param(
    [string]$TaskName = "AriyxLeadIntelligenceDaily",
    [string]$StartTime = "08:00",
    [int]$DurationDays = 0,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$JobScript = Join-Path $ScriptDir "run_daily_job.ps1"

if (-not (Test-Path $JobScript)) {
    Write-Error "Daily job script missing at $JobScript"
    exit 1
}

$CmdArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$JobScript`""

Write-Output "Task Name:      $TaskName"
Write-Output "Daily Time:     $StartTime"
Write-Output "Max Days Guard: $(if ($DurationDays -gt 0) { "$DurationDays days" } else { "Ongoing indefinitely (no day limit)" })"
Write-Output "Action Command: powershell.exe $CmdArgs"

if ($DryRun) {
    Write-Output "[DRY-RUN] No Windows Scheduled Task was registered."
    exit 0
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $CmdArgs
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Ariyx Systems automated B2B daily outbound lead research & qualification runner (ongoing indefinitely)." `
    -Force

Write-Output "[REGISTERED] Windows Scheduled Task '$TaskName' scheduled daily at $StartTime (ongoing indefinitely)."
