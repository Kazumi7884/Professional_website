"""Ask a local OpenAI-compatible model for a review draft without editing site sources."""
from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent


def prompt():
    projects = json.loads((HERE / 'projects.json').read_text(encoding='utf-8'))
    facts = json.loads((HERE / 'repositories.json').read_text(encoding='utf-8'))
    return """You are reviewing a personal portfolio site. Write a short, plain update draft for the owner to review. Use only the supplied facts. Keep each point concrete. Never claim mastery, employment, completion, or contribution that is not stated. Mark each point as VERIFIED, INFERENCE, or ASK OWNER. Do not rewrite existing authored posts. Do not give marketing copy.\n\nEDITORIAL PROJECT DATA:\n""" + json.dumps(projects, ensure_ascii=False) + "\n\nPUBLIC REPOSITORY SNAPSHOT:\n" + json.dumps(facts, ensure_ascii=False)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def review(endpoint, model):
    parsed = urlsplit(endpoint)
    if (parsed.scheme != 'http' or parsed.username or parsed.password or
            parsed.fragment or not parsed.port or
            not ipaddress.ip_address(parsed.hostname).is_loopback):
        raise ValueError('Review requires a literal loopback HTTP endpoint')
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are a careful local editorial reviewer.'},
            {'role': 'user', 'content': prompt()},
        ],
        'temperature': 0.2,
        'max_tokens': 512,
        'chat_template_kwargs': {'enable_thinking': False},
    }).encode('utf-8')
    request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=90) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('Review response exceeds 1 MiB')
    data = json.loads(raw)
    reply = data['choices'][0]['message']['content']
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError('Local model returned no review text; no draft was written')
    return reply


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Draft a local-only editorial review. It never edits source files.')
    parser.add_argument('--endpoint', default='http://127.0.0.1:11435/v1/chat/completions')
    parser.add_argument('--model', default='simple')
    parser.add_argument('--output', type=Path, help='Optional review-draft file. Omit to print only.')
    args = parser.parse_args()
    draft = review(args.endpoint, args.model)
    if args.output:
        with args.output.open('x', encoding='utf-8') as output:
            output.write(draft + '\n')
        print(f'Review draft written to {args.output}')
    else:
        print(draft)
