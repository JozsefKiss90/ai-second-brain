param(
    [ValidateRange(5, 1440)][int]$Minutes = 15,
    [string]$BrainHome = '',
    [string]$TaskName = 'Workflow Second Brain Refresh'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $BrainHome) {
    $BrainHome = if ($env:SECOND_BRAIN_HOME) { $env:SECOND_BRAIN_HOME } else { Join-Path $env:LOCALAPPDATA 'WorkflowSecondBrain' }
}
if (-not (Test-Path (Join-Path $BrainHome 'automation.json'))) { throw 'Run brain init and configure automation.json first.' }
$runner = Join-Path $PSScriptRoot 'auto.ps1'
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`" -BrainHome `"$BrainHome`"" -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $Minutes)
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 14)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Opt-in OpenCode capture, local indexing and bounded AI enrichment. Runs only while this user is logged on.' -Force | Out-Null
Write-Host "Registered '$TaskName' every $Minutes minutes while you are logged on."
Write-Host "Review $BrainHome\automation-console.log and brain status after the first run."
