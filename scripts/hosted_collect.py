"""One-shot dispatch ledger and independent, resumable artifact recovery.

Dispatch is an external mutation: use only after explicit approval of this plan.
A recorded dispatch is never sent again, even if gh loses its connection.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import time
import uuid

from scripts.contract import REPOSITORY, require
from scripts.evidence import configuration_hash, load
from scripts.single_response import CASE_ORDER


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True,
                          text=True, encoding='utf-8').stdout


def initialize(root, destination, commit):
    require(len(commit) == 40 and all(x in '0123456789abcdef' for x in commit), 'full commit required')
    save_new(destination / 'plan.json', dict(version=1, repository=REPOSITORY,
        commit=commit, configuration_hash=configuration_hash(root), cases=list(CASE_ORDER),
        approved=False, planned_requests=22, proxy_ceiling_sum=110, created_at=now()))


def dispatch(destination, case_id, call=gh):
    plan = load(destination / 'plan.json')
    require(plan['approved'] is True, 'explicit final plan approval required')
    require(plan['cases'] == list(CASE_ORDER) and plan['planned_requests'] == 22, 'scope differs')
    head = json.loads(call('api', f'repos/{REPOSITORY}/commits/main'))
    require(head['sha'] == plan['commit'], 'main moved from frozen inference commit')
    require(plan['configuration_hash'] == configuration_hash(Path.cwd()), 'local configuration moved')
    index = CASE_ORDER.index(case_id)
    for previous in CASE_ORDER[:index]:
        receipt = load(destination / previous / 'archive.json')
        require(receipt['archived'] is True and receipt['continue_allowed'] is True,
                'previous case requires recovery or infrastructure review')
    token = uuid.uuid4().hex
    record = dict(case_id=case_id, commit=plan['commit'], configuration_hash=plan['configuration_hash'],
                  token=token, recorded_at=now(), status='dispatch_recorded')
    # Exclusive creation precedes the network call. Never retry this operation.
    save_new(destination / case_id / 'dispatch.json', record)
    call('workflow', 'run', 'single-response.lock.yml', '--repo', REPOSITORY,
         '--ref', 'main', '-f', 'case_id=' + case_id, '-f', 'dispatch_token=' + token)


def bind(destination, case_id, run_id, call=gh):
    record = load(destination / case_id / 'dispatch.json')
    run = json.loads(call('api', f'repos/{REPOSITORY}/actions/runs/{int(run_id)}'))
    require(run['id'] == int(run_id) and run['head_sha'] == record['commit'], 'run/commit differs')
    require(run['event'] == 'workflow_dispatch' and run['run_attempt'] == 1, 'unexpected event or rerun')
    require(run['path'] == '.github/workflows/single-response.lock.yml', 'wrong workflow')
    require(run['display_title'] == f"single-response {case_id} {record['token']}", 'dispatch token differs')
    for other in destination.glob('*/binding.json'):
        existing = load(other)
        require(existing['id'] != run['id'] or other.parent.name == case_id, 'run ID reused')
    target = destination / case_id / 'binding.json'
    if target.exists():
        require(load(target)['id'] == run['id'], 'case already bound to another run')
    else:
        save_new(target, run)
    return run


def download(destination, case_id, call=gh):
    """Read-only recovery is independent of dispatch and may be repeated."""
    case_dir = destination / case_id
    binding = load(case_dir / 'binding.json')
    run = bind(destination, case_id, binding['id'], call)
    require(run['status'] == 'completed', 'run not terminal; recover later without dispatch')
    target = case_dir / 'bundles'
    target.mkdir(exist_ok=True)
    # gh refuses overwriting artifacts. Recover into a new directory per collection.
    recovery = target / uuid.uuid4().hex
    call('run', 'download', str(run['id']), '--repo', REPOSITORY, '--dir', str(recovery))
    save_new(recovery / 'run.json', run)
    return recovery


def run_case(repo, destination, case_id, call=gh, pause=time.sleep):
    """One case only; uncertain dispatches require bind/download recovery, not this command."""
    require(not (destination / case_id / 'dispatch.json').exists(), 'dispatch already recorded; recover only')
    require(load(destination / 'plan.json')['approved'] is True, 'explicit final plan approval required')
    try:
        call('variable', 'set', 'CLARIFICATION_SINGLE_RESPONSE_ENABLED', '--repo', REPOSITORY, '--body', 'true')
        dispatch(destination, case_id, call)
        record = load(destination / case_id / 'dispatch.json')
        title = f"single-response {case_id} {record['token']}"
        run = None
        for _ in range(20):
            rows = json.loads(call('api', f'repos/{REPOSITORY}/actions/workflows/single-response.lock.yml/runs?event=workflow_dispatch&per_page=100'))['workflow_runs']
            matches = [r for r in rows if r['display_title'] == title]
            require(len(matches) <= 1, 'multiple matching runs; pause for recovery')
            if matches:
                run = bind(destination, case_id, matches[0]['id'], call)
                break
            pause(10)
        require(run is not None, 'run not found; recover by token without redispatch')
        for _ in range(120):
            run = bind(destination, case_id, run['id'], call)
            if run['status'] == 'completed':
                break
            pause(10)
        require(run['status'] == 'completed', 'run still active; recover without redispatch')
        bundle = download(destination, case_id, call)
        from scripts.hosted_evidence import import_bundle
        import_bundle(repo, destination, case_id, bundle)
        require(load(destination / case_id / 'archive.json')['continue_allowed'],
                'infrastructure failure; pause and recover, additional inference needs authorization')
    finally:
        # Also executed on authentication/network errors or Ctrl+C. A hard process
        # kill can interrupt this call; operators must independently check the switch.
        call('variable', 'set', 'CLARIFICATION_SINGLE_RESPONSE_ENABLED', '--repo', REPOSITORY, '--body', 'false')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'run', 'dispatch', 'bind', 'download', 'import'])
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--case', choices=CASE_ORDER)
    parser.add_argument('--commit')
    parser.add_argument('--run-id', type=int)
    parser.add_argument('--bundle', type=Path)
    args = parser.parse_args()
    if args.command == 'init':
        initialize(Path.cwd(), args.study, args.commit)
    else:
        require(args.case is not None, 'case required')
        if args.command == 'run':
            run_case(Path.cwd(), args.study, args.case)
        elif args.command == 'dispatch':
            dispatch(args.study, args.case)
        elif args.command == 'bind':
            require(args.run_id is not None, 'run ID required; recover by dispatch token, never redispatch')
            bind(args.study, args.case, args.run_id)
        elif args.command == 'download':
            print(download(args.study, args.case))
        else:
            from scripts.hosted_evidence import import_bundle
            require(args.bundle is not None, 'bundle required')
            import_bundle(Path.cwd(), args.study, args.case, args.bundle)


if __name__ == '__main__':
    main()
