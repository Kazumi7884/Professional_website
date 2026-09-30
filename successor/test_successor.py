import contextlib
from functools import partial
from http.server import ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


builder = module('build')
refresh = module('refresh')
serve = module('serve')
local_review = module('local_review')


class PublishedJourneys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = builder.build()
        cls.pages, _ = builder.make_site()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(serve.Preview, directory=str(builder.ROOT / 'build')))
        cls.server.RequestHandlerClass.func.log_message = lambda *args: None
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.origin = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def test_unknown_url_recovers_with_real_404(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(self.origin + '/missing-entry/')
        self.assertEqual(caught.exception.code, 404)
        soup = BeautifulSoup(caught.exception.read(), 'html.parser')
        self.assertIsNotNone(soup.select_one('main a[href="/search/"]'))

    def test_every_internal_link_and_anchor_resolves(self):
        self.assertGreater(builder.check(builder.ROOT / 'build')['internal_references_checked'], 100)

    def test_private_authoring_files_are_not_served(self):
        for route in ['/successor/courses.json', '/content/about.md', '/.git/config', '/tools/studio.py', '/successor/projects.json']:
            with self.subTest(route=route), self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(self.origin + route)
            self.assertEqual(caught.exception.code, 404)

    def test_published_index_excludes_private_and_noindex_pages(self):
        with urllib.request.urlopen(self.origin + '/search-index.json') as response:
            urls = {row['url'] for row in json.load(response)}
        self.assertNotIn('/writing/', urls)
        self.assertNotIn('/404.html', urls)
        self.assertIn('/learning/courses/c-sharp-masterclass/', urls)


def journey(route, title):
    def test(self):
        with urllib.request.urlopen(self.origin + route) as response:
            self.assertEqual(response.status, 200)
            soup = BeautifulSoup(response.read(), 'html.parser')
        self.assertEqual(len(soup.select('main h1')), 1)
        self.assertIn(title, soup.title.get_text())
        for anchor in soup.select('nav a,main a[href^="/"]'):
            with urllib.request.urlopen(self.origin + anchor['href']) as target:
                self.assertEqual(target.status, 200)
    return test


for number, (route, page) in enumerate(builder.make_site()[0].items()):
    setattr(PublishedJourneys, f'test_route_{number:03d}_{route.strip("/").replace("/", "_") or "home"}', journey(route, page['title']))


class ContentSafety(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'content').mkdir()
            (root / 'content/note.md').write_text(text, encoding='utf-8')
            return builder.content_pages(root)

    def test_draft_is_not_published(self):
        self.assertEqual(self.parse('---\ntitle: Secret\ndraft: true\n---\nPrivate'), {})

    def test_published_post_appears(self):
        self.assertIn('/note/', self.parse('---\ntitle: New note\ndraft: false\n---\nActual body'))

    def test_removed_post_disappears(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'content').mkdir()
            path = root / 'content/note.md'; path.write_text('---\ntitle: New\n---\nBody')
            self.assertIn('/note/', builder.content_pages(root))
            path.unlink()
            self.assertEqual(builder.content_pages(root), {})

    def test_body_is_preserved(self):
        text = 'My prose — my punctuation.\n\n```csharp\nConsole.WriteLine("Kaz");\n```'
        self.assertEqual(self.parse('---\ntitle: Voice\n---\n' + text)['/note/']['body'], text)

    def test_code_renders_as_code(self):
        soup = BeautifulSoup(builder.render_markdown('```csharp\nif (a < 2) { }\n```'), 'html.parser')
        self.assertEqual(soup.code.get_text().strip(), 'if (a < 2) { }')

    def test_broken_link_fails_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'index.html').write_text('<a href="/absent/">Missing</a>')
            with self.assertRaises(ValueError): builder.check(root)

    def test_missing_fragment_fails_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'index.html').write_text('<a href="#absent">Missing</a>')
            with self.assertRaises(ValueError): builder.check(root)

    def test_existing_fragment_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'index.html').write_text('<a href="#note">Read</a><h1 id="note">Note</h1>')
            self.assertEqual(builder.check(root)['internal_references_checked'], 1)

    def test_unsafe_build_destination_refused(self):
        with self.assertRaises(ValueError): builder.build(builder.ROOT)

    def test_unmarked_output_preserved(self):
        with tempfile.TemporaryDirectory(dir=builder.ROOT) as temp:
            path = Path(temp); (path / 'precious.txt').write_text('Keep me')
            with self.assertRaises(ValueError): builder.build(path)
            self.assertEqual((path / 'precious.txt').read_text(), 'Keep me')

    def test_failed_render_preserves_last_build(self):
        builder.build()
        home = builder.ROOT / 'build/index.html'
        previous = home.read_bytes()
        with patch.object(builder, 'make_site', side_effect=ValueError('fixture')):
            with self.assertRaises(ValueError): builder.build()
        self.assertEqual(home.read_bytes(), previous)


for number, text in enumerate(['body without metadata', '---\ntitle: ""\n---\nBody', '---\ntitle: 5\n---\nBody', '---\n[]\n---\nBody', '---\ntitle: Test\ndraft: "false"\n---\nBody', '---\ntitle: Test\ndraft: 1\n---\nBody']):
    def invalid(self, value=text):
        with self.assertRaises(ValueError): self.parse(value)
    setattr(ContentSafety, f'test_invalid_metadata_{number}', invalid)

for number, route in enumerate(['../escape', '//elsewhere', '/a/../b/', '/%2e%2e/x/', '/a\\b/', '/a?x/', '/a#x/', '/C:/data/', '/a\x00b/', '/a/./b/', '/%5csecret/', '/a%3Ab/']):
    def reject(self, value=route):
        with self.assertRaises(ValueError): builder.safe_route(value)
    setattr(ContentSafety, f'test_route_boundary_{number}', reject)

for number, body in enumerate(['<script>alert(1)</script>', '<img src=x onerror=alert(1)>', '[bad](javascript:alert%281%29)', '[bad](data:text/html,hi)', '[bad](vbscript:evil)', '<iframe src="https://example.org"></iframe>', '<svg onload=alert(1)></svg>', '[bad](//example.org)', '<a onclick="x()">x</a>', '<style>body{display:none}</style>']):
    def sanitize(self, value=body):
        soup = BeautifulSoup(builder.render_markdown(value), 'html.parser')
        self.assertFalse(soup.select('script,iframe,svg,style,[onclick],[onerror],[onload]'))
        for anchor in soup.select('[href]'):
            self.assertFalse(anchor['href'].startswith(('javascript:', 'data:', 'vbscript:', '//')))
    setattr(ContentSafety, f'test_markdown_safety_{number}', sanitize)


class SnapshotSafety(unittest.TestCase):
    name = 'Kazumi7884/space-invaders-0.1-coursework-upload'

    def data(self):
        return {'private': False, 'full_name': self.name, 'html_url': 'https://github.com/' + self.name, 'language': 'C#', 'license': None}

    def test_public_facts_do_not_leak_extra_fields(self):
        data = self.data() | {'token': 'fixture-secret', 'permissions': {'admin': True}}
        result = refresh.public_snapshot(self.name, data)
        self.assertNotIn('token', result); self.assertNotIn('permissions', result)

    def test_unknown_license_stays_unknown(self):
        self.assertIsNone(refresh.public_snapshot(self.name, self.data())['license'])

    def test_private_repo_rejected(self):
        with self.assertRaises(ValueError): refresh.public_snapshot(self.name, self.data() | {'private': True})

    def test_missing_visibility_rejected(self):
        data = self.data(); del data['private']
        with self.assertRaises(ValueError): refresh.public_snapshot(self.name, data)

    def test_mismatched_repository_rejected(self):
        with self.assertRaises(ValueError): refresh.public_snapshot(self.name, self.data() | {'full_name': 'Other/Repo'})

    def test_untrusted_destination_rejected(self):
        with self.assertRaises(ValueError): refresh.public_snapshot(self.name, self.data() | {'html_url': 'https://elsewhere.test'})

    def test_failure_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'facts.json'; path.write_text('last good snapshot')
            def offline(name): raise OSError('Offline fixture')
            with self.assertRaises(OSError): refresh.refresh(path, offline)
            self.assertEqual(path.read_text(), 'last good snapshot')

    def test_refresh_updates_facts_only(self):
        original = (HERE / 'projects.json').read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'facts.json'
            refresh.refresh(path, lambda name: self.data())
            self.assertEqual(json.loads(path.read_text())['repositories'][0]['language'], 'C#')
        self.assertEqual((HERE / 'projects.json').read_bytes(), original)


class LocalReviewSafety(unittest.TestCase):
    def test_prompt_marks_the_review_as_non_authoritative(self):
        text = local_review.prompt()
        self.assertIn('Never claim mastery', text)
        self.assertIn('Do not rewrite existing authored posts', text)
        self.assertIn('PUBLIC REPOSITORY SNAPSHOT', text)

    def test_local_review_reads_a_reply_without_writing_sources(self):
        before = (HERE / 'projects.json').read_bytes()
        class Response:
            def read(self, limit):
                if limit != 1024 * 1024 + 1:
                    raise AssertionError('Unexpected response limit')
                return b'{"choices":[{"message":{"content":"ASK OWNER: confirm this."}}]}'
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with patch.object(local_review.urllib.request, 'urlopen', return_value=Response()):
            self.assertEqual(local_review.review('http://127.0.0.1:11435/v1/chat/completions', 'simple'), 'ASK OWNER: confirm this.')
        self.assertEqual((HERE / 'projects.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
