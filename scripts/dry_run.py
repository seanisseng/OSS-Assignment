"""Offline export and import. This module never launches an agent or calls a network."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re

from scripts.contract import digest, require
from scripts.evidence import configuration_hash, file_hash, load, review_record, timestamp, trace_evidence


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def case_path(repo, case_id):
    require(re.fullmatch(r'[a-z0-9-]{1,64}', case_id) is not None, 'invalid case ID')
    return repo / 'evals/golden/inputs' / (case_id + '.json')


def prepare(repo, case_id, workspace):
    repo, workspace = repo.resolve(), workspace.resolve()
    source = case_path(repo, case_id)
    review = review_record(repo)
    destination = repo / f'evals/golden/preparations/{case_id}.json'
    require(not destination.exists(), 'case already prepared; archive attempts as a separate study before retrying')
    require(not workspace.is_relative_to(repo), 'export outside the repository to avoid inherited project context')
    case = load(source)
    require(case['case_id'] == case_id, 'case mismatch')
    skill = repo / '.claude/skills/bug-report-clarification/SKILL.md'
    manifest = dict(case_id=case_id, input_hash=digest(case), skill_sha256=file_hash(skill))
    workspace.mkdir(parents=True, exist_ok=False)
    (workspace / 'output').mkdir()
    save(workspace / 'input/case.json', case)
    save(workspace / 'input/manifest.json', manifest)
    installed = workspace / '.github/skills/bug-report-clarification/SKILL.md'
    installed.parent.mkdir(parents=True)
    installed.write_bytes(skill.read_bytes())
    (workspace / 'AGENTS.md').write_bytes((repo / 'AGENTS.md').read_bytes())
    prompt = (repo / '.github/workflows/clarify.md').read_text(encoding='utf-8').split('---', 2)[2].strip()
    prompt += ('\n\nDry-run adapter: safeoutputs MCP is unavailable. Leave the exact raw JSON in '
               'output/recommendation.json; do not publish. Use only the exported files. '
               'Do not browse or execute report code.\n')
    (workspace / 'prompt.md').write_text(prompt, encoding='utf-8')
    preparation = manifest | dict(configuration_hash=configuration_hash(repo),
        reviewed_at=review['reviewed_at'], prepared_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        files={p.relative_to(workspace).as_posix(): file_hash(p)
               for p in workspace.rglob('*') if p.is_file()})
    save(destination, preparation)
    return preparation


def record(repo, case_id, workspace, raw_trace, status, started_at, finished_at, model_requested):
    case_path(repo, case_id)
    review = review_record(repo)
    require(status in {'completed', 'failed', 'interrupted'}, 'invalid attempt status')
    require(timestamp(review['reviewed_at']) <= timestamp(started_at) <= timestamp(finished_at),
            'review/run timestamps out of order')
    root = repo / 'evals/golden'
    preparation = load(root / f'preparations/{case_id}.json')
    require(preparation['configuration_hash'] == configuration_hash(repo), 'configuration changed since export')
    require(preparation['input_hash'] == digest(load(case_path(repo, case_id))), 'input changed since export')
    require(timestamp(preparation['prepared_at']) <= timestamp(started_at), 'run predates export')
    for name, wanted in preparation['files'].items():
        require(file_hash(workspace / name) == wanted, 'exported input changed: ' + name)
    skill = repo / '.claude/skills/bug-report-clarification/SKILL.md'
    traced = trace_evidence(raw_trace, skill.read_text(encoding='utf-8'), require_skill=False)
    destination = root / f'transcripts/{case_id}.json'
    require(not destination.exists() and not (root / f'actual/{case_id}.json').exists(), 'attempt already recorded')
    raw = root / f'transcripts/raw/{case_id}.jsonl'
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(raw_trace.read_bytes())
    output = workspace / 'output/recommendation.json'
    require(output.exists() or status != 'completed', 'completed attempt requires raw output')
    output_hash = None
    if output.exists():
        require(not output.is_symlink() and output.stat().st_size <= 32768, 'unsafe/oversized output')
        target = root / f'actual/{case_id}.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output.read_bytes())
        output_hash = file_hash(target)
    record_value = dict(case_id=case_id, mode='dry-run', status=status, fresh_session=True,
        session_id=traced['session_id'], input_hash=preparation['input_hash'],
        configuration_hash=preparation['configuration_hash'], skill_sha256=file_hash(skill),
        preparation_sha256=file_hash(root / f'preparations/{case_id}.json'),
        started_at=started_at, finished_at=finished_at, engine='coding-assistant dry run',
        model_requested=model_requested, model_reported=None, model_version_pinned=False,
        usage=traced['usage'], trace_sha256=file_hash(raw), output_sha256=output_hash)
    save(destination, record_value)
    freeze_path = root / 'freeze.json'
    freeze = load(freeze_path)
    freeze['evaluation_started'] = True
    save(freeze_path, freeze)
    return record_value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('prepare')
    export.add_argument('case_id')
    export.add_argument('workspace', type=Path)
    archive = sub.add_parser('record')
    archive.add_argument('case_id')
    archive.add_argument('workspace', type=Path)
    archive.add_argument('raw_trace', type=Path)
    archive.add_argument('--status', choices=['completed', 'failed', 'interrupted'], required=True)
    archive.add_argument('--started-at', required=True)
    archive.add_argument('--finished-at', required=True)
    archive.add_argument('--model-requested', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(Path.cwd(), args.case_id, args.workspace)
        else:
            result = record(Path.cwd(), args.case_id, args.workspace, args.raw_trace, args.status,
                            args.started_at, args.finished_at, args.model_requested)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
