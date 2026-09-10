"""Fifty distinct page-level review goals, plus asset and feed integrity checks.

The report counts route/goal checks, not invented feature changes. Each goal
examines every authored route; synthetic archives are also link-crawled.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'


def run():
    report = json.loads((ROOT / '.cache/build.json').read_text())
    config = json.loads((ROOT / 'site.json').read_text())
    documents = {}
    for item in report['pages']:
        raw = (OUT / item['file']).read_text(encoding='utf-8')
        documents[item['url']] = (BeautifulSoup(raw, 'html.parser'), raw, item)
    selected = {url: values for url, values in documents.items() if values[2]['source']}
    titles = Counter(s.title.get_text() if s.title else '' for s, raw, item in selected.values())

    def attr(s, selector, key):
        node = s.select_one(selector)
        return node.get(key, '') if node else ''

    def local_target(value, current):
        target = urlsplit(urljoin(config['url'] + current, value))
        if target.netloc != urlsplit(config['url']).netloc:return None, target
        path = unquote(target.path).lstrip('/')
        dest = OUT / path
        if not dest.suffix:dest = dest / 'index.html'
        return dest, target

    def local_links(s, url):
        for link in s.select('a[href]'):
            target, _ = local_target(link['href'],url)
            if target is not None and not target.is_file():return False
        return True

    def fragments(s, url):
        for link in s.select('a[href]'):
            path, target = local_target(link['href'],url)
            if path is None or not target.fragment or not path.is_file():continue
            dest = documents.get(target.path, (None,))[0]
            if dest is None:dest = BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            if not dest.find(id=unquote(target.fragment)):return False
        return True

    def assets_exist(s,url):
        for node in s.select('[src], link[href]'):
            value = node.get('src',node.get('href',''))
            if node.name == 'link' and 'canonical' in node.get('rel',[]):continue
            path, _ = local_target(value,url)
            if path is not None and not path.is_file():return False
        return True

    def schema(s):
        try:return json.loads(s.select_one('script[type="application/ld+json"]').string)
        except (TypeError,AttributeError,ValueError):return {}

    def named(node):
        return bool(node.get('aria-label') or node.get_text(strip=True) or any(i.get('alt') for i in node.find_all('img')))

    # Each callable receives one parsed page and its source: no repeated network
    # requests or rebuilds just to inflate the number of review passes.
    goals = [
      ('Standards-mode HTML',lambda s,r,u:r.lower().startswith('<!doctype html>')),
      ('British English document language',lambda s,r,u:attr(s,'html','lang')=='en-GB'),
      ('Early UTF-8 declaration',lambda s,r,u:'charset="utf-8"' in r[:1024].lower()),
      ('Mobile viewport without zoom restriction',lambda s,r,u:attr(s,'meta[name="viewport"]','content')=='width=device-width, initial-scale=1'),
      ('Descriptive browser title',lambda s,r,u:s.title and 5<len(s.title.get_text())<160),
      ('Unique authored-page titles',lambda s,r,u:titles[s.title.get_text()]==1),
      ('Nonempty page descriptions',lambda s,r,u:15<=len(attr(s,'meta[name="description"]','content'))<=350),
      ('Single canonical declaration',lambda s,r,u:len(s.select('link[rel="canonical"]'))==1),
      ('Canonical matches the public route',lambda s,r,u:attr(s,'link[rel="canonical"]','href')==config['url']+u),
      ('Explicit indexing policy',lambda s,r,u:attr(s,'meta[name="robots"]','content') in ('index, follow','noindex, follow')),
      ('Social title matches the page',lambda s,r,u:attr(s,'meta[property="og:title"]','content')==s.title.get_text()),
      ('Social description matches the page',lambda s,r,u:attr(s,'meta[property="og:description"]','content')==attr(s,'meta[name="description"]','content')),
      ('Social URL matches the canonical',lambda s,r,u:attr(s,'meta[property="og:url"]','content')==config['url']+u),
      ('Appropriate social page type',lambda s,r,u:attr(s,'meta[property="og:type"]','content') in ('article','website')),
      ('Consistent social site identity',lambda s,r,u:attr(s,'meta[property="og:site_name"]','content')==config['title']),
      ('X title consistency',lambda s,r,u:attr(s,'meta[name="twitter:title"]','content')==s.title.get_text()),
      ('X description consistency',lambda s,r,u:attr(s,'meta[name="twitter:description"]','content')==attr(s,'meta[name="description"]','content')),
      ('Discoverable RSS feed',lambda s,r,u:attr(s,'link[type="application/rss+xml"]','href')=='/index.xml'),
      ('Working favicon reference',lambda s,r,u:attr(s,'link[rel="icon"]','href')=='/favicon.ico' and (OUT/'favicon.ico').is_file()),
      ('One local fingerprinted stylesheet',lambda s,r,u:len(s.select('link[rel="stylesheet"]'))==1 and bool(re.search(r'\.[a-f0-9]{12}\.css$',attr(s,'link[rel="stylesheet"]','href')))),
      ('Deferred enhancement scripts',lambda s,r,u:all(n.has_attr('defer') or 'theme-init.' in n['src'] for n in s.select('script[src]'))),
      ('Executable scripts kept in separate files',lambda s,r,u:all(n.has_attr('src') or n.get('type')=='application/ld+json' for n in s.find_all('script'))),
      ('Valid structured data',lambda s,r,u:schema(s).get('@context')=='https://schema.org'),
      ('Structured data identifies this route',lambda s,r,u:schema(s).get('url')==config['url']+u),
      ('Identified authorship',lambda s,r,u:bool(schema(s).get('author',{}).get('name')) and bool(attr(s,'meta[name="author"]','content'))),
      ('One main landmark',lambda s,r,u:len(s.find_all('main'))==1),
      ('One descriptive top-level heading',lambda s,r,u:len(s.find_all('h1'))==1 and bool(s.h1.get_text(strip=True))),
      ('Keyboard skip target',lambda s,r,u:attr(s,'a.skip-link','href')=='#main-content' and attr(s,'main','id')=='main-content'),
      ('Breadcrumb orientation',lambda s,r,u:u=='/' or bool(s.select_one('nav[aria-label="Breadcrumb"] [aria-current="page"]'))),
      ('Consistent primary menu destinations',lambda s,r,u:[a['href'] for a in s.select('#site-navigation a')]==[p[1] for p in config['navigation']]),
      ('Correct menu current-location state',lambda s,r,u:all(u==a['href'] if a.get('aria-current')=='page' else u.startswith(a['href']) for a in s.select('#site-navigation [aria-current]'))),
      ('Footer recovery navigation',lambda s,r,u:{'/sitemap/','/about/','/index.xml'}.issubset({a['href'] for a in s.select('.site-footer a')})),
      ('Unique HTML identifiers',lambda s,r,u:len([n['id'] for n in s.select('[id]')])==len({n['id'] for n in s.select('[id]')})),
      ('Internal destinations exist',lambda s,r,u:local_links(s,u)),
      ('In-page and cross-page anchors resolve',lambda s,r,u:fragments(s,u)),
      ('Local scripts, styles and media exist',lambda s,r,u:assets_exist(s,u)),
      ('Every form control has a label',lambda s,r,u:all(n.get('aria-label') or (n.get('id') and s.find('label',attrs={'for':n['id']})) for n in s.select('input:not([type="hidden"]),select,textarea'))),
      ('ARIA references resolve',lambda s,r,u:all(s.find(id=ident) for n in s.find_all(True) for key in ('aria-controls','aria-labelledby','aria-describedby') for ident in n.get(key,'').split())),
      ('Links have accessible names',lambda s,r,u:all(named(n) for n in s.select('a[href]'))),
      ('Buttons have names and explicit types',lambda s,r,u:all(named(n) and n.get('type') in ('button','submit','reset') for n in s.find_all('button'))),
      ('Images reserve space and supply alternatives',lambda s,r,u:all(n.has_attr('alt') and int(n.get('width',0))>0 and int(n.get('height',0))>0 for n in s.find_all('img'))),
      ('New-tab links protect the opener',lambda s,r,u:all('noopener' in n.get('rel',[]) for n in s.select('a[target="_blank"]'))),
      ('No executable URL schemes',lambda s,r,u:all(urlsplit(n.get('href',n.get('src',''))).scheme.lower() not in ('javascript','vbscript','data') for n in s.select('[href],[src]'))),
      ('Styles kept outside the markup',lambda s,r,u:not s.select('[style],style')),
      ('Events kept outside the markup',lambda s,r,u:not any(key.lower().startswith('on') for n in s.find_all(True) for key in n.attrs)),
      ('No unsolicited audio or video autoplay',lambda s,r,u:not s.select('audio[autoplay],video[autoplay]')),
      ('No insecure embedded resources',lambda s,r,u:not any(n.get('src','').startswith('http:') for n in s.select('[src]'))),
      ('No unrendered template syntax',lambda s,r,u:not re.search(r'\{\{[<%]|\{%\s*(if|for|block)',r)),
      ('Page payload under 2 MiB',lambda s,r,u:len(r.encode('utf-8'))<2*1024*1024),
      ('Readable content without JavaScript',lambda s,r,u:len(s.main.get_text(' ',strip=True))>100),
    ]
    assert len(goals)==50
    evidence=[]
    for number,(goal,test) in enumerate(goals,1):
        checks=[]
        for url,(soup,raw,item) in selected.items():
            try:passed=bool(test(soup,raw,url));error=''
            except Exception as exc:passed=False;error=str(exc)
            checks.append({'target':url,'passed':passed,**({'error':error} if error else {})})
        failed=[c['target'] for c in checks if not c['passed']]
        evidence.append({'iteration':number,'goal':goal,'targets':len(checks),'passed':len(checks)-len(failed),'failed':failed,'checks':checks})
    extra=[]
    for url,(soup,raw,item) in documents.items():
        if not local_links(soup,url):
            for a in soup.select('a[href]'):
                path,_=local_target(a['href'],url)
                if path is not None and not path.is_file():extra.append(f'{url}: broken link {a["href"]}')
        if not fragments(soup,url):extra.append(f'{url}: unresolved fragment')
    for source in (OUT/'assets/images').rglob('*'):
        if source.suffix.lower() in ('.png','.webp','.jpg','.jpeg'):
            try:
                with Image.open(source) as image:image.verify()
            except Exception as exc:extra.append(f'Invalid image {source.relative_to(OUT)}: {exc}')
    try:
        with Image.open(OUT/'favicon.ico') as image:image.verify()
    except Exception as exc:extra.append(f'Invalid favicon: {exc}')
    for name in ('index.xml','sitemap.xml'):
        try:ET.parse(OUT/name)
        except Exception as exc:extra.append(f'Invalid {name}: {exc}')
    results={'generated':datetime.now(timezone.utc).isoformat(), 'authored_pages':len(selected),
             'total_pages':len(documents),'checks':sum(x['targets'] for x in evidence),
             'passing_checks':sum(x['passed'] for x in evidence),'iterations':evidence,'additional_failures':extra,
             'source_digest':hashlib.sha256((ROOT/'templates/page.html').read_bytes()+(ROOT/'assets/css/site.css').read_bytes()).hexdigest()}
    destination=ROOT/'docs/validation-report.json'
    destination.write_text(json.dumps(results,indent=2),encoding='utf-8')
    lines=['# V5 validation report','',
           'These are 50 automated review goals applied to every authored route. Counts are route/goal checks, not a claim of 1,500 different code changes or 50 human visual redesigns.', '',
           f'Authored routes: {len(selected)}. All generated routes: {len(documents)}. Checks: {results["passing_checks"]}/{results["checks"]}.', '',
           '| Review | Goal | Passed / targets |','| --- | --- | --- |']
    lines += [f'| {i["iteration"]} | {i["goal"]} | {i["passed"]} / {i["targets"]} |' for i in evidence]
    lines += ['', 'The JSON report records every exact route and outcome. Pages without a particular element are checked for absence of violations; this does not invent missing elements to inflate coverage.', '',
              'Static checks do not prove browser rendering, live performance scores, external link availability, game-data accuracy, or Windows execution. Those limits remain explicit.', '', 'Additional failures:', '']
    lines += ['- '+e for e in extra] or ['None.']
    (ROOT/'docs/VALIDATION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for item in evidence:
        if item['failed']:print(item['iteration'],item['goal'],item['failed'][:8])
    for message in extra[:40]:print(message)
    ok=all(not i['failed'] for i in evidence) and not extra
    print(f'{results["passing_checks"]}/{results["checks"]} route/goal checks; {len(extra)} additional failures.')
    return ok


if __name__=='__main__':
    raise SystemExit(0 if run() else 1)
