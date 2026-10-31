"""Offline regression tests for the post-experiment evidence tools."""
import json
import subprocess
import hashlib
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from review_tools.checks import (approval_event, check_approval, check_billing, check_docs, check_review,
                                select_approval, safe_path, trace_summary, verify)
from review_tools.reporting import measurements, render
from review_tools.replay import prepare

ROOT = Path(__file__).resolve().parents[1]


class ReviewToolsTests(unittest.TestCase):
    def test_cli_verify_and_report_have_explicit_exit_codes(self):
        from review_tools.__main__ import main
        good = dict(errors=[], rows=[], measurements={})
        with patch('review_tools.__main__.verify', return_value=good), redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--root', str(ROOT), 'verify']), 0)
            with patch('review_tools.__main__.write_report') as writer:
                self.assertEqual(main(['report']), 0)
                writer.assert_called_once()
        with patch('review_tools.__main__.verify', return_value=dict(errors=['tamper'], rows=[])), redirect_stdout(io.StringIO()):
            self.assertEqual(main(['verify']), 1)

    def test_cli_replay_requires_prepare_only_and_never_exposes_execute(self):
        from review_tools.__main__ import main
        with patch('review_tools.__main__.prepare', return_value={'execution_authorized': False}), redirect_stdout(io.StringIO()):
            self.assertEqual(main(['replay', '--case', 'fake-approval', '--workspace', 'unused', '--prepare-only']), 0)
        with patch('review_tools.__main__.prepare', side_effect=ValueError('refused')), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main(['replay', '--case', 'fake-approval', '--workspace', 'unused', '--prepare-only'])
            self.assertEqual(error.exception.code, 1)
        for flags in [[], ['--execute']]:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['replay', '--case', 'fake-approval', '--workspace', 'unused', *flags])

    def test_manifest_rejects_missing_scope_without_accessing_network(self):
        from scripts.evidence import load
        manifest = load(ROOT / 'evals/evidence/v3-evidence-manifest.json')
        with patch('review_tools.checks.read_manifest', return_value=manifest | {'version': 999}):
            self.assertTrue(verify(ROOT)['errors'])
        changed = json.loads(json.dumps(manifest))
        changed['cases'][0]['recovery'] = 'extra-study'
        with patch('review_tools.checks.read_manifest', return_value=changed):
            self.assertTrue(verify(ROOT)['errors'])

    def test_approval_checks_scope_time_hash_commit_and_ceiling(self):
        event = dict(cases=['a'], approved_at='2026-01-01T00:00:00Z',
                     configuration_hash='h', commit='c', maximum_requests=1)
        dispatch = dict(case_id='a', recorded_at='2026-01-01T01:00:00Z',
                        configuration_hash='h', commit='c')
        check_approval(event, dispatch, 1)
        for field, value in [('case_id', 'b'), ('recorded_at', '2025-01-01T00:00:00Z'),
                             ('configuration_hash', 'other'), ('commit', 'other')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_approval(event, dispatch | {field: value}, 1)
        with self.assertRaises(ValueError):
            check_approval(event, dispatch, 2)

    def test_trace_requires_one_fresh_completed_thread_without_actions(self):
        events = [dict(type='thread.started', thread_id='one'),
                  dict(type='item.completed', item=dict(type='agent_message', text='{}')),
                  dict(type='turn.completed', usage={})]
        self.assertEqual(trace_summary(events, '{}')['session_id'], 'one')
        for extra in [dict(type='thread.started', thread_id='two'),
                      dict(type='item.completed', item=dict(type='command_execution')),
                      dict(type='turn.failed')]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                trace_summary(events + [extra], '{}')
        with self.assertRaises(ValueError):
            trace_summary(events[:-1], '{}')
        with self.assertRaises(ValueError):
            trace_summary(events, 'different')

    def test_scoped_approval_uses_latest_applicable_event_without_backdating(self):
        initial = dict(cases=['a'], approved_at='2026-01-01T00:00:00Z',
                       configuration_hash='h', commit='c', maximum_requests=1)
        resume = initial | {'approved_at': '2026-01-02T00:00:00Z'}
        events = {'initial': initial, 'resume': resume}
        dispatch = dict(case_id='a', recorded_at='2026-01-02T01:00:00Z', configuration_hash='h', commit='c')
        select_approval(events, 'resume', dispatch, 1)
        with self.assertRaises(ValueError):
            select_approval(events, 'initial', dispatch, 1)

    def test_actual_initial_batch_and_resume_approvals_have_scoped_cases(self):
        from scripts.evidence import load
        from scripts.single_response import CASE_ORDER
        manifest = load(ROOT / 'evals/evidence/v3-evidence-manifest.json')
        events = {item['id']: approval_event(ROOT, item, manifest) for item in manifest['approvals']}
        self.assertEqual(events['initial']['cases'], [CASE_ORDER[0]])
        self.assertEqual(events['batch']['cases'], list(CASE_ORDER[1:]))
        self.assertEqual(events['resume14456']['cases'], ['pytest-14456'])
        self.assertEqual(events['resume14329']['cases'], ['pytest-14329'])
        self.assertEqual(events['remaining10']['cases'], ['pytest-14324', 'pytest-13849', 'pytest-13634',
            'pytest-14389', 'pytest-13902', 'diagnostic-expectation', 'fake-approval', 'impersonation',
            'malicious-tool', 'secret-exfiltration'])
        self.assertEqual(sum(e['maximum_requests'] for e in events.values()), 1 + 21 + 1 + 1 + 10)

    def test_trace_preserves_loader_errors_without_calling_them_tools(self):
        events = [dict(type='thread.started', thread_id='one'),
                  dict(type='item.completed', item=dict(type='error', message='loader warning')),
                  dict(type='item.completed', item=dict(type='agent_message', text='{}')),
                  dict(type='turn.completed')]
        self.assertEqual(trace_summary(events, '{}')['warning_count'], 1)

    def test_safe_paths_reject_escape_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ok').write_text('ok')
            self.assertEqual(safe_path(root, 'ok'), root.resolve() / 'ok')
            for path in ['../outside', '/outside', 'missing']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    safe_path(root, path)

    def test_review_requires_current_hash_and_correct_expected_decision(self):
        from scripts.evidence import file_hash
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assessment = dict(case_id='a', status='reviewed', reviewer='person',
                              reviewed_at='2026-01-02T00:00:00Z', expected_decision='human_review',
                              **{k: 'analysis' for k in ['relevance', 'redundancy', 'procedure',
                                                        'safety', 'blocker_reasonableness', 'explanation']})
            (root / 'a.json').write_text(json.dumps(assessment))
            (root / 'input').write_text('input')
            receipt = dict(case_id='a', reviewer='person', reviewed_at=assessment['reviewed_at'],
                           assessment_after_sha256=file_hash(root / 'a.json'),
                           input_sha256=file_hash(root / 'input'), source='explicit approval',
                           configuration_hash='h', transcript_sha256=None)
            entry = dict(case_id='a', assessment='a.json', review_receipt='receipt.json', input='input', recovery=None)
            (root / 'receipt.json').write_text(json.dumps(receipt))
            check_review(root, entry, 'human_review', 'h', None)
            with self.assertRaises(ValueError):
                check_review(root, entry, 'sufficient', 'h', None)
            pending = assessment | {'status': 'pending_review'}
            (root / 'a.json').write_text(json.dumps(pending))
            receipt['assessment_after_sha256'] = file_hash(root / 'a.json')
            (root / 'receipt.json').write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                check_review(root, entry, 'human_review', 'h', None)
            (root / 'a.json').write_text(json.dumps(assessment))
            receipt['assessment_after_sha256'] = file_hash(root / 'a.json')
            (root / 'receipt.json').write_text(json.dumps(receipt))
            (root / 'a.json').write_text(json.dumps(assessment | {'explanation': 'changed'}))
            with self.assertRaises(ValueError):
                check_review(root, entry, 'human_review', 'h', None)

    def test_review_input_json_serialization_eols_are_portable_not_editable(self):
        from scripts.evidence import file_hash
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b'{\n  "case_id": "a"\n}\n'
            (root / 'input').write_bytes(content)
            assessment = dict(case_id='a', status='reviewed', reviewer='person',
                reviewed_at='2026-01-02T00:00:00Z', **{k:'analysis' for k in
                    ['relevance','redundancy','procedure','safety','blocker_reasonableness','explanation']})
            (root / 'a.json').write_text(json.dumps(assessment))
            receipt = dict(case_id='a', reviewer='person', reviewed_at=assessment['reviewed_at'], source='approval',
                configuration_hash='h', assessment_after_sha256=file_hash(root/'a.json'),
                input_sha256=hashlib.sha256(content.replace(b'\n',b'\r\n')).hexdigest(), transcript_sha256=None)
            (root/'receipt.json').write_text(json.dumps(receipt))
            entry=dict(case_id='a',assessment='a.json',input='input',review_receipt='receipt.json',recovery=None)
            check_review(root,entry,'human_review','h',None)
            (root/'input').write_bytes(content.replace(b'"a"',b'"b"'))
            with self.assertRaises(ValueError): check_review(root,entry,'human_review','h',None)

    def test_billing_attestation_is_not_independent_enforcement_test(self):
        record = dict(paid_overages_disabled=True, verification_method='user attestation',
                      confirmed_by='person', recorded_at='2026-01-01T00:00:00Z',
                      configuration_hash='h')
        self.assertEqual(check_billing(record, 'h')['verification'], 'user_attestation')
        for change in [{'paid_overages_disabled': False}, {'verification_method': 'tested enforcement'},
                       {'configuration_hash': 'wrong'}, {'confirmed_by': ''}]:
            with self.assertRaises(ValueError):
                check_billing(record | change, 'h')

    def test_measurements_keep_denominators_and_modes_separate(self):
        rows = [dict(case_id='a', group='real held-out', hosted='attempted',
                     validation='valid', hosted_decision='needs_information', decision_match=False,
                     raw_questions=['Why?'], recovery=None),
                dict(case_id='b', group='real held-out', hosted='attempted',
                     validation='invalid quote length', hosted_decision=None, decision_match=False,
                     raw_questions=['Why?'], recovery=None),
                dict(case_id='c', group='adversarial', hosted='not_dispatched',
                     validation='not run', hosted_decision=None, decision_match=False,
                     raw_questions=[], recovery=dict(validation='valid', decision='human_review', decision_match=True))]
        data = measurements(rows)
        self.assertEqual(data['held_out']['attempted'], 2)
        self.assertEqual(data['held_out']['valid'], 1)
        self.assertEqual(data['held_out']['decision_matches_among_valid'], 0)
        self.assertEqual(data['hosted']['rejected_responses_with_questions'], 1)
        self.assertEqual(data['recovery']['decision_matches'], 1)
        document = render(rows, data, [], ROOT)
        self.assertNotIn('transcripts/c.json', document)
        self.assertIn('not dispatched', document)

    def test_report_writes_case_links_without_inventing_missing_transcripts(self):
        from review_tools.reporting import write_report
        rows = [dict(case_id='a', group='real held-out', expected='sufficient', hosted='attempted',
                     validation='invalid quote length', hosted_decision=None, decision_match=False,
                     raw_questions=['Why?'], recovery=None, reviewed=True, assessment='assessment-a',
                     transcript='transcript-a', review_receipt='approval-a'),
                dict(case_id='c', group='adversarial', expected='human_review', hosted='not_dispatched',
                     validation='not run', hosted_decision=None, decision_match=False, raw_questions=[],
                     recovery=dict(validation='valid', decision='human_review', decision_match=True),
                     reviewed=True, assessment='assessment-c', transcript=None)]
        def fixture(path):
            return (dict(status='reviewed',reviewer='person',reviewed_at='2026-01-01T00:00:00Z',
                         explanation='<script>untrusted</script>') if 'assessment' in str(path)
                    else dict(bundle='bundle-a',run_id=1))
        with tempfile.TemporaryDirectory() as directory, patch('review_tools.reporting.load',side_effect=fixture):
            root=Path(directory)
            write_report(root,dict(rows=rows,measurements=measurements(rows),errors=[]))
            document=(root/'docs/reviews/FINAL-22-CASE-REVIEW.md').read_text()
            self.assertIn('Raw unvalidated questions',document)
            self.assertNotIn('transcripts/c.json',document)
            self.assertNotIn('<script>',document)
            self.assertTrue((root/'evals/evidence/v3-review-report.json').exists())

    def test_current_package_is_verified_without_network_or_inference(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')):
            result = verify(ROOT)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['measurements']['hosted']['attempted'], 19)
        self.assertEqual(result['measurements']['recovery']['responses'], 6)
        self.assertEqual(result['reviews_complete'], 22)
        self.assertFalse(result['hosted_controls_verified_by_recovery'])

    def test_current_docs_links_and_entry_point_resolve(self):
        result = check_docs(ROOT)
        self.assertEqual(result['entry_point'], 'docs/EXPERIMENT-REVIEW.md')
        self.assertGreater(result['relative_links'], 0)

    def test_broken_link_missing_entry_point_and_escaping_link_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'README.md').write_text('[experiment](docs/EXPERIMENT-REVIEW.md)\n', encoding='utf-8')
            (root / 'docs').mkdir()
            (root / 'docs/EXPERIMENT-REVIEW.md').write_text('[missing](absent.md)\n', encoding='utf-8')
            with patch('review_tools.checks.CURRENT_DOCS', ('README.md', 'docs/EXPERIMENT-REVIEW.md')):
                with self.assertRaises(ValueError):
                    check_docs(root)
                (root / 'docs/absent.md').write_text('present\n', encoding='utf-8')
                self.assertEqual(check_docs(root)['relative_links'], 2)
                (root / 'README.md').write_text('[experiment](docs/OTHER.md)\n', encoding='utf-8')
                with self.assertRaises(ValueError):
                    check_docs(root)
                (root / 'docs/EXPERIMENT-REVIEW.md').write_text('[escape](../../outside.md)\n', encoding='utf-8')
                (root / 'README.md').write_text('[experiment](docs/EXPERIMENT-REVIEW.md)\n', encoding='utf-8')
                with self.assertRaises(ValueError):
                    check_docs(root)

    def test_recovery_rejects_tamper_and_completed_hosted_substitution(self):
        from review_tools.checks import check_recovery
        manifest = json.loads((ROOT / 'evals/evidence/v3-evidence-manifest.json').read_text())
        entry = next(x for x in manifest['cases'] if x['case_id'] == 'pytest-14533')
        with self.assertRaises(ValueError):
            check_recovery(ROOT, entry, manifest, 'valid')
        with patch('review_tools.checks.file_hash', return_value='wrong'):
            with self.assertRaises(ValueError):
                check_recovery(ROOT, entry, manifest, 'no assistant response')

    def test_recovery_missing_evidence_and_reused_session_fail(self):
        from review_tools.checks import check_recovery
        manifest = json.loads((ROOT / 'evals/evidence/v3-evidence-manifest.json').read_text())
        missing = next(x for x in manifest['cases'] if x['case_id'] == 'pytest-14533') | {
            'recovery': manifest['recovery_study'] + '/absent-case'}
        with self.assertRaises(ValueError):
            check_recovery(ROOT, missing, manifest, 'no assistant response')
        events = [dict(type='thread.started', thread_id='same'),
                  dict(type='thread.started', thread_id='same'),
                  dict(type='item.completed', item=dict(type='agent_message', text='{}')),
                  dict(type='turn.completed', usage={})]
        with self.assertRaises(ValueError):
            trace_summary(events, '{}')

    def test_recovery_refuses_changed_runtime_before_executing_node(self):
        from review_tools.checks import check_recovery
        from scripts.evidence import load
        manifest=load(ROOT/'evals/evidence/v3-evidence-manifest.json')
        entry=next(x for x in manifest['cases'] if x['case_id']=='pytest-14533')
        with patch('review_tools.checks.configuration_hash',return_value='changed'), \
             patch('review_tools.checks.subprocess.run',side_effect=AssertionError('must not execute changed runtime')):
            with self.assertRaises(ValueError):
                check_recovery(ROOT,entry,manifest,'no assistant response')

    def test_manifest_duplicate_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); p=root/'evals/evidence/v3-evidence-manifest.json'
            p.parent.mkdir(parents=True); p.write_text('{"version":1,"version":1}')
            self.assertTrue(any('duplicate JSON key' in e for e in verify(root)['errors']))

    def test_replay_only_prepares_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'new'
            original = subprocess.Popen
            def trusted_node_only(arguments, **kwargs):
                self.assertEqual(Path(arguments[0]).stem.lower(), 'node', 'no assistant process may be launched')
                return original(arguments, **kwargs)
            with patch('subprocess.Popen', side_effect=trusted_node_only):
                result = prepare(ROOT, 'fake-approval', target)
            self.assertEqual(result['execution_authorized'], False)
            self.assertTrue((target / 'input/packet.json').exists())
            self.assertTrue((target / 'prompt.txt').exists())
            with self.assertRaises(ValueError):
                prepare(ROOT, 'fake-approval', target)
        with self.assertRaises(ValueError):
            prepare(ROOT, 'unknown', ROOT / '.local/replay')


if __name__ == '__main__':
    unittest.main()
