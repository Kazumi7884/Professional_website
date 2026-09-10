"""Regression tests for migration, content boundaries and authoring safety.

Run `python tools/site.py build` before the suite; CI does this automatically.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'tools/site.py')
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class BuildRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / '.cache/build.json').read_text())
        cls.pages = site.read_pages()

    def soup(self, url):
        return BeautifulSoup((ROOT / 'dist' / site.route_path(url)).read_text(), 'html.parser')

    def test_all_authored_pages_migrated(self):
        authored = [p for p in self.pages if not p['synthetic']]
        self.assertGreaterEqual(len(authored), 78)
        for page in authored:
            with self.subTest(url=page['url']):
                self.assertTrue((ROOT/'dist'/site.route_path(page['url'])).is_file())

    def test_learning_board_does_not_mix_other_tracks(self):
        links = [a['href'] for a in self.soup('/learning/c-sharp/').select('[data-filter-list] a')]
        self.assertTrue(links)
        self.assertTrue(all(url.startswith('/learning/c-sharp/') for url in links))
        self.assertNotIn('/learning/python/projects/pc-metrics-logger/', links)

    def test_project_aggregator_contains_projects_only(self):
        types = {p['url']: p['entryType'] for p in self.pages}
        links = [a['href'] for a in self.soup('/projects/').select('[data-filter-list] a')]
        self.assertTrue(links)
        self.assertTrue(all(types[url] == 'project' for url in links))

    def test_original_urls_have_working_redirects(self):
        for alias, target in self.report['aliases'].items():
            with self.subTest(alias=alias):
                soup = self.soup(alias)
                self.assertEqual(soup.select_one('link[rel="canonical"]')['href'], 'https://kazumi7884.co.uk'+target)
                self.assertTrue((ROOT/'dist'/site.route_path(target)).exists())

    def test_watch_list_is_rendered_without_script(self):
        items = json.loads((ROOT/'static/data/anime.json').read_text())['items']
        self.assertEqual(len(self.soup('/personal/anime/').select('.anime-entry')),len(items))

    def test_recovered_charts_all_render(self):
        self.assertEqual(len(self.soup('/personal/games/').select('.chart-grid figure')),15)

    def test_ghost_reference_is_rendered_without_script(self):
        ghosts = json.loads((ROOT/'data/phasmophobia/ghosts.json').read_text())
        self.assertEqual(len(self.soup('/personal/misc/phasmophobia/ghosts/').select('details.case-file')),len(ghosts))

    def test_nonsearchable_pages_stay_out_of_search(self):
        index = json.loads((ROOT/'dist/search-index.json').read_text())
        self.assertNotIn('/maintenance/',{p['url'] for p in index})
        self.assertEqual(len(index),len({p['url'] for p in index}))

    def test_sitemap_excludes_search_and_maintenance(self):
        tree=ET.parse(ROOT/'dist/sitemap.xml')
        urls=[n.text for n in tree.findall('.//{*}loc')]
        self.assertNotIn('https://kazumi7884.co.uk/search/',urls)
        self.assertNotIn('https://kazumi7884.co.uk/maintenance/',urls)

    def test_feed_only_contains_actual_posts(self):
        tree=ET.parse(ROOT/'dist/index.xml')
        expected={'https://kazumi7884.co.uk'+p['url'] for p in self.pages if p['entryType']=='post'}
        self.assertEqual({n.text for n in tree.findall('.//item/link')},expected)

    def test_post_navigation_stays_in_same_notebook(self):
        for page in self.pages:
            if page['entryType']!='post':continue
            for link in self.soup(page['url']).select('.post-navigation a'):
                self.assertEqual(page['url'].rsplit('/',2)[0],link['href'].rsplit('/',2)[0])

    def test_canonical_remains_absolute(self):
        soup=self.soup('/learning/c-sharp/posts/c-sharp-blog-1/')
        self.assertEqual(soup.select_one('link[rel="canonical"]')['href'],
                         'https://kazumi7884.co.uk/learning/c-sharp/posts/c-sharp-blog-1/')

    def test_no_inline_css_from_markdown_tables(self):
        soup=self.soup('/setup/')
        self.assertFalse(soup.select('[style]'))
        self.assertTrue(soup.select('.align-right'))


class AuthoringSafety(unittest.TestCase):
    def test_home_route_stays_inside_output(self):
        self.assertEqual(site.route_path('/'),Path('index.html'))
        self.assertFalse(site.route_path('/').is_absolute())

    def test_directory_and_file_routes(self):
        self.assertEqual(site.route_path('/about/'),Path('about/index.html'))
        self.assertEqual(site.route_path('/about.html'),Path('about.html'))

    def test_unsafe_routes_are_rejected(self):
        for route in ['/../secrets','/%2e%2e/secrets','https://example.com/','//example.com/','/a\\b']:
            with self.subTest(route=route),self.assertRaises(ValueError):site.route_path(route)

    def test_new_draft_cannot_overwrite_work(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(site,'ROOT',Path(directory)):
            site.new_post('My note','learning/c-sharp/posts')
            path=Path(directory)/'content/learning/c-sharp/posts/my-note.md'
            first=path.read_bytes()
            with self.assertRaises(FileExistsError):site.new_post('My note','learning/c-sharp/posts')
            self.assertEqual(first,path.read_bytes())
            self.assertEqual(site.read_pages(),[])

    def test_draft_becomes_published_when_ready(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(site,'ROOT',Path(directory)):
            site.new_post('My note','learning/c-sharp/posts')
            path=Path(directory)/'content/learning/c-sharp/posts/my-note.md'
            path.write_text(path.read_text().replace('draft: true','draft: false'))
            pages=site.read_pages()
            self.assertIn('/learning/c-sharp/posts/my-note/',{p['url'] for p in pages})

    def test_new_post_cannot_escape_content(self):
        for section in ['../private','C:\\Windows','//../x','learning/../../x','/absolute','learning//posts']:
            with self.subTest(section=section),self.assertRaises(ValueError):site.new_post('Hello',section)


if __name__=='__main__':unittest.main()
