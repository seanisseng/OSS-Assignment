"""Fetch one older block of 50 candidate bodies; preserve the original audit."""
import json
import datetime as dt
from pathlib import Path
import subprocess
import sys
import urllib.parse
import urllib.request

from scripts import collect


def main():
    credential = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                                text=True, capture_output=True, check=True)
    collect.TOKEN = next(x.split('=', 1)[1] for x in credential.stdout.splitlines() if x.startswith('password='))
    query = 'repo:pytest-dev/pytest is:issue label:"type: bug" created:<2026-10-01'
    block = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    if not 2 <= block <= 10:
        raise ValueError('block must be between 2 and 10')
    data = collect.get('search/issues?q=' + urllib.parse.quote(query) + f'&sort=created&order=desc&per_page=50&page={block}')
    root = Path(f'evals/golden/candidates/block-{block}')
    collect.save(root / 'search.json', data)
    collect.save(root / 'provenance.json', dict(query=query, block=block, block_size=50,
        collected_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        purpose='Candidate search only; does not expand the original workload audit denominator.'))
    fields = '\n'.join('i%d: issue(number:%d) { number userContentEdits(first:1) { totalCount } }' % (x['number'], x['number']) for x in data['items'])
    request = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': 'query { repository(owner:"pytest-dev",name:"pytest") {' + fields + '} }'}).encode(),
        headers={'Authorization': 'Bearer ' + collect.TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=45) as response:
        edits = json.load(response)
    collect.save(root / 'edit-provenance.json', edits)
    for issue in data['items']:
        if edits['data']['repository']['i'+str(issue['number'])]['userContentEdits']['totalCount'] == 0:
            print(str(issue['number']) + ' ' + issue['title'] + ' (' + str(len(issue['body'])) + ' chars)', flush=True)


if __name__ == '__main__':
    main()
