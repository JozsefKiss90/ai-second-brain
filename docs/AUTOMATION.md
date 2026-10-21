# Automatic OpenCode capture and AI-generated retrieval summaries

Version 0.2 adds an opt-in pipeline. It is disabled until each user configures it.
It runs on that person's Windows PC, using her existing OpenCode login.

## What happens

1. `brain capture` lists sessions for explicitly selected project directories and
   exports changed conversations through the documented OpenCode CLI.
2. It stores user/assistant text as local Markdown notes with session identity,
   message dates and provenance. It omits reasoning, attachments and tool dumps.
3. `brain sync` imports those notes and preserves previous versions.
4. `brain enrich` generates retrieval summaries, likely search questions,
   keywords and source-quoted atoms. Long records are split at original source
   line boundaries. Atoms are accepted only if quoted text exists in their cited
   line spans. Summaries/questions remain unverified generated retrieval aids.
5. `brain auto` performs all three stages using the configured limits.
6. Windows Task Scheduler can run `brain auto` periodically while you are logged on.

No mailbox, ChatGPT website, Claude history, global clipboard or browser capture
is included. This version captures OpenCode main sessions, not spawned subagents.
It uses session list/export, not OpenCode's private database schema.

## 1. Update and migrate your local workspace

Close OpenCode before the initial update/migration. In PowerShell:

```powershell
Set-Location C:\Code\ai-second-brain
git pull --ff-only

# Make a consistent backup before the additive schema migration.
$brainHome = if ($env:SECOND_BRAIN_HOME) { $env:SECOND_BRAIN_HOME } else { Join-Path $env:LOCALAPPDATA 'WorkflowSecondBrain' }
$backup = Join-Path $brainHome ('backups\before-automation-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sqlite3')
& .\.venv\Scripts\brain.exe backup $backup

& .\.venv\Scripts\python.exe -m pip install -e '.[mcp]'
& .\.venv\Scripts\brain.exe init
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Stop if the backup or migration fails. `init` adds the summary-job table and
creates private automation.json; it does not overwrite existing notes/profile.
Source lines and record IDs already used by your notes are retained.

## 2. Check the local OpenCode CLI

```powershell
opencode --version
opencode session list --help
opencode export --help
opencode run --help
```

The capture interface was exercised with OpenCode V1 1.19.3 and a synthetic
session. The implementation requires `--pure`, JSON session listing, export,
and `run --model --agent --format json --dir --title`. Older versions may need
an intentional update using the official V1 installation route. Do not mix V1
and V2 commands. If opencode.ps1 is blocked, use opencode.cmd in these manual
commands; Python resolves the command shim through PATH.

In automation.json, `opencode_executable` defaults to `opencode`. If Task
Scheduler cannot find it, use the full executable/command-shim path shown by:

```powershell
Get-Command opencode.cmd, opencode.exe -ErrorAction SilentlyContinue
```

Do not place an entire shell command in this field; it accepts one executable
path, not arguments. PATH/user login may differ for scheduled versus interactive
sessions. First complete a manual run using the same Windows user.

## 3. Enable capture for a specific project

Open the private config:

```powershell
notepad (Join-Path $brainHome 'automation.json')
```

The generated JSON initially resembles:

```json
{
  "capture": {
    "enabled": false,
    "projects": [],
    "exclude_session_ids": [],
    "max_sessions_per_project": 100,
    "settle_seconds": 120
  },
  "enrichment": {
    "enabled": false,
    "model": "",
    "max_jobs_per_run": 3,
    "max_input_chars": 18000,
    "retry_after_seconds": 3600
  },
  "opencode_executable": "opencode"
}
```

Set capture.enabled to true. Put exact project directories in capture.projects,
using JSON double backslashes or forward slashes:

```json
"projects": ["C:/Code/ai-second-brain", "C:/Code/my-automation-project"]
```

Use real existing directories; omit the second example until you have that
project. A selected folder does not imply consent to all projects below it.
Only sessions whose actual directory matches an entry are captured. Add worktree
paths separately. Do not select the private summary-worker directory.

Wait at least two minutes after a conversation changes, then run:

```powershell
& .\.venv\Scripts\brain.exe capture
& .\.venv\Scripts\brain.exe sync
& .\.venv\Scripts\brain.exe status
```

Captured notes are under `$brainHome\inbox\opencode`. Do not edit generated
notes by hand; the next capture may replace them. Put corrections in separate
curated notes. Capture persists per-session update state and reruns only changed
sessions; it recreates missing capture files when possible.

### Why an existing session might be skipped

- It was updated less than settle_seconds ago.
- Its directory is outside the explicit project list.
- It is a spawned subagent or the enrichment worker's session.
- Its ID is listed in exclude_session_ids.
- Its turns use brain_* MCP tools. Both sides of those retrieval turns are omitted
  to avoid recycling remembered answers as independent new evidence. Independent
  coding turns from the same conversation remain eligible. An older export that
  lacks the parent-turn identifiers is skipped conservatively if it uses brain tools.

Your earlier Second Brain retrieval tests may therefore be skipped. Test capture
with a fresh ordinary coding conversation in an approved project and ask it not
to use brain tools, for example planning a non-sensitive CSV-processing script.
Original tool stdout/stderr is not captured. Paste a diagnostic into the chat or
save a troubleshooting note if the exact tool output needs to be remembered.

The initial scan covers at most 100 recent sessions per selected project. Increase
max_sessions_per_project deliberately for an older archive (maximum 10000).
A warning reports a reached list limit; this is not an unlimited archive crawler.
OpenCode exports over 16 MB or extracted transcripts over 2 MB are rejected
visibly. Closed/deleted sessions that OpenCode no longer exports cannot be recovered.
Capture does not automatically purge already indexed history when sessions disappear.

## 4. Enable AI enrichment with an explicitly free model

List actual model identifiers:

```powershell
opencode models opencode
```

Choose an available ID that starts with `opencode/` and ends with `-free` and
verify the provider's current free-model/privacy terms. Do not copy the model's
human display label from the footer as its ID. If login is needed, complete
`opencode` → `/connect` interactively before using the background worker.

Set enrichment.enabled=true and enrichment.model to that exact ID. Start with
max_jobs_per_run=1. Leave capture enabled/disabled as desired; enrichment can
summarize your existing manually imported notes too.

```powershell
& .\.venv\Scripts\brain.exe enrich
& .\.venv\Scripts\brain.exe status
```

This command sends original source text to the chosen hosted model. No source
text is sent while enrichment is disabled. Test on non-sensitive material first.
An ID's `-free` suffix is an execution allowlist, not a contractual guarantee of
future pricing: verify current provider terms before enabling scheduled use.

The worker invokes OpenCode with a fresh read-only `brain_enricher` agent in a
disposable local Git worktree. Only that worktree's `source.txt` is readable;
shell, edit, web, delegation and unrelated file reads remain denied. It explicitly sets both the main and auxiliary small-model
settings to the selected model. External plugins are disabled with --pure.
It does not continue your interactive chat, load the project's brain MCP config,
read your auth file itself, or silently switch to a different model.

Each source chunk has a stable job keyed to its revision, source line range,
input hash, prompt version and model. Completed jobs are reused. Changed records
get new jobs. Failed requests back off for at least one hour by default; raw
search remains available. After diagnosing a failed request, use `brain enrich
--retry-failed` to retry it immediately within the same per-run budget.
The worker has a three-minute request timeout and a
per-run job limit. Long individual lines beyond the configured input limit need
splitting in the original note; they are reported rather than silently truncated.

After successful enrichment, restart OpenCode if it was running pre-upgrade:

```text
Search my Second Brain for Python environment setup.
If the result is generated metadata, read the original source before answering.
Show the original evidence and explain what the generated summary adds.
Cite only original source lines as evidence for factual claims.
```

`brain_read` now includes labelled generated_metadata alongside original lines.
Search results distinguish original_source from generated_retrieval_metadata.
A generated summary is an index aid, not a new independently authoritative fact.

### Optional OpenAI enrichment

OpenAI is still selected manually for difficult interactive questions. If you
also want an OpenAI model to produce batch summaries, set its exact provider/model
ID in automation.json and run explicitly:

```powershell
& .\.venv\Scripts\brain.exe enrich --allow-paid
```

That flag permits the configured non-free model for this manual run only.
`brain auto` and the scheduled task never grant it. If you leave a non-free
model configured, scheduled enrichment refuses to run it. Restore the free-model
ID before enabling normal scheduling. Account access/usage is handled by OpenCode.

## 5. Run the pipeline once, then schedule it

With the desired capture/enrichment settings enabled:

```powershell
& .\.venv\Scripts\brain.exe auto
& .\.venv\Scripts\brain.exe status
```

Check captured/imported/completed counts and errors. With both features disabled,
auto still imports manually maintained inbox notes; it never calls a model.
Once manual operation works, register the local task:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-automation-task.ps1 -Minutes 15
```

The supplied installer registers `Workflow Second Brain Refresh` for the current
user, without elevated privileges. It replaces an existing task of that name.
It starts in about one minute, repeats every 15 minutes, and runs only while you
are logged on. It uses an explicit private workspace path and ignores overlap.
The default execution limit is 14 minutes; keep modest job/session limits.
The OS lock also prevents overlapping manual/scheduled automation runs.

Inspect the last run:

```powershell
Get-ScheduledTaskInfo -TaskName 'Workflow Second Brain Refresh'
Get-Content (Join-Path $brainHome 'automation-console.log')
& .\.venv\Scripts\brain.exe status
```

The last console report is overwritten on each run, not appended indefinitely.
The machine must be on and the user logged in; this is polling, not a live event
hook. The automation script has not been executed on your PC by a remote agent.

Stop scheduling:

```powershell
Disable-ScheduledTask -TaskName 'Workflow Second Brain Refresh'
```

Or disable capture/enrichment in automation.json while retaining ordinary imports.
Removing the task does not delete your notes, original sessions or summary cache.

## Diagnostics and limitations

- `capture` only writes transcript notes. Use sync afterward, or auto for all stages.
- `enrich` only processes already indexed current revisions.
- Check last_automation_run and summary_jobs_current_revisions in brain status.
- Failed jobs retry after their cooldown; jobs left running by interruption also
  become eligible after that cooldown. Pending work beyond the per-run budget is
  reported in the last run and picked up by subsequent runs.
- Source date comes from the latest included message creation timestamp; ingest
  time and provider inference time do not replace it.
- Conversation claims are stored as unverified conversation evidence. They are
  not promoted to approved decisions merely by being summarized.
- Full original imported text is retained; this feature does not implement a
  privacy purge. Existing history/backups need separate retention handling.
- Global OpenCode provider settings are retained so existing authentication can
  work. The isolated worker is not an OS sandbox; it permits only its approved source read.
- Summary JSON/schema/quotes are checked locally. This cannot prove the accuracy
  of every generated sentence; original-source verification remains necessary.

## Validation

The deterministic tests cover capture scope/deduplication/revisions, feedback-loop
exclusion, model gating, quote validation, enrichment caching, bounded job counts,
retry cooldown, additive migration, locks, and the existing storage/MCP features.
A synthetic session was imported into an isolated real OpenCode 1.19.3 installation;
session-list/export capture, indexing, search and unchanged-session skipping worked.
Native Windows scheduled-task execution was not performed in the authoring
environment. Verify scheduling with the manual steps above.

Official interfaces:
- https://opencode.ai/docs/cli/
- https://opencode.ai/docs/agents/
- https://opencode.ai/docs/config/


### Diagnosing a failed enrichment request

A failed job means metadata was not generated; raw-source search remains usable.
Errors now classify recognized provider access/quota/CLI failures without saving
raw provider responses or source text in diagnostic logs. After updating, run:

```powershell
& .\.venv\Scripts\brain.exe enrich --retry-failed
& .\.venv\Scripts\brain.exe status
```

If it reports HTTP 403 / FreeTierError, this is a provider rejection rather than
missing indexed notes or invalid summary JSON. Similar failures are reported on
the official OpenCode tracker, including issue #52907. They do not prove the
cause on your machine. Do not bypass access checks or switch to paid models
silently. Verify your version and a harmless prompt in the official CLI:

```powershell
opencode --version
opencode run --model opencode/deepseek-v4.1-flash-free --format json "Reply with OK only."
```

If that succeeds but enrichment fails, compare the classified worker error;
the next check is worker configuration, rather than reinstalling Python or
assuming your free account is exhausted. Restart OpenCode after code updates.
Use brain_read explicitly to inspect generated_metadata; summaries are attached
to source records and are not independent records with separate IDs.


### Fix for a successful ordinary CLI call but a rejected no-tools worker

Controlled tests on OpenCode 1.19.3 found that the ordinary CLI and --pure CLI
both succeeded, while an agent with all tools disabled received a free-tier 403.
This does not establish a general provider policy; it is the observed compatibility
failure. The worker now uses a normal read-only agent, with access only to its
single temporary numbered-source file. No headers, credentials or client identity
are spoofed. It does not switch providers or models to get around a rejection.

Git establishes a disposable worktree so OpenCode's relative read permissions
have a precise scope. The worker sets an explicit --dir and disables snapshots.
It accepts only successful read events for that exact file; other tool events
or paths cause enrichment to fail. Existing quote/schema/cache validation remains.
After pulling this fix, retry with `brain enrich --retry-failed`.
