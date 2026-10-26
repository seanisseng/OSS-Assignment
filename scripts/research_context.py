"""Recover edit provenance and pre-report pytest source; read-only remote calls."""
import base64
import json
from pathlib import Path
import subprocess
import urllib.request

from scripts import collect

RELEVANT = {
    15052: 'src/_pytest/fixtures.py', 15051: 'src/_pytest/fixtures.py',
    15005: 'src/_pytest/approx.py', 14775: 'src/_pytest/fixtures.py',
    14533: 'src/_pytest/fixtures.py', 14456: 'src/_pytest/python_api.py',
    14389: 'src/_pytest/raises.py', 14329: 'src/_pytest/nodes.py',
    14324: 'src/_pytest/raises.py', 13986: 'src/_pytest/subtests.py',
    13902: 'doc/en/how-to/subtests.rst', 13849: 'src/_pytest/config/findpaths.py',
    13716: 'src/_pytest/main.py', 13634: 'src/_pytest/config/__init__.py',
    13403: 'src/_pytest/assertion/rewrite.py',
}

def main():
    credential = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                                text=True, capture_output=True, check=True)
    collect.TOKEN = next(x.split('=', 1)[1] for x in credential.stdout.splitlines() if x.startswith('password='))
    release = collect.get('repos/github/gh-aw/git/ref/tags/v0.93.5')['object']
    if release['type'] == 'tag':
        release = collect.get('repos/github/gh-aw/git/tags/' + release['sha'])['object']
    collect.save(Path('evals/evidence/compiler-release.json'), release)
    print('Compiler release commit:', release['sha'])
    issues = json.loads(Path('evals/golden/audit/search.json').read_text(encoding='utf-8'))['items']
    fields = '\n'.join('i%d: issue(number:%d) { number lastEditedAt userContentEdits(first:1) { totalCount } }' % (x['number'], x['number']) for x in issues)
    query = 'query { repository(owner:"pytest-dev",name:"pytest") {' + fields + '} }'
    request = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': query}).encode(),
        headers={'Authorization': 'Bearer ' + collect.TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=45) as response:
        edits = json.load(response)
    collect.save(Path('evals/golden/audit/edit-provenance.json'), edits)
    eligible = [x for x in issues if edits.get('data', {}).get('repository', {}).get('i'+str(x['number']), {}).get('userContentEdits', {}).get('totalCount') == 0]
    print('Unedited eligible:', [x['number'] for x in eligible])
    for issue in eligible:
        number = issue['number']
        target = Path(f'evals/golden/context/{number}')
        if (target / 'provenance.json').exists():
            sha = json.loads((target / 'provenance.json').read_text())['commit']
        else:
            commits = collect.get('repos/pytest-dev/pytest/commits?per_page=1&until=' + issue['created_at'])
            sha = commits[0]['sha']
        filenames = {'src/_pytest/fixtures.py', 'src/_pytest/python.py', 'pyproject.toml', 'LICENSE'}
        if number in RELEVANT:
            filenames.add(RELEVANT[number])
        for name in sorted(filenames):
            if (target / name).exists():
                continue
            data = collect.get('repos/pytest-dev/pytest/contents/' + name + '?ref=' + sha)
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(base64.b64decode(data['content']))
        collect.save(target / 'provenance.json', dict(issue=number, commit=sha, cutoff=issue['created_at'],
                     source='https://github.com/pytest-dev/pytest/tree/' + sha))
        print('Preserved context', number, flush=True)


if __name__ == '__main__':
    main()
