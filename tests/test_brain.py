import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from second_brain.core import Brain


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.brain = Brain(self.home)
        self.brain.init()
        self.note = self.home / 'inbox' / 'note.md'
        self.note.write_text('# Árvíztűrő troubleshooting\nError: npm.ps1 disabled\nUse npm.cmd --version\n', encoding='utf-8')

    def meta(self, **fields):
        self.note.with_name('note.md.meta.json').write_text(json.dumps(fields), encoding='utf-8')

    def test_idempotent_import_and_revision_history(self):
        self.assertEqual(self.brain.ingest()['imported'], 1)
        self.assertEqual(self.brain.ingest()['unchanged'], 1)
        old = self.brain.search('npm')[0]['id']
        self.note.write_text('Replacement command: python --version', encoding='utf-8')
        self.brain.ingest()
        self.assertEqual(self.brain.search('npm'), [])
        self.assertEqual(self.brain.search('npm', history=True)[0]['id'], old)
        self.assertEqual(self.brain.status()['revisions'], 2)

    def test_metadata_changes_and_old_dates(self):
        self.meta(source_date='2020-01-01T00:00:00Z', project='alpha')
        self.brain.ingest()
        r = self.brain.search('npm', project='alpha')[0]
        self.assertTrue(r['metadata']['source_date'].startswith('2020'))
        self.meta(source_date='2020-01-01T00:00:00Z', project='beta')
        self.assertEqual(self.brain.ingest()['imported'], 1)
        self.assertEqual(self.brain.search('npm', project='alpha'), [])

    def test_bad_metadata_preserves_previous(self):
        self.brain.ingest()
        self.meta(source_date='2020-01-01')
        self.assertEqual(len(self.brain.ingest()['errors']), 1)
        self.assertEqual(len(self.brain.search('npm')), 1)

    def test_unicode_punctuation_and_safe_queries(self):
        self.brain.ingest()
        self.assertEqual(len(self.brain.search('arvizturo')), 1)
        self.assertEqual(len(self.brain.search('npm.cmd --version')), 1)
        self.assertEqual(self.brain.search('" : * ()'), [])
        self.assertEqual(self.brain.search('nonexistent_xyz'), [])

    def test_exact_evidence_and_bounds(self):
        self.brain.ingest()
        rid = self.brain.search('npm')[0]['id']
        lines = self.brain.read(rid)['lines']
        self.assertEqual(lines[2]['text'], 'Use npm.cmd --version')
        with self.assertRaises(ValueError):
            self.brain.read(rid, 1, 500)
        with self.assertRaises(ValueError):
            self.brain.read(99999)
        with self.assertRaises(ValueError):
            self.brain.search('npm', limit=100)

    def test_missing_source_retained_and_reported(self):
        self.brain.ingest()
        self.note.unlink()
        self.assertEqual(self.brain.ingest()['missing_sources_retained'], ['note.md'])
        self.assertEqual(len(self.brain.search('npm')), 1)

    def test_backup_restores_search(self):
        self.brain.ingest()
        backup = self.home / 'snapshot.sqlite3'
        self.brain.backup(backup)
        # SQLite's transaction context does not close the connection.
        # Explicitly close it before TemporaryDirectory cleanup on Windows.
        with closing(sqlite3.connect(backup)) as c:
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(c.execute("SELECT count(*) FROM chunks WHERE chunks MATCH 'npm'").fetchone()[0], 1)
        with self.assertRaises(ValueError):
            self.brain.backup(backup)

    def test_symlink_escape(self):
        outside = self.home / 'outside.md'
        outside.write_text('outside-secret', encoding='utf-8')
        link = self.home / 'inbox' / 'escape.md'
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest('symlink creation requires privileges')
        result = self.brain.ingest()
        self.assertTrue(any(e['source'] == 'escape.md' for e in result['errors']))
        self.assertEqual(self.brain.search('outside-secret'), [])

    def test_profile_not_overwritten(self):
        p = self.home / 'profile.json'
        p.write_text('{"display_name":"My own profile"}', encoding='utf-8')
        self.brain.init()
        self.assertEqual(self.brain.profile()['display_name'], 'My own profile')


if __name__ == '__main__':
    unittest.main()
