$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
& (Join-Path $repoRoot '.venv\Scripts\python.exe') -m second_brain.cli sync
exit $LASTEXITCODE
