"""Local writing desk: Markdown files remain the only content database.

The server binds to loopback, validates Host/Origin and requires a per-run token
on API requests. It never exposes a file editor on the public static website.
"""
from __future__ import annotations

from datetime import date
import hashlib
import hmac
import http.server
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
WRITE_LOCK = threading.Lock()
LIMIT = 1024 * 1024


class Conflict(ValueError):
    """The on-disk file changed after the author opened it."""


def content_path(relative):
    parts = relative.split('/') if isinstance(relative, str) else []
    valid_segment = re.compile(r'[A-Za-z0-9_-]+\Z')
    if (not parts or len(relative) > 240 or any(not valid_segment.fullmatch(part) for part in parts[:-1])
            or not parts[-1].endswith('.md') or not valid_segment.fullmatch(parts[-1][:-3])):
        raise ValueError('Choose a Markdown file inside content/.')
    root = (ROOT / 'content').resolve()
    path = root / relative
    resolved = os.path.abspath(path)
    if not resolved.startswith(str(root) + os.sep) or not path.resolve().is_relative_to(root):
        raise ValueError('File must stay inside content/.')
    # Reject symlinks even when their current target is inside the content tree.
    if any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
        raise ValueError('Symbolic links cannot be edited in the writing desk.')
    return Path(resolved)


def read_document(path):
    raw = path.read_text(encoding='utf-8')
    match = re.match(r'\A---\s*\n(.*?)\n---[ \t]*(?:\n|$)(.*)\Z', raw, re.S)
    if not match:
        raise ValueError('The file needs YAML metadata between --- lines.')
    meta = yaml.safe_load(match[1])
    if not isinstance(meta, dict) or not meta.get('title'):
        raise ValueError('The file needs a title.')
    return {'metadata': meta, 'body': match[2].lstrip('\n'),
            'revision': hashlib.sha256(raw.encode()).hexdigest()}


def catalogue():
    entries = []
    for path in sorted((ROOT / 'content').rglob('*.md')):
        relative = path.relative_to(ROOT / 'content').as_posix()
        try:
            item = read_document(content_path(relative))
            meta = item['metadata']
            entries.append({'path': relative, 'title': str(meta['title']),
                            'draft': meta.get('draft') is True,
                            'kind': meta.get('entryType', 'page'), 'date': str(meta.get('date', ''))})
        except (ValueError, OSError, yaml.YAMLError):
            entries.append({'path': relative, 'title': relative, 'error': True})
    return entries


def save_document(payload):
    """Preserve unknown metadata; reject stale writes and never overwrite new slugs."""
    path = content_path(payload.get('path'))
    supplied = payload.get('metadata')
    body = payload.get('body')
    if not isinstance(supplied, dict) or not isinstance(body, str):
        raise ValueError('Post metadata and body are required.')
    title = supplied.get('title', '')
    if not isinstance(title, str) or not title.strip() or len(title) > 180:
        raise ValueError('Use a title between 1 and 180 characters.')
    if not isinstance(supplied.get('description', ''), str) or len(supplied.get('description', '')) > 350:
        raise ValueError('Keep the summary under 350 characters.')
    if type(supplied.get('draft')) is not bool:
        raise ValueError('Choose Draft or Ready for publishing.')
    if supplied.get('entryType') not in ('post', 'page', 'section', 'dashboard', 'phasmophobia', 'sitemap'):
        raise ValueError('Projects and resources are not authorable entry types on this site.')
    tags = supplied.get('tags', [])
    if not isinstance(tags, list) or len(tags) > 20 or any(not isinstance(t, str) or not t.strip() or len(t) > 60 for t in tags):
        raise ValueError('Use up to 20 tags, each under 60 characters.')
    date_value = supplied.get('date', '')
    if date_value:
        try:
            date.fromisoformat(date_value)
        except (TypeError, ValueError):
            raise ValueError('Use a valid date in YYYY-MM-DD format.') from None
    if not supplied['draft'] and (not body.strip() or not supplied.get('description', '').strip() or not date_value):
        raise ValueError('Add a date, summary and post text before marking ready.')
    with WRITE_LOCK:
        exists = path.exists()
        current = read_document(path) if exists else None
        revision = payload.get('revision')
        if exists and (not revision or revision != current['revision']):
            raise Conflict('This file changed on disk. Download your Markdown, then reopen the file to review the newer version.')
        if not exists and revision:
            raise Conflict('This file was moved or deleted. Download your Markdown before reopening it.')
        metadata = dict(current['metadata']) if current else {}
        # Clients may edit these fields only. Aliases, URLs, custom layouts and
        # other existing metadata survive every round trip unchanged.
        for key in ('title', 'description', 'date', 'entryType', 'draft', 'tags'):
            metadata[key] = supplied.get(key, '' if key != 'tags' else [])
        metadata['title'] = title.strip()
        metadata['lastmod'] = date.today().isoformat()
        raw = '---\n' + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True) + '---\n\n' + body.rstrip() + '\n'
        path.parent.mkdir(parents=True, exist_ok=True)
        if not exists:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(raw)
        else:
            # Write a sibling temporary file, then atomically replace. This
            # avoids partial documents if the process stops during the write.
            descriptor, temporary = tempfile.mkstemp(prefix='.studio-', dir=path.parent)
            try:
                with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return {'path': path.relative_to((ROOT / 'content').resolve()).as_posix(), **read_document(path)}


def preview_html(body):
    """Use the production Markdown extensions and strip active HTML for preview."""
    if not isinstance(body, str):
        raise ValueError('Post text is required.')
    soup = BeautifulSoup(markdown.markdown(body, extensions=['extra', 'toc', 'sane_lists']), 'html.parser')
    allowed = {'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'strong', 'em', 'del', 's',
               'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
               'img', 'figure', 'figcaption', 'dl', 'dt', 'dd', 'sup', 'sub', 'div', 'span'}
    for node in list(soup.find_all(True)):
        if node.name in ('script', 'style', 'iframe', 'object', 'embed', 'svg', 'math'):
            node.decompose()
            continue
        if node.name is None:
            continue
        if node.name not in allowed:
            node.unwrap()
            continue
        for attr in list(node.attrs):
            if attr not in ('href', 'src', 'alt', 'title', 'id', 'class'):
                del node[attr]
        for attr in ('href', 'src'):
            if attr not in node.attrs:
                continue
            value = node[attr]
            parsed = urlsplit(re.sub(r'[\x00-\x20]', '', value))
            if parsed.scheme not in ('', 'https', 'http', 'mailto') or value.startswith('//'):
                del node[attr]
        if node.name == 'a':
            node['target'] = '_blank'
            node['rel'] = 'noopener noreferrer'
    return str(soup)


def make_handler(token, port, build_fn):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'SAMEORIGIN')
            super().end_headers()

        def send_json(self, value, status=200):
            # Escaping markup also makes the JSON inert if embedded by a client.
            data = json.dumps(value, ensure_ascii=False, default=str).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def trusted(self, api=False):
            actual_port = self.server.server_address[1]
            origins = {f'http://127.0.0.1:{actual_port}', f'http://localhost:{actual_port}'}
            hosts = {f'127.0.0.1:{actual_port}', f'localhost:{actual_port}'}
            if self.headers.get('Host') not in hosts:
                self.send_json({'error': 'This writing desk accepts localhost requests only.'}, 403)
                return False
            origin = self.headers.get('Origin')
            if origin and origin not in origins:
                self.send_json({'error': 'Request origin rejected.'}, 403)
                return False
            if api and not hmac.compare_digest(self.headers.get('X-Studio-Token', ''), token):
                self.send_json({'error': 'Reload the writing desk to reconnect.'}, 403)
                return False
            return True

        def do_GET(self):
            route = urlsplit(self.path)
            if not self.trusted(route.path.startswith('/__studio/api/')):
                return
            try:
                if route.path == '/__studio/api/posts':
                    return self.send_json({'posts': catalogue()})
                if route.path == '/__studio/api/post':
                    relative = parse_qs(route.query).get('path', [''])[0]
                    return self.send_json({'path': relative, **read_document(content_path(relative))})
                if route.path in ('/__studio', '/__studio/'):
                    env = Environment(loader=FileSystemLoader(ROOT / 'studio'), autoescape=select_autoescape(['html']))
                    data = env.get_template('index.html').render(token=token).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    return self.wfile.write(data)
                asset_paths = {
                    '/__studio/studio.css': ROOT / 'studio/studio.css',
                    '/__studio/studio.js': ROOT / 'studio/studio.js',
                    '/__studio/site.css': ROOT / 'assets/css/site.css',
                    '/__studio/purify.min.js': ROOT / 'studio/vendor/purify.min.js',
                }
                if route.path in asset_paths:
                    path = asset_paths[route.path]
                    data = path.read_bytes()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/css' if path.suffix == '.css' else 'text/javascript')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    return self.wfile.write(data)
                if route.path.startswith('/__studio'):
                    return self.send_error(404)
                return super().do_GET()
            except FileNotFoundError:
                self.send_json({'error': 'The file no longer exists.'}, 404)
            except (ValueError, yaml.YAMLError) as exc:
                self.send_json({'error': str(exc)}, 400)

        def do_POST(self):
            if not self.trusted(api=True):
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= LIMIT:
                    return self.send_json({'error': 'Request must be under 1 MiB.'}, 413)
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.send_json({'error': 'JSON required.'}, 415)
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError('Request must be an object.')
                route = urlsplit(self.path).path
                if route == '/__studio/api/save':
                    return self.send_json(save_document(payload))
                if route == '/__studio/api/preview':
                    return self.send_json({'html': preview_html(payload.get('body'))})
                if route == '/__studio/api/build':
                    with WRITE_LOCK:
                        report = build_fn()
                    return self.send_json({'pages': len(report['pages']), 'seconds': report['seconds']})
                self.send_error(404)
            except Conflict as exc:
                self.send_json({'error': str(exc)}, 409)
            except (ValueError, yaml.YAMLError) as exc:
                self.send_json({'error': str(exc)}, 400)
            except OSError:
                self.send_json({'error': 'Could not write or read the file. Check permissions and disk space; your text is still in the editor.'}, 500)
            except Exception:
                self.send_json({'error': 'The build failed. Your saved Markdown is retained; run the check command to see the full error.'}, 500)

        def list_directory(self, path):
            self.send_error(404)

    return Handler


def serve(port, build_fn):
    build_fn()
    token = secrets.token_urlsafe(32)
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', port), make_handler(token, port, build_fn))
    except OSError as exc:
        if port == 0:
            raise
        print(f'Port {port} is unavailable ({exc}); selecting an available localhost port.', flush=True)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), make_handler(token, 0, build_fn))
    actual_port = server.server_address[1]
    with server:
        print(f'Writing desk: http://127.0.0.1:{actual_port}/__studio/ — Ctrl+C to stop.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
