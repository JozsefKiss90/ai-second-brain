import copy
import json
import tempfile
import time
import unittest
from pathlib import Path

from second_brain.core import Brain
from second_brain.automation import (DEFAULTS, capture, config, enrich, lock,
    model_events, render_session, run, safe_failure, source_chunks, summarize, validate_metadata)


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.brain = Brain(self.home / 'private')
        self.brain.init()
        self.project = self.home / 'project'
        self.project.mkdir()
        self.cfg = copy.deepcopy(DEFAULTS)
        self.cfg['capture'].update(enabled=True, projects=[str(self.project)])
        self.cfg['enrichment'].update(enabled=True, model='opencode/test-free')
        stamp = int((time.time()-1000)*1000)
        self.session = {'info': {'id': 'ses_fixture123', 'title': 'Test conversation',
            'directory': str(self.project), 'time': {'created': stamp, 'updated': stamp}},
            'messages': [{'info': {'role': 'user', 'time': {'created': stamp}},
                'parts': [{'type': 'text', 'text': 'Use uv venv --python 3.12 --seed .venv'}]},
                {'info': {'role': 'assistant', 'agent': 'build', 'time': {'created': stamp+1}},
                 'parts': [{'type': 'text', 'text': 'A suggested command, not a confirmed successful run.'},
                           {'type': 'reasoning', 'text': 'private-reasoning'},
                           {'type': 'tool', 'tool': 'shell', 'state': {'output': 'secret-tool-dump'}}]}]}

    def runner(self, executable, args, cwd, **kwargs):
        if 'list' in args:
            i = self.session['info']
            return json.dumps([{'id': i['id'], 'directory': i['directory'], 'updated': i['time']['updated']}])
        return json.dumps(self.session)

    def note(self):
        (self.brain.home / 'inbox' / 'test.md').write_text('Use uv for Python.\nThe command was uv venv.\n', encoding='utf-8')
        self.brain.ingest()

    def payload(self):
        return {'summary': 'The note discusses environment setup.', 'questions': ['How did I bootstrap?'],
                'keywords': ['bootstrap'], 'atoms': [{'kind': 'command', 'quote': 'uv venv', 'start_line': 2, 'end_line': 2}]}

    def test_defaults_are_opt_in_and_profile_preserved(self):
        loaded = config(self.brain)
        self.assertFalse(loaded['capture']['enabled'])
        self.assertFalse(loaded['enrichment']['enabled'])
        self.assertEqual(run(self.brain)['enrichment']['completed'], 0)
        p = self.brain.home / 'automation.json'
        p.write_text(json.dumps(self.cfg))
        self.brain.init()
        self.assertEqual(config(self.brain)['enrichment']['model'], 'opencode/test-free')

    def test_capture_is_incremental_and_preserves_dates(self):
        first = capture(self.brain, self.cfg, self.runner)
        self.assertEqual(first['captured'], 1)
        second = capture(self.brain, self.cfg, self.runner)
        self.assertEqual(second['unchanged'], 1)
        self.brain.ingest()
        result = self.brain.search('uv')[0]
        original = self.brain.read(result['id'])
        self.assertEqual(original['metadata']['authority'], 'conversation')
        self.assertNotIn('private-reasoning', '\n'.join(x['text'] for x in original['lines']))
        self.assertNotIn('secret-tool-dump', '\n'.join(x['text'] for x in original['lines']))
        self.assertEqual(original['metadata']['source_date_provenance'], 'latest included message creation timestamp')
        self.session['info']['time']['updated'] += 1
        self.session['messages'][0]['parts'][0]['text'] += '\nNew decision.'
        self.assertEqual(capture(self.brain, self.cfg, self.runner)['captured'], 1)
        self.assertEqual(self.brain.ingest()['imported'], 1)
        self.assertEqual(self.brain.status()['revisions'], 2)

    def test_scope_and_feedback_exclusion(self):
        self.session['info']['directory'] = str(self.home / 'another-project')
        self.assertEqual(capture(self.brain, self.cfg, self.runner)['skipped'], 1)
        self.session['info']['directory'] = str(self.project)
        self.session['messages'][1]['parts'].append({'type': 'tool', 'tool': 'brain_brain_read'})
        self.assertIsNone(render_session(self.session, self.project))
        self.session['messages'][1]['parts'].pop()
        self.session['messages'][1]['info']['agent'] = 'brain_enricher'
        self.assertIsNone(render_session(self.session, self.project))
        self.session['info']['directory'] = ''
        with self.assertRaises(ValueError):
            render_session(self.session, self.project)

    def test_mixed_session_omits_retrieval_turn_but_keeps_new_coding_turn(self):
        self.session['messages'][0]['info']['id'] = 'msg_question'
        self.session['messages'][1]['info']['parentID'] = 'msg_question'
        self.session['messages'][1]['parts'].append({'type':'tool','tool':'brain_brain_search'})
        stamp = self.session['info']['time']['updated']
        self.session['messages'].append({'info': {'id':'msg_new','role':'user','time':{'created':stamp+2}},
                                        'parts':[{'type':'text','text':'Independent new coding task'}]})
        body, _ = render_session(self.session, self.project)
        self.assertIn('Independent new coding task', body)
        self.assertNotIn('Use uv', body)
        self.assertNotIn('suggested command', body)

    def test_active_sessions_and_bad_exports_do_not_advance_state(self):
        self.session['info']['time']['updated'] = int(time.time()*1000)
        self.assertEqual(capture(self.brain, self.cfg, self.runner)['skipped'], 1)
        self.assertFalse((self.brain.home / 'capture-state.json').exists())
        self.session['info']['time']['updated'] -= 1000000
        def invalid(*args, **kwargs):
            return self.runner(*args, **kwargs) if 'list' in args[1] else '{truncated'
        self.assertEqual(len(capture(self.brain, self.cfg, invalid)['errors']), 1)
        self.assertFalse((self.brain.home / 'capture-state.json').exists())

    def test_summary_search_provenance_and_cache(self):
        self.note()
        result = enrich(self.brain, self.cfg, generator=lambda _: self.payload())
        self.assertEqual(result['completed'], 1)
        found = self.brain.search('bootstrap')[0]
        self.assertEqual(found['evidence_kind'], 'generated_retrieval_metadata')
        source = self.brain.read(found['id'])
        self.assertEqual(source['lines'][1]['text'], 'The command was uv venv.')
        self.assertEqual(source['generated_metadata'][0]['model'], 'opencode/test-free')
        cached = enrich(self.brain, self.cfg, generator=lambda _: self.fail('cache should prevent inference'))
        self.assertEqual(cached['cached'], 1)

    def test_hallucinated_quotes_rejected_and_raw_search_survives(self):
        self.note()
        payload = self.payload()
        payload['atoms'][0]['quote'] = 'a fabricated command'
        failed = enrich(self.brain, self.cfg, generator=lambda _: payload)
        self.assertEqual(len(failed['errors']), 1)
        self.assertEqual(len(self.brain.search('Python')), 1)
        self.assertEqual(self.brain.search('bootstrap'), [])
        retry = enrich(self.brain, self.cfg, generator=lambda _: self.fail('retry must back off'))
        self.assertEqual(retry['deferred'], 1)
        fixed = enrich(self.brain, self.cfg, generator=lambda _: self.payload(), retry_failed=True)
        self.assertEqual(fixed['completed'], 1)

    def test_non_free_model_requires_explicit_manual_permission(self):
        self.note()
        self.cfg['enrichment']['model'] = 'openai/some-model'
        with self.assertRaisesRegex(ValueError, 'allow-paid'):
            enrich(self.brain, self.cfg, generator=lambda _: self.payload())
        self.assertEqual(enrich(self.brain, self.cfg, allow_paid=True, generator=lambda _: self.payload())['completed'], 1)

    def test_chunking_and_budget(self):
        chunks = list(source_chunks('abc\ndef\nghi\n', 12))
        self.assertEqual([(a,b) for a,b,_ in chunks], [(1,1),(2,2),(3,3)])
        self.assertEqual(''.join(t for _,_,t in chunks), '1: abc\n2: def\n3: ghi\n')
        with self.assertRaises(ValueError):
            list(source_chunks('x'*100, 10))
        self.note()
        (self.brain.home / 'inbox' / 'other.md').write_text('Another text\n')
        self.brain.ingest()
        self.cfg['enrichment']['max_jobs_per_run'] = 1
        result = enrich(self.brain, self.cfg, generator=lambda _: {'summary':'note','questions':[],'keywords':[],'atoms':[]})
        self.assertEqual(result['completed'], 1)
        self.assertEqual(result['pending'], 1)

    def test_json_events_and_provider_error(self):
        text = json.dumps(self.payload())
        events = '\n'.join([json.dumps({'type': 'step_start'}),
                            json.dumps({'type': 'text', 'part': {'text': text}})])
        self.assertEqual(model_events(events), self.payload())
        with self.assertRaises(ValueError):
            model_events(json.dumps({'type':'error'}))
        with self.assertRaises(ValueError):
            model_events(json.dumps({'type':'tool_use'}))
        with self.assertRaises(ValueError):
            model_events('[]')

    def test_provider_errors_are_classified_without_exposing_private_text(self):
        error = {'type':'error','error':{'name':'APIError','data':{
            'statusCode':403, 'message':"OpenCode's free tier can only be used from within OpenCode. SECRET",
            'responseBody':'PRIVATE SOURCE TEXT'}}}
        reason = safe_failure(json.dumps(error), 'private token: SECRET', 1)
        self.assertIn('FreeTierError', reason)
        self.assertNotIn('SECRET', reason)
        self.assertNotIn('PRIVATE', reason)
        with self.assertRaisesRegex(ValueError, 'FreeTierError'):
            model_events(json.dumps(error))
        error['error']['data']['statusCode'] = 429
        self.assertIn('429', safe_failure(json.dumps(error)))

    def test_unknown_cli_errors_do_not_dump_stderr(self):
        reason = safe_failure('', 'API_KEY=SECRET / private-source', 1)
        self.assertIn('exit 1', reason)
        self.assertNotIn('SECRET', reason)
        self.assertIn('option unsupported', safe_failure('', 'Unknown argument: pure', 1))

    def test_worker_denies_tools_and_uses_only_explicit_model(self):
        seen = {}
        def fake(exe, args, cwd, **kwargs):
            seen.update(args=args, cwd=cwd, **kwargs)
            return json.dumps({'type':'text','part':{'text':json.dumps(self.payload())}})
        summarize(self.brain, self.cfg, '1: Source', fake)
        override = json.loads(seen['env']['OPENCODE_CONFIG_CONTENT'])
        self.assertEqual(override['agent']['brain_enricher']['permission'], {'*':'deny'})
        self.assertEqual(override['small_model'], 'opencode/test-free')
        self.assertNotIn('Source', ' '.join(seen['args']))
        self.assertFalse(Path(seen['args'][seen['args'].index('--file')+1]).exists())
        self.assertNotEqual(seen['cwd'], self.project)

    def test_lock_prevents_overlap(self):
        with lock(self.brain):
            with self.assertRaisesRegex(ValueError, 'active'):
                with lock(self.brain):
                    self.fail('overlap allowed')

    def test_resume_old_workspace_migration(self):
        # init adds new automation structures without replacing the existing evidence.
        self.note()
        with self.brain.connect() as c:
            c.execute('DROP TABLE summary_jobs')
        self.brain.init()
        self.assertEqual(len(self.brain.search('Python')), 1)
        self.assertEqual(enrich(self.brain, self.cfg, generator=lambda _: self.payload())['completed'], 1)
