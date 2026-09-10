#!/usr/bin/env python3
"""Build Kaz's Markdown notebooks into portable HTML, CSS and JavaScript.

Run from any working directory. Source files are authoritative; dist is a
disposable build. No network request or account credential is needed to build.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import html
import http.server
import json
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
import zipfile

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown
from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'


def slug(value):
    """Use readable stable route segments, independent of the operating system."""
    return re.sub(r'[^a-z0-9]+', '-', str(value).lower()).strip('-')


def route_path(route):
    """Reject output traversal before converting a public URL to a file path."""
    parsed = urlsplit(route)
    parts = unquote(parsed.path).split('/')
    if parsed.scheme or parsed.netloc or '..' in parts or '\\' in route:
        raise ValueError(f'Unsafe local route: {route}')
    name = parsed.path.lstrip('/')
    return Path(name if Path(name).suffix else (name.rstrip('/') + '/' if name else '') + 'index.html')


def read_pages():
    pages = []
    for source in sorted((ROOT / 'content').rglob('*.md')):
        raw = source.read_text(encoding='utf-8')
        match = re.match(r'\A---\s*\n(.*?)\n---[ \t]*(?:\n|$)(.*)\Z', raw, re.S)
        if not match:
            raise ValueError(f'Missing front matter: {source.relative_to(ROOT)}')
        meta = yaml.safe_load(match[1])
        if not isinstance(meta, dict) or not meta.get('title'):
            raise ValueError(f'Missing title: {source}')
        if meta.get('draft') is True:
            continue
        relative = source.relative_to(ROOT / 'content')
        stem = relative.with_suffix('').as_posix()
        route = '/' + (stem.removesuffix('_index').rstrip('/') if source.stem == '_index' else stem) + '/'
        route = '/' if route == '//' else route
        route = meta.get('url', route)
        route_path(route)
        engine = markdown.Markdown(extensions=['extra', 'toc', 'sane_lists'], output_format='html')
        body = engine.convert(match[2])
        plain = BeautifulSoup(body, 'html.parser').get_text(' ', strip=True)
        pages.append({**meta, 'url': route, 'title': str(meta['title']),
                      'description': str(meta.get('description') or plain[:155] or meta['title']),
                      'body': body, 'toc': engine.toc if engine.toc_tokens else '',
                      'text': plain, 'source': relative.as_posix(),
                      'section': route.strip('/').split('/')[0] or 'home',
                      'is_section': source.stem == '_index',
                      'date': str(meta.get('date', '')), 'lastmod': str(meta.get('lastmod', '')),
                      'minutes': max(1, (len(plain.split()) + 199) // 200),
                      'entryType': meta.get('entryType', 'page'), 'synthetic': False})
    # Missing directory indexes become real browsable boards, not broken crumbs.
    known = {p['url'] for p in pages}
    for page in pages[:]:
        for parent in Path(page['url'].strip('/')).parents:
            url = '/' + parent.as_posix().strip('.') + '/'
            if url != '//' and url not in known:
                title = parent.name.replace('-', ' ').title()
                pages.append(empty_page(url, title, 'Posts and notes in ' + title + '.'))
                known.add(url)
    # Preserve navigable tag/category/stack archives from the original metadata.
    for taxonomy in ('tags', 'categories', 'stack'):
        terms = sorted({str(t) for p in pages for t in (p.get(taxonomy) or [])})
        if terms:
            pages.append(empty_page('/' + taxonomy + '/', taxonomy.title(), 'Browse by ' + taxonomy + '.'))
        for term in terms:
            pages.append({**empty_page(f'/{taxonomy}/{slug(term)}/', term, f'Posts filed under {term}.'),
                          'taxonomy': taxonomy, 'term': term})
    return pages


def empty_page(url, title, description):
    return dict(url=url, title=title, description=description, body='', toc='', text='',
                source='', section=url.strip('/').split('/')[0], is_section=True,
                date='', lastmod='', minutes=1, entryType='section', synthetic=True)


def optimise_html(document, route, aliases):
    """Resolve retained links and reserve image space in the actual final markup."""
    soup = BeautifulSoup(document, 'html.parser')
    for node in soup.select('[href], [src]'):
        attr = 'href' if node.has_attr('href') else 'src'
        value = node[attr]
        parsed = urlsplit(value)
        if node.name == 'a' and parsed.netloc == 'kazumi7884.co.uk':
            value = parsed.path + (('#' + parsed.fragment) if parsed.fragment else '')
        path, sep, fragment = value.partition('#')
        if path in aliases:
            value = aliases[path] + (sep + fragment if sep else '')
        node[attr] = value
        if parsed.scheme and parsed.scheme not in ('http', 'https', 'mailto', 'tel'):
            raise ValueError(f'Unsafe URL in {route}: {value}')
        if node.get('target') == '_blank':
            node['rel'] = ['noopener', 'noreferrer']
    for img in soup.find_all('img'):
        img['decoding'] = 'async'
        img['loading'] = 'lazy'
        path = ROOT / 'static' / img.get('src', '').lstrip('/')
        if path.is_file() and path.suffix.lower() in ('.png', '.webp', '.jpg', '.jpeg'):
            with Image.open(path) as source:
                img['width'], img['height'] = map(str, source.size)
        else:
            if not img.has_attr('width'): img['width'] = '225'
            if not img.has_attr('height'): img['height'] = '320'
        if not img.has_attr('alt'): img['alt'] = ''
    for table in soup.select('.prose table'):
        wrapper = soup.new_tag('div', attrs={'class': 'table-scroll', 'tabindex': '0', 'role': 'region', 'aria-label': 'Scrollable data table'})
        table.wrap(wrapper)
        for th in table.find_all('th'):
            th['scope'] = 'col'
    # Markdown table alignment otherwise emits inline CSS. Move this limited
    # semantic choice into named classes while leaving authored code untouched.
    for cell in soup.select('td[style], th[style]'):
        match = re.fullmatch(r'text-align:\s*(left|center|right);?', cell['style'])
        if match:
            cell['class'] = cell.get('class', []) + ['align-' + match[1]]
            del cell['style']
    for node in soup.select('audio, video'):
        node.attrs.pop('autoplay', None)
        node['controls'] = ''
        node['preload'] = 'none'
    return '<!DOCTYPE html>\n' + str(soup).replace('<!DOCTYPE html>\n', '', 1)


def build():
    started = time.perf_counter()
    config = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
    if not re.fullmatch(r'https://[a-zA-Z0-9.-]+(?::[0-9]+)?', config['url']):
        raise ValueError('site.json url must be an HTTPS origin without a trailing slash')
    pages = read_pages()
    urls = [p['url'] for p in pages]
    if len(urls) != len(set(urls)):
        raise ValueError('Duplicate page URL; choose unique titles/slugs for taxonomy entries')
    aliases = json.loads((ROOT / 'data/legacy-routes.json').read_text(encoding='utf-8')) if (ROOT / 'data/legacy-routes.json').exists() else {}
    for old, new in aliases.items():
        route_path(old)
        if new not in urls:raise ValueError(f'Legacy redirect destination does not exist: {new}')
    for page in pages:
        for alias in page.get('aliases', []):
            route_path(alias)
            if alias in aliases and aliases[alias] != page['url']:
                raise ValueError(f'Alias collision: {alias}')
            if alias not in urls:
                aliases[alias] = page['url']
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / 'static', OUT)
    (OUT / 'assets/css').mkdir(parents=True, exist_ok=True)
    (OUT / 'assets/js').mkdir(parents=True, exist_ok=True)
    assets = {}
    for source in sorted((ROOT / 'assets').rglob('*')):
        if not source.is_file():
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        dest = source.relative_to(ROOT).with_name(source.stem + '.' + digest + source.suffix)
        (OUT / dest).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, OUT / dest)
        assets[source.name] = '/' + dest.as_posix()
    env = Environment(loader=FileSystemLoader(ROOT / 'templates'), autoescape=select_autoescape(['html']))
    env.filters['slug'] = slug
    data = {name: json.loads((ROOT / path).read_text(encoding='utf-8')) for name, path in {
        'steam': 'data/steam.json', 'pc': 'data/pc.json', 'anime': 'static/data/anime.json',
        'ghosts': 'data/phasmophobia/ghosts.json', 'maps': 'data/phasmophobia/maps.json',
        'items': 'data/phasmophobia/items.json', 'general': 'data/phasmophobia/general.json'}.items()}
    posts = sorted([p for p in pages if p['entryType'] == 'post'], key=lambda p: (p['date'], p['url']), reverse=True)
    rendered = []
    for page in pages:
        if page.get('taxonomy'):
            children = [p for p in pages if page['term'] in (p.get(page['taxonomy']) or [])]
        elif page['url'] == '/blog/':
            children = posts
        elif page['url'] in ('/projects/', '/resources/'):
            kind = 'project' if page['url'] == '/projects/' else 'resource'
            children = [p for p in pages if p['entryType'] == kind]
        else:
            children = [p for p in pages if p['url'] != page['url'] and p['url'].startswith(page['url']) and not p['is_section']]
        boards = [p for p in pages if p['is_section'] and p['url'] != page['url'] and
                  p['url'].rstrip('/').rsplit('/', 1)[0] + '/' == page['url']]
        siblings = [p for p in posts if p['url'].rsplit('/', 2)[0] == page['url'].rsplit('/', 2)[0]]
        pos = next((i for i, p in enumerate(siblings) if p['url'] == page['url']), -1)
        crumb_urls = ['/' + '/'.join(page['url'].strip('/').split('/')[:i]) + '/'
                      for i in range(1, len(page['url'].strip('/').split('/')))]
        crumbs = [p for url in crumb_urls for p in pages if p['url'] == url]
        schema = {'@context': 'https://schema.org', '@type': 'BlogPosting' if page['entryType'] == 'post' else 'WebPage',
                  'name': page['title'], 'headline': page['title'], 'description': page['description'],
                  'url': config['url'] + page['url'], 'inLanguage': 'en-GB',
                  'author': {'@type': 'Person', 'name': page.get('author', config['author'])}}
        if page['entryType'] == 'post' and page['date']:
            schema['datePublished'] = page['date']
            schema['dateModified'] = page['lastmod'] or page['date']
        room = ('phasmo' if '/phasmophobia' in page['url'] else 'anime' if page.get('layout') == 'anime'
                else 'games' if page.get('layout') == 'games' else 'journal' if '/writing' in page['url']
                else 'pc' if page.get('layout') == 'pc' else page['section'])
        doc = env.get_template('page.html').render(page=page, pages=pages, config=config, assets=assets,
            data=data, posts=posts, children=sorted(children, key=lambda p:(p['date'],p['title']), reverse=True),
            boards=sorted(boards, key=lambda p:p['title']), crumbs=crumbs, schema=schema, room=room,
            previous=siblings[pos+1] if 0 <= pos < len(siblings)-1 else None,
            following=siblings[pos-1] if pos > 0 else None)
        dest = OUT / route_path(page['url'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(optimise_html(doc, page['url'], aliases), encoding='utf-8')
        rendered.append({'url': page['url'], 'file': dest.relative_to(OUT).as_posix(), 'source': page['source']})
    # Portable aliases also work on hosts without Apache redirect support.
    for old, new in aliases.items():
        dest = OUT / route_path(old)
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f'<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><title>Page moved | Kaz</title><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={html.escape(new)}"><link rel="canonical" href="{config["url"]}{html.escape(new)}"></head><body><a href="{html.escape(new)}">Continue to the page</a></body></html>', encoding='utf-8')
    index = [{'title':p['title'], 'url':p['url'], 'description':p['description'], 'text':p['text'], 'section':p['section']}
             for p in pages if not p.get('noindex') and p.get('searchable', True) and not p['synthetic']]
    (OUT / 'search-index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
    root = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for p in pages:
        if p.get('noindex') or p['url'] == '/search/':continue
        item = ET.SubElement(root, 'url')
        ET.SubElement(item, 'loc').text = config['url'] + p['url']
        if p['lastmod']: ET.SubElement(item, 'lastmod').text = p['lastmod']
    ET.ElementTree(root).write(OUT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for key, value in [('title', config['title']), ('link', config['url']), ('description', config['description']), ('language', 'en-gb')]:
        ET.SubElement(channel, key).text = value
    for p in posts:
        item = ET.SubElement(channel, 'item')
        for key, value in [('title', p['title']), ('link', config['url'] + p['url']), ('guid', config['url'] + p['url']), ('description', p['description'])]:
            ET.SubElement(item, key).text = value
        if p['date']:
            from email.utils import format_datetime
            from datetime import datetime, timezone
            ET.SubElement(item, 'pubDate').text = format_datetime(datetime.fromisoformat(p['date']).replace(tzinfo=timezone.utc))
    ET.ElementTree(rss).write(OUT / 'index.xml', encoding='utf-8', xml_declaration=True)
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {config["url"]}/sitemap.xml\n', encoding='utf-8')
    notfound = env.get_template('404.html').render(config=config, assets=assets)
    (OUT / '404.html').write_text(notfound, encoding='utf-8')
    report = {'pages': rendered, 'aliases': aliases, 'assets': assets, 'seconds': round(time.perf_counter()-started,3)}
    (ROOT / '.cache').mkdir(exist_ok=True)
    (ROOT / '.cache/build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Built {len(pages)} pages and {len(aliases)} legacy redirects in {report["seconds"]}s.')
    return report


def new_post(title, section):
    """Write a draft without ever replacing an existing post."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*', section):
        raise ValueError('Use a section path such as learning/c-sharp/posts')
    name = slug(title)
    if not name: raise ValueError('Use a title containing letters or numbers')
    path = ROOT / 'content' / section / (name + '.md')
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {'title':title, 'description':'Write a short summary here.', 'date':date.today().isoformat(),
                'lastmod':date.today().isoformat(), 'entryType':'post', 'draft':True, 'tags':[]}
    with path.open('x', encoding='utf-8') as stream:
        stream.write('---\n' + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True) + '---\n\n## What I tried\n\n\n## What I learned\n\n\n## Next time\n')
    print(path.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('build','check','package'):commands.add_parser(name)
    preview = commands.add_parser('preview')
    preview.add_argument('--port', type=int, default=8000)
    studio = commands.add_parser('studio')
    studio.add_argument('--port', type=int, default=8000)
    new = commands.add_parser('new')
    new.add_argument('title')
    new.add_argument('--section', default='learning/c-sharp/posts')
    args = parser.parse_args()
    if args.command == 'new':return new_post(args.title, args.section)
    if args.command == 'studio':
        from studio import serve
        return serve(args.port, build)
    build()
    if args.command in ('check','package'):
        from audit import run
        if not run():raise SystemExit(1)
    if args.command == 'preview':
        from functools import partial
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print(f'Preview: http://localhost:{args.port} — Ctrl+C to stop. Rebuild after edits.')
        with http.server.ThreadingHTTPServer(('127.0.0.1',args.port), handler) as server:
            try:server.serve_forever()
            except KeyboardInterrupt:pass
    if args.command == 'package':
        dest = ROOT / 'deploy/site-upload.zip'
        dest.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as archive:
            for source in sorted(OUT.rglob('*')):
                if source.is_file():archive.write(source, source.relative_to(OUT))
        print(dest)


if __name__ == '__main__':
    main()
