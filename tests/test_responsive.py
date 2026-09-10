"""Static responsive and search-contract checks for the generated site.

These checks do not replace browser screenshots; they protect the contracts that
make the layouts testable at mobile, common desktop and ultrawide widths.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
CSS = (ROOT / 'assets/css/site.css').read_text(encoding='utf-8')

VIEWPORTS = {
    'mobile': (390, 844),
    '4:3': (1024, 768),
    '5:4': (1280, 1024),
    '21:9': (2560, 1080),
    '32:9': (5120, 1440),
}


class ResponsiveContracts(unittest.TestCase):
    def test_all_requested_viewports_have_named_contracts(self):
        self.assertEqual(set(VIEWPORTS), {'mobile', '4:3', '5:4', '21:9', '32:9'})

    def test_mobile_reflow_breakpoint_exists(self):
        self.assertRegex(CSS, r'@media\s*\(max-width:\s*620px\)')

    def test_tablet_reflow_breakpoint_exists(self):
        self.assertRegex(CSS, r'@media\s*\(max-width:\s*900px\)')

    def test_layout_uses_fluid_columns(self):
        self.assertIn('minmax(0, 1fr)', CSS)

    def test_media_never_exceeds_its_container(self):
        self.assertIn('max-width: 100%', CSS)

    def test_tables_and_code_can_scroll_without_page_overflow(self):
        self.assertIn('.table-scroll { overflow-x: auto', CSS)
        self.assertIn('pre { max-width: 100%; overflow: auto', CSS)

    def test_all_generated_pages_have_viewport_metadata(self):
        pages = list(DIST.rglob('*.html'))
        self.assertGreater(len(pages), 0)
        for page in pages:
            markup = page.read_text(encoding='utf-8')
            with self.subTest(page=page):
                if 'http-equiv="refresh"' in markup:
                    continue
                self.assertRegex(markup, r'name="viewport"[^>]+width=device-width|width=device-width[^>]+name="viewport"')

    def test_ultrawide_shell_has_a_readable_maximum(self):
        self.assertRegex(CSS, r'\.page-shell\s*\{[^}]*max-width:\s*1280px')

    def test_mobile_cards_stack(self):
        self.assertRegex(CSS, r'\.anime-grid, \.chart-grid, \.hobby-directory\s*\{\s*grid-template-columns:\s*1fr')

    def test_mobile_post_layout_stacks(self):
        self.assertRegex(CSS, r'\.homepage-columns, \.post-layout\s*\{\s*grid-template-columns:\s*1fr')

    def test_touch_controls_keep_minimum_height(self):
        self.assertRegex(CSS, r'button, select\s*\{\s*min-height:\s*44px')


class SearchContracts(unittest.TestCase):
    def test_search_index_is_generated(self):
        index = DIST / 'search-index.json'
        self.assertTrue(index.is_file())
        self.assertIsInstance(json.loads(index.read_text(encoding='utf-8')), list)

    def test_search_index_contains_authored_collections(self):
        urls = {item['url'] for item in json.loads((DIST / 'search-index.json').read_text(encoding='utf-8'))}
        self.assertIn('/learning/c-sharp/posts/c-sharp-blog-1/', urls)
        self.assertIn('/personal/misc/writing/posts/steam-viz/', urls)
        self.assertIn('/personal/misc/phasmophobia/ghosts/', urls)

    def test_search_index_excludes_drafts(self):
        index = json.loads((DIST / 'search-index.json').read_text(encoding='utf-8'))
        self.assertFalse(any(item['url'].endswith('my-note/') for item in index))

    def test_search_script_uses_same_origin_index(self):
        script = (ROOT / 'assets/js/search.js').read_text(encoding='utf-8')
        self.assertIn("fetch('/search-index.json'", script)
        self.assertIn("credentials: 'same-origin'", script)

    def test_search_results_are_dom_text_not_html(self):
        script = (ROOT / 'assets/js/search.js').read_text(encoding='utf-8')
        self.assertIn('link.textContent = page.title', script)
        self.assertIn('description.textContent = page.description', script)


if __name__ == '__main__':
    unittest.main()
