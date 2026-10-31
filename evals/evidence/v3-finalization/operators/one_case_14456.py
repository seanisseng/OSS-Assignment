"""User-authorized single new case after infrastructure review; never redispatch."""
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
CASE = 'pytest-14456'
VARIABLE = 'CLARIFICATION_SINGLE_RESPONSE_ENABLED'
AUTH = STUDY / 'resume-one-case-14456.json'


def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True,
                          text=True, encoding='utf-8', timeout=120).stdout


def switch(value):
    gh('variable', 'set', VARIABLE, '--repo', REPOSITORY, '--body', value)
    print('SWITCH', value, flush=True)


def recent():
    return json.loads(gh('api', f'repos/{REPOSITORY}/actions/workflows/'
                        'single-response.lock.yml/runs?per_page=100'))['workflow_runs']


def main():
    plan = load(STUDY / 'plan.json')
    require(configuration_hash(ROOT) == plan['configuration_hash'], 'configuration changed')
    require(json.loads(gh('api', f'repos/{REPOSITORY}/commits/main'))['sha'] == plan['commit'],
            'remote main changed')
    require(plan['approved'] is True and plan['cases'] == list(CASE_ORDER), 'plan differs')
    rows = recent()
    require(all(r['status'] == 'completed' for r in rows), 'another run is active')
    require(not (STUDY / CASE / 'dispatch.json').exists(), 'already dispatched: recover only')
    for previous in CASE_ORDER[:CASE_ORDER.index(CASE)]:
        receipt = load(STUDY / previous / 'archive.json')
        require(receipt['archived'] is True, 'previous evidence missing')
        require(receipt['continue_allowed'] is True or previous == 'pytest-14533',
                'unreviewed infrastructure failure')
    trace = load(ROOT / load(ROOT / 'evals/golden/transcripts/pytest-14533.json')['bundle']
                 / 'single-response-raw/execution.json')
    require(trace.get('error') == 'gateway HTTP 429', 'reviewed failure differs')
    save_new(AUTH, dict(recorded_at=now(), reviewer='seanisseng', approved=True,
        source='User selected: Try only the next unrun case, pytest-14456, and stop afterward (recommended).',
        case_id=CASE, configuration_hash=plan['configuration_hash'], commit=plan['commit'],
        maximum_new_dispatches=1, resume_after='pytest-14533',
        infrastructure_review='Earlier HTTP 429 remains a failed result; this authorizes only the next new case.',
        automatic_batch_resume=False, redispatch_authorized=False))
    token = uuid.uuid4().hex
    try:
        switch('true')
        # Exclusive local ledger creation before the one external dispatch attempt.
        save_new(STUDY / CASE / 'dispatch.json', dict(case_id=CASE, commit=plan['commit'],
            configuration_hash=plan['configuration_hash'], token=token,
            recorded_at=now(), status='dispatch_recorded'))
        gh('workflow', 'run', 'single-response.lock.yml', '--repo', REPOSITORY,
           '--ref', 'main', '-f', 'case_id=' + CASE, '-f', 'dispatch_token=' + token)
        print('DISPATCHED_ONCE', CASE, token, flush=True)
        title = f'single-response {CASE} {token}'
        run = None
        for _ in range(20):
            matches = [r for r in recent() if r['display_title'] == title]
            require(len(matches) <= 1, 'ambiguous token')
            if matches:
                run = bind(STUDY, CASE, matches[0]['id'], gh)
                break
            time.sleep(10)
        require(run is not None, 'not found: recover by token only')
        print('BOUND', run['id'], run['html_url'], flush=True)
        last = None
        deadline = time.monotonic() + 1500
        while time.monotonic() < deadline:
            run = bind(STUDY, CASE, run['id'], gh)
            status = (run['status'], run['conclusion'])
            if status != last:
                print('RUN_STATUS', *status, flush=True)
                last = status
            if run['status'] == 'completed':
                break
            time.sleep(15)
        require(run['status'] == 'completed', 'poll timeout: recover by bound run ID only')
        bundle = download(STUDY, CASE, gh)
        print('DOWNLOADED', str(bundle), flush=True)
        import_bundle(ROOT, STUDY, CASE, bundle)
        transcript = load(ROOT / f'evals/golden/transcripts/{CASE}.json')
        print('IMPORTED', json.dumps({k: transcript[k] for k in
              ['case_id', 'run_id', 'status', 'validation', 'continue_allowed', 'requests_sent']}), flush=True)
    finally:
        switch('false')
        value = json.loads(gh('api', f'repos/{REPOSITORY}/actions/variables/{VARIABLE}'))['value']
        require(value == 'false', 'switch clearing not verified')
        print('SWITCH_VERIFIED_FALSE; STOPPED_AFTER_ONE_CASE', flush=True)


if __name__ == '__main__':
    main()
