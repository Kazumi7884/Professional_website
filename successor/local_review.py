"""Ask a local OpenAI-compatible model for a review draft without editing site sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent


def prompt():
    projects = json.loads((HERE / 'projects.json').read_text(encoding='utf-8'))
    facts = json.loads((HERE / 'repositories.json').read_text(encoding='utf-8'))
    return """You are reviewing a personal portfolio site. Write a short, plain update draft for the owner to review. Use only the supplied facts. Keep each point concrete. Never claim mastery, employment, completion, or contribution that is not stated. Mark each point as VERIFIED, INFERENCE, or ASK OWNER. Do not rewrite existing authored posts. Do not give marketing copy.\n\nEDITORIAL PROJECT DATA:\n""" + json.dumps(projects, ensure_ascii=False) + "\n\nPUBLIC REPOSITORY SNAPSHOT:\n" + json.dumps(facts, ensure_ascii=False)


def review(endpoint, model):
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are a careful local editorial reviewer.'},
            {'role': 'user', 'content': prompt()},
        ],
        'temperature': 0.2,
    }).encode('utf-8')
    request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=90) as response:
        data = json.loads(response.read(1024 * 1024 + 1))
    return data['choices'][0]['message']['content']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Draft a local-only editorial review. It never edits source files.')
    parser.add_argument('--endpoint', default='http://127.0.0.1:11435/v1/chat/completions')
    parser.add_argument('--model', default='simple')
    parser.add_argument('--output', type=Path, help='Optional review-draft file. Omit to print only.')
    args = parser.parse_args()
    draft = review(args.endpoint, args.model)
    if args.output:
        args.output.write_text(draft + '\n', encoding='utf-8')
        print(f'Review draft written to {args.output}')
    else:
        print(draft)
