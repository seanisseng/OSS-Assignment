"""Fail-closed verification of declared hosted and recovery evidence."""
import json
import subprocess
import hashlib
import ast
import re
from collections import Counter
from pathlib import Path

from scripts.contract import require, digest
from scripts.evidence import configuration_hash, file_hash, load, timestamp, review_record
from scripts.hosted_evidence import inspect_attempt, controls
from scripts.single_response import CASE_ORDER, frozen_case, build_packet, encoded, validate_response, closed_json
from scripts.scoring import decision_match

MANIFEST = 'evals/evidence/v3-evidence-manifest.json'
RECOVERY_CASES = {'pytest-14533', 'pytest-14456', 'fake-approval', 'impersonation',
                  'malicious-tool', 'secret-exfiltration'}
HASH = '27a34c7f05d374bac7752be9c774c77886f4432aa466db7c1c22b07e97634ece'
CURRENT_DOCS = (
    'README.md',
    'DESIGN.md',
    'docs/EXPERIMENT-REVIEW.md',
    'docs/DRY-RUN.md',
    'docs/OPERATIONS.md',
    'docs/FUTURE-STUDY.md',
    'docs/REVIEW-GUIDE.md',
    'docs/V3-PHASE1-RESULT.md',
    'docs/reviews/FINAL-22-CASE-REVIEW.md',
)
MARKDOWN_LINK = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
ENTRY_POINT = 'docs/EXPERIMENT-REVIEW.md'


def safe_path(root, relative):
    root = Path(root).resolve()
    value = Path(relative)
    require(not value.is_absolute() and '..' not in value.parts, 'unsafe relative evidence path')
    target = root / value
    require(target.resolve().is_relative_to(root) and target.exists(), 'missing/escaped evidence path: ' + str(relative))
    require(not any(p.is_symlink() for p in [target, *target.parents] if p != root.parent),
            'symlink evidence refused')
    return target


def read_manifest(root):
    manifest = closed_json(safe_path(root, MANIFEST).read_text(encoding='utf-8'))
    require(isinstance(manifest, dict) and set(manifest) == {
        'version', 'study_id', 'configuration_hash', 'inference_commit', 'skill_sha256',
        'recovery_study', 'recovery_model', 'recovery_plan_sha256', 'approval_hash_kind',
        'approvals', 'cases', 'startup_failures'}, 'unknown/missing manifest fields')
    require(manifest['approval_hash_kind'] == 'canonical-json-sha256', 'unknown approval digest format')
    for entry in manifest['cases']:
        require(isinstance(entry, dict) and set(entry) == {'case_id', 'expected_decision', 'input',
            'assessment', 'review_receipt', 'hosted', 'approval_id', 'transcript', 'recovery'},
            'unknown/missing case manifest fields')
    for event in manifest['approvals']:
        require(isinstance(event, dict) and set(event) == {'id', 'source', 'source_json_sha256',
            'selector', 'normalization'}, 'unknown/missing approval manifest fields')
    return manifest


def check_approval(event, dispatch, assigned_count):
    require(dispatch['case_id'] in event['cases'], 'approval does not cover case')
    require(timestamp(event['approved_at']) <= timestamp(dispatch['recorded_at']), 'dispatch predates scoped approval')
    require(event['configuration_hash'] == dispatch['configuration_hash'], 'approval configuration differs')
    require(event['commit'] == dispatch['commit'], 'approval commit differs')
    require(type(assigned_count) is int and 0 < assigned_count <= event['maximum_requests'], 'approval scope exceeded')


def select_approval(events, selected, dispatch, assigned_count):
    event = events[selected]
    check_approval(event, dispatch, assigned_count)
    applicable = [e for e in events.values() if dispatch['case_id'] in e['cases']
                  and e['configuration_hash'] == dispatch['configuration_hash']
                  and e['commit'] == dispatch['commit']
                  and timestamp(e['approved_at']) <= timestamp(dispatch['recorded_at'])]
    require(timestamp(event['approved_at']) == max(timestamp(e['approved_at']) for e in applicable),
            'later scoped approval supersedes selected event')
    return event


def approval_event(root, item, manifest):
    path = safe_path(root, item['source'])
    require(digest(load(path)) == item['source_json_sha256'], 'approval source hash differs')
    source = load(path)
    for key in item.get('selector', []):
        source = source[key] if isinstance(source, dict) else source[int(key)]
    require(source['approved'] is True and source['configuration_hash'] == HASH, 'approval source is not approved')
    require(source.get('reviewer') == 'seanisseng', 'approval reviewer differs')
    kind = item['normalization']
    if kind == 'initial_one':
        require(source['status'] == 'User approved version 3 configuration and exactly one hosted pytest-15052 request',
                'initial approval scope differs')
        cases, maximum = [CASE_ORDER[0]], 1
    elif kind == 'remaining_twenty_one':
        require(source['scope'] == '21 remaining case requests; total study 22; no publication', 'batch approval scope differs')
        cases, maximum = list(CASE_ORDER[1:]), 21
    elif kind == 'scoped_resume':
        cases = source.get('cases', [source.get('case_id')])
        maximum = source['maximum_new_dispatches']
        require(source['commit'] == manifest['inference_commit'] and source['redispatch_authorized'] is False,
                'resume approval policy differs')
    else:
        raise ValueError('unknown approval normalization')
    require(cases and set(cases) <= set(CASE_ORDER) and len(cases) == len(set(cases)), 'invalid approval cases')
    require(type(maximum) is int and maximum == len(cases), 'approval ceiling differs')
    return dict(cases=cases, maximum_requests=maximum, approved_at=source.get('reviewed_at', source.get('recorded_at')),
                configuration_hash=source['configuration_hash'], commit=manifest['inference_commit'], kind=kind)


def trace_summary(events, final):
    require(events and all(isinstance(e, dict) for e in events), 'invalid native trace')
    threads = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
    require(len(threads) == 1 and threads[0], 'exactly one fresh thread required')
    turns = [e for e in events if e.get('type') == 'turn.completed']
    require(len(turns) == 1 and not any(e.get('type') == 'turn.failed' for e in events), 'native turn incomplete/repeated')
    items = [e['item'] for e in events if isinstance(e.get('item'), dict)]
    actions = [i for i in items if i.get('type') not in {'agent_message', 'reasoning', 'plan', 'error'}]
    require(not actions, 'unexpected native tool action')
    messages = [i.get('text', '').strip() for i in items if i.get('type') == 'agent_message']
    require(final.strip() and final.strip() in messages, 'final message differs from native trace')
    return dict(session_id=threads[0], usage=turns[0].get('usage'),
                warning_count=sum(i.get('type') == 'error' for i in items))


def check_review(root, entry, expected, config_hash, transcript):
    path = safe_path(root, entry['assessment'])
    assessment = load(path)
    require(assessment['case_id'] == entry['case_id'], 'assessment case differs')
    require(assessment.get('expected_decision', expected) == expected, 'assessment describes wrong frozen expectation')
    require(assessment['status'] == 'reviewed' and assessment['reviewer'], 'current assessment approval pending')
    for key in ['relevance', 'redundancy', 'procedure', 'safety', 'blocker_reasonableness', 'explanation']:
        require(isinstance(assessment.get(key), str) and assessment[key].strip(), 'review analysis missing: ' + key)
    receipt = load(safe_path(root, entry['review_receipt']))
    require(receipt['case_id'] == entry['case_id'] and receipt['reviewer'] == assessment['reviewer'], 'review identity differs')
    require(receipt['reviewed_at'] == assessment['reviewed_at'] and receipt.get('source'), 'review approval source/time differs')
    timestamp(receipt['reviewed_at'])
    require(receipt['configuration_hash'] == config_hash, 'review configuration differs')
    require(receipt.get('revision', 1) == assessment.get('revision', 1), 'review revision differs')
    require(receipt['assessment_after_sha256'] == file_hash(path), 'review receipt is stale/superseded')
    if assessment.get('supersedes'):
        previous = assessment['supersedes']
        old_path = safe_path(root, previous['assessment'])
        old_receipt = load(safe_path(root, previous['receipt']))
        require(old_receipt['case_id'] == entry['case_id'] and receipt.get('supersedes') == previous['receipt'],
                'review revision history differs')
        require(previous['assessment_sha256'] == file_hash(old_path) == old_receipt['assessment_after_sha256'],
                'superseded signed assessment changed')
        require(timestamp(receipt['reviewed_at']) >= timestamp(old_receipt['reviewed_at']), 'revision approval was backdated')
    input_path = safe_path(root, entry['input'])
    if receipt['input_sha256'] != file_hash(input_path):
        # Older receipts hashed Windows JSON-file whitespace. Preserve the
        # receipt and original Git input, allowing only LF/CRLF serialization.
        # Field values remain bound by frozen_case's independent object digest.
        load(input_path)
        normalized = input_path.read_bytes().replace(b'\r\n', b'\n')
        require(receipt['input_sha256'] in {hashlib.sha256(normalized).hexdigest(),
                hashlib.sha256(normalized.replace(b'\n', b'\r\n')).hexdigest()}, 'review input differs')
    if transcript:
        require(receipt['transcript_sha256'] == file_hash(transcript), 'review transcript differs')
        require(timestamp(receipt['reviewed_at']) >= timestamp(load(transcript)['imported_at']), 'review predates hosted import')
    else:
        require(receipt.get('transcript_sha256') is None, 'missing hosted transcript given a review hash')
    if entry['recovery']:
        result = safe_path(root, entry['recovery'] + '/result.json')
        require(receipt.get('recovery_result_sha256') == file_hash(result), 'review recovery differs')
        require(timestamp(receipt['reviewed_at']) >= timestamp(load(result)['finished_at']), 'review predates recovery')
    return assessment


def check_billing(record, config_hash):
    require(record['paid_overages_disabled'] is True and record['configuration_hash'] == config_hash,
            'zero-overage declaration/configuration absent')
    require(record.get('confirmed_by') and record.get('verification_method', '').startswith('user attestation'),
            'billing attestation must not claim independent enforcement test')
    timestamp(record['recorded_at'])
    return dict(verification='user_attestation', historical_deductions_verified=False,
                rate_limit_reset_verified=False)


def check_docs(root):
    """Check the current entry point and every relative link in current Markdown."""
    root = Path(root).resolve()
    readme = safe_path(root, 'README.md').read_text(encoding='utf-8')
    require(f']({ENTRY_POINT})' in readme, 'README lacks the current submission entry point')
    checked = 0
    for relative in CURRENT_DOCS:
        path = safe_path(root, relative)
        for target in MARKDOWN_LINK.findall(path.read_text(encoding='utf-8')):
            target = target.split('#', 1)[0]
            if not target or re.match(r'^[a-z][a-z0-9+.-]*:', target, re.I) or target.startswith('/'):
                continue
            resolved = (path.parent / target).resolve()
            require(resolved.is_relative_to(root), 'doc link escapes repository: ' + relative + ' -> ' + target)
            require(resolved.exists(), 'broken doc link: ' + relative + ' -> ' + target)
            checked += 1
    return dict(entry_point=ENTRY_POINT, documents=len(CURRENT_DOCS), relative_links=checked)


def check_recovery(root, entry, manifest, hosted_validation):
    require(configuration_hash(Path(root)) == manifest['configuration_hash'] == HASH,
            'changed runtime cannot reconstruct recovery request')
    require(entry['case_id'] in RECOVERY_CASES and entry['recovery'], 'recovery not allowlisted')
    require(hosted_validation in {'no assistant response', 'not run'}, 'recovery cannot replace completed hosted answer')
    folder = safe_path(root, entry['recovery'])
    require(folder.is_relative_to(Path(root).resolve() / manifest['recovery_study']), 'foreign recovery study')
    result = load(folder / 'result.json')
    require(result['case_id'] == entry['case_id'] and result['configuration_hash'] == HASH, 'recovery binding differs')
    for name, wanted in result['files'].items():
        require(file_hash(safe_path(folder, name)) == wanted, 'recovery file hash differs: ' + name)
    require(result['status'] == 'completed' and result['exit_code'] == 0 and result['fresh_session'] is True
            and result['process_attempts'] == 1, 'recovery execution incomplete/repeated')
    require(result['model_requested'] == manifest['recovery_model'] and result['model_reported'] is None,
            'recovery model claim differs')
    require(result['hosted_controls_tested'] is False and result['native_system_prompt_equivalence'] is False,
            'recovery overclaims hosted controls')
    packet = load(folder / 'packet.json')
    case = frozen_case(root, entry['case_id'])
    skill = (Path(root) / '.claude/skills/bug-report-clarification/SKILL.md').read_text(encoding='utf-8')
    require((folder / 'packet.json').read_bytes() == encoded(build_packet(case, skill)), 'recovery packet differs')
    require(result['packet_sha256'] == file_hash(folder / 'packet.json')
            and result['skill_sha256'] == manifest['skill_sha256']
            and result['input_hash'] == packet['input_hash'], 'recovery packet/skill identity differs')
    request = load(folder / 'hosted-request-template.json')
    proc = subprocess.run(['node', '-e',
        'const h=require(process.argv[1]);let s="";process.stdin.on("data",x=>s+=x);'
        'process.stdin.on("end",()=>process.stdout.write(JSON.stringify(h.makeRequest(JSON.parse(s)))));',
        str(Path(root) / 'scripts/single_response_harness.cjs')], input=json.dumps(packet),
        text=True, encoding='utf-8', capture_output=True, check=True, timeout=30)
    require(request == json.loads(proc.stdout), 'canonical recovery messages differ')
    prompt = (folder / 'prompt.txt').read_text(encoding='utf-8')
    require(result['prompt_sha256'] == file_hash(folder / 'prompt.txt')
            and all(m['content'] in prompt for m in request['messages']), 'canonical messages not delivered')
    raw = (folder / 'assistant-response.txt').read_text(encoding='utf-8')
    events = [json.loads(line) for line in (folder / 'stdout.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    native = trace_summary(events, raw)
    require(native['session_id'] == result['session_id'] and native['usage'] == result['usage'], 'native recovery trace differs')
    envelope = validate_response(case, packet, raw)
    require(envelope == load(folder / 'validated-envelope.json'), 'recovery derived envelope differs')
    original = result.get('original_hosted_attempt')
    if hosted_validation == 'not run':
        require(original is None, 'unrun hosted case has prior attempt')
    else:
        transcript = safe_path(root, entry['transcript'])
        require(original and original['transcript_sha256'] == file_hash(transcript)
                and original['run_id'] == load(transcript)['run_id'], 'recovery lost original hosted attempt')
    return dict(validation='valid', decision=envelope['recommendation']['decision'], session_id=native['session_id'],
                model_requested=result['model_requested'], model_reported=None,
                observed_tool_actions=0, result_sha256=file_hash(folder / 'result.json'))


def verify(root):
    root = Path(root).resolve()
    errors, rows, sessions, runs = [], [], set(), set()
    output = dict(errors=errors, rows=rows, reviews_complete=0, hosted_controls_verified_by_recovery=False)
    try:
        manifest = read_manifest(root)
        require(type(manifest['version']) is int and manifest['version'] == 1 and manifest['study_id'] == 'v3',
                'unknown evidence manifest')
        require(configuration_hash(root) == manifest['configuration_hash'] == HASH, 'frozen runtime changed')
        require([e['case_id'] for e in manifest['cases']] == list(CASE_ORDER), '22-case manifest scope/order differs')
        require({e['case_id'] for e in manifest['cases'] if e['recovery']} == RECOVERY_CASES, 'recovery scope differs')
        review_record(root)
        frozen = load(root / 'evals/golden/final-configuration.json')
        require(manifest['inference_commit'] == frozen['inference_commit'] and frozen['approved'] is True, 'inference commit/approval differs')
        approvals = {e['id']: approval_event(root, e, manifest) for e in manifest['approvals']}
        require(len(approvals) == len(manifest['approvals']), 'duplicate approval ID')
        require(manifest['skill_sha256'] == file_hash(root / '.claude/skills/bug-report-clarification/SKILL.md'),
                'manifest skill hash differs')
        require(len(manifest['startup_failures']) == 2, 'startup failure scope differs')
        for startup in manifest['startup_failures']:
            path = safe_path(root, startup['result'])
            require(file_hash(path) == startup['sha256'], 'startup failure record differs')
            failed = load(path)
            require(failed['status'] == 'failed' and not (path.parent / 'assistant-response.txt').exists(),
                    'startup refusal incorrectly treated as assessment')
            for name, wanted in failed['files'].items():
                require(file_hash(safe_path(path.parent, name)) == wanted, 'startup evidence hash differs')
        assignments = Counter(e['approval_id'] for e in manifest['cases'] if e['hosted'] == 'attempted')
        recovery_plan_path = safe_path(root, manifest['recovery_study'] + '/plan.json')
        require(file_hash(recovery_plan_path) == manifest['recovery_plan_sha256'], 'recovery authorization changed')
        recovery_plan = load(recovery_plan_path)
        require(recovery_plan['approved'] is True and set(recovery_plan['cases']) == RECOVERY_CASES
                and recovery_plan['configuration_hash'] == HASH, 'recovery authorization/scope differs')
        key = {x['case_id']: x for x in load(root / 'evals/golden/expectations.json')['expectations']}
        previous = None
        total = 0
        for entry in manifest['cases']:
            case_id = entry['case_id']
            require(entry['input'] == f'evals/golden/inputs/{case_id}.json'
                    and entry['assessment'] == f'evals/golden/assessments/{case_id}.json', 'case paths differ')
            if entry['hosted'] == 'attempted':
                require(entry['transcript'] == f'evals/golden/transcripts/{case_id}.json', 'transcript path differs')
            if entry['recovery']:
                require(entry['recovery'] == manifest['recovery_study'] + '/' + case_id, 'recovery path differs')
            expected = key[case_id]['decision'] if case_id in key else load(root / f'evals/golden/adversarial/{case_id}.json')['expected_decision']
            require(entry['expected_decision'] == expected, 'manifest describes wrong expectation: ' + case_id)
            group = ('diagnostic' if case_id.startswith('diagnostic-') else 'adversarial' if case_id not in key
                     else 'real held-out' if key[case_id]['split'] == 'held-out' else 'real development')
            row = dict(case_id=case_id, group=group, expected=expected, hosted=entry['hosted'], validation='not run',
                       hosted_decision=None, decision_match=False, raw_questions=[], recovery=None, reviewed=False,
                       assessment=entry['assessment'], transcript=entry['transcript'])
            row['review_receipt'] = entry['review_receipt']
            rows.append(row)
            transcript = None
            try:
                if entry['hosted'] == 'attempted':
                    transcript = safe_path(root, entry['transcript'])
                    record = load(transcript)
                    require(record['run_id'] not in runs, 'hosted run reused')
                    runs.add(record['run_id'])
                    checked = inspect_attempt(root, case_id)
                    require(checked['evidence_complete'], '; '.join(checked['errors']))
                    require(record['validation'] == checked['validation'], 'recorded validation differs')
                    dispatch = record['dispatch']
                    require(dispatch['case_id'] == case_id and dispatch['commit'] == manifest['inference_commit'],
                            'foreign inference case/commit')
                    event = select_approval(approvals, entry['approval_id'], dispatch, assignments[entry['approval_id']])
                    if previous:
                        require(timestamp(previous['imported_at']) <= timestamp(dispatch['recorded_at']), 'hosted sequence overlaps')
                        if previous['continue_allowed'] is False:
                            require(event['kind'] == 'scoped_resume' and timestamp(previous['imported_at']) <= timestamp(event['approved_at']),
                                    'infrastructure stop lacks fresh scoped resume')
                    previous = record
                    total += record['requests_sent']
                    row.update(validation=checked['validation'], run_id=record['run_id'])
                    bundle = safe_path(root, record['bundle'])
                    trace = load(bundle / 'single-response-raw/execution.json')
                    require(record['requests_sent'] == trace['requests_sent'], 'hosted request count differs from native trace')
                    require(record['workflow_status'] == load(bundle / 'run.json')['conclusion'], 'workflow status differs')
                    raw = bundle / 'single-response-raw/assistant-response.txt'
                    if trace['status'] == 'response_received':
                        provider = load(bundle / 'single-response-raw/provider-response.json')
                        require(trace['model_reported'] == provider['model'] and trace['usage'] == provider['usage'],
                                'native model/usage metadata differs')
                    if raw.exists():
                        try:
                            row['raw_questions'] = load(raw)['recommendation']['questions']
                        except (ValueError, KeyError, TypeError):
                            pass
                    if checked['validation'] == 'valid':
                        actual = load(root / f'evals/golden/actual/{case_id}.json')
                        row['hosted_decision'] = actual['decision']
                        row['decision_match'] = decision_match(key[case_id], actual) if case_id in key else actual['decision'] == expected
                else:
                    require(entry['hosted'] == 'not_dispatched' and entry['transcript'] is None and entry['approval_id'] is None,
                            'invalid hosted disposition')
                    require(not (root / f'evals/golden/hosted/v3/{case_id}/dispatch.json').exists()
                            and not (root / f'evals/golden/transcripts/{case_id}.json').exists()
                            and not (root / f'evals/golden/actual/{case_id}.json').exists(), 'unrun case has hidden hosted evidence')
                if entry['recovery']:
                    recovery = check_recovery(root, entry, manifest, row['validation'])
                    require(recovery['session_id'] not in sessions, 'recovery session reused')
                    sessions.add(recovery['session_id'])
                    actual = load(root / entry['recovery'] / 'validated-envelope.json')['recommendation']
                    recovery['decision_match'] = decision_match(key[case_id], actual) if case_id in key else recovery['decision'] == expected
                    row['recovery'] = recovery
                    require(timestamp(recovery_plan['recorded_at']) <= timestamp(load(root / entry['recovery'] / 'result.json')['started_at']),
                            'recovery predates authorization')
                check_review(root, entry, expected, HASH, transcript)
                row['reviewed'] = True
                output['reviews_complete'] += 1
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                errors.append(case_id + ': ' + str(error))
        require(total <= 22, 'hosted request ceiling exceeded')
        require(len(sessions) == 6, 'six recovery sessions not verified')
        controls(root)
        billing_item = load(root / 'evals/evidence/single-response-controls.json')['paid_overages_confirmation']
        billing_path = safe_path(root, billing_item['path'])
        require(file_hash(billing_path) == billing_item['sha256'], 'billing declaration hash differs')
        output['billing'] = check_billing(load(billing_path), HASH)
        output['docs'] = check_docs(root)
        for path in (root / 'review_tools').glob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        output['review_tool_files'] = {p.name: file_hash(p) for p in sorted((root / 'review_tools').glob('*.py'))}
        output.update(configuration_hash=HASH, inference_commit=manifest['inference_commit'], hosted_requests=total)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        errors.append('Package: ' + str(error))
    from review_tools.reporting import measurements
    output['measurements'] = measurements(rows)
    return output
