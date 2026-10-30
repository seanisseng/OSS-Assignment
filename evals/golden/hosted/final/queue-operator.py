"""User-requested queue orchestration; frozen inference code is unchanged.

This operator was added after the first result at the user's explicit request.
It changes dispatch sequencing, so it is not the original sequential protocol.
"""
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path.cwd()))

from scripts.contract import REPOSITORY, require
from scripts.evidence import configuration_hash, load
from scripts.hosted_collect import bind, download, gh, save_new
from scripts.hosted_evidence import import_bundle
from scripts.single_response import CASE_ORDER

ROOT = Path.cwd()
STUDY = ROOT / 'evals/golden/hosted/final'
STATE = STUDY / 'queue-state.json'
STOP = STUDY / 'infrastructure-stop.json'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def update_state(**values):
    state = load(STATE)
    state.update(values, updated_at=now())
    temporary = STATE.with_suffix('.tmp')
    temporary.write_bytes((json.dumps(state, indent=2)+'\n').encode())
    temporary.replace(STATE)


def read_call(*args):
    for attempt in range(3):
        try:
            return gh(*args)
        except subprocess.CalledProcessError:
            if args[0] != 'api' or attempt == 2:
                raise
            time.sleep(5)  # Read-only recovery only; no dispatch retries.


def stop_queue(reason):
    if not STOP.exists():
        save_new(STOP, dict(recorded_at=now(), reason=reason,
                           note='Queued workflows may start before this best-effort monitor detects a failure.'))
    gh('variable', 'set', 'CLARIFICATION_SINGLE_RESPONSE_ENABLED', '--repo', REPOSITORY, '--body', 'false')
    for case_id in CASE_ORDER:
        path = STUDY / case_id / 'binding.json'
        if path.exists() and not (STUDY / case_id / 'archive.json').exists():
            run = json.loads(read_call('api', f'repos/{REPOSITORY}/actions/runs/{load(path)["id"]}'))
            if run['status'] != 'completed':
                try:
                    gh('run', 'cancel', str(run['id']), '--repo', REPOSITORY)
                except subprocess.CalledProcessError:
                    pass  # Preserve uncertainty; never dispatch a replacement.


def queue():
    plan = load(STUDY / 'plan.json')
    require(plan['approved'] is True, 'approval absent')
    require(configuration_hash(ROOT) == plan['configuration_hash'], 'configuration moved')
    head = json.loads(read_call('api', f'repos/{REPOSITORY}/commits/main'))
    require(head['sha'] == plan['commit'], 'main moved')
    require(not STOP.exists(), 'infrastructure stop recorded')
    try:
        for case_id in CASE_ORDER[2:]:
            require(not STOP.exists(), 'monitor stopped queue for infrastructure failure')
            token = uuid.uuid4().hex
            record = dict(case_id=case_id, commit=plan['commit'], configuration_hash=plan['configuration_hash'],
                          token=token, recorded_at=now(), status='dispatch_recorded',
                          sequencing='queued by explicit user instruction')
            save_new(STUDY / case_id / 'dispatch.json', record)
            # Exactly one dispatch attempt. Connection loss is not retried.
            gh('workflow', 'run', 'single-response.lock.yml', '--repo', REPOSITORY,
               '--ref', 'main', '-f', 'case_id='+case_id, '-f', 'dispatch_token='+token)
            print('DISPATCHED', case_id, flush=True)
        for attempt in range(20):
            require(not STOP.exists(), 'monitor stopped queue for infrastructure failure')
            rows = json.loads(read_call('api', f'repos/{REPOSITORY}/actions/workflows/single-response.lock.yml/runs?event=workflow_dispatch&per_page=100'))['workflow_runs']
            missing = []
            for case_id in CASE_ORDER[2:]:
                if (STUDY / case_id / 'binding.json').exists():
                    continue
                record = load(STUDY / case_id / 'dispatch.json')
                title = f'single-response {case_id} {record["token"]}'
                matches = [r for r in rows if r['display_title'] == title]
                require(len(matches) <= 1, 'ambiguous dispatch token')
                if matches:
                    run = bind(STUDY, case_id, matches[0]['id'], read_call)
                    print('BOUND', case_id, run['id'], run['html_url'], flush=True)
                else:
                    missing.append(case_id)
            if not missing:
                last = load(STUDY / CASE_ORDER[-1] / 'binding.json')
                update_state(status='queued', last_case=CASE_ORDER[-1], last_run_id=last['id'], last_run_url=last['html_url'])
                print('LAST_QUEUED', last['html_url'], flush=True)
                return
            time.sleep(10)
        raise ValueError('Some run IDs are not yet visible; recover existing dispatch tokens only')
    except BaseException as error:
        update_state(status='queue_interrupted', error=str(error))
        stop_queue(str(error))
        raise


def monitor():
    print('Background collector started', now(), flush=True)
    try:
        deadline = time.monotonic()+6*60*60
        while time.monotonic() < deadline:
            state = load(STATE)
            if state['status'] == 'queue_interrupted' or STOP.exists():
                return
            # Avoid a binding-write race with the queue process while it is binding.
            candidates = CASE_ORDER if state['status'] == 'queued' else CASE_ORDER[:2]
            for case_id in candidates:
                case_dir = STUDY / case_id
                if (case_dir / 'archive.json').exists() or not (case_dir / 'binding.json').exists():
                    continue
                binding = load(case_dir / 'binding.json')
                run = json.loads(read_call('api', f'repos/{REPOSITORY}/actions/runs/{binding["id"]}'))
                if run['status'] != 'completed':
                    continue
                bundle = download(STUDY, case_id, read_call)
                import_bundle(ROOT, STUDY, case_id, bundle)
                print('ARCHIVED', case_id, run['conclusion'], flush=True)
                if not load(case_dir / 'archive.json')['continue_allowed']:
                    raise ValueError(f'{case_id}: infrastructure failure; no replacement inference authorized')
            if all((STUDY / case_id / 'archive.json').exists() for case_id in CASE_ORDER):
                update_state(status='all_archived', archived=22, finished_at=now())
                print('All 22 cases archived; model failures are retained.', flush=True)
                return
            time.sleep(15)
        raise TimeoutError('Collector deadline; recover existing runs without redispatch')
    except BaseException as error:
        print('COLLECTION_STOP', type(error).__name__, str(error), flush=True)
        stop_queue(str(error))
        update_state(status='infrastructure_paused', error=str(error))
        raise
    finally:
        gh('variable', 'set', 'CLARIFICATION_SINGLE_RESPONSE_ENABLED', '--repo', REPOSITORY, '--body', 'false')
        print('Launch switch cleared', now(), flush=True)


if __name__ == '__main__':
    queue() if sys.argv[1] == 'queue' else monitor()
