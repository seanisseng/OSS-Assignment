"""Bounded assessment packets and a tool-free, one-request transport."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch

from scripts import single_response
from scripts.single_response import build_packet, PACKET_BYTES, validate_response
from scripts.contract import digest
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

    def test_packet_keeps_full_report_and_traceback_excerpt_provenance(self):
        original = digest(self.case)
        packet = build_packet(self.case, self.skill)
        self.assertEqual(packet['report']['body'], self.case['body'])
        self.assertEqual(packet['input_hash'], original)
        self.assertEqual(packet['skill'], self.skill)
        excerpt = packet['excerpts'][0]
        self.assertEqual(excerpt['key'], 'pkg/example.py')
        self.assertLessEqual(excerpt['start_line'], 12)
        self.assertGreaterEqual(excerpt['end_line'], 12)
        lines = self.case['context'][excerpt['key']].splitlines(keepends=True)
        self.assertEqual(excerpt['text'], ''.join(lines[excerpt['start_line']-1:excerpt['end_line']]))
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
                self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False).encode()), PACKET_BYTES)

    def test_validation_never_repairs_or_invents_a_recommendation(self):
        packet = build_packet(self.case, self.skill)
        result = self.result()
        self.assertEqual(validate_response(self.case, packet, json.dumps(result)), result)
        for raw in ['not json', json.dumps(result | {'command': 'execute'}),
                    json.dumps(result | {'input_hash': 'wrong'}),
                    json.dumps(result | {'evidence': ['not-supplied.py']})]:
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                validate_response(self.case, packet, raw)

    def test_node_transport_checks(self):
        result = subprocess.run(['node', '--test', 'tests/single_response.test.cjs'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
                        'RUNNER_TEMP':str(root / 'runner')}), patch.object(single_response,'api') as api:
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
        raw=source.split('name: single-response-raw',1)[1].split('jobs:',1)[0]
        self.assertTrue('if-no-files-found: warn' in raw,'Raw capture should not mask a refusal')
        self.assertTrue('max-ai-credits: 5\n' in source,'Expected five-credit analysis setting')
        self.assertTrue('max-daily-ai-credits: 15\n' in source,'Expected separate declared daily setting')
        lock=Path('.github/workflows/single-response.lock.yml').read_text(encoding='utf-8')
        execution=lock.split('- name: Execute GitHub Copilot CLI',1)[1].split('\n      - name:',1)[0]
        conditions=[line for line in execution.splitlines() if line.startswith('        if:')]
        self.assertFalse(conditions,'Default success condition must gate execution after refused preparation')

    def test_mocked_preparation_request_capture_and_clean_validation(self):
        repo = Path.cwd()
        harness = repo / 'scripts/single_response_harness.cjs'
        case = self.case | {'case_id': 'pytest-15051'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in {
                'evals/golden/inputs/pytest-15051.json': case,
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
                       'CASE_ID':'pytest-15051','SINGLE_RESPONSE_ENABLED':'true',
                       'RUNNER_TEMP':str(root / 'runner')}
                with patch.dict(os.environ,env), patch.object(single_response,'review_record',
                        return_value={'configuration_hash':'approved'}), patch.object(
                        single_response,'api',return_value={'total_count':2}) as api:
                    single_response.prepare()
                    api.assert_called_once()
                    for key, value in [('SINGLE_RESPONSE_ENABLED','false'),
                                       ('CASE_ID','other'),('GITHUB_RUN_ATTEMPT','2'),
                                       ('GITHUB_REPOSITORY','pytest-dev/pytest')]:
                        with patch.dict(os.environ,{key:value}), self.assertRaises(ValueError):
                            single_response.prepare()
                    for count in [0,1,3,True,'2']:
                        api.return_value={'total_count':count}
                        with self.assertRaises(ValueError):
                            single_response.prepare()
                    api.return_value={'total_count':2}
                    swapped = case | {'case_id':'a-different-case'}
                    with patch.object(single_response,'load',side_effect=[swapped,
                            {'expectations':[{'case_id':swapped['case_id'],
                                              'input_hash':digest(swapped)}]}]):
                        with self.assertRaisesRegex(ValueError,'case mismatch'):
                            single_response.prepare()
                    # Restore a successful preparation before the mocked execution phase.
                    single_response.prepare()
                    self.assertEqual(json.loads((root / 'output/preparation.json').read_text())['status'],
                                     'prepared')
                result = self.result() | {'case_id':case['case_id'],'input_hash':digest(case)}
                raw = json.dumps({'model':'mock','choices':[{'finish_reason':'stop',
                    'message':{'role':'assistant','content':json.dumps(result)}}]})
                child_env = os.environ | {'GITHUB_WORKSPACE':str(root),
                    'GH_AW_SAFE_OUTPUTS':str(root / 'safeoutputs/outputs.jsonl'),
                    'MOCK_RESPONSE':raw}
                code = ('global.fetch=async()=>new Response(process.env.MOCK_RESPONSE);'
                        'require(process.argv[1]).main({stepStartFile:process.argv[2]}).catch(e=>{console.error(e);process.exitCode=1;});')
                step_start=root / 'step-start.txt'
                step_start.write_text(str(time.time_ns() // 1000000))
                proc = subprocess.run(['node','-e',code,str(harness),str(step_start),'ignored-cli-arguments'],
                    env=child_env,capture_output=True,text=True,encoding='utf-8')
                self.assertEqual(proc.returncode,0,proc.stderr)
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
                single_response.validate_artifact()
                execution = json.loads((root / 'staged/execution.json').read_text())
                self.assertEqual(execution['requests_sent'],1)
                execution['requests_sent']=2
                (root / 'staged/execution.json').write_text(json.dumps(execution))
                with self.assertRaisesRegex(ValueError,'execution trace'):
                    single_response.validate_artifact()
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
