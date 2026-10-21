# Windows setup and everyday use

For the complete newcomer walkthrough, including MCP in other projects, daily
prompts, imports, automatic capture and acceptance checks, start with the
**[user manual](USER_MANUAL.md)**. This page is the shorter installation reference.

## 1. Check prerequisites

Open PowerShell (or VS Code's PowerShell terminal):

```powershell
git --version
py -3.12 --version
node --version
npm.cmd --version
opencode --version
```

If needed, install the missing tools using their official installers or winget:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id Python.Python.3.12 --exact --source winget
winget install --id OpenJS.NodeJS.LTS --exact --source winget
```

Reopen the terminal. For OpenCode V1, the documented Windows npm route is:

```powershell
npm.cmd install -g opencode-ai
```

OpenCode V1 and V2 share the command name. This starter uses V1 config/AGENTS.md
conventions. Do not mix V2 installation instructions into an existing V1 setup.
If PowerShell blocks a command's .ps1 shim, use npm.cmd or opencode.cmd.

Official installation: https://opencode.ai/docs/

## 2. Set up this repository

Clone the real repository URL, enter it, review scripts/setup.ps1 and run it as
shown in README. It uses a local venv without requiring activation.

For a machine that prohibits PowerShell script execution, run these individually:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e '.[mcp]'
& .\.venv\Scripts\brain.exe init
& .\.venv\Scripts\python.exe .\scripts\configure.py
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Setup is idempotent for the profile and data. Existing opencode.json/jsonc is
retained; merge the generated local snippet's brain MCP entry manually if needed.
The config embeds the absolute private workspace and venv path. If you move this
repository, regenerate/update this configuration before restarting OpenCode.

## 3. Personalize

Run `brain profile` or open `%LOCALAPPDATA%\WorkflowSecondBrain\profile.json` in
VS Code. See WORKFLOWS.md. Change recurring tasks, languages, coding skill
expectations and output preferences. Do not copy another person's private data.

## 4. Connect models

Start `opencode` in the repository directory. Run `/connect`, choose the available
OpenCode provider/Zen option and follow its sign-in instructions. Select an
explicitly free model with `/models`; verify its pricing and data terms.
Free models are not an unlimited permanent entitlement.

For hard tasks, connect OpenAI through `/connect`. Use ChatGPT Plus/Pro login if
supported for your account, or a separately billed API key. Use your own account.
Switch models manually with `/models` and return to the free model afterward.
The application's free_model/hard_model profile fields do not switch models.
Ordinary local indexing/search makes no inference calls. If you enable optional
enrichment, the Python application invokes OpenCode with the configured model.

Official provider guidance: https://opencode.ai/docs/providers/
Current free-model terms: https://opencode.ai/v2/docs/console/models/

## 5. Add notes and ask questions

Save UTF-8 .md/.txt files into your private inbox; run `brain sync`. Use selected
explicit conversation exports as text, or enable opt-in OpenCode capture using
the [manual](USER_MANUAL.md#5-enable-conversation-capture-and-summaries).
Read evidence through OpenCode's brain MCP tools. `opencode mcp list` checks server
connection. If the MCP server fails, verify the generated executable path and run
`brain status` directly first. MCP uses stdio and does not open a network port.

## 6. Schedule local imports

For capture → imports → optional AI enrichment, use the supplied task installer
after completing the [manual acceptance exercise](USER_MANUAL.md#6-prove-capture-works-then-schedule-it).
The following alternative schedules **only imports of inbox files**; it neither
captures conversations nor generates summaries. Choose the pipeline task for
normal automatic capture rather than registering both schedules.

Task Scheduler → Create Task, using your own user account:

- Trigger daily; repeat every 15 minutes for 1 day.
- Program: full path to this repository's `.venv\Scripts\brain.exe`.
- Arguments: `sync` (or `--home "C:\Your\Workspace" sync` for a custom workspace).
- Start in: full repository directory, without quote characters.
- Run only when logged on initially; no elevated privileges needed.
- If running already: Do not start a new instance.
- Enable running after a missed start; choose battery rules intentionally.

Test Run, Last Run Result and `brain status`. This is periodic folder polling,
not live capture. No AI calls happen. A powered-off PC cannot refresh notes.
Database writes are serialized with a bounded SQLite timeout. Manual overlapping
runs may wait then fail rather than run simultaneously.

## 7. Updates and backups

Before updating code, create a backup to a new filename using `brain backup`.
Then `git pull --ff-only` and rerun setup. The private workspace is outside Git.
Version 0.2 adds automation tables through `brain init`; follow AUTOMATION.md
for backup and migration steps before enabling capture/enrichment. Back up private notes/profile separately as well.

Common issues: reopen terminal for PATH changes; use command shims when script
execution is blocked; check JSON sidecar syntax and timezone-aware dates; check
MCP logs if tools are not discovered. Search is lexical: try translated terms or
add bilingual keywords in notes when a paraphrase does not match.

For optional automatic capture and AI summaries, follow [AUTOMATION.md](AUTOMATION.md).
