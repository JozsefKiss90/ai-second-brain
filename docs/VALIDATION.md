# Validation record

Prepared 21 October 2026.

Executed in the Linux authoring environment with Python 3.12:

- Editable Python package build/install: passed.
- Nine storage/search unit tests: passed.
- One MCP stdio integration test using official SDK mcp 1.30.0: passed.
  The client initialized the server, discovered all four tools, searched a
  synthetic note, read its original evidence, and received an error for an
  unknown record ID.
- Python compilation: passed.

Total: 10 tests passed, no skips in this environment.

Not executed here: native Windows PowerShell setup, Windows Task Scheduler,
OpenCode model authentication/UI, live free/OpenAI inference, and GitHub Actions.
The CI workflow is supplied for Windows and Linux once the repository is pushed.

No personal documents, external accounts or model calls were used in tests.


## Version 0.2 automation validation

All 23 local unit/integration tests passed. Added tests for incremental/project-scoped capture, feedback exclusions,
summary validation/cache/model gating, retry and migration handling, and locks.
A real OpenCode V1 1.19.3 synthetic-session import/list/export capture smoke test
passed. The real CLI also accepted the isolated no-tools agent configuration.
Cloud inference and Windows Task Scheduler were not executed here.
See AUTOMATION.md for target-PC verification before enabling scheduling.
