"""Exercise real file round trips and local HTTP boundaries, using temp folders."""
import importlib.util
import http.client
import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('writing_studio', ROOT / 'tools/studio.py')
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class StudioFiles(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.scope = patch.object(studio, 'ROOT', self.root)
        self.scope.start()
        self.data = {'path': 'blog/test-post.md', 'revision': None,
                     'metadata': {'title': 'A title with --- and : punctuation', 'description': 'A useful summary.',
                                  'date': '2026-09-10', 'draft': True, 'entryType': 'post', 'tags': ['C#']},
                     'body': '## First heading\n\nMy **own** words.\n\n---\n\nAnother paragraph.'}

    def tearDown(self):
        self.scope.stop()
        self.directory.cleanup()

    def test_create_draft_round_trip(self):
        result = studio.save_document(self.data)
        self.assertTrue(result['metadata']['draft'])
        self.assertEqual(result['body'].strip(), self.data['body'])
        self.assertEqual(result['metadata']['title'], self.data['metadata']['title'])
        self.assertEqual(len(result['revision']), 64)

    def test_new_post_does_not_overwrite_existing(self):
        studio.save_document(self.data)
        self.data['body'] = 'Do not overwrite'
        with self.assertRaises(studio.Conflict): studio.save_document(self.data)
        self.assertNotEqual(studio.read_document(studio.content_path(self.data['path']))['body'].strip(), self.data['body'])

    def test_stale_revision_is_rejected(self):
        result = studio.save_document(self.data)
        self.data['revision'] = result['revision']
        studio.content_path(self.data['path']).write_text(studio.content_path(self.data['path']).read_text(encoding='utf-8') + '\nExternal edit\n', encoding='utf-8')
        with self.assertRaises(studio.Conflict): studio.save_document(self.data)

    def test_unknown_metadata_survives(self):
        result = studio.save_document(self.data)
        path = studio.content_path(self.data['path'])
        path.write_text(path.read_text(encoding='utf-8').replace('draft: true', 'draft: true\nurl: /my-original-url/\naliases: [/old/]\nlayout: journal'), encoding='utf-8')
        result = studio.read_document(path)
        self.data['revision'] = result['revision']
        self.data['metadata']['draft'] = False
        self.data['metadata']['url'] = '/untrusted-client-change/'
        saved = studio.save_document(self.data)
        self.assertEqual(saved['metadata']['url'], '/my-original-url/')
        self.assertEqual(saved['metadata']['aliases'], ['/old/'])
        self.assertEqual(saved['metadata']['layout'], 'journal')
        self.assertFalse(saved['metadata']['draft'])

    def test_deleted_file_cannot_be_recreated_silently(self):
        result = studio.save_document(self.data)
        self.data['revision'] = result['revision']
        studio.content_path(self.data['path']).unlink()
        with self.assertRaises(studio.Conflict): studio.save_document(self.data)

    def test_invalid_metadata_cannot_write_a_file(self):
        for key, value in [('draft', 'false'), ('tags', 'C#'), ('date', '2026-02-31'), ('entryType', 'executable')]:
            with self.subTest(key=key):
                data = {**self.data, 'metadata': {**self.data['metadata'], key: value}}
                with self.assertRaises(ValueError): studio.save_document(data)
        self.assertFalse((self.root / 'content').exists())

    def test_ready_requires_summary_body_and_date(self):
        for key in ('description', 'date', 'body'):
            data = {**self.data, 'metadata': {**self.data['metadata'], 'draft': False}}
            if key == 'body': data['body'] = ''
            else: data['metadata'][key] = ''
            with self.subTest(key=key), self.assertRaises(ValueError): studio.save_document(data)

    def test_traversal_and_non_markdown_paths_are_rejected(self):
        for path in ('../site.json', '/etc/passwd', 'blog/../../x.md', 'blog/a.html', 'blog\\a.md', 'blog/%2e%2e/a.md'):
            with self.subTest(path=path), self.assertRaises(ValueError): studio.content_path(path)

    def test_symlink_escape_rejected(self):
        (self.root / 'content').mkdir()
        try: (self.root / 'content' / 'escape').symlink_to(self.root, target_is_directory=True)
        except OSError: self.skipTest('Symlink creation unavailable on this Windows account')
        with self.assertRaises(ValueError): studio.content_path('escape/post.md')

    def test_specialised_page_types_survive_save(self):
        for kind in ('dashboard', 'phasmophobia', 'sitemap'):
            data = {**self.data, 'path': f'{kind}.md', 'metadata': {**self.data['metadata'], 'entryType': kind}}
            self.assertEqual(studio.save_document(data)['metadata']['entryType'], kind)

    def test_catalogue_includes_drafts(self):
        studio.save_document(self.data)
        self.assertTrue(studio.catalogue()[0]['draft'])

    def test_preview_removes_active_html_but_retains_markdown(self):
        body = '## Heading\n\n**Text**\n\n<script>alert(1)</script><img src="x" onerror="alert(1)"><a href="javascript:alert(1)">bad</a>'
        soup = BeautifulSoup(studio.preview_html(body), 'html.parser')
        self.assertEqual(soup.h2.text, 'Heading')
        self.assertTrue(soup.strong)
        self.assertFalse(soup.select('script, [onerror], a[href]'))


class StudioHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), http.server.BaseHTTPRequestHandler)
        cls.port = cls.server.server_port
        cls.server.RequestHandlerClass = studio.make_handler('test-token', cls.port, lambda: {'pages': [], 'seconds': 0})
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def request(self, headers):
        connection = http.client.HTTPConnection('127.0.0.1', self.port)
        connection.request('POST', '/__studio/api/preview', json.dumps({'body': '**Hello**'}),
                           {'Content-Type': 'application/json', **headers})
        response = connection.getresponse(); body = response.read(); connection.close()
        return response.status, body

    def test_local_preview_with_token(self):
        status, body = self.request({'X-Studio-Token': 'test-token'})
        self.assertEqual(status, 200); self.assertIn(b'<strong>Hello</strong>', body)

    def test_missing_token_rejected(self):
        self.assertEqual(self.request({})[0], 403)

    def test_cross_origin_rejected(self):
        self.assertEqual(self.request({'X-Studio-Token': 'test-token', 'Origin': 'https://example.com'})[0], 403)

    def test_rebinding_host_rejected(self):
        self.assertEqual(self.request({'X-Studio-Token': 'test-token', 'Host': 'attacker.example'})[0], 403)


class ThemeContrast(unittest.TestCase):
    def test_all_three_palettes_meet_high_contrast_text_target(self):
        import re
        css = (ROOT / 'assets/css/site.css').read_text(encoding='utf-8')
        palettes = re.findall(r':root(?:\[data-theme="(?:halo|resident)"\])?\s*\{([^}]+)', css)[:3]
        self.assertEqual(len(palettes), 3)
        def luminance(colour):
            rgb = [int(colour[i:i+2], 16)/255 for i in (1,3,5)]
            return sum(c*w for c,w in zip([v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb], [.2126,.7152,.0722]))
        for palette in palettes:
            colours = dict(re.findall(r'--([a-z]+):\s*(#[0-9a-f]{6})', palette))
            for foreground in ('ink', 'muted', 'accent', 'green'):
                for background in ('bg', 'surface', 'inset', 'bar', 'code'):
                    light, dark = sorted([luminance(colours[foreground]), luminance(colours[background])], reverse=True)
                    with self.subTest(foreground=colours[foreground], background=colours[background]):
                        self.assertGreaterEqual((light+.05)/(dark+.05), 7)


if __name__ == '__main__': unittest.main()
