"""Prepare a fresh reproduction workspace; never launch an assistant."""
import json
from pathlib import Path

from scripts.contract import require
from scripts.evidence import file_hash, load
from review_tools.checks import RECOVERY_CASES, check_recovery, safe_path, read_manifest


def prepare(root, case_id, workspace):
    root, target = Path(root).resolve(), Path(workspace).resolve()
    require(case_id in RECOVERY_CASES, 'case is not in the recovery allowlist')
    require(not target.exists() and not target.is_relative_to(root), 'use a new workspace outside the repository')
    require(not Path(workspace).is_symlink(), 'symlink workspace refused')
    manifest = read_manifest(root)
    entry = next(e for e in manifest['cases'] if e['case_id'] == case_id)
    validation = 'no assistant response' if entry['hosted'] == 'attempted' else 'not run'
    check_recovery(root, entry, manifest, validation)
    folder = safe_path(root, entry['recovery'])
    result = load(folder / 'result.json')
    target.mkdir(parents=True)
    (target / 'input').mkdir()
    (target / 'output').mkdir()
    for source, destination in [('packet.json', 'input/packet.json'), ('prompt.txt', 'prompt.txt'),
                                ('hosted-request-template.json', 'hosted-request-template.json')]:
        (target / destination).write_bytes((folder / source).read_bytes())
    command = list(result['command'])
    command[0] = 'codex'
    command[command.index('--cd') + 1] = str(target)
    command[command.index('--output-last-message') + 1] = str(target / 'output/assistant-response.txt')
    record = dict(case_id=case_id, execution_authorized=False,
        note='Preparation only. Future model execution requires separate approval and a new study; never overwrite originals.',
        model_requested=result['model_requested'], original_result_sha256=file_hash(folder / 'result.json'),
        command_arguments=command, stdin_file='prompt.txt',
        files={p.relative_to(target).as_posix(): file_hash(p) for p in target.rglob('*') if p.is_file()})
    (target / 'replay-preparation.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record
