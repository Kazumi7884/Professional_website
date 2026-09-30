"""Build Kaz's static successor from authored content and reviewed snapshots."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
from html import escape
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import markdown
from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
TRACKS = {"c-sharp": "C# & .NET", "python": "Python & data", "web": "Web development", "security": "Security"}
NAV = [("Home", "/"), ("Work", "/work/"), ("Learning", "/learning/"), ("Journal", "/blog/"), ("Personal", "/personal/"), ("About", "/about/")]


def e(value):
    return escape(str(value), quote=True)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_route(route):
    decoded = unquote(route)
    if not route.startswith("/") or route.startswith("//") or any(c in decoded for c in "\\?#:\x00") or any(part in (".", "..") for part in decoded.split("/")):
        raise ValueError(f"Unsafe route: {route!r}")
    return route


def taxonomy_route(taxonomy, term):
    slug = re.sub(r'[^a-z0-9]+', '-', term.lower()).strip('-')
    if not slug:
        raise ValueError(f"Taxonomy term has no usable URL: {term!r}")
    return f'/{taxonomy}/{slug}/'


def output_path(root, route):
    safe_route(route)
    path = root / route.lstrip("/")
    if route.endswith("/"):
        path /= "index.html"
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Route outside output")
    return path


def content_pages(root=ROOT):
    pages = {}
    for path in sorted((root / "content").rglob("*.md")):
        raw = path.read_text(encoding="utf-8-sig")
        parts = re.split(r"^---\s*$", raw, maxsplit=2, flags=re.M)
        if len(parts) != 3:
            raise ValueError(f"Missing front matter: {path}")
        meta = yaml.safe_load(parts[1])
        if not isinstance(meta, dict) or not isinstance(meta.get("title"), str) or not meta["title"].strip():
            raise ValueError(f"Invalid metadata: {path}")
        if "draft" in meta and not isinstance(meta["draft"], bool):
            raise ValueError(f"Draft must be boolean: {path}")
        if meta.get("draft"):
            continue
        rel = path.relative_to(root / "content").with_suffix("")
        route = "/" + rel.as_posix() + "/"
        if rel.name == "_index":
            route = "/" + rel.parent.as_posix().strip(".") + "/"
            route = route.replace("//", "/")
        safe_route(route)
        if route in pages:
            raise ValueError(f"Duplicate route: {route}")
        pages[route] = {"title": meta["title"], "description": meta.get("description", ""), "body": parts[2].strip(), "meta": meta, "source": path.relative_to(root).as_posix()}
    return pages


def render_markdown(body):
    # Raw authored HTML is treated as text; only Markdown generates elements.
    renderer = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "sane_lists"])
    renderer.preprocessors.deregister('html_block')
    renderer.inlinePatterns.deregister('html')
    rendered = renderer.convert(body)
    soup = BeautifulSoup(rendered, "html.parser")
    for node in soup.select('[style]'):
        del node['style']
    for tag in soup.find_all(["a", "img"]):
        attr = "href" if tag.name == "a" else "src"
        url = tag.get(attr, "")
        if urlsplit(url).scheme not in ("", "https", "http", "mailto") or url.startswith("//"):
            del tag[attr]
        if tag.name == "img":
            tag["loading"] = "lazy"
            tag["decoding"] = "async"
            candidate = ROOT / "static" / url.lstrip("/")
            if candidate.is_file() and candidate.resolve().is_relative_to((ROOT / "static").resolve()):
                with Image.open(candidate) as image:
                    tag["width"], tag["height"] = image.size
    for table in soup.find_all("table"):
        wrapper = soup.new_tag("div", attrs={"class": "table-wrap", "tabindex": "0", "role": "region", "aria-label": "Scrollable table"})
        table.wrap(wrapper)
    return str(soup)


def link(route, title, cls=""):
    return f'<a href="{e(route)}"' + (f' class="{e(cls)}"' if cls else "") + f'>{e(title)}</a>'


def section(title, number=""):
    return f'<div class="section-head"><h2>{e(title)}</h2><span>{e(number)}</span></div>'


def topic(route, page):
    stamp = str(page.get("meta", {}).get("date", ""))
    return f'<li class="topic"><div class="meta">{e(stamp or "Workshop")}</div><div><h3>{link(route, page["title"])}</h3><p>{e(page.get("description", ""))}</p></div></li>'


def topic_list(items):
    return '<ul class="topics">' + "".join(topic(route, page) for route, page in items) + "</ul>"


def progress(course):
    value = course["progress"]
    if value is None:
        return '<div class="progress">Not started<span class="status"><br>Udemy: Start course</span></div>'
    return f'<div class="progress"><b>{value}% complete</b><progress max="100" value="{value}" aria-label="{e(course["title"])} completion">{value}%</progress><span class="status">Udemy snapshot</span></div>'


def course_rows(courses):
    return '<ul class="course-list">' + "".join(f'<li class="course"><div><h3>{link("/learning/courses/" + c["slug"] + "/", c["title"])}</h3><p>{e(c["instructors"])}</p><p class="meta">{e(" · ".join(c["topics"]))}</p></div>{progress(c)}</li>' for c in courses) + '</ul>'


def profile():
    return '<aside class="profile" aria-label="About Kaz"><div class="profile-head"><p class="profile-kicker">profile</p><h2>Kaz</h2><p>Computing graduate. Still learning.</p></div><div class="profile-body"><dl><dt>Currently here for</dt><dd>C#, console apps and writing things down properly.</dd><dt>Also around</dt><dd>Games, anime and whatever I decide to write about.</dd></dl>' + link('/about/', 'A little about me') + '<br>' + link('https://github.com/Kazumi7884', 'Find me on GitHub') + '</div></aside>'


def filters(label):
    return f'<div class="filter"><label for="filter-input">{e(label)}</label><input id="filter-input" type="search" data-filter placeholder="Type to filter"><p class="meta" data-filter-status role="status"></p></div>'


def records(data):
    if isinstance(data, dict) and 'categories' in data:
        data = [item for category in data['categories'] for item in category['items']]
    out = []
    for item in data:
        title = item.get("name", item.get("title", "Reference"))
        pieces = [f'<article class="record" data-record><h3>{e(title)}</h3>']
        for key, value in item.items():
            if key in {"name", "title", "id", "image", "url"} or value in (None, "", [], {}):
                continue
            label = re.sub(r"([a-z])([A-Z])", r"\1 \2", key).replace("_", " ").capitalize()
            if isinstance(value, list):
                pieces.append(f'<details><summary>{e(label)}</summary><ul>' + ''.join(f'<li>{e(v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False))}</li>' for v in value) + '</ul></details>')
            elif not isinstance(value, dict):
                pieces.append(f'<p><b>{e(label)}:</b> {e(value)}</p>')
        if item.get("url", "").startswith("https://"):
            pieces.append(link(item["url"], 'Source page'))
        pieces.append('</article>')
        out.append(''.join(pieces))
    return '<div class="records">' + ''.join(out) + '</div><p class="empty" data-filter-empty hidden>No entries match. Try a shorter term or clear the filter.</p>'


def make_site():
    pages = content_pages()
    courses = read_json(HERE / "courses.json")
    projects = read_json(HERE / "projects.json")["projects"]
    repository_snapshot = read_json(HERE / 'repositories.json')
    for c in courses["courses"]:
        if c["progress"] is not None and (type(c["progress"]) is not int or not 0 <= c["progress"] <= 100):
            raise ValueError("Invalid progress")
    posts = [(r, p) for r, p in pages.items() if p["meta"].get("entryType") == "post"]
    notes = [(r, p) for r, p in posts if r.startswith('/learning/')]
    journal = [(r, p) for r, p in posts if r.startswith('/personal/')]
    bodies = {}

    def add(route, title, description, body):
        pages[route] = {"title": title, "description": description, "body": "", "meta": {}}
        bodies[route] = body

    def related(routes):
        return topic_list([(r, pages[r]) for r in routes]) if routes else '<p class="empty">No authored notes published for this course yet.</p>'

    def project_list(items):
        return topic_list([('/work/projects/' + p['slug'] + '/', {'title': p['title'], 'description': p['summary']}) for p in items])

    def repository_updates():
        rows = []
        for fact in repository_snapshot['repositories']:
            pushed = fact.get('pushed_at') or 'not recorded'
            rows.append('<li class="topic"><div class="meta">last push<br>' + e(pushed[:10]) + '</div><div><h3>' + link(fact['html_url'], fact['full_name']) + '</h3><p>' + e(fact.get('description') or 'No description recorded.') + '</p><p class="meta">' + e(fact.get('language') or 'Language not recorded') + ' · licence: ' + e(fact.get('license') or 'unknown') + '</p></div></li>')
        return '<p class="snapshot">Repository facts last checked ' + e(repository_snapshot['observed_at'][:10]) + '. This is a dated public snapshot, not a live activity feed.</p><ul class="topics">' + ''.join(rows) + '</ul>'

    for taxonomy in ('tags', 'categories'):
        terms = sorted({str(term) for p in pages.values() for term in (p['meta'].get(taxonomy) or [])})
        term_pages = []
        routes = {}
        for term in terms:
            route = taxonomy_route(taxonomy, term)
            if route in routes:
                raise ValueError(f"Taxonomy URL collision: {routes[route]!r} and {term!r} both use {route}")
            routes[route] = term
            matches = [(r, p) for r, p in pages.items() if term in (p['meta'].get(taxonomy) or [])]
            add(route, term, 'Entries filed under ' + term + '.', '<h1>' + e(term) + '</h1>' + topic_list(matches))
            term_pages.append((route, pages[route]))
        add('/' + taxonomy + '/', taxonomy.title(), 'Browse the notebook by ' + taxonomy + '.', '<h1>' + taxonomy.title() + '</h1>' + topic_list(term_pages))

    home = '<div class="home-grid"><div><div class="welcome"><p class="eyebrow">welcome to my corner of the internet</p><h1>Hi, I’m Kaz.</h1><p>This is where I keep the learning side and the personal side together. There are notes, projects, games, and posts about whatever is going on.</p></div><div class="split-door"><section><h2>Work &amp; learning</h2><p>Courses, C# notes and the work I can actually point to.</p>' + link('/work/', 'See work and learning') + '</section><section><h2>Personal stuff</h2><p>Posts, game notes, anime and things I want to keep around.</p>' + link('/personal/', 'Go to the personal side') + '</section></div>' + section('Latest learning notes', 'learning') + topic_list(notes[:2]) + '</div>' + profile() + '</div>'
    home += section('Recent personal posts', 'journal') + topic_list(journal)
    add('/', 'Kaz · personal site and learning notes', 'Learning notes, practical work and personal posts by Kaz.', home)
    add('/work/', 'Work and learning', 'Practical work, source evidence and learning context.', '<div class="intro"><p class="eyebrow">the professional side</p><h1>Work and learning</h1><p>This is the part where I keep the source, what I did, and what I still need to work on in the same place.</p></div><div class="work-grid"><div>' + section('Things I have made', 'evidence') + project_list(projects) + section('Notes from learning', 'written work') + topic_list(notes) + '</div><aside class="aside"><h2>What I’m focusing on</h2><p>C# is where I have the most written work so far. I am also working through Python, web development and security courses.</p>' + link('/work/skills/', 'Skills and evidence') + '<h2>Repository updates</h2><p>Public repository facts are checked separately from the write-ups.</p>' + link('/work/repository-updates/', 'See the latest snapshot') + '<h2>Background</h2><p>MSc Computing and Information Systems, completed in 2024.</p>' + link('/about/', 'Read my background') + '</aside></div>')
    tracks = '<nav class="track-nav" aria-label="Learning tracks">' + ''.join(link('/learning/' + k + '/', v) for k, v in TRACKS.items()) + '</nav>'
    snapshot = f'<p class="snapshot">Owned Udemy courses, observed {e(courses["observed_at"])}. Completion is course progress, not a skill rating. This is a saved snapshot.</p>'
    bodies['/learning/'] = '<div class="intro"><h1>The learning notebook</h1><p>Course study, the notes I’ve written, and the practical work that connects them.</p></div>' + tracks + section('Start with the written work') + topic_list(notes) + section('On my course shelf') + snapshot + course_rows(courses['courses'])
    for key, name in TRACKS.items():
        relevant = [c for c in courses['courses'] if c['track'] == key]
        note_routes = list(dict.fromkeys(r for c in relevant for r in c['notes']))
        work = [p for p in projects if p['track'] == key]
        description = 'Study context and published evidence for ' + name + '.'
        body = f'<div class="intro"><h1>{e(name)}</h1><p>{e(description)}</p></div>' + tracks + section('Owned courses') + snapshot + course_rows(relevant) + section('Authored notes & related practice') + related(note_routes)
        if work:
            body += section('Related work') + project_list(work)
        if key == 'c-sharp':
            body += '<details><summary>Original notebook introduction</summary>' + render_markdown(pages['/learning/c-sharp/']['body']) + '</details>'
            bodies['/learning/c-sharp/'] = body
        else:
            add('/learning/' + key + '/', name, description, body)
    add('/learning/courses/', 'Course shelf', 'Verified owned courses and dated Udemy progress.', '<h1>Course shelf</h1>' + snapshot + tracks + course_rows(courses['courses']))
    for c in courses['courses']:
        work = [p for p in projects if p['slug'] in c['projects']]
        body = f'<div class="intro"><p class="meta">Owned course · {e(TRACKS[c["track"]])}</p><h1>{e(c["title"])}</h1><p>{e(c["instructors"])}</p></div>' + progress(c) + snapshot + f'<p>{e(c["relationship"])}</p><div class="actions">' + link('https://www.udemy.com/course-dashboard-redirect/?course_id=' + c['id'], 'Open this course on Udemy', 'button') + link('/learning/' + c['track'] + '/', 'Back to ' + TRACKS[c['track']]) + '</div>' + section('Connected notes') + related(c['notes'])
        if work:
            body += section('Related practice') + project_list(work)
        body += '<p class="meta">Connections describe shared topics. They do not certify mastery or claim this work was submitted for the course.</p>'
        add('/learning/courses/' + c['slug'] + '/', c['title'], c['relationship'], body)
    for p in projects:
        body = f'<div class="intro"><p class="meta">{e(p["kind"])}</p><h1>{e(p["title"])}</h1><p>{e(p["summary"])}</p></div><div class="work-grid"><div><h2>What the evidence shows</h2><p>{e(p["contribution"])}</p><h2>Scope & limitations</h2><p>{e(p["limitations"])}</p><div class="actions">' + link(p['source'], 'Read the source evidence', 'button') + '</div>' + section('Related notebook entries') + related(p['evidence']) + '</div><aside class="aside"><h2>Study connections</h2><p>Related subjects, not a claim that the work came from a course.</p>' + course_rows([c for c in courses['courses'] if c['slug'] in p['courses']]) + '</aside></div>'
        fact = next((row for row in repository_snapshot['repositories'] if row['full_name'] == p.get('repo')), None)
        if fact:
            body += '<p class="snapshot">GitHub facts observed ' + e(repository_snapshot['observed_at'][:10]) + ': primary language ' + e(fact['language']) + '; last repository push ' + e(fact['pushed_at'][:10]) + '. This date is repository activity, not a measure of current proficiency.</p>'
        add('/work/projects/' + p['slug'] + '/', p['title'], p['summary'], body)
    add('/work/skills/', 'Skills & evidence', 'Documented practice separated from course study.', '<h1>Skills &amp; evidence</h1><p>Follow the written work to see what has been practised. Course ownership and progress are shown separately.</p>' + section('Documented practice') + topic_list([('/learning/c-sharp/', {'title': 'C# console input, output & strings', 'description': 'Two lessons and a console-app overview, plus separate object-oriented coursework.'}), ('/work/projects/steam-study/', {'title': 'Python & data visualisation', 'description': 'An authored Steam study with saved charts; reproducibility is not verified.'})]) + section('Course study') + tracks + snapshot + course_rows(courses['courses']))
    add('/work/repository-updates/', 'Repository updates', 'Reviewed public repository facts.', '<div class="intro"><p class="eyebrow">public repository snapshot</p><h1>Repository updates</h1><p>This is the practical record of what the selected public repositories have done recently. It does not try to turn a push date into a skill claim.</p></div>' + repository_updates() + '<div class="actions">' + link('https://github.com/Kazumi7884', 'Open my GitHub', 'button') + link('/work/', 'Back to work and learning') + '</div>')
    bodies['/blog/'] = '<div class="intro"><p class="eyebrow">posts from both sides of the site</p><h1>The journal</h1><p>Learning entries and personal posts, all in one place.</p></div>' + topic_list(posts)
    bodies['/personal/'] = '<div class="home-grid"><div><div class="intro"><p class="eyebrow">the non-professional bit</p><h1>My corner of the web.</h1><p>Games, anime, field notes and somewhere to start writing again.</p></div>' + section('Journal entries', 'posts') + topic_list(journal) + section('The shelves', 'stuff I keep track of') + topic_list([(r, pages[r]) for r in ['/personal/games/', '/personal/anime/', '/personal/misc/phasmophobia/', '/personal/reviews/', '/setup/']]) + '</div>' + profile() + '</div>'
    bodies['/personal/misc/writing/'] = '<h1>Personal writing</h1>' + topic_list(journal)
    add('/personal/misc/writing/posts/', 'Personal posts', 'All authored personal posts.', '<h1>Personal posts</h1>' + topic_list(journal))
    bodies['/learning/c-sharp/posts/'] = '<h1>C# notebook entries</h1>' + topic_list(notes)
    steam = read_json(ROOT / 'data/steam.json')
    bodies['/personal/games/'] = '<h1>Games &amp; Steam</h1><p>Saved charts from my Steam library. The original article explains the data and tools.</p><p class="snapshot">Offline snapshot carried forward from V5. No live Steam connection.</p>' + link('/personal/misc/writing/posts/steam-viz/', 'Read the full Steam study') + filters('Find a chart') + '<div class="records">' + ''.join(f'<figure class="record" data-record><figcaption><h2>{e(c["title"])}</h2><p>{e(c["description"])}</p></figcaption>{render_markdown("![" + c["alt"] + "](" + c["image"] + ")")}</figure>' for c in steam['charts']) + '</div><p class="empty" data-filter-empty hidden>No charts match. Clear the filter to show all charts.</p>'
    anime = read_json(ROOT / 'static/data/anime.json')
    bodies['/personal/anime/'] = '<h1>The anime shelf</h1><p class="snapshot">MyAnimeList snapshot from ' + e(anime['syncedAt'][:10]) + '. This list is not live.</p>' + filters('Find an anime or status') + records(anime['items'])
    for kind in ['ghosts', 'items', 'maps']:
        route = '/personal/misc/phasmophobia/' + kind + '/'
        bodies[route] = '<h1>' + e(pages[route]['title']) + '</h1>' + render_markdown(pages[route]['body']) + '<p class="snapshot">Saved personal reference from V5. Game updates may change these details.</p>' + filters('Filter ' + kind + ' and notes') + records(read_json(ROOT / ('data/phasmophobia/' + kind + '.json')))
    guide = '/personal/misc/phasmophobia/'
    bodies[guide] = '<h1>Phasmophobia field notes</h1>' + render_markdown(pages[guide]['body']) + topic_list([(guide + k + '/', pages[guide + k + '/']) for k in ['ghosts', 'items', 'maps', 'general-info', 'cursed-possessions']])
    general = read_json(ROOT / 'data/phasmophobia/general.json')
    bodies[guide + 'general-info/'] = '<h1>General investigation notes</h1>' + render_markdown(pages[guide + 'general-info/']['body']) + '<p class="snapshot">Saved V5 reference; not checked against the current game version.</p>' + records(general['sections'])
    add('/offline.html', 'You are offline', 'Saved pages remain available offline.', '<h1>You’re offline.</h1><p>Pages you have already visited may be available. Reconnect to load an unsaved page.</p>' + link('/', 'Try the saved home page', 'button'))
    add('/search/', 'Search the notebook', 'Search published pages and authored notes.', '<h1>Search the notebook</h1><form class="search-form" id="search-form" role="search"><label class="sr-only" for="query">Search published pages</label><input id="query" name="q" type="search" placeholder="Try C#, strings or Steam"><button type="submit">Search</button><button type="reset">Clear</button></form><p id="search-status" role="status">Enter a word or topic to search.</p><button id="search-retry" hidden>Retry loading search</button><ul class="search-results" id="search-results"></ul><noscript><p>Interactive search needs JavaScript. You can browse every page in the <a href="/sitemap/">site directory</a>.</p></noscript>')
    add('/404.html', 'Page not found', 'Find your way back to the notebook.', '<h1>This page isn’t here.</h1><p>The address may have changed. The directory and search can help you find the original entry.</p><div class="actions">' + link('/', 'Back to home', 'button') + link('/search/', 'Search the notebook') + link('/sitemap/', 'Browse all pages') + '</div>')
    bodies['/sitemap/'] = '<h1>Site directory</h1>' + topic_list([(r, p) for r, p in pages.items() if r not in ['/sitemap/', '/404.html']])
    for route, page in pages.items():
        if route in bodies:
            continue
        body = render_markdown(page['body'])
        if page['meta'].get('entryType') == 'post':
            bodies[route] = '<div class="article-frame"><aside class="author-gutter"><b>Kaz</b><p>From the notebook</p><p>' + e(page['meta'].get('date', '')) + '</p>' + link('/about/', 'About the author') + '</aside><article class="article"><h1>' + e(page['title']) + '</h1>' + body + '<div class="actions">' + link('/blog/', 'All journal entries') + link('/learning/' if route.startswith('/learning/') else '/personal/', 'Back to this section') + '</div></article></div>'
        else:
            bodies[route] = '<article class="article"><h1>' + e(page['title']) + '</h1>' + body + '</article>'
    return pages, bodies


def frame(route, page, body, origin):
    def nav():
        return ''.join(f'<a href="{r}"' + (' aria-current="page"' if route == r else '') + f'>{label}</a>' for label, r in NAV)
    canonical = origin.rstrip('/') + route
    robots = '<meta name="robots" content="noindex">' if page.get('meta', {}).get('noindex') or route in ('/404.html', '/offline.html') else ''
    return f'''<!doctype html>
<html lang="en" data-theme="balanced"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(page['title'])} | Kaz</title><meta name="description" content="{e(page['description'])}">{robots}<link rel="canonical" href="{e(canonical)}"><link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/v6/site.css"><script src="/v6/theme.js"></script><script src="/v6/site.js" defer></script><link rel="alternate" type="application/rss+xml" title="Kaz’s journal" href="/feed.xml"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="masthead"><div class="shell"><div class="mastrow"><a href="/" class="brand"><b>Kaz.</b><span>personal posts + learning notes</span></a><div class="theme-control"><label for="theme">Theme</label><select id="theme"><option value="balanced">Forum</option><option value="forerunner">Forerunner</option><option value="resident">Umbrella</option></select></div></div><div class="navrow"><nav class="primary" aria-label="Main navigation">{nav()}</nav><details class="mobile-nav"><summary>Menu</summary><nav aria-label="Mobile navigation">{nav()}</nav></details><a class="search-link" href="/search/">Search</a></div></div></header><div class="shell"><div class="breadcrumb">{link('/', 'Kaz’s site')} / {e('Home' if route == '/' else page['title'])}</div><main class="page" id="main" tabindex="-1">{body}</main></div><footer class="footer"><div class="shell"><div>Kaz’s site<br>Personal posts. Learning notes. Work I can point to.</div><div>{link('/sitemap/', 'Site directory')}{link('/about/', 'About')}{link('/feed.xml', 'RSS feed')}{link('https://github.com/Kazumi7884', 'GitHub')}</div></div></footer></body></html>'''


def check(output):
    errors = []
    documents = {p: BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser') for p in output.rglob('*.html')}
    checked = 0
    for path, soup in documents.items():
        for node in soup.select('[href], [src]'):
            url = node.get('href', node.get('src', ''))
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            target = output_path(output, parsed.path) if parsed.path.startswith('/') else (path if not parsed.path else path.parent / parsed.path)
            if target.is_dir():
                target /= 'index.html'
            checked += 1
            if not target.exists():
                errors.append(f'{path.relative_to(output)}: missing {url}')
            elif parsed.fragment and target in documents and not documents[target].find(id=unquote(parsed.fragment)):
                errors.append(f'{path.relative_to(output)}: missing anchor {url}')
        if soup.select('[style],script:not([src])'):
            errors.append(f'{path}: inline CSS/JS')
    if errors:
        raise ValueError('\n'.join(errors))
    return {'html_documents': len(documents), 'internal_references_checked': checked}


def build(output=ROOT / 'build', origin=None):
    origin = origin or read_json(ROOT / 'site.json')['url']
    if urlsplit(origin).scheme not in ('https', 'http') or not urlsplit(origin).netloc:
        raise ValueError('Origin must be an absolute HTTP(S) URL')
    pages, bodies = make_site()
    output = Path(output).resolve()
    if output in (ROOT.resolve(), HERE.resolve()) or not output.is_relative_to(ROOT.resolve()):
        raise ValueError('Output must be a build directory inside the repository')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.v6-build-', dir=output.parent) as temp:
        staging = Path(temp)
        shutil.copytree(ROOT / 'static/assets/images', staging / 'assets/images')
        shutil.copy2(ROOT / 'static/favicon.ico', staging / 'favicon.ico')
        (staging / 'v6').mkdir()
        for name in ['site.css', 'site.js', 'theme.js']:
            shutil.copy2(HERE / name, staging / 'v6' / name)
        index = []
        aliases = read_json(ROOT / 'data/legacy-routes.json')
        aliases['/search.html'] = '/search/'
        for route, page in pages.items():
            path = output_path(staging, route)
            path.parent.mkdir(parents=True, exist_ok=True)
            html = frame(route, page, bodies[route], origin)
            path.write_text(html, encoding='utf-8')
            if route not in ('/404.html', '/offline.html', '/search/', '/sitemap/') and not page['meta'].get('noindex') and page['meta'].get('searchable', True):
                text = BeautifulSoup(bodies[route], 'html.parser').get_text(' ', strip=True)
                index.append({'title': page['title'], 'url': route, 'summary': page['description'], 'text': text, 'tags': page['meta'].get('tags') or []})
            for alias in page['meta'].get('aliases') or []:
                if alias != route and alias not in pages:
                    aliases[alias] = route
        redirects = []
        for alias, target in aliases.items():
            if target not in pages:
                raise ValueError('Alias target missing: ' + target)
            if alias in pages or output_path(staging, alias).exists():
                continue
            path = output_path(staging, alias)
            path.parent.mkdir(parents=True, exist_ok=True)
            page = {'title': 'Page moved', 'description': 'This entry has a new address.'}
            path.write_text(frame(target, page, '<h1>This entry has moved.</h1>' + link(target, 'Read the entry at its current address', 'button'), origin), encoding='utf-8')
            redirects.append(f'{alias} {target} 301')
        (staging / '_redirects').write_text('\n'.join(redirects), encoding='utf-8')
        base_htaccess = (ROOT / 'static' / '.htaccess').read_text(encoding='utf-8').rstrip()
        generated_redirects = '\n'.join('Redirect 301 ' + row.rsplit(' ', 1)[0] for row in redirects)
        (staging / '.htaccess').write_text(base_htaccess + ('\n' + generated_redirects if generated_redirects else '') + '\n', encoding='utf-8')
        (staging / 'search-index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
        rss = ET.Element('rss', version='2.0'); channel = ET.SubElement(rss, 'channel')
        for key, value in [('title', 'Kaz’s journal'), ('link', origin), ('description', 'Authored learning and personal notes')]:
            ET.SubElement(channel, key).text = value
        for route, page in pages.items():
            if page['meta'].get('entryType') == 'post':
                item = ET.SubElement(channel, 'item')
                for key, value in [('title', page['title']), ('link', origin.rstrip('/') + route), ('guid', origin.rstrip('/') + route), ('description', page['description'])]:
                    ET.SubElement(item, key).text = value
        ET.ElementTree(rss).write(staging / 'feed.xml', encoding='utf-8', xml_declaration=True)
        sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for route in pages:
            if route not in ('/404.html', '/offline.html') and not pages[route]['meta'].get('noindex'):
                ET.SubElement(ET.SubElement(sitemap, 'url'), 'loc').text = origin.rstrip('/') + route
        ET.ElementTree(sitemap).write(staging / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
        (staging / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + origin.rstrip('/') + '/sitemap.xml\n', encoding='utf-8')
        digest = hashlib.sha256(''.join(bodies.values()).encode() + (HERE / 'site.js').read_bytes() + (HERE / 'site.css').read_bytes()).hexdigest()[:16]
        (staging / 'sw.js').write_text((HERE / 'worker.js').read_text(encoding='utf-8').replace('__BUILD__', digest), encoding='utf-8')
        report = check(staging)
        if output.exists() and not (output / 'build-info.json').is_file():
            raise ValueError('Refusing to replace an unmarked directory')
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staging, output)
    report['canonical_pages'] = len(pages)
    report['css_js_bytes'] = sum((HERE / n).stat().st_size for n in ['site.css', 'site.js', 'theme.js'])
    (output / 'build-info.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build')
    parser.add_argument('--origin')
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.origin), indent=2))

