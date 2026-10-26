"""Read-only GitHub collection. Never uses credentials or executes issue text."""
import datetime as dt
import json
from pathlib import Path
import urllib.request
import subprocess

ROOT = Path('evals/golden')
TOKEN = None


def get(path):
    headers = {'User-Agent': 'OSS-Assignment-research'}
    if TOKEN:
        headers['Authorization'] = 'Bearer ' + TOKEN
    request = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    global TOKEN
    credential = subprocess.run(['git', 'credential', 'fill'],
        input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, check=True)
    TOKEN = next((line.split('=', 1)[1] for line in credential.stdout.splitlines()
                  if line.startswith('password=')), None)
    query = 'repo:pytest-dev/pytest is:issue label:"type: bug" created:<2026-10-01'
    import urllib.parse
    results = get('search/issues?q=' + urllib.parse.quote(query) + '&sort=created&order=desc&per_page=50')
    save(ROOT / 'audit/search.json', results)
    observations = []
    for issue in results['items']:
        number = issue['number']
        cached = ROOT / f'audit/raw/{number}.json'
        if cached.exists():
            stored = json.loads(cached.read_text(encoding='utf-8'))
            comments, events = stored['comments'], stored['events']
        else:
            comments = get(f'repos/pytest-dev/pytest/issues/{number}/comments?per_page=100')
            events = get(f'repos/pytest-dev/pytest/issues/{number}/events?per_page=100')
        save(ROOT / f'audit/raw/{number}.json', dict(issue=issue, comments=comments, events=events))
        responses = [c for c in comments if c['user']['login'] != issue['user']['login']
                     and c['user']['type'] != 'Bot' and not c['user']['login'].endswith('[bot]')]
        created = dt.datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
        hours = None
        if responses:
            hours = (dt.datetime.fromisoformat(responses[0]['created_at'].replace('Z', '+00:00')) - created).total_seconds() / 3600
        observations.append(dict(number=number, created_at=issue['created_at'],
                                 first_response_hours=hours, clarification='uncoded',
                                 categories=[], original_reconstructable=issue['created_at'] == issue['updated_at']))
    save(ROOT / 'audit/observations.json', observations)
    save(ROOT / 'audit/provenance.json', dict(query=query, collected_at=dt.datetime.now(dt.timezone.utc).isoformat(),
         denominator=len(observations), comment_page_limit=100, events_page_limit=100,
         warning='updated_at includes other activity; reconstructability requires timeline review.'))
    print(f'Collected {len(observations)} reports; clarification coding remains human/AI review work.')


if __name__ == '__main__':
    main()
