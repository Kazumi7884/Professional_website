"""Focused regressions for authored-page section indexes and code readability."""
import importlib.util
from pathlib import Path
import unittest

from bs4 import BeautifulSoup


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("design_reference_builder", HERE / "build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class EditorialNavigationTests(unittest.TestCase):
    def test_short_entry_is_not_given_a_contents_box(self):
        html = '<h2 id="intro">Intro</h2><h2 id="next">Next</h2>'
        self.assertEqual(builder.article_outline(html), "")

    def test_three_headings_create_named_navigation(self):
        html = '<h2 id="one">One</h2><h2 id="two">Two</h2><h3 id="three">Three</h3>'
        result = BeautifulSoup(builder.article_outline(html), "html.parser")
        self.assertEqual(result.nav.get("aria-label"), "Sections in this entry")
        self.assertEqual([a["href"] for a in result.select("a")], ["#one", "#two", "#three"])
        self.assertEqual(len(result.select("li.article-outline-subsection")), 1)

    def test_only_real_heading_ids_are_linked(self):
        html = '<h2>Unlinked</h2><p id="paragraph">Not a heading</p>' + "".join(
            '<h2 id="heading-' + str(i) + '">Section</h2>' for i in range(3)
        )
        result = BeautifulSoup(builder.article_outline(html), "html.parser")
        self.assertEqual(len(result.select("a")), 3)
        self.assertNotIn("#paragraph", [a["href"] for a in result.select("a")])

    def test_heading_text_and_fragment_are_escaped(self):
        html = (
            '<h2 id="one&quot;two">A &lt;script&gt;B&lt;/script&gt;</h2>'
            '<h2 id="middle">Middle</h2><h2 id="end">End</h2>'
        )
        markup = builder.article_outline(html)
        result = BeautifulSoup(markup, "html.parser")
        self.assertEqual(result.select_one("a")["href"], '#one"two')
        self.assertNotIn("<script>", markup)
        self.assertEqual(len(result.select("script")), 0)

    def test_six_sections_use_responsive_long_layout(self):
        html = "".join(f'<h2 id="s{i}">Section {i}</h2>' for i in range(6))
        result = BeautifulSoup(builder.article_outline(html), "html.parser")
        self.assertIn("article-outline-long", result.nav["class"])

    def test_markdown_heading_slugs_resolve_to_outline_links(self):
        rendered = builder.render_markdown(
            "## First section\n\nSome notes.\n\n"
            "## Second section\n\nMore notes.\n\n"
            "### A detail\n\nLast note."
        )
        contents = BeautifulSoup(rendered, "html.parser")
        outline = BeautifulSoup(builder.article_outline(rendered), "html.parser")
        ids = {heading["id"] for heading in contents.select("h2[id],h3[id]")}
        self.assertEqual({link["href"][1:] for link in outline.select("a")}, ids)

    def test_code_examples_are_keyboard_scrollable_regions(self):
        rendered = BeautifulSoup(builder.render_markdown(
            "```csharp\nConsole.WriteLine(42);\n```"
        ), "html.parser")
        self.assertEqual(rendered.pre["tabindex"], "0")
        self.assertEqual(rendered.pre["role"], "region")
        self.assertIn("Code example", rendered.pre["aria-label"])
        self.assertEqual(rendered.code.get_text().strip(), "Console.WriteLine(42);")

    def test_no_external_runtime_dependency_added(self):
        css = (HERE / "site.css").read_text(encoding="utf-8")
        self.assertIn(".article-outline-long ol{columns:2", css)
        self.assertIn("overflow-x:auto", css)
        self.assertNotIn("@import", css)
        self.assertLess(
            sum((HERE / file).stat().st_size for file in ("site.css", "site.js", "theme.js")),
            45 * 1024,
        )


class OriginalSiteContractTests(unittest.TestCase):
    def test_learning_subjects_restore_original_scope(self):
        pages, bodies = builder.make_site()
        expected = {'angular', 'asp-net', 'bash', 'c-sharp', 'css', 'cybersecurity',
                    'data-analytics', 'html', 'javascript', 'powershell', 'python',
                    'r', 'react', 'ruby', 'ruby-on-rails', 'sql'}
        self.assertEqual(set(builder.TRACKS), expected)
        hub = BeautifulSoup(bodies['/learning/'], 'html.parser')
        for subject in expected:
            base = '/learning/' + subject + '/'
            self.assertIsNotNone(hub.select_one('a[href="' + base + '"]'))
            for suffix in ('', 'posts/', 'projects/', 'resources/'):
                self.assertIn(base + suffix, pages)
        self.assertTrue(pages['/learning/ruby-on-rails/posts/']['meta']['noindex'])

    def test_home_is_personal_not_a_recruitment_landing_page(self):
        _, bodies = builder.make_site()
        home = BeautifulSoup(bodies['/'], 'html.parser')
        doors = home.select('.split-door a')
        self.assertEqual([a['href'] for a in doors], ['/learning/', '/personal/'])
        self.assertIsNone(home.select_one('a[href="/work/projects/"]'))

    def test_project_details_have_one_canonical_subject_owner(self):
        pages, bodies = builder.make_site()
        for slug, topic in [('space-invaders', 'c-sharp'), ('steam-study', 'python')]:
            route = '/learning/' + topic + '/projects/' + slug + '/'
            self.assertIn(route, pages)
            self.assertIn('/work/projects/' + slug + '/', pages[route]['meta']['aliases'])
            self.assertNotIn('/work/projects/' + slug + '/', pages)
            self.assertIn(route, bodies['/learning/' + topic + '/projects/'])

    def test_posts_are_not_mixed_across_learning_topics(self):
        _, bodies = builder.make_site()
        self.assertIn('/learning/c-sharp/posts/c-sharp-lesson-1/', bodies['/learning/c-sharp/posts/'])
        self.assertNotIn('/learning/c-sharp/posts/c-sharp-lesson-1/', bodies['/learning/python/posts/'])
        self.assertNotIn('/personal/misc/writing/posts/steam-viz/', bodies['/learning/python/posts/'])
        self.assertIn('/personal/misc/writing/', bodies['/blog/'])
        self.assertNotIn('/personal/misc/writing/posts/steam-viz/', bodies['/blog/'])

    def test_learning_navigation_active_on_project_details(self):
        pages, bodies = builder.make_site()
        route = '/learning/c-sharp/projects/space-invaders/'
        soup = BeautifulSoup(builder.frame(route, pages[route], bodies[route], 'https://kazumi7884.co.uk'), 'html.parser')
        self.assertEqual(soup.select_one('nav.primary a[aria-current="page"]')['href'], '/learning/')
        self.assertEqual(soup.select_one('nav[aria-label="Mobile navigation"] a[aria-current="page"]')['href'], '/learning/')

    def test_standalone_page_does_not_highlight_home(self):
        pages, bodies = builder.make_site()
        soup = BeautifulSoup(builder.frame('/skills/', pages['/skills/'], bodies['/skills/'], 'https://kazumi7884.co.uk'), 'html.parser')
        self.assertFalse(soup.select('nav.primary a[aria-current]'))

    def test_music_is_explicit_and_does_not_autoplay(self):
        pages, bodies = builder.make_site()
        player = BeautifulSoup(bodies['/music/'], 'html.parser').audio
        self.assertTrue(player.has_attr('controls'))
        self.assertFalse(player.has_attr('autoplay'))
        self.assertEqual(player['preload'], 'none')
        page = BeautifulSoup(builder.frame('/', pages['/'], bodies['/'], 'https://kazumi7884.co.uk'), 'html.parser')
        self.assertEqual(page.select_one('a[href="/music/"]')['target'], '_blank')

    def test_career_pages_render_without_visible_html_markup(self):
        pages = builder.content_pages()
        for route in ('/skills/', '/experience/', '/education/', '/contact/'):
            with self.subTest(route=route):
                rendered = BeautifulSoup(builder.render_markdown(pages[route]['body']), 'html.parser')
                visible = rendered.get_text(' ', strip=True)
                self.assertNotIn('<div', visible)
                self.assertNotIn('<section', visible)
                self.assertNotIn('<article', visible)
                self.assertGreaterEqual(len(rendered.select('a[href]')), 1)
                self.assertTrue(len(visible) > 100)


if __name__ == "__main__":
    unittest.main()
