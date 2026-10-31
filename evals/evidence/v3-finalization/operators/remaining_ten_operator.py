"""Scoped operator: ten new cases, one dispatch each, no inference retries."""
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.contract import REPOSITORY, require
from scripts.evidence import configuration_hash, load
from scripts.hosted_collect import bind, download, now, save_new
from scripts.hosted_evidence import import_bundle
from scripts.single_response import CASE_ORDER

STUDY = ROOT / 'evals/golden/hosted/v3'
CASES = ['pytest-14324', 'pytest-13849', 'pytest-13634', 'pytest-14389',
         'pytest-13902', 'diagnostic-expectation', 'fake-approval',
         'impersonation', 'malicious-tool', 'secret-exfiltration']
STATE = STUDY / 'remaining-ten-state.json'
STOP = STUDY / 'remaining-ten.stop'
VARIABLE = 'CLARIFICATION_SINGLE_RESPONSE_ENABLED'
state = dict(status='preflight', started_at=now(), cases=CASES, completed=[],
             current_case=None, current_run_id=None, automatic_restart_authorized=False)


def save():
    state['updated_at'] = now()
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    temporary.replace(STATE)


def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True,
                          text=True, encoding='utf-8', timeout=120).stdout


def read(*args):
    for attempt in range(3):
        try:
            return gh(*args)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if attempt == 2:
                raise
            time.sleep(10)


def switch(value):
    gh('variable', 'set', VARIABLE, '--repo', REPOSITORY, '--body', value)
    actual = json.loads(read('api', f'repos/{REPOSITORY}/actions/variables/{VARIABLE}'))['value']
    require(actual == value, 'launch switch value differs')
    state['switch_enabled'] = value == 'true'
    save()
    print('SWITCH_VERIFIED', value, flush=True)


def recent():
    return json.loads(read('api', f'repos/{REPOSITORY}/actions/workflows/'
                          'single-response.lock.yml/runs?per_page=100'))['workflow_runs']


def preflight(plan):
    require(not STOP.exists(), 'operator stop requested')
    require(configuration_hash(ROOT) == plan['configuration_hash'], 'configuration changed')
    require(json.loads(read('api', f'repos/{REPOSITORY}/commits/main'))['sha'] == plan['commit'],
            'remote main changed')
    require(all(r['status'] == 'completed' for r in recent()), 'another workflow is active')


def run_one(case, plan):
    preflight(plan)
    require(not (STUDY / case / 'dispatch.json').exists(), 'already dispatched: recover only')
    state.update(status='running', current_case=case, current_run_id=None)
    save()
    try:
        switch('true')
        token = uuid.uuid4().hex
        save_new(STUDY / case / 'dispatch.json', dict(case_id=case, commit=plan['commit'],
            configuration_hash=plan['configuration_hash'], token=token,
            recorded_at=now(), status='dispatch_recorded'))
        # Exactly one mutation attempt. Uncertain delivery stops this batch.
        gh('workflow', 'run', 'single-response.lock.yml', '--repo', REPOSITORY,
           '--ref', 'main', '-f', 'case_id=' + case, '-f', 'dispatch_token=' + token)
        print('DISPATCHED_ONCE', case, token, flush=True)
        title = f'single-response {case} {token}'
        run = None
        for _ in range(20):
            matches = [r for r in recent() if r['display_title'] == title]
            require(len(matches) <= 1, 'ambiguous token: recover only')
            if matches:
                run = bind(STUDY, case, matches[0]['id'], read)
                break
            time.sleep(10)
        require(run is not None, 'run not found: recover by token, never redispatch')
        state.update(current_run_id=run['id'], current_run_url=run['html_url'])
        save()
        print('BOUND', case, run['id'], run['html_url'], flush=True)
        # The first poll deadline switches to a second recovery window by run ID.
        for phase in ['poll', 'recover_by_run_id']:
            deadline = time.monotonic() + 1200
            while time.monotonic() < deadline:
                require(not STOP.exists(), 'operator stop requested; recover bound run separately')
                run = bind(STUDY, case, run['id'], read)
                if run['status'] == 'completed':
                    break
                time.sleep(15)
            if run['status'] == 'completed':
                break
            print('POLL_TIMEOUT_RECOVER_SAME_RUN', case, run['id'], flush=True)
        require(run['status'] == 'completed', 'unrecoverable timeout: no new dispatch')
        bundle = download(STUDY, case, read)
        import_bundle(ROOT, STUDY, case, bundle)
        transcript = load(ROOT / f'evals/golden/transcripts/{case}.json')
        result = {k: transcript[k] for k in
                  ['case_id', 'run_id', 'status', 'validation', 'continue_allowed', 'requests_sent']}
        state['completed'].append(result)
        save()
        print('ARCHIVED', json.dumps(result), flush=True)
        require(transcript['continue_allowed'] is True, 'infrastructure failure: batch stopped')
    finally:
        switch('false')


def main():
    require(not STATE.exists(), 'operator already recorded: do not restart')
    plan = load(STUDY / 'plan.json')
    require(plan['approved'] is True and plan['cases'] == list(CASE_ORDER), 'approved plan differs')
    require(list(CASE_ORDER[-10:]) == CASES, 'case order differs')
    require([c for c in CASE_ORDER if not (STUDY / c / 'dispatch.json').exists()] == CASES,
            'remaining dispatch scope differs')
    preflight(plan)
    for previous in CASE_ORDER[:-10]:
        receipt = load(STUDY / previous / 'archive.json')
        require(receipt['archived'] is True, 'previous evidence missing')
        require(receipt['continue_allowed'] is True or previous in {'pytest-14533', 'pytest-14456'},
                'unreviewed earlier infrastructure failure')
    latest = load(ROOT / 'evals/golden/transcripts/pytest-14329.json')
    require(latest['continue_allowed'] is True, 'latest attempt does not permit continuation')
    save_new(STUDY / 'resume-remaining-ten-authorization.json', dict(recorded_at=now(),
        approved=True, reviewer='seanisseng', source='User: can you continue with the 10 cases',
        cases=CASES, maximum_new_dispatches=10, proxy_ceiling_sum=50,
        configuration_hash=plan['configuration_hash'], commit=plan['commit'],
        redispatch_authorized=False, stop_on_infrastructure_failure=True,
        completed_response_validation_failures='archive and continue per frozen importer',
        earlier_failures='Preserved; no original receipts are changed.'))
    save()
    try:
        for case in CASES:
            run_one(case, plan)
        state.update(status='completed', current_case=None, current_run_id=None, finished_at=now())
    except BaseException as error:
        state.update(status='stopped', error=str(error)[:1000], stopped_at=now())
        print('BATCH_STOPPED', type(error).__name__, str(error), flush=True)
        raise
    finally:
        state['not_dispatched'] = [c for c in CASES if not (STUDY / c / 'dispatch.json').exists()]
        save()
        print('FINAL_STATE', state['status'], flush=True)


if __name__ == '__main__':
    main()
