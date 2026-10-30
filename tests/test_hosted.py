"""Native evidence import and dispatch recovery without network or inference."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from scripts.contract import digest
from scripts.evidence import configuration_hash, file_hash
from scripts.hosted_collect import bind, dispatch, download, initialize, run_case, save_new
from scripts.hosted_evidence import controls, import_bundle, inspect_attempt, inspect_bundle, study_evidence
from scripts.single_response import (ALLOWED_CASES, CASE_ORDER, PACKET_BYTES, build_packet,
                                     encoded, frozen_case)


class HostedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case_id = CASE_ORDER[0]
        for path in ['scripts/single_response_harness.cjs',
                     '.claude/skills/bug-report-clarification/SKILL.md',
                     'evals/golden/expectations.json', 'evals/golden/single-response-inputs.json']:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        for case_id in CASE_ORDER:
            for path in [f'evals/golden/inputs/{case_id}.json', f'evals/golden/adversarial/{case_id}.json']:
                if Path(path).exists():
                    target = self.root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
        self.study = self.root / 'evals/golden/hosted/final'
        self.bundle = self.study / self.case_id / 'bundles/first'
        self.bundle.mkdir(parents=True)
        self.commit = 'a' * 40
        self.dispatch_record = dict(case_id=self.case_id, commit=self.commit,
            configuration_hash=configuration_hash(self.root), token='unique', recorded_at='2026-10-31T00:00:00Z')
        self.run = dict(id=123, head_sha=self.commit, event='workflow_dispatch', run_attempt=1,
            path='.github/workflows/single-response.lock.yml',
            display_title=f'single-response {self.case_id} unique', status='completed', conclusion='success',
            repository={'full_name':'seanisseng/OSS-Assignment'},
            created_at='2026-10-31T00:00:01Z', updated_at='2026-10-31T00:01:00Z')
        self.case = frozen_case(self.root, self.case_id)
        skill_path = self.root / '.claude/skills/bug-report-clarification/SKILL.md'
        self.packet = build_packet(self.case, skill_path.read_text(encoding='utf-8'))
        self.manifest = dict(case_id=self.case_id, input_hash=digest(self.case),
            packet_sha256=__import__('hashlib').sha256(encoded(self.packet)).hexdigest(),
            skill_sha256=file_hash(skill_path), artifact_only=True, sandbox_issue=None,
            commit=self.commit, run_id='123', run_attempt='1',
            configuration_hash=configuration_hash(self.root))
        self.envelope = dict(version=2, assessment=dict(supplied_facts=[dict(source='issue',
            quote=self.case['body'][:40])], gaps=[]), recommendation=dict(case_id=self.case_id,
            input_hash=digest(self.case),decision='sufficient',missing=[],evidence=['issue'],
            reasoning='The supplied report permits investigation.',questions=[],comment=''))
        proc = subprocess.run(['node','-e',
            'const h=require(process.argv[1]);let s="";process.stdin.on("data",x=>s+=x);'
            'process.stdin.on("end",()=>process.stdout.write(JSON.stringify(h.makeRequest(JSON.parse(s)))));',
            str((self.root / 'scripts/single_response_harness.cjs').resolve())],
            input=json.dumps(self.packet),text=True,encoding='utf-8',capture_output=True,check=True)
        self.request = json.loads(proc.stdout)
        self.write('run.json', self.run)
        self.write('single-response-input/manifest.json', self.manifest)
        path = self.bundle / 'single-response-input/packet.json'
        path.write_bytes(encoded(self.packet))
        self.write('single-response-raw/preparation.json', dict(status='prepared',requests_sent=0))
        self.trace = self.manifest | dict(status='response_received',requests_sent=1,
            terminal_safe_output='noop',model_requested='auto',tools=[],timeout_ms=540000)
        self.write('single-response-raw/execution.json', self.trace)
        self.write('single-response-raw/request.json', self.request)
        self.response(json.dumps(self.envelope))
        for name, value in [('dispatch',self.dispatch_record),('binding',self.run)]:
            save_new(self.study / self.case_id / (name+'.json'),value)

    def write(self, name, value):
        path = self.bundle / name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value),encoding='utf-8')

    def response(self, content):
        self.write('single-response-raw/provider-response.json',dict(choices=[dict(finish_reason='stop',
            message=dict(role='assistant',content=content))]))
        (self.bundle / 'single-response-raw/assistant-response.txt').write_text(content,encoding='utf-8')
        for name in ['recommendation','assessment']:
            self.write(f'single-response-raw/{name}.json',self.envelope[name])

    def inspect(self):
        return inspect_bundle(self.root,self.case_id,self.bundle,self.dispatch_record,self.run)

    def test_all_22_frozen_packets_and_explicit_adversarial_preparation(self):
        self.assertEqual(len(ALLOWED_CASES),22)
        self.assertEqual(set(CASE_ORDER), {p.stem for p in (self.root / 'evals/golden/inputs').glob('*.json')})
        for case_id in CASE_ORDER:
            case = frozen_case(self.root,case_id)
            packet = build_packet(case,self.packet['skill'])
            self.assertLessEqual(len(encoded(packet)),PACKET_BYTES)
            self.assertEqual(packet['omitted_context'],[])
            self.assertNotIn('expectations',packet)
        for value in ['../fake-approval','not-allowed','pytest-1']:
            with self.assertRaises(ValueError):
                frozen_case(self.root,value)
        path=self.root / 'evals/golden/inputs/fake-approval.json'
        value=json.loads(path.read_text());value['body']+='changed';path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'frozen input'):
            frozen_case(self.root,'fake-approval')

    def test_import_is_resumable_and_draft_is_not_review(self):
        self.assertEqual(self.inspect()['validation'],'valid')
        import_bundle(self.root,self.study,self.case_id,self.bundle)
        import_bundle(self.root,self.study,self.case_id,self.bundle)
        outcome=inspect_attempt(self.root,self.case_id)
        self.assertTrue(outcome['skill_read'])
        self.assertIn('review pending',str(outcome['errors']))
        actual=json.loads((self.root / f'evals/golden/actual/{self.case_id}.json').read_text())
        self.assertEqual(actual,self.envelope['recommendation'])

    def test_reviewed_wrong_decision_has_complete_evidence_and_tampering_fails(self):
        self.envelope['recommendation']['decision']='human_review'
        self.response(json.dumps(self.envelope))
        import_bundle(self.root,self.study,self.case_id,self.bundle)
        path=self.root / f'evals/golden/assessments/{self.case_id}.json'
        value=json.loads(path.read_text())
        value.update(status='reviewed',reviewer='fixture reviewer',reviewed_at='2026-10-31T00:02:00Z',
                     relevance='Fixture reviewed',redundancy='Fixture reviewed',procedure='Fixture reviewed',
                     safety='Fixture reviewed',blocker_reasonableness='Fixture no-action decision',
                     explanation='Fixture review: disagrees with sufficient primary.')
        path.write_text(json.dumps(value))
        self.assertEqual(inspect_attempt(self.root,self.case_id)['errors'],[])
        self.write('single-response-raw/request.json',{})
        self.assertIn('hash mismatch',str(inspect_attempt(self.root,self.case_id)['errors']))

    def test_artifact_only_controls_require_explanations_not_publication_or_phone_tests(self):
        value=dict(configuration_hash=configuration_hash(self.root),paid_overages_disabled=True,
            usage_before=dict(availability='unavailable',explanation='Fixture cannot access account'),
            usage_after=dict(availability='unavailable',explanation='Fixture cannot access account'))
        for name in ['publication','phone_cancellation','malicious_tool','skill_procedure','billing','launch_switch']:
            value[name]=dict(status='unnecessary' if name=='publication' else 'untested',explanation='Fixture status')
        evidence=self.root / 'evals/evidence/switch.json'
        save_new(evidence,{'value':'false'})
        value['launch_switch']=dict(status='tested',explanation='Fixture false value',evidence=[
            dict(path=evidence.relative_to(self.root).as_posix(),sha256=file_hash(evidence))])
        target=self.root / 'evals/evidence/single-response-controls.json'
        save_new(target,value)
        controls(self.root)
        value['phone_cancellation']['explanation']=''
        target.write_text(json.dumps(value))
        with self.assertRaises(ValueError): controls(self.root)

    def test_final_study_rejects_unapproved_or_mixed_commit_records(self):
        freeze=dict(approved=False,configuration_hash=configuration_hash(self.root),cases=list(CASE_ORDER),
            planned_requests=22,expectations_hash=digest(json.loads((self.root / 'evals/golden/expectations.json').read_text())['expectations']),
            input_inventory=json.loads((self.root / 'evals/golden/single-response-inputs.json').read_text()),
            inference_commit=self.commit,approved_at='2026-10-30T00:00:00Z')
        target=self.root / 'evals/golden/final-configuration.json'
        save_new(target,freeze)
        with self.assertRaisesRegex(ValueError,'approval pending'): study_evidence(self.root)
        freeze['approved']=True;target.write_text(json.dumps(freeze))
        for index,case_id in enumerate(CASE_ORDER):
            save_new(self.root / f'evals/golden/transcripts/{case_id}.json',dict(requests_sent=1,
                dispatch=dict(commit=self.commit,recorded_at=f'2026-10-31T00:{index:02}:00Z'),
                binding=dict(head_sha=self.commit),imported_at=f'2026-10-31T00:{index:02}:30Z'))
        study_evidence(self.root)
        path=self.root / f'evals/golden/transcripts/{CASE_ORDER[-1]}.json'
        value=json.loads(path.read_text());value['dispatch']['commit']='b'*40;path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'commits differ'): study_evidence(self.root)

    def test_invalid_model_output_can_have_complete_native_evidence(self):
        self.response('not JSON')
        outcome=self.inspect()
        self.assertNotEqual(outcome['validation'],'valid')
        self.assertTrue(outcome['continue_allowed'])
        import_bundle(self.root,self.study,self.case_id,self.bundle)
        self.assertFalse((self.root / f'evals/golden/actual/{self.case_id}.json').exists())

    def test_tampered_packet_skill_delivery_derived_response_and_incomplete_trace_rejected(self):
        mutations=[('single-response-input/manifest.json', self.manifest | {'packet_sha256':'wrong'}),
            ('single-response-raw/request.json',self.request | {'messages':[]}),
            ('single-response-raw/recommendation.json',{}),
            ('single-response-raw/execution.json',self.trace | {'status':'request_sent'}),
            ('single-response-raw/execution.json',self.trace | {'run_id':'456'}),
            ('single-response-raw/execution.json',self.trace | {'requests_sent':2})]
        for name, value in mutations:
            path=self.bundle / name; original=path.read_bytes()
            self.write(name,value)
            with self.subTest(name=name,value=value),self.assertRaises(ValueError):
                self.inspect()
            path.write_bytes(original)

    def test_missing_artifacts_and_reused_run_id_rejected(self):
        path=self.bundle / 'single-response-raw/request.json'
        original=path.read_bytes();path.unlink()
        with self.assertRaises(OSError):
            self.inspect()
        path.write_bytes(original)
        save_new(self.root / 'evals/golden/transcripts/other.json',dict(run_id=123))
        with self.assertRaisesRegex(ValueError,'reused'):
            import_bundle(self.root,self.study,self.case_id,self.bundle)

    def test_refusal_and_cancellation_are_preserved(self):
        self.write('single-response-raw/preparation.json',dict(status='refused',requests_sent=0,reason='disabled'))
        self.assertFalse(self.inspect()['continue_allowed'])
        self.write('run.json',self.run | {'conclusion':'cancelled'})
        self.assertEqual(self.inspect()['workflow_status'],'cancelled')

    def test_dispatch_records_before_failure_and_never_resends(self):
        destination=self.root / 'new-study'
        initialize(self.root,destination,self.commit)
        plan=json.loads((destination / 'plan.json').read_text());plan['approved']=True
        (destination / 'plan.json').write_text(json.dumps(plan))
        calls=[]
        def call(*args):
            calls.append(args)
            if args[0]=='api': return json.dumps({'sha':self.commit})
            self.assertTrue((destination / self.case_id / 'dispatch.json').exists())
            raise ConnectionError('lost after sending')
        # configuration_hash uses cwd; bind to the fixture for this isolated test.
        from unittest.mock import patch
        with patch('scripts.hosted_collect.configuration_hash',return_value=plan['configuration_hash']):
            with self.assertRaises(ConnectionError): dispatch(destination,self.case_id,call)
            with self.assertRaises(FileExistsError): dispatch(destination,self.case_id,call)
        self.assertEqual(sum(args[0]=='workflow' for args in calls),1)

    def test_bind_and_download_recover_without_dispatch(self):
        calls=[]
        def call(*args):
            calls.append(args)
            if args[0]=='api': return json.dumps(self.run)
            return ''
        bind(self.study,self.case_id,123,call)
        download(self.study,self.case_id,call)
        self.assertFalse(any(args[0]=='workflow' for args in calls))
        wrong=self.run | {'head_sha':'b'*40}
        with self.assertRaises(ValueError):
            bind(self.study,self.case_id,123,lambda *args:json.dumps(wrong))

    def test_run_disables_launch_switch_on_connection_failure(self):
        destination=self.root / 'new-study'
        initialize(self.root,destination,self.commit)
        plan=json.loads((destination / 'plan.json').read_text());plan['approved']=True
        (destination / 'plan.json').write_text(json.dumps(plan))
        calls=[]
        def call(*args):
            calls.append(args)
            if args[0]=='api': raise ConnectionError('authentication lost')
            return ''
        with self.assertRaises(ConnectionError):
            run_case(self.root,destination,self.case_id,call,pause=lambda seconds:None)
        self.assertEqual(calls[-1][-1],'false')
        self.assertFalse(any(args[0]=='workflow' for args in calls))

    def test_truncated_model_output_is_a_failure_but_not_an_infrastructure_retry(self):
        self.trace.update(status='failed',error='incomplete response or tool request')
        self.trace.pop('terminal_safe_output')
        self.write('single-response-raw/execution.json',self.trace)
        self.response('{"version":')
        outcome=self.inspect()
        self.assertTrue(outcome['continue_allowed'])
        self.assertNotEqual(outcome['validation'],'valid')


if __name__ == '__main__':
    unittest.main()
