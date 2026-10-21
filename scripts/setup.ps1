$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12, then rerun setup.' }
}
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
& $python -m pip install -e '.[mcp]'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $python -m second_brain.cli init
if ($LASTEXITCODE -ne 0) { throw 'Initialization failed.' }
& $python (Join-Path $PSScriptRoot 'configure.py')
if ($LASTEXITCODE -ne 0) { throw 'OpenCode configuration failed.' }
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
Write-Host 'Setup complete. Read docs\WINDOWS.md, personalize your profile, then start opencode.'
