"""Compile-time checks for preserving native Auto without dropping the proxy."""
import hashlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import compile_workflows


class NativeAutoTests(unittest.TestCase):
    def test_only_the_expected_launcher_is_changed(self):
        source = b'prefix\n      role: "main",\n      configuredModel,\n      aliasMap: aliases,\nsuffix\n'
        expected = hashlib.sha256(source).hexdigest()
        result = compile_workflows.preserve_native_auto(source, expected)
        self.assertIn(b'preserveAuto: configuredModel === "auto",', result)
        self.assertEqual(result.replace(
            b'      preserveAuto: configuredModel === "auto",\n', b''), source)
        with self.assertRaisesRegex(ValueError, 'hash'):
            compile_workflows.preserve_native_auto(source + b'changed', expected)
        with self.assertRaisesRegex(ValueError, 'hash'):
            compile_workflows.preserve_native_auto(result, expected)

    def test_unknown_or_ambiguous_source_is_rejected(self):
        for source in [b'unknown', b'      role: "main",\n      configuredModel,\n      aliasMap:' * 2]:
            with self.assertRaisesRegex(ValueError, 'unique'):
                compile_workflows.preserve_native_auto(source, hashlib.sha256(source).hexdigest())

    def fixture(self):
        return ('# gh-aw-metadata: {"compiler_version":"v0.93.5"}\n'
                '          COPILOT_MODEL: auto\n          COPILOT_MODEL: auto\n'
                '      - name: Execute GitHub Copilot CLI\n        run: copilot\n'
                '      - name: Execute threat detection with AWF\n'
                '        id: detection_agentic_execution\n'
                "        if: always() && steps.guard.outputs.enabled == 'true'\n"
                '        continue-on-error: true\n        run: detect\n')

    def test_both_runtime_jobs_receive_the_same_guarded_correction(self):
        source = self.fixture()
        result = compile_workflows.correct_workflow(source)
        self.assertTrue(all(line == line.rstrip() for line in result.splitlines()))
        self.assertEqual(result.count('name: Preserve native Copilot Auto'), 2)
        self.assertEqual(result.count(compile_workflows.PINNED_HARNESS_SHA256), 2)
        self.assertEqual(result.count('COPILOT_MODEL: auto'), 2)
        self.assertEqual(result.count("if: always() && steps.guard.outputs.enabled == 'true'"), 2)
        for original in ['run: copilot', 'run: detect', 'continue-on-error: true']:
            self.assertIn(original, result)

    def test_incomplete_changed_or_repeated_compilation_is_rejected(self):
        source = self.fixture()
        for changed in [source.replace('v0.93.5', 'v9.0.0'),
                        source.replace('COPILOT_MODEL: auto', 'COPILOT_MODEL:'),
                        source.replace('Execute threat detection with AWF', 'Changed step'),
                        compile_workflows.correct_workflow(source)]:
            with self.assertRaises(ValueError):
                compile_workflows.correct_workflow(changed)

    def test_compile_uses_pinned_release_and_corrects_both_workflows(self):
        with patch.object(compile_workflows.subprocess, 'run', return_value=SimpleNamespace(
                stdout='gh aw version v0.93.5\n')) as run, patch.object(
                compile_workflows.Path, 'read_text', side_effect=[self.fixture(),self.fixture(),
                    '# custom single_response_harness.cjs\nCOPILOT_MODEL: auto\n']), patch.object(
                compile_workflows.Path, 'write_bytes') as write:
            compile_workflows.main()
        self.assertEqual(write.call_count, 3)
        for call in run.call_args_list[1:]:
            self.assertIn(compile_workflows.ACTION_SHA, call.args[0])
            self.assertIn('--no-check-update', call.args[0])
        for call in write.call_args_list[:2]:
            self.assertIn(b'preserveAuto: configuredModel === "auto"', call.args[0])
        self.assertNotIn(b'preserveAuto', write.call_args_list[2].args[0])

    def test_compile_refuses_unreviewed_compiler_without_writing(self):
        with patch.object(compile_workflows.subprocess, 'run', return_value=SimpleNamespace(
                stdout='gh aw version v9.0.0\n')), patch.object(
                compile_workflows.Path, 'write_bytes') as write:
            with self.assertRaisesRegex(ValueError, 'reviewed'):
                compile_workflows.main()
            write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
