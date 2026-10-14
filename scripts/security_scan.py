"""Scan tracked source and built public text without printing credential values."""
import json
from pathlib import Path
import re
import subprocess
import sys

from detect_secrets import SecretsCollection
from detect_secrets.settings import default_settings

ROOT = Path(__file__).resolve().parents[1]


def intentional_fixture(path, finding, line):
    if finding['type'] == 'Hex High Entropy String' and path == 'docs/validation-report.json':
        return bool(re.fullmatch(r'\s*"source_digest": "[a-f0-9]{64}"\s*', line))
    if finding['type'] == 'Basic Auth Credentials' and path in ('successor/test_successor.py', 'tests/test_security_audit.py'):
        return bool(re.search(r'https?://user:(secret|pass)@(127\.0\.0\.1|api\.myanimelist\.net)', line))
    return False


def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    paths = [ROOT / name for name in tracked if name]
    # Include new candidate files before their first commit as well.
    paths += [ROOT / name for name in subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0') if name]
    paths += [p for p in (ROOT / 'build').rglob('*') if p.is_file()]
    findings = []
    with default_settings():
        for path in sorted(set(paths)):
            if not path.is_file() or path.is_symlink():
                continue
            collection = SecretsCollection()
            collection.scan_file(str(path))
            rows = collection.json().get(str(path), [])
            if rows:
                lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
                relative = path.relative_to(ROOT).as_posix()
                for row in rows:
                    if not intentional_fixture(relative, row, lines[row['line_number'] - 1]):
                        findings.append({'path': relative, 'line': row['line_number'], 'type': row['type']})
    print(json.dumps({'files_considered': len(set(paths)), 'findings': findings}, indent=2))
    return bool(findings)


if __name__ == '__main__':
    sys.exit(main())
