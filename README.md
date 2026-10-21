# Workflow Second Brain

A personal coding and automation memory for **Windows + OpenCode**, using a free
model for everyday work and an explicitly selected OpenAI model for harder tasks.
Each person uses the same application code with her own local data and preferences.

## What works in this starter

- Import UTF-8 Markdown/text notes from a private inbox; skip unchanged content.
- Keep old revisions, exact source lines, optional dates and project metadata.
- Search locally with SQLite FTS5/BM25 and a small source-date freshness boost.
- Read evidence through a read-only local MCP server in OpenCode.
- Personalize recurring tasks, language, tools and answer style in a private profile.
- Back up the SQLite database consistently through its backup API.
- Optionally capture selected OpenCode conversations and enrich them with AI summaries.
- Run the capture/index/enrichment pipeline from Windows Task Scheduler.

No model calls occur during ordinary indexing/search. Optional enrichment calls
the explicitly configured model through OpenCode. Model selection and generation run
in OpenCode. Free hosting has provider quotas and changing terms; OpenAI use
requires your own supported account/login or separately billed API access.

**Version 0.2 adds opt-in OpenCode conversation capture and AI enrichment.**
Follow [automation setup](docs/AUTOMATION.md) to enable them locally.
Mailbox/Git/other-chat connectors, PDF/Word parsing, a GUI and automatic fact-conflict
resolution remain future stages. Source authority/status are returned as evidence;
they are not proof that a retrieved claim is true. AGENTS.md asks the assistant
to retrieve first, but does not enforce retrieval on every response.

## Quick start on Windows

Prerequisites: Git, Python 3.12, Node.js LTS, VS Code (optional), OpenCode V1.
See [full Windows instructions](docs/WINDOWS.md) for installation and checks.

```powershell
# Clone your actual repository, then enter it:
git clone https://github.com/JozsefKiss90/ai-second-brain.git
Set-Location ai-second-brain
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

The one-process execution-policy option applies only to this invocation. Review
the script first; if your organization blocks it, ask IT or run its documented
Python commands individually. It does not change the global execution policy.

Setup creates `.venv`, installs the package/MCP SDK, initializes your private
workspace and writes a local, Git-ignored OpenCode configuration. It retains
existing OpenCode config and produces a merge snippet instead of replacing it.

Your private data lives at `%LOCALAPPDATA%\WorkflowSecondBrain`, outside Git.
Set `SECOND_BRAIN_HOME` before setup to use another private location; use a local,
non-synced active database. Each person should use an independent workspace.

## First successful query

```powershell
Copy-Item .\examples\* "$env:LOCALAPPDATA\WorkflowSecondBrain\inbox\"
& .\.venv\Scripts\brain.exe sync
& .\.venv\Scripts\brain.exe search 'npm execution policy'
opencode
```

In OpenCode: connect your provider with `/connect`, choose a currently free model
with `/models`, then ask:

> Read brain_profile. Use brain_search to find the npm PowerShell error example,
> then brain_read the original lines. Explain the working command and cite the
> record ID, source file and lines. Do not execute the command.

If using `SECOND_BRAIN_HOME`, copy examples to that workspace's inbox instead.
The included examples are synthetic. Personal notes are never included by default.

## Personalize and share

Follow [workflow personalization](docs/WORKFLOWS.md). Use your own model accounts,
local profile and source notes. Share application improvements, not private memory.

Follow [GitHub publishing and colleague onboarding](docs/GITHUB.md). The current repository is public; it contains application code and synthetic
examples only. Personal data remains outside it. The colleague clones the code, runs setup and chooses
her own models. No shared API key or central server is required.

## Commands

```powershell
& .\.venv\Scripts\brain.exe init
& .\.venv\Scripts\brain.exe sync
& .\.venv\Scripts\brain.exe status
& .\.venv\Scripts\brain.exe profile
& .\.venv\Scripts\brain.exe capture
& .\.venv\Scripts\brain.exe enrich
& .\.venv\Scripts\brain.exe auto
& .\.venv\Scripts\brain.exe search 'Python environment' --project demo
& .\.venv\Scripts\brain.exe search 'old error' --history
& .\.venv\Scripts\brain.exe read 1 --start-line 1 --end-line 80
& .\.venv\Scripts\brain.exe backup 'C:\Backups\brain-2026-10-21.sqlite3'
```

Use `brain --home PATH COMMAND` to select an explicit workspace. `sync` reports
malformed inputs and exits nonzero if any import failed. Missing source files are
reported but remain in the index; this is intentional history preservation, not
a privacy deletion mechanism. To remove a source completely, stop clients and
create a fresh workspace from a curated inbox, then retire the old workspace and
backups according to your retention needs. Fine-grained purge is not implemented.

## Validation

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitHub Actions is configured for Windows and Ubuntu/Python 3.12. Local tests are
not a claim that the GitHub workflow has already run or that native Windows was
available in the authoring environment. Dependencies are version-ranged; a fully
locked, hash-pinned environment is a future hardening step.

## Boundaries

Local storage/search does not mean local AI inference: retrieved text goes to the
selected hosted model. Check the model's actual data policy. Keep API credentials
in OpenCode's authentication store, never source files. Do not index credentials.
MCP exposes only search, read, status and profile; assistant permissions are not
an OS sandbox. Backups contain original source text and need equal protection.

See [architecture and roadmap](docs/ARCHITECTURE.md) for the implementation scope.
