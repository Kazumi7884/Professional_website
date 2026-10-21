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


if __name__ == "__main__":
    unittest.main()
