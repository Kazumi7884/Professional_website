"""Refresh public, allowlisted facts without altering editorial project claims."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.request

HERE = Path(__file__).resolve().parent


def public_snapshot(name, data):
    if not re.fullmatch(r'Kazumi7884/[A-Za-z0-9_.-]+', name):
        raise ValueError('Repository is outside the permitted owner')
    if data.get('private') is not False or data.get('full_name') != name or data.get('visibility', 'public') != 'public':
        raise ValueError('Repository is not a verified public selection')
    expected = 'https://github.com/' + name
    if data.get('html_url') != expected:
        raise ValueError('Unexpected source URL')
    return {key: data.get(key) for key in ['full_name', 'html_url', 'description', 'language', 'pushed_at', 'default_branch', 'archived']} | {'license': (data.get('license') or {}).get('spdx_id')}


def refresh(destination=HERE / 'repositories.json', fetch=None):
    allowlist = json.loads((HERE / 'projects.json').read_text())['repositories']
    if fetch is None:
        def fetch(name):
            request = urllib.request.Request('https://api.github.com/repos/' + name, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Kaz-portfolio-snapshot'})
            with urllib.request.urlopen(request, timeout=15) as response:
                data = response.read(1024 * 1024 + 1)
                if len(data) > 1024 * 1024:
                    raise ValueError('Oversized repository response')
                return json.loads(data)
    facts = [public_snapshot(name, fetch(name)) for name in allowlist]
    target = Path(destination)
    stable = {'status': 'verified', 'repositories': facts}
    if target.is_file():
        try:
            existing = json.loads(target.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            existing = None
        if isinstance(existing, dict) and {key: existing.get(key) for key in stable} == stable:
            return existing
    result = {'observed_at': datetime.now(timezone.utc).isoformat(), **stable}
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(target)
    return result


if __name__ == '__main__':
    refresh()
    print('Public repository facts refreshed. Editorial claims are unchanged.')

