"""Native hosted provenance, separate from recommendation correctness and review.

No synthetic Codex tool events are created. Original downloaded bundles are kept.
"""
import json
from pathlib import Path
import subprocess

from scripts.contract import REPOSITORY, digest, require
from scripts.evidence import configuration_hash, file_hash, load, timestamp
from scripts.single_response import build_packet, encoded, frozen_case, validate_response, CASE_ORDER
from scripts.hosted_collect import now, save_new


def inventory(bundle):
    require(not bundle.is_symlink(), 'symlink bundle refused')
    paths = sorted(bundle.rglob('*'))
    require(all(not p.is_symlink() for p in paths), 'symlink artifact refused')
    return {p.relative_to(bundle).as_posix(): file_hash(p) for p in paths if p.is_file()}


def inspect_bundle(repo, case_id, bundle, dispatch, binding):
    case = frozen_case(repo, case_id)
    run = load(bundle / 'run.json')
    require(run['id'] == binding['id'] and run['head_sha'] == dispatch['commit'], 'run provenance mismatch')
    require(run['event'] == 'workflow_dispatch' and run['run_attempt'] == 1, 'rerun or foreign event')
    require(run['path'] == '.github/workflows/single-response.lock.yml', 'wrong workflow')
    require(run['repository']['full_name'] == REPOSITORY, 'foreign run repository')
    require(run['display_title'] == f"single-response {case_id} {dispatch['token']}", 'wrong dispatch')
    require(run['status'] == 'completed' and run['conclusion'] in
            {'success', 'failure', 'cancelled', 'timed_out', 'startup_failure', 'action_required'},
            'run not terminal')
    require(timestamp(dispatch['recorded_at']) <= timestamp(run['created_at']) <=
            timestamp(run['updated_at']), 'dispatch/run time mismatch')
    require(dispatch['configuration_hash'] == configuration_hash(repo), 'configuration hash mismatch')
    raw = bundle / 'single-response-raw'
    preparation = load(raw / 'preparation.json')
    if preparation['status'] == 'refused':
        require(preparation['requests_sent'] == 0 and bool(preparation['reason']), 'invalid refusal')
        return dict(validation='preparation refused', result=None, skill_delivered=False,
                    workflow_status=run['conclusion'], continue_allowed=False, requests_sent=0)
    require(preparation['status'] == 'prepared' and preparation['requests_sent'] == 0, 'preparation incomplete')
    manifest = load(bundle / 'single-response-input/manifest.json')
    packet_path = bundle / 'single-response-input/packet.json'
    skill_path = repo / '.claude/skills/bug-report-clarification/SKILL.md'
    skill = skill_path.read_text(encoding='utf-8')
    packet = build_packet(case, skill)
    require(packet_path.read_bytes() == encoded(packet), 'delivered packet differs')
    require(manifest['case_id'] == case_id and manifest['input_hash'] == digest(case), 'input hash mismatch')
    require(manifest['packet_sha256'] == file_hash(packet_path) and
            manifest['skill_sha256'] == file_hash(skill_path), 'packet/skill hash mismatch')
    require(manifest['artifact_only'] is True and manifest['sandbox_issue'] is None, 'publication target present')
    for record in [manifest, load(raw / 'execution.json')]:
        require(record['commit'] == run['head_sha'] and str(record['run_id']) == str(run['id'])
                and str(record['run_attempt']) == '1', 'execution run binding differs')
        require(record['configuration_hash'] == dispatch['configuration_hash'], 'execution configuration differs')
    trace = load(raw / 'execution.json')
    require(trace['packet_sha256'] == manifest['packet_sha256'] and
            trace['skill_sha256'] == manifest['skill_sha256'], 'execution hashes differ')
    require(trace['status'] in {'failed', 'response_received'}, 'incomplete execution: terminal record absent')
    require(type(trace['requests_sent']) is int and trace['requests_sent'] in {0, 1}, 'request count differs')
    require(trace['model_requested'] == 'auto' and trace['tools'] == [], 'execution policy differs')
    if trace['requests_sent']:
        require(type(trace['timeout_ms']) is int and 0 < trace['timeout_ms'] <= 540000, 'runtime limit differs')
    request = load(raw / 'request.json')
    # Reconstruct the native request using the frozen harness, never a tool transcript.
    proc = subprocess.run(['node', '-e',
        'const h=require(process.argv[1]);let s="";process.stdin.on("data",x=>s+=x);'
        'process.stdin.on("end",()=>process.stdout.write(JSON.stringify(h.makeRequest(JSON.parse(s)))));',
        str((repo / 'scripts/single_response_harness.cjs').resolve())],
        input=json.dumps(packet), text=True, encoding='utf-8', capture_output=True, check=True)
    require(request == json.loads(proc.stdout), 'native request or skill delivery differs')
    result, validation = None, 'no assistant response'
    provider_path = raw / 'provider-response.json'
    assistant_path = raw / 'assistant-response.txt'
    if assistant_path.exists():
        require(provider_path.stat().st_size <= 65536 and assistant_path.stat().st_size <= 32768,
                'oversized captured response')
        provider = load(provider_path)
        require(provider['choices'][0]['message']['content'] == assistant_path.read_text(encoding='utf-8'),
                'assistant text differs from exact provider response')
        try:
            result = validate_response(case, packet, assistant_path.read_text(encoding='utf-8'))
            validation = 'valid'
        except (ValueError, KeyError, TypeError) as error:
            validation = str(error)
            result = None
        if result is not None:
            for name in ['recommendation', 'assessment']:
                require(load(raw / (name + '.json')) == result[name], 'derived output differs')
    if trace['status'] == 'response_received':
        require(assistant_path.is_file(), 'received response lacks assistant text')
        require(trace['requests_sent'] == 1 and trace.get('terminal_safe_output') == 'noop',
                'completion acknowledgement missing')
        provider = load(provider_path)
        require(len(provider['choices']) == 1 and provider['choices'][0]['finish_reason'] == 'stop',
                'incomplete provider response')
    else:
        require(bool(trace.get('error')), 'failure reason missing')
    # Semantic/schema failures with a completed inference can continue. Gateway,
    # startup, auth, timeout and framework failures pause the sequence.
    model_output_error = trace.get('error') in {
        'incomplete response or tool request', 'tool request rejected',
        'empty response', 'recommendation too large'}
    if model_output_error:
        validation, result = trace['error'], None
    can_continue = (trace['status'] == 'response_received' or model_output_error) and run['conclusion'] in {'success', 'failure'}
    return dict(validation=validation, result=result, skill_delivered=True,
                workflow_status=run['conclusion'], continue_allowed=can_continue,
                requests_sent=trace['requests_sent'])


def import_bundle(repo, study, case_id, bundle):
    root = repo / 'evals/golden'
    require(bundle.resolve().is_relative_to((root / 'hosted').resolve()), 'archive bundles under golden/hosted first')
    dispatch = load(study / case_id / 'dispatch.json')
    binding = load(study / case_id / 'binding.json')
    outcome = inspect_bundle(repo, case_id, bundle, dispatch, binding)
    for other in (root / 'transcripts').glob('*.json'):
        require(str(load(other).get('run_id')) != str(binding['id']) or other.stem == case_id, 'run ID reused')
    record = dict(mode='single-response', case_id=case_id, run_id=binding['id'],
                  status='completed' if outcome['result'] is not None else 'failed',
                  bundle=bundle.relative_to(repo).as_posix(), files=inventory(bundle),
                  dispatch=dispatch, binding=binding, imported_at=now(),
                  **{k:v for k,v in outcome.items() if k != 'result'})
    target = root / f'transcripts/{case_id}.json'
    if target.exists():
        existing = load(target)
        require({k:v for k,v in existing.items() if k != 'imported_at'} ==
                {k:v for k,v in record.items() if k != 'imported_at'}, 'existing import differs')
    else:
        save_new(target, record)
    if outcome['result'] is not None:
        target = root / f'actual/{case_id}.json'
        if target.exists():
            require(load(target) == outcome['result']['recommendation'], 'existing actual differs')
        else:
            save_new(target, outcome['result']['recommendation'])
    # Assessment is explicitly a draft. No human review or timestamp is fabricated.
    target = root / f'assessments/{case_id}.json'
    if not target.exists():
        save_new(target, dict(case_id=case_id, status='draft',
            model_assessment=outcome['result']['assessment'] if outcome['result'] else None,
            reviewer=None, reviewed_at=None, relevance=None, redundancy=None,
            procedure=None, safety=None, blocker_reasonableness=None,
            explanation='Pending case review.'))
    target = study / case_id / 'archive.json'
    if not target.exists():
        save_new(target, dict(archived=True, continue_allowed=outcome['continue_allowed'], imported_at=now()))


def inspect_attempt(repo, case_id):
    errors = []
    outcome = dict(validation='not run', session_id=None, skill_read=False, errors=errors,
                   evidence_complete=False, reviewed=False)
    try:
        root = repo / 'evals/golden'
        record = load(root / f'transcripts/{case_id}.json')
        require(record['case_id'] == case_id and record['mode'] == 'single-response', 'wrong evidence mode')
        bundle = (repo / record['bundle']).resolve()
        require(bundle.is_relative_to((root / 'hosted').resolve()), 'unsafe bundle location')
        require(inventory(bundle) == record['files'], 'archived evidence hash mismatch')
        result = inspect_bundle(repo, case_id, bundle, record['dispatch'], record['binding'])
        require(record['run_id'] == record['binding']['id'], 'run ID mismatch')
        outcome.update(validation=result['validation'], session_id=str(record['run_id']),
                       skill_read=result['skill_delivered'])
        actual = root / f'actual/{case_id}.json'
        if result['result']:
            require(load(actual) == result['result']['recommendation'], 'canonical actual differs')
        else:
            require(not actual.exists(), 'invalid response has canonical recommendation')
        outcome['evidence_complete'] = True
        assessment = load(root / f'assessments/{case_id}.json')
        require(assessment['case_id'] == case_id and assessment['status'] == 'reviewed', 'case review pending')
        require(bool(assessment['reviewer']) and bool(assessment['explanation']), 'review details absent')
        for name in ['relevance', 'redundancy', 'procedure', 'safety', 'blocker_reasonableness']:
            require(isinstance(assessment.get(name), str) and bool(assessment[name].strip()),
                    'review missing ' + name)
        require(timestamp(assessment['reviewed_at']) >= timestamp(load(bundle / 'run.json')['updated_at']),
                'review predates run completion')
        outcome['reviewed'] = True
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        errors.append(('Case review: ' if outcome['evidence_complete'] else 'Hosted evidence: ') + str(error))
    return outcome


def controls(repo):
    """Artifact-only submission requires accurate statuses, not live publication."""
    record = load(repo / 'evals/evidence/single-response-controls.json')
    require(record['configuration_hash'] == configuration_hash(repo), 'control configuration differs')
    for name in ['publication', 'phone_cancellation', 'malicious_tool', 'skill_procedure', 'billing', 'launch_switch']:
        item = record[name]
        require(item['status'] in {'tested', 'untested', 'unsupported', 'unnecessary'}, 'invalid control status')
        require(isinstance(item['explanation'], str) and bool(item['explanation'].strip()), 'control explanation absent')
        if item['status'] == 'tested':
            require(bool(item['evidence']), 'tested control needs evidence')
            for entry in item['evidence']:
                path = (repo / entry['path']).resolve()
                require(path.is_relative_to((repo / 'evals').resolve()), 'unsafe control evidence')
                require(file_hash(path) == entry['sha256'], 'control evidence hash differs')
    require(record['publication']['status'] == 'unnecessary', 'artifact-only publication status differs')
    require(record['launch_switch']['status'] == 'tested', 'launch switch off evidence required')
    require(record['paid_overages_disabled'] is True, 'paid overages must be disabled')
    for name in ['usage_before', 'usage_after']:
        require(record[name]['availability'] in {'available', 'unavailable'}, 'usage availability required')
        require(bool(record[name]['explanation']), 'usage explanation required')
    return record


def study_evidence(repo):
    root = repo / 'evals/golden'
    freeze = load(root / 'final-configuration.json')
    require(freeze['approved'] is True, 'final configuration approval pending')
    require(freeze['configuration_hash'] == configuration_hash(repo), 'frozen configuration differs')
    require(freeze['cases'] == list(CASE_ORDER) and freeze['planned_requests'] == 22,
            'final study scope differs')
    require(freeze['expectations_hash'] == digest(load(root / 'expectations.json')['expectations']),
            'final expectation hash differs')
    require(freeze['input_inventory'] == load(root / 'single-response-inputs.json'), 'final input inventory differs')
    commit = freeze['inference_commit']
    require(isinstance(commit, str) and len(commit) == 40, 'inference commit absent')
    total = 0
    previous_finished = None
    for case_id in CASE_ORDER:
        record = load(root / f'transcripts/{case_id}.json')
        dispatch, binding = record['dispatch'], record['binding']
        require(dispatch['commit'] == binding['head_sha'] == commit, 'inference commits differ')
        require(timestamp(freeze['approved_at']) <= timestamp(dispatch['recorded_at']), 'dispatch predates approval')
        if previous_finished is not None:
            require(previous_finished <= timestamp(dispatch['recorded_at']), 'cases not sequentially archived')
        previous_finished = timestamp(record['imported_at'])
        total += record['requests_sent']
    require(total <= 22, 'more than 22 requests recorded')
    return freeze
