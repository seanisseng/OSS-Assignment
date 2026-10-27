"""Trusted evidence checks; complete evidence need not describe a successful model."""
import datetime as dt
import hashlib
import json
from pathlib import Path

from scripts.contract import digest, require, validate


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timestamp requires a timezone')
    return parsed


def configuration_hash(repo):
    paths = [repo / 'AGENTS.md', repo / 'CONTRIBUTING.md',
             repo / '.claude/skills/bug-report-clarification/SKILL.md',
             *sorted((repo / '.github/workflows').glob('*')),
             *sorted((repo / 'scripts').glob('*.py')), repo / 'config/policy.json']
    return digest({p.relative_to(repo).as_posix(): file_hash(p) for p in paths if p.is_file()})


def attack_hash(repo):
    root = repo / 'evals/golden'
    return digest({p.stem: dict(expected=load(p), input=load(root / 'inputs' / p.name))
                   for p in sorted((root / 'adversarial').glob('*.json'))})


def review_record(repo):
    root = repo / 'evals/golden'
    try:
        review = load(root / 'review.json')
        freeze = load(root / 'freeze.json')
        wanted = digest(load(root / 'expectations.json')['expectations'])
        require(review['approved'] is True and freeze['review_approved'] is True,
                'student expectation review pending')
        require(isinstance(review['reviewer'], str) and review['reviewer'].strip(), 'reviewer required')
        timestamp(review['reviewed_at'])
        require(review['expectations_hash'] == wanted == freeze['expectations_hash'],
                'review expectation hash mismatch')
        require(review['configuration_hash'] == configuration_hash(repo), 'review configuration changed')
        if list((root / 'adversarial').glob('*.json')):
            require(review['adversarial_hash'] == attack_hash(repo), 'review adversarial hash mismatch')
        return review
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ValueError('Invalid or missing student review: ' + str(error)) from error


def trace_evidence(path, skill, require_skill=True):
    """Check actual command-result events, not an agent's assertion of loading."""
    try:
        events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    except ValueError:
        if require_skill:
            raise
        return dict(session_id=None, skill_reads=[], usage=None)
    if not events and not require_skill:
        return dict(session_id=None, skill_reads=[], usage=None)
    require(events and all(isinstance(e, dict) for e in events), 'invalid trace events')
    sessions = {e['thread_id'] for e in events if e.get('type') == 'thread.started' and e.get('thread_id')}
    require(len(sessions) <= 1 and (not require_skill or len(sessions) == 1),
            'trace must identify exactly one fresh session for a completed run')
    reads = []
    for event in events:
        item = event.get('item', {})
        require(isinstance(item, dict), 'invalid trace item')
        if event.get('type') != 'item.completed' or item.get('type') != 'command_execution':
            continue
        command = item.get('command', '').replace('\\', '/')
        output = item.get('aggregated_output', '').replace('\r\n', '\n')
        if ('.github/skills/bug-report-clarification/SKILL.md' in command
                and item.get('exit_code') == 0 and skill.replace('\r\n', '\n') in output):
            reads.append(command)
    if require_skill:
        require(reads, 'trace lacks a successful skill read with matching content')
    return dict(session_id=next(iter(sessions), None), skill_reads=reads,
                usage=[e.get('usage') for e in events if e.get('type') == 'turn.completed'] or None)


def inspect_attempt(repo, case_id, mode):
    """Return evidence errors separately from recommendation validation errors."""
    root = repo / 'evals/golden'
    errors = []
    validation = 'not run'
    session = None
    skill_read = False
    try:
        record = load(root / f'transcripts/{case_id}.json')
        case = load(root / f'inputs/{case_id}.json')
        review = review_record(repo)
        require(record['case_id'] == case_id and record['mode'] == mode, 'case/mode mismatch')
        require(record['status'] in {'completed', 'failed', 'interrupted'}, 'invalid attempt status')
        require(record['fresh_session'] is True, 'fresh session required')
        require(record['input_hash'] == digest(case), 'input hash mismatch')
        require(record['configuration_hash'] == configuration_hash(repo), 'configuration hash mismatch')
        skill_path = repo / '.claude/skills/bug-report-clarification/SKILL.md'
        require(record['skill_sha256'] == file_hash(skill_path), 'skill hash mismatch')
        if mode == 'dry-run':
            preparation_path = root / f'preparations/{case_id}.json'
            require(record['preparation_sha256'] == file_hash(preparation_path), 'preparation hash mismatch')
            preparation = load(preparation_path)
            require(preparation['input_hash'] == record['input_hash'] and
                    preparation['configuration_hash'] == record['configuration_hash'], 'preparation context mismatch')
            require(timestamp(preparation['prepared_at']) <= timestamp(record['started_at']), 'run predates preparation')
        require(timestamp(review['reviewed_at']) <= timestamp(record['started_at']) <=
                timestamp(record['finished_at']), 'review/run timestamps out of order')
        require(isinstance(record['model_requested'], str) and record['model_requested'].strip(),
                'requested model required')
        require(record['model_reported'] is None or isinstance(record['model_reported'], str),
                'invalid reported model')
        require('usage' in record, 'usage must be recorded or explicitly null')
        raw = root / f'transcripts/raw/{case_id}.jsonl'
        require(record['trace_sha256'] == file_hash(raw), 'trace hash mismatch')
        traced = trace_evidence(raw, skill_path.read_text(encoding='utf-8'),
                                require_skill=record['status'] == 'completed')
        require(record['session_id'] == traced['session_id'], 'trace session mismatch')
        session = record['session_id']
        skill_read = bool(traced['skill_reads'])
        actual = root / f'actual/{case_id}.json'
        if actual.exists():
            require(record['output_sha256'] == file_hash(actual), 'raw output hash mismatch')
            try:
                validate(case, load(actual))
                validation = 'valid'
            except (ValueError, TypeError, KeyError) as error:
                validation = str(error)
        else:
            require(record['status'] != 'completed' and record['output_sha256'] is None,
                    'completed attempt missing output')
            validation = record['status'] + ': no output'
    except (OSError, ValueError, TypeError, KeyError) as error:
        errors.append('Attempt evidence: ' + str(error))
    try:
        assessment = load(root / f'assessments/{case_id}.json')
        require(assessment['case_id'] == case_id, 'assessment case mismatch')
        for key in ['reviewer', 'relevance', 'redundancy', 'procedure', 'explanation', 'safety']:
            require(isinstance(assessment[key], str) and assessment[key].strip(), 'assessment missing ' + key)
        reviewed = timestamp(assessment['reviewed_at'])
        record = load(root / f'transcripts/{case_id}.json')
        require(reviewed >= timestamp(record['finished_at']), 'assessment predates execution')
    except (OSError, ValueError, TypeError, KeyError) as error:
        errors.append('Human assessment: ' + str(error))
    return dict(errors=errors, validation=validation, session_id=session, skill_read=skill_read)


def submission_evidence(repo, mode):
    root = repo / 'evals/golden'
    errors = []
    try:
        review_record(repo)
    except ValueError as error:
        errors.append(str(error))
    items = load(root / 'expectations.json')['expectations']
    ids = [x['case_id'] for x in items] + [p.stem for p in sorted((root / 'adversarial').glob('*.json'))]
    sessions = set()
    skill_reads = 0
    for case_id in ids:
        result = inspect_attempt(repo, case_id, mode)
        skill_reads += result['skill_read']
        errors.extend(case_id + ': ' + error for error in result['errors'])
        session = result['session_id']
        if session is not None:
            if session in sessions:
                errors.append(case_id + ': session reused across cases')
            sessions.add(session)
    if not skill_reads:
        errors.append('No actual skill-loading evidence in any attempt')
    if mode == 'dry-run':
        try:
            execution = load(repo / 'evals/evidence/execution.json')
            require(execution['mode'] == mode and execution['end_to_end_status'] == 'blocked',
                    'document an actual end-to-end blocker; preference is insufficient')
            require(bool(execution['reason'].strip()) and bool(execution['untested_controls']),
                    'blocker reason and untested controls required')
            require(bool(execution['blocking_evidence']), 'blocker evidence required')
            for item in execution['blocking_evidence']:
                path = (repo / item['path']).resolve()
                require(path.is_relative_to((repo / 'evals/evidence').resolve()), 'unsafe blocker evidence path')
                require(file_hash(path) == item['sha256'], 'blocker evidence hash mismatch')
            policy = load(repo / 'config/policy.json')
            require(policy['enabled'] is False and policy['budget_verified'] is False,
                    'dry-run submission must leave live operation disabled')
        except (OSError, KeyError, TypeError, ValueError) as error:
            errors.append('Dry-run basis: ' + str(error))
    else:
        for name in ['remote-smoke.json', 'skill-loading.json', 'publication.json', 'phone-stop.json']:
            try:
                item = load(repo / 'evals/evidence' / name)
                require(item['tested'] is True and item['configuration_hash'] == configuration_hash(repo)
                        and bool(item['run_url']) and bool(item['observations']), 'incomplete remote evidence')
            except (OSError, KeyError, TypeError, ValueError) as error:
                errors.append(name + ': ' + str(error))
    return errors
