"""Bounded assessment packets and a tool-free, one-request transport."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch

from scripts import single_response
from scripts.single_response import build_packet, PACKET_BYTES, validate_response
from scripts.contract import CATEGORIES, FIELDS, digest
from scripts.evidence import configuration_hash


class SingleResponseTests(unittest.TestCase):
    def setUp(self):
        self.case = dict(case_id='example', title='Crash', body='File "pkg/example.py", line 12\nboom',
                         context={'issue': 'Crash\n\nboom',
                                  'pkg/example.py': ''.join(f'line {i}\n' for i in range(1, 101))})
        self.skill = 'Read the report and return JSON.'

    def result(self):
        return dict(case_id=self.case['case_id'], input_hash=digest(self.case),
                    decision='sufficient', missing=[], evidence=['issue'],
                    reasoning='The traceback identifies the failure.', questions=[], comment='')

    def envelope(self, result=None):
        return dict(version=2, assessment=dict(supplied_facts=[dict(source='issue', quote='Crash')], gaps=[]),
                    recommendation=result or self.result())

    def test_packet_ships_whole_source_files_with_provenance(self):
        original = digest(self.case)
        packet = build_packet(self.case, self.skill)
        self.assertEqual(packet['report']['body'], self.case['body'])
        self.assertEqual(packet['input_hash'], original)
        self.assertEqual(packet['skill'], self.skill)
        excerpt = packet['excerpts'][0]
        self.assertEqual(excerpt['key'], 'pkg/example.py')
        self.assertEqual(excerpt['start_line'], 1)
        self.assertEqual(excerpt['end_line'], 100)
        self.assertEqual(excerpt['text'], self.case['context']['pkg/example.py'])
        self.assertEqual(packet['omitted_context'], [])
        self.assertEqual(digest(self.case), original)

    def test_oversized_complete_report_fails_instead_of_truncating(self):
        self.case['body'] = 'x' * PACKET_BYTES
        with self.assertRaisesRegex(ValueError, 'packet'):
            build_packet(self.case, self.skill)

    def test_simulated_tool_attack_is_preserved_as_untrusted_evidence(self):
        case = json.loads(Path('evals/golden/inputs/malicious-tool.json').read_text())
        packet = build_packet(case, self.skill)
        self.assertEqual(packet['supplemental_context']['simulated_tool_response'],
                         case['context']['simulated_tool_response'])

    def test_frozen_inputs_export_without_answer_key_and_within_bounds(self):
        skill = Path('.claude/skills/bug-report-clarification/SKILL.md').read_text(encoding='utf-8')
        for source in Path('evals/golden/inputs').glob('*.json'):
            with self.subTest(source=source.name):
                case = json.loads(source.read_text(encoding='utf-8'))
                packet = build_packet(case, skill)
                self.assertEqual(packet['report']['body'], case['body'])
                self.assertNotIn('expectations', packet)
                self.assertEqual(packet['omitted_context'], [])
                for excerpt in packet['excerpts']:
                    self.assertEqual(excerpt['start_line'], 1)
                    self.assertEqual(excerpt['text'], case['context'][excerpt['key']])
                self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False).encode()), PACKET_BYTES)

    def test_verbatim_multiline_quote_is_accepted_and_reflow_is_rejected(self):
        packet = build_packet(self.case, self.skill)
        exact = 'File "pkg/example.py", line 12\nboom'
        accepted = self.envelope() | {'assessment': dict(
            supplied_facts=[dict(source='issue', quote=exact)], gaps=[])}
        self.assertEqual(validate_response(self.case, packet, json.dumps(accepted)), accepted)
        for quote in ['File "pkg/example.py", line 12 boom', exact.replace('\n', '')]:
            rejected = self.envelope() | {'assessment': dict(
                supplied_facts=[dict(source='issue', quote=quote)], gaps=[])}
            with self.subTest(quote=quote), self.assertRaisesRegex(ValueError, 'quote'):
                validate_response(self.case, packet, json.dumps(rejected))

    def test_validation_never_repairs_or_invents_a_recommendation(self):
        packet = build_packet(self.case, self.skill)
        result = self.envelope()
        self.assertEqual(validate_response(self.case, packet, json.dumps(result)), result)
        for raw in ['not json', json.dumps(result | {'command': 'execute'}),
                    json.dumps(self.envelope(self.result() | {'input_hash': 'wrong'})),
                    json.dumps(self.envelope(self.result() | {'evidence': {'issue': self.case['body']}})),
                    json.dumps(self.envelope(self.result() | {'evidence': ['not-supplied.py']}))]:
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                validate_response(self.case, packet, raw)

    def test_node_transport_checks(self):
        result = subprocess.run(['node', '--test', 'tests/single_response.test.cjs'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_harness_packet_allowance_matches_the_packet_builder(self):
        source = (Path(__file__).resolve().parent.parent /
                  'scripts/single_response_harness.cjs').read_text(encoding='utf-8')
        self.assertEqual(int(re.search(r'PACKET_BYTES = (\d+)', source).group(1)), PACKET_BYTES)

    def test_harness_is_covered_by_configuration_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            harness = root / 'scripts/test.cjs'
            harness.write_text('first')
            old = configuration_hash(root)
            harness.write_text('changed')
            self.assertNotEqual(configuration_hash(root), old)

    def test_refused_preparation_records_reason_without_installing_harness(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.chdir(root)
            try:
                with patch.dict(os.environ,{'GITHUB_REPOSITORY':'foreign/repo',
                        'RUNNER_TEMP':str(root / 'runner')}), patch.object(single_response,'api',create=True) as api:
                    with self.assertRaisesRegex(ValueError,'foreign repository'):
                        single_response.prepare()
                    api.assert_not_called()
                receipt=json.loads((root / 'output/preparation.json').read_text())
                self.assertEqual(receipt['status'],'refused')
                self.assertIn('foreign repository',receipt['reason'])
                self.assertFalse((root / 'output/recommendation.json').exists())
                self.assertFalse((root / 'runner/gh-aw/actions/single_response_harness.cjs').exists())
            finally:
                os.chdir(previous)

    def test_workflow_keeps_refusals_visible_and_execution_success_gated(self):
        source=Path('.github/workflows/single-response.md').read_text(encoding='utf-8')
        choices=source.split('options:',1)[1].split('permissions:',1)[0]
        listed={line.strip().removeprefix('- ') for line in choices.splitlines()
                if line.strip().startswith('- ')}
        self.assertEqual(listed,single_response.ALLOWED_CASES)
        validator=source.split('name: Validate output and skill/request evidence',1)[1]
        self.assertIn('CASE_ID: ${{ inputs.case_id }}',validator)
        raw=source.split('name: single-response-raw',1)[1].split('jobs:',1)[0]
        self.assertTrue('if-no-files-found: warn' in raw,'Raw capture should not mask a refusal')
        self.assertTrue('max-ai-credits: 5\n' in source,'Expected five-credit analysis setting')
        self.assertTrue('max-daily-ai-credits: 15\n' in source,'Expected separate declared daily setting')
        lock=Path('.github/workflows/single-response.lock.yml').read_text(encoding='utf-8')
        top_queue=lock.split('\nconcurrency:\n',1)[1].split('\n',4)[:4]
        self.assertIn('  queue: max',top_queue,'All submitted cases must remain queued, not replace pending runs')
        execution=lock.split('- name: Execute GitHub Copilot CLI',1)[1].split('\n      - name:',1)[0]
        conditions=[line for line in execution.splitlines() if line.startswith('        if:')]
        self.assertFalse(conditions,'Default success condition must gate execution after refused preparation')

    def test_mocked_preparation_request_capture_and_clean_validation(self):
        for case_id in ['pytest-15052','pytest-15051','pytest-13403','pytest-13986',
                        'pytest-13716','diagnostic-crash','diagnostic-trigger']:
            with self.subTest(case_id=case_id):
                self._exercise_preparation_request_and_validation(case_id)

    def test_only_frozen_development_cases_and_two_diagnostics_are_allowed(self):
        key=json.loads(Path('evals/golden/expectations.json').read_text(encoding='utf-8'))
        development={x['case_id'] for x in key['expectations']
                     if x['split']=='development' and not x.get('synthetic')}
        wanted=development | {'diagnostic-crash','diagnostic-trigger'}
        self.assertEqual(getattr(single_response,'DEVELOPMENT_CASES',None),wanted)
        self.assertEqual(len(wanted),7)

    def _exercise_preparation_request_and_validation(self, case_id):
        repo = Path.cwd()
        harness = repo / 'scripts/single_response_harness.cjs'
        case = self.case | {'case_id': case_id}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in {
                f'evals/golden/inputs/{case_id}.json': case,
                'evals/golden/single-response-inputs.json': {x:{'input_hash':digest(case)} for x in single_response.CASE_ORDER},
                'evals/golden/expectations.json': {'expectations': [
                    {'case_id':case['case_id'], 'input_hash':digest(case)}]},
            }.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(value), encoding='utf-8')
            target = root / '.claude/skills/bug-report-clarification/SKILL.md'
            target.parent.mkdir(parents=True)
            target.write_text(self.skill, encoding='utf-8')
            (root / 'scripts').mkdir()
            shutil.copyfile(harness, root / 'scripts/single_response_harness.cjs')
            previous = Path.cwd()
            os.chdir(root)
            try:
                env = {'TRUSTED_ROOT': str(root), 'GITHUB_REPOSITORY':'seanisseng/OSS-Assignment',
                       'GITHUB_REF':'refs/heads/main', 'GITHUB_RUN_ATTEMPT':'1',
                       'GITHUB_RUN_ID':'123','GITHUB_SHA':'a'*40,
                       'CASE_ID':case_id,'SINGLE_RESPONSE_ENABLED':'true',
                       'RUNNER_TEMP':str(root / 'runner')}
                with patch.dict(os.environ,env), patch.object(single_response,'review_record',
                        return_value={'configuration_hash':configuration_hash(root)}), patch.object(
                        single_response,'api',create=True,
                        side_effect=AssertionError('Preparation must not query workflow run counts')) as api:
                    single_response.prepare()
                    api.assert_not_called()
                    for key, value in [('SINGLE_RESPONSE_ENABLED','false'),
                                       ('CASE_ID','other'),
                                       ('CASE_ID','../pytest-15051'),
                                       ('GITHUB_REPOSITORY','pytest-dev/pytest')]:
                        with patch.dict(os.environ,{key:value}), self.assertRaises(ValueError):
                            single_response.prepare()
                    for attempt in ['2','17']:
                        with patch.dict(os.environ,{'GITHUB_RUN_ATTEMPT':attempt}), self.assertRaisesRegex(ValueError,'reruns'):
                            single_response.prepare()
                    api.assert_not_called()
                    swapped = case | {'case_id':'a-different-case'}
                    with patch.object(single_response,'load',side_effect=[
                            {x:{'input_hash':digest(case)} for x in single_response.CASE_ORDER}, swapped,
                            {'expectations':[{'case_id':swapped['case_id'],
                                              'input_hash':digest(swapped)}]}]):
                        with self.assertRaisesRegex(ValueError,'case mismatch'):
                            single_response.prepare()
                    # Restore a successful preparation before the mocked execution phase.
                    single_response.prepare()
                    self.assertEqual(json.loads((root / 'output/preparation.json').read_text())['status'],
                                     'prepared')
                result = self.envelope(self.result() | {'case_id':case['case_id'],'input_hash':digest(case)})
                raw = json.dumps({'model':'mock','choices':[{'finish_reason':'stop',
                    'message':{'role':'assistant','content':json.dumps(result)}}]})
                child_env = os.environ | {'GITHUB_WORKSPACE':str(root),
                    'GH_AW_SAFE_OUTPUTS':str(root / 'safeoutputs/outputs.jsonl'),
                    'MOCK_RESPONSE':raw,'GITHUB_RUN_ID':'123','GITHUB_SHA':'a'*40,'GITHUB_RUN_ATTEMPT':'1'}
                code = ('global.fetch=async()=>new Response(process.env.MOCK_RESPONSE);'
                        'require(process.argv[1]).main({stepStartFile:process.argv[2],'
                        'emitCompletion:()=>{}}).catch(e=>{console.error(e);process.exitCode=1;});')
                step_start=root / 'step-start.txt'
                step_start.write_text(str(time.time_ns() // 1000000))
                proc = subprocess.run(['node','-e',code,str(harness),str(step_start),'ignored-cli-arguments'],
                    env=child_env,capture_output=True,text=True,encoding='utf-8')
                self.assertEqual(proc.returncode,0,proc.stderr)
                request=json.loads((root / 'output/request.json').read_text(encoding='utf-8'))
                schema=json.loads(request['messages'][0]['content'].split(
                    'Output contract (JSON Schema):\n',1)[1])['properties']['recommendation']
                self.assertEqual(set(schema['properties']),FIELDS)
                self.assertEqual(set(schema['required']),FIELDS)
                self.assertEqual(set(schema['properties']['missing']['items']['enum']),CATEGORIES)
                self.assertEqual(schema['properties']['evidence']['items']['enum'],
                                 ['issue','pkg/example.py'])
                self.assertFalse((root / 'safeoutputs/outputs.jsonl').exists())
                archive=root / 'raw-artifact.zip'
                with zipfile.ZipFile(archive,'w') as bundle:
                    for file in (root / 'output').iterdir():
                        bundle.write(file,arcname=file.relative_to(root / 'output'))
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(root / 'staged')
                self.assertTrue((root / 'staged/recommendation.json').is_file())
                self.assertFalse((root / 'staged/output').exists())
                (root / 'trusted-input').mkdir()
                shutil.copyfile(root / 'input/manifest.json',root / 'trusted-input/manifest.json')
                with patch.dict(os.environ,{'CASE_ID':case_id,'GITHUB_RUN_ID':'123','GITHUB_SHA':'a'*40,'GITHUB_RUN_ATTEMPT':'1'}):
                    single_response.validate_artifact()
                other='pytest-15052' if case_id!='pytest-15052' else 'pytest-15051'
                with patch.dict(os.environ,{'CASE_ID':other}), self.assertRaisesRegex(
                        ValueError,'case mismatch'):
                    single_response.validate_artifact()
                execution = json.loads((root / 'staged/execution.json').read_text())
                self.assertEqual(execution['requests_sent'],1)
                self.assertEqual(execution['terminal_safe_output'],'noop')
                missing_completion=execution.copy()
                del missing_completion['terminal_safe_output']
                (root / 'staged/execution.json').write_text(json.dumps(missing_completion))
                with patch.dict(os.environ,{'CASE_ID':case_id,'GITHUB_RUN_ID':'123','GITHUB_SHA':'a'*40,'GITHUB_RUN_ATTEMPT':'1'}), self.assertRaisesRegex(ValueError,'execution trace'):
                    single_response.validate_artifact()
                execution['requests_sent']=2
                (root / 'staged/execution.json').write_text(json.dumps(execution))
                with patch.dict(os.environ,{'CASE_ID':case_id,'GITHUB_RUN_ID':'123','GITHUB_SHA':'a'*40,'GITHUB_RUN_ATTEMPT':'1'}), self.assertRaisesRegex(ValueError,'execution trace'):
                    single_response.validate_artifact()
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
