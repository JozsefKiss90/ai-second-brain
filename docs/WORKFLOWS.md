# Customize coding and automation workflows

Each user edits her own profile.json in the private workspace printed by `brain init`.
Keep it out of Git. This is workflow personalization, not model training.

Example fields:

```json
{
  "display_name": "My automation assistant",
  "languages": ["English", "Hungarian"],
  "workflows": ["Excel automation", "Python scripts", "troubleshooting", "agent handoffs"],
  "preferred_tools": ["Windows", "PowerShell", "VS Code", "OpenCode", "Python"],
  "answer_style": "Give numbered steps. Explain commands before execution. Cite prior solutions.",
  "free_model": "",
  "hard_model": "",
  "paid_fallback": false
}
```

Set model IDs only after checking the actual provider/model listing. These fields
are informational: select models in OpenCode's `/models`. No hidden API calls run.

## First personalization conversation

Tell OpenCode:

> Read brain_profile. Help me personalize this assistant for my daily coding
> and automation work. Ask about my five recurring tasks, coding experience,
> typical inputs/outputs, preferred language, tools, folder conventions, and
> commands that require confirmation. Propose changes to my private profile.
> Do not modify application code or import private material without my request.

Changes to profile.json require editing the local file in VS Code or an explicitly
authorized editing workflow; the MCP server is read-only.

## A useful note format

```markdown
# Short descriptive title
Project: ...
Status: confirmed / draft / superseded
Problem: ...
Exact error: ...
Working command: ...
Why this worked: ...
Decision and rationale: ...
Unresolved questions: ...
Source link or conversation export: ...
```

Save notes as UTF-8 .md or .txt in the private inbox. Optional metadata sidecar:
`my-note.md.meta.json`, containing source_date, project, authority and status.
Use timezone-aware dates: `2026-10-21T11:00:00+02:00`. Missing dates remain unknown.

## Ready-to-use requests

- “Search my previous PowerShell errors. Find the exact fix for this message,
  then explain whether it applies here. Do not execute it yet.”
- “Before writing this Excel script, search for my previous formatting and
  file-naming decisions. Cite them and ask about missing requirements.”
- “Create a handoff: goal, current state, decisions, failed attempts, exact
  commands, tests, next steps. Separate recorded evidence from suggestions.”
- “Compare these technical options against my recorded constraints. Show
  conflicts and stale assumptions. I will select an OpenAI model if needed.”
- “Draft a reusable workflow from these notes. Show it for review before I save
  it as a confirmed source.”

## Share software, keep personal memory separate

Both people may clone the same repository and `git pull` code updates. Each has
an independent workspace on her own PC, own profile, model accounts and index.
Code changes can be reviewed through branches and pull requests. A repository
clone does not synchronize the two people's memories or provide shared chat.

Optional: [automatic OpenCode capture and generated retrieval summaries](AUTOMATION.md)
can replace some manual note capture. This is configured independently per user.
