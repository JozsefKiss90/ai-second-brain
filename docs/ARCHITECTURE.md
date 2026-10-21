# Architecture and scope

Flow: UTF-8 source files → normalized revision records → FTS5 line chunks →
BM25 candidate search → bounded source reads → OpenCode/free or OpenAI model.

Private state is separate from software: a per-user LOCALAPPDATA workspace holds
profile.json, inbox and brain.sqlite3; code and examples are in GitHub. An explicit
SECOND_BRAIN_HOME or --home supports alternate workspace locations.

Index imports use SHA-256 over normalized body and canonical metadata. Changed
records add a revision and retain old evidence; search defaults to current
revisions. Sidecar-only changes also trigger a revision. Imports use a SQLite
transaction, per-file savepoints, WAL and a five-second writer wait.

Search uses quoted Unicode tokens joined with OR. This broad lexical search is
not fuzzy/semantic retrieval. Candidates are ordered by ascending SQLite BM25,
then reciprocal rank (1/(60+rank)) receives at most a 15% source-date recency
boost with a 180-day half-life. This is a starting heuristic, not a validated
optimal ranker. Metadata authority/status are exposed, not automatically resolved.
One leading chunk per revision is returned; use read to inspect adjacent evidence.

MCP uses the official Python SDK as an optional dependency. Core storage/search
requires only Python's standard library with SQLite FTS5/JSON support. SDK protocol
startup/integration and native Windows behavior require their own verification;
unit tests alone are not an end-to-end cloud-model test.

## Next implementation stages

1. Validate native Windows installation and live OpenCode/MCP calls on the target PC.
2. Implemented in v0.2: opt-in OpenCode capture plus quote-validated summaries,
   retrieval questions and exact atoms. See AUTOMATION.md. Raw search survives
   enrichment failure. Native Windows scheduling/live inference need target-PC checks.
3. Add explicit opt-in connectors: conversation exports, Git history, PDFs/Word,
   then read-only email. Each needs its own provenance/cursor/error tests.
4. Add reviewable retention/purge and supersession management.
5. Add a deterministic retrieval-first answer wrapper only if required. Current
   OpenCode retrieval is prompted, not programmatically mandatory.
6. Evaluate multilingual/paraphrase failures before adding embeddings/hybrid search.

No automatic paid fallback, autonomous source deletion, email sending, account
sharing, or invisible chat-history capture is implemented.

Automation adds an idempotent summary_jobs table; original chunks/record IDs
remain unchanged. Generated index chunks are marked by negative internal chunk
IDs, then mapped to original line ranges and labelled in tool responses.
