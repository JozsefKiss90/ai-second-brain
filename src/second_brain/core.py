from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def default_home():
    if os.environ.get('SECOND_BRAIN_HOME'):
        return Path(os.environ['SECOND_BRAIN_HOME']).expanduser().resolve()
    base = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share'))
    return (base / 'WorkflowSecondBrain').resolve()


PROFILE = {
    'display_name': 'My coding assistant',
    'languages': ['English'],
    'workflows': ['troubleshooting', 'script-writing', 'technical-decisions', 'agent-handoffs'],
    'preferred_tools': ['Windows', 'PowerShell', 'VS Code', 'OpenCode'],
    'answer_style': 'Explain steps, cite source lines, preserve exact commands.',
    'free_model': '',
    'hard_model': '',
    'paid_fallback': False,
}


def source_date(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError('source_date must be a timezone-aware ISO timestamp')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('source_date needs a timezone')
    return d.astimezone(timezone.utc).isoformat()


class Brain:
    def __init__(self, home=None):
        self.home = Path(home).resolve() if home else default_home()
        self.db = self.home / 'brain.sqlite3'

    def init(self):
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / 'inbox').mkdir(exist_ok=True)
        profile = self.home / 'profile.json'
        if not profile.exists():
            profile.write_text(json.dumps(PROFILE, indent=2), encoding='utf-8')
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS revisions(
              id INTEGER PRIMARY KEY, source TEXT NOT NULL, digest TEXT NOT NULL,
              title TEXT NOT NULL, body TEXT NOT NULL, meta TEXT NOT NULL,
              ingested_at TEXT NOT NULL, current INTEGER NOT NULL DEFAULT 1);
            CREATE INDEX IF NOT EXISTS source_idx ON revisions(source,current);
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
              revision UNINDEXED, start_line UNINDEXED, end_line UNINDEXED,
              title, text, tokenize='unicode61 remove_diacritics 2');
            CREATE TABLE IF NOT EXISTS runs(
              id INTEGER PRIMARY KEY, finished_at TEXT, imported INTEGER, errors TEXT);
            ''')
        return {'home': str(self.home), 'profile': str(profile)}

    @contextmanager
    def connect(self, readonly=False):
        if readonly:
            c = sqlite3.connect(self.db.as_uri() + '?mode=ro', uri=True, timeout=5)
        else:
            c = sqlite3.connect(self.db, timeout=5)
            c.execute('PRAGMA journal_mode=WAL')
        c.row_factory = sqlite3.Row
        try:
            yield c
            if not readonly:
                c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def profile(self):
        return json.loads((self.home / 'profile.json').read_text(encoding='utf-8-sig'))

    def ingest(self):
        root = (self.home / 'inbox').resolve()
        imported, unchanged, errors = 0, 0, []
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            seen = set()
            for p in sorted(root.rglob('*')):
                if p.suffix.lower() not in {'.txt', '.md'} or not p.is_file():
                    continue
                key = p.relative_to(root).as_posix()
                seen.add(key)
                try:
                    if not p.resolve().is_relative_to(root):
                        raise ValueError('source escapes inbox')
                    raw = p.read_bytes()
                    if len(raw) > 2_000_000:
                        raise ValueError('file exceeds 2 MB limit; split it first')
                    body = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
                    side = p.with_name(p.name + '.meta.json')
                    if side.exists() and not side.resolve().is_relative_to(root):
                        raise ValueError('metadata escapes inbox')
                    meta = json.loads(side.read_text(encoding='utf-8-sig')) if side.exists() else {}
                    if not isinstance(meta, dict):
                        raise ValueError('metadata must be an object')
                    meta['source_date'] = source_date(meta.get('source_date'))
                    for field in ('project', 'authority', 'status'):
                        if field in meta and not isinstance(meta[field], str):
                            raise ValueError(field + ' must be text')
                    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
                    digest = hashlib.sha256((body + '\0' + encoded).encode()).hexdigest()
                    previous = c.execute('SELECT digest FROM revisions WHERE source=? AND current=1', (key,)).fetchone()
                    if previous and previous['digest'] == digest:
                        unchanged += 1
                        continue
                    title = next((x.lstrip('# ').strip() for x in body.splitlines() if x.strip()), p.stem)[:200]
                    c.execute('SAVEPOINT one_file')
                    try:
                        c.execute('UPDATE revisions SET current=0 WHERE source=?', (key,))
                        cur = c.execute('INSERT INTO revisions(source,digest,title,body,meta,ingested_at) VALUES(?,?,?,?,?,?)',
                                        (key, digest, title, body, encoded, now()))
                        rid = cur.lastrowid
                        lines = body.splitlines()
                        # Bounded line chunks preserve exact source references. Very long lines
                        # stay intact in storage; search/read responses have character limits.
                        for start in range(0, len(lines), 70):
                            stop = min(start + 80, len(lines))
                            c.execute('INSERT INTO chunks VALUES(?,?,?,?,?)',
                                      (rid, start + 1, stop, title, '\n'.join(lines[start:stop])))
                        c.execute('RELEASE one_file')
                    except BaseException:
                        c.execute('ROLLBACK TO one_file')
                        c.execute('RELEASE one_file')
                        raise
                    imported += 1
                except (ValueError, OSError, sqlite3.Error) as exc:
                    errors.append({'source': key, 'error': str(exc)[:300]})
            current = {r['source'] for r in c.execute('SELECT source FROM revisions WHERE current=1')}
            missing = sorted(current - seen)
            c.execute('INSERT INTO runs(finished_at,imported,errors) VALUES(?,?,?)',
                      (now(), imported, json.dumps(errors)))
        return {'imported': imported, 'unchanged': unchanged, 'errors': errors,
                'missing_sources_retained': missing}

    def search(self, query, limit=8, project=None, history=False):
        if not 1 <= limit <= 20:
            raise ValueError('limit must be between 1 and 20')
        terms = re.findall(r'[^\W_]+', query[:2000], re.UNICODE)[:30]
        if not terms:
            return []
        match = ' OR '.join('"' + t + '"' for t in terms)
        sql = '''SELECT r.id,r.source,r.title,r.meta,r.ingested_at,r.current,
                 chunks.start_line,chunks.end_line,
                 substr(chunks.text,1,1800) AS excerpt,bm25(chunks) AS lexical_score
                 FROM chunks JOIN revisions r ON r.id=chunks.revision
                 WHERE chunks MATCH ?'''
        args = [match]
        if not history:
            sql += ' AND r.current=1'
        if project:
            sql += " AND json_extract(r.meta,'$.project')=?"
            args.append(project)
        sql += ' ORDER BY lexical_score LIMIT 100'
        with self.connect(readonly=True) as c:
            rows = c.execute(sql, args).fetchall()
        result = []
        for rank, row in enumerate(rows, 1):
            item = dict(row)
            meta = json.loads(item.pop('meta'))
            stamp = meta.get('source_date')
            boost = 1.0
            if stamp:
                days = max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds()/86400)
                boost += 0.15 * math.exp(-math.log(2)*days/180)
            item.update(metadata=meta, rank_score=boost/(60+rank), freshness_multiplier=boost)
            result.append(item)
        result.sort(key=lambda x: x['rank_score'], reverse=True)
        # Return one leading chunk per revision. Read adjacent lines when needed.
        unique, used = [], set()
        for item in result:
            if item['id'] not in used:
                unique.append(item)
                used.add(item['id'])
            if len(unique) == limit:
                break
        return unique

    def read(self, record_id, start_line=1, end_line=120):
        if not 1 <= start_line <= end_line or end_line-start_line >= 200:
            raise ValueError('request 1-200 lines, using positive line numbers')
        with self.connect(readonly=True) as c:
            r = c.execute('SELECT * FROM revisions WHERE id=?', (record_id,)).fetchone()
        if r is None:
            raise ValueError('record not found')
        out = dict(r)
        body = out.pop('body')
        out['metadata'] = json.loads(out.pop('meta'))
        out['lines'] = [{'line': n, 'text': line[:4000]} for n, line in
                        enumerate(body.splitlines(), 1) if start_line <= n <= end_line]
        # Bound total response independently of source line lengths.
        budget, bounded = 20000, []
        for line in out['lines']:
            if budget <= 0:
                break
            original_len = len(line['text'])
            bounded.append({'line': line['line'], 'text': line['text'][:budget]})
            budget -= original_len
        out['truncated'] = len(bounded) < len(out['lines']) or any(len(x) > 4000 for x in body.splitlines()[start_line-1:end_line]) or budget < 0
        out['lines'] = bounded
        return out

    def status(self):
        with self.connect(readonly=True) as c:
            count = c.execute('SELECT count(*) FROM revisions WHERE current=1').fetchone()[0]
            revisions = c.execute('SELECT count(*) FROM revisions').fetchone()[0]
            last = c.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 1').fetchone()
        return {'documents': count, 'revisions': revisions, 'last_run': dict(last) if last else None}

    def backup(self, destination):
        dest = Path(destination).expanduser().resolve()
        if dest == self.db or dest.exists():
            raise ValueError('choose a new backup path outside the active DB')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self.connect(readonly=True) as c:
            target = sqlite3.connect(dest)
            try:
                c.backup(target)
            finally:
                target.close()
        return {'backup': str(dest)}
