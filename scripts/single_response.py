"""Trusted packet preparation and validation; never executes report/source code."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from scripts.contract import REPOSITORY, digest, require, validate
from scripts.evidence import file_hash, load, review_record
from scripts.runtime import api


PACKET_BYTES = 32768
EXCERPT_LINES = 21
MAX_EXCERPTS = 4


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def build_packet(case, skill):
    """Only explicit report file/line references select source, never expectations."""
    sources = {k for k in case['context'] if re.search(r'\.(?:py|toml|ini|cfg|md|rst|txt)$', k)}
    supplemental = {k:v for k,v in case['context'].items() if k != 'issue' and k not in sources}
    issue = case['context'].get('issue')
    if issue and issue not in {case['body'], case['title'] + '\n\n' + case['body']}:
        supplemental['issue'] = issue
    packet = dict(format='single-response-v1', case_id=case['case_id'], input_hash=digest(case),
                  skill=skill, report=dict(title=case['title'], body=case['body']),
                  supplemental_context=supplemental, excerpts=[], omitted_context=sorted(sources))
    require(len(encoded(packet)) <= PACKET_BYTES, 'complete report exceeds packet allowance')
    references = re.findall(
        r'([\w./\\-]+\.(?:py|toml|ini|cfg))[^\n]{0,8}?(?:line\s+|:)(\d+)',
        case['body'])
    used = set()
    for filename, line_number in references:
        name = filename.replace('\\', '/')
        matches = [k for k in case['context'] if k != 'issue' and
                   (k == name or name.endswith('/' + k) or k.endswith('/' + name))]
        if len(matches) != 1:
            continue
        key, number = matches[0], int(line_number)
        lines = case['context'][key].splitlines(keepends=True)
        if not 1 <= number <= len(lines) or (key, number) in used:
            continue
        radius = EXCERPT_LINES // 2
        start, end = max(1, number - radius), min(len(lines), number + radius)
        text = ''.join(lines[start-1:end])
        excerpt = dict(key=key, start_line=start, end_line=end, text=text,
                       source_sha256=hashlib.sha256(case['context'][key].encode()).hexdigest(),
                       excerpt_sha256=hashlib.sha256(text.encode()).hexdigest())
        candidate = packet | {'excerpts': packet['excerpts'] + [excerpt]}
        if len(encoded(candidate)) <= PACKET_BYTES:
            packet = candidate
            used.add((key, number))
        if len(packet['excerpts']) == MAX_EXCERPTS:
            break
    # This lists files not excerpted at all; complete snapshots are never modified.
    packet['omitted_context'] = sorted(set(packet['omitted_context']) -
                                        {x['key'] for x in packet['excerpts']})
    return packet


def validate_response(case, packet, raw):
    require(packet['case_id'] == case['case_id'] and packet['input_hash'] == digest(case),
            'packet input mismatch')
    try:
        result = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise ValueError('response is not JSON') from error
    validate(case, result)
    supplied = {'issue'} | set(packet['supplemental_context']) | {x['key'] for x in packet['excerpts']}
    require(set(result['evidence']) <= supplied, 'evidence was not supplied in packet')
    return result


def prepare():
    root = Path(os.environ.get('TRUSTED_ROOT', '.')).resolve()
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'foreign repository')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/main', 'main required')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'retries forbidden')
    require(os.environ.get('SINGLE_RESPONSE_ENABLED') == 'true', 'single response disabled')
    require(os.environ.get('CASE_ID') == 'pytest-15051', 'only development case 15051 allowed')
    review = review_record(root)
    runs = api('actions/workflows/single-response.lock.yml/runs?per_page=1')
    require(type(runs['total_count']) is int and runs['total_count'] == 1,
            'single-response smoke attempt exhausted or unknown')
    case = load(root / 'evals/golden/inputs/pytest-15051.json')
    require(case['case_id'] == 'pytest-15051', 'smoke case mismatch')
    expected = next(x for x in load(root / 'evals/golden/expectations.json')['expectations']
                    if x['case_id'] == case['case_id'])
    require(digest(case) == expected['input_hash'], 'frozen input differs')
    skill = root / '.claude/skills/bug-report-clarification/SKILL.md'
    packet = build_packet(case, skill.read_text(encoding='utf-8'))
    Path('input').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    packet_path = Path('input/packet.json')
    packet_path.write_bytes(encoded(packet))
    manifest = dict(case_id=case['case_id'], input_hash=digest(case), sandbox_issue=None,
                    artifact_only=True, skill_sha256=file_hash(skill),
                    packet_sha256=file_hash(packet_path), input_format=packet['format'],
                    configuration_hash=review['configuration_hash'])
    Path('input/manifest.json').write_bytes(encoded(manifest))
    actions = Path(os.environ['RUNNER_TEMP']) / 'gh-aw/actions'
    actions.mkdir(parents=True, exist_ok=True)
    destination = actions / 'single_response_harness.cjs'
    require(not destination.is_symlink(), 'symlink harness refused')
    shutil.copyfile(root / 'scripts/single_response_harness.cjs', destination)


def validate_artifact():
    manifest = load('trusted-input/manifest.json')
    require(manifest['case_id'] == 'pytest-15051' and manifest['artifact_only'] is True
            and manifest['sandbox_issue'] is None, 'not the artifact-only smoke case')
    case = load('evals/golden/inputs/pytest-15051.json')
    require(manifest['input_hash'] == digest(case), 'manifest input differs')
    skill = Path('.claude/skills/bug-report-clarification/SKILL.md')
    require(file_hash(skill) == manifest['skill_sha256'], 'skill differs')
    packet = build_packet(case, skill.read_text(encoding='utf-8'))
    require(hashlib.sha256(encoded(packet)).hexdigest() == manifest['packet_sha256'],
            'packet differs from trusted preparation')
    path = Path('staged/recommendation.json')
    require(not path.is_symlink() and path.stat().st_size <= 32768, 'unsafe/oversized output')
    result = validate_response(case, packet, path.read_text(encoding='utf-8'))
    request = load('staged/request.json')
    require(request['model'] == 'auto' and request['tools'] == [] and
            request['tool_choice'] == 'none' and request['n'] == 1, 'request policy differs')
    require(packet['skill'] in request['messages'][0]['content'] and
            json.loads(request['messages'][1]['content']) == {k:v for k,v in packet.items() if k != 'skill'},
            'packet or skill not present in captured request')
    trace = load('staged/execution.json')
    require(type(trace['requests_sent']) is int and trace['requests_sent'] == 1
            and trace['status'] == 'response_received'
            and trace['packet_sha256'] == manifest['packet_sha256'], 'invalid execution trace')
    print('Recommendation validates. Semantic skill compliance still needs human review.')
    print('Exact approval hash:', digest(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'validate'])
    command = parser.parse_args().command
    prepare() if command == 'prepare' else validate_artifact()
