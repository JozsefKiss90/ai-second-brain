import argparse
import json
import sqlite3
import sys
from .core import Brain


def main():
    p = argparse.ArgumentParser(description='Personal coding workflow memory')
    p.add_argument('--home', help='Private workspace; defaults to LOCALAPPDATA/WorkflowSecondBrain')
    s = p.add_subparsers(dest='command', required=True)
    for name in ('init', 'sync', 'status', 'profile', 'mcp'):
        s.add_parser(name)
    for name in ('capture', 'auto'):
        s.add_parser(name)
    e = s.add_parser('enrich')
    e.add_argument('--allow-paid', action='store_true', help='Explicitly permit the configured non-free model for this manual run only')
    e.add_argument('--retry-failed', action='store_true', help='Retry failed jobs now, still respecting the per-run job budget')
    q = s.add_parser('search')
    q.add_argument('query')
    q.add_argument('--limit', type=int, default=8)
    q.add_argument('--project')
    q.add_argument('--history', action='store_true')
    r = s.add_parser('read')
    r.add_argument('record_id', type=int)
    r.add_argument('--start-line', type=int, default=1)
    r.add_argument('--end-line', type=int, default=120)
    b = s.add_parser('backup')
    b.add_argument('destination')
    a = p.parse_args()
    brain = Brain(a.home)
    try:
        if a.command == 'mcp':
            from .server import serve
            serve(brain)
            return
        if a.command == 'init':
            out = brain.init()
        elif a.command == 'sync':
            out = brain.ingest()
        elif a.command in ('capture', 'enrich', 'auto'):
            from .automation import run
            out = run(brain, a.command, getattr(a, 'allow_paid', False),
                      retry_failed=getattr(a, 'retry_failed', False))
        elif a.command == 'search':
            out = brain.search(a.query, a.limit, a.project, a.history)
        elif a.command == 'read':
            out = brain.read(a.record_id, a.start_line, a.end_line)
        elif a.command == 'backup':
            out = brain.backup(a.destination)
        elif a.command == 'profile':
            out = brain.profile()
        else:
            out = brain.status()
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if isinstance(out, dict) and out.get('errors'):
            sys.exit(1)
    except (ValueError, OSError, sqlite3.Error, ImportError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
