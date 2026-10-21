param([string]$BrainHome = '')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $BrainHome) {
    $BrainHome = if ($env:SECOND_BRAIN_HOME) { $env:SECOND_BRAIN_HOME } else { Join-Path $env:LOCALAPPDATA 'WorkflowSecondBrain' }
}
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Run setup before scheduling automation.' }
if (-not (Test-Path (Join-Path $BrainHome 'automation.json'))) { throw 'Run brain init and configure automation.json first.' }
$env:PYTHONUTF8 = '1'
Set-Location $repoRoot
# Keep only the latest console report; transcripts/provider output are not logged.
$log = Join-Path $BrainHome 'automation-console.log'
& $python -m second_brain.cli --home $BrainHome auto 2>&1 | Out-File -FilePath $log -Encoding utf8 -Width 2000
exit $LASTEXITCODE
