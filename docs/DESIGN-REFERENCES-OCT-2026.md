# Design-reference review — 21 October 2026

Scope: `Kazumi7884/Professional_website`, specifically the static `successor/`
implementation. The referenced X post lists six **resources**, not six source
repositories. The goal is a better site without turning it into an AI-generated
template, migrating frameworks, or installing unrelated services.

## Source assessment and attribution

| Resource | What is useful | Decision |
| --- | --- | --- |
| [OpenDesign](https://github.com/nexu-io/open-design) (Apache-2.0) | Portable design systems, design brief -> prototype -> review workflows | **Adopt its process**: this site's `successor/DESIGN.md` remains authoritative. No workspace/server installation. |
| [VibePrompt](https://vibeprompts.dev/) | UI briefs, layout and Tailwind examples | **Reference only** for writing concrete briefs. Avoid copying Tailwind snippets into the plain-CSS site. No verified source repository or code imported. |
| [git-ai](https://github.com/feder-cr/git-ai) (MIT) | Agent-focused history, reviews, verification and concurrent landings | **Do not install**. It is a separate pre-1.0 Git-compatible source-control server, not a website improvement; our existing GitHub PR workflow is simpler. |
| [Hairline](https://github.com/lucasmarkes/hairline) | Small line-art figures; works in vanilla JavaScript as well as React | **Defer**. A moving illustration is not inherently better for written work and adds runtime bytes and review surface. Never import React just for a figure. Consider only when it communicates real content, with reduced-motion and a static fallback. |
| [Oil UI](https://github.com/oil-oil/oil-ui) | Start from the reader's task, compare genuinely different directions and test real screen sizes | **Adopt its review method** below, not an unreviewed third-party instruction file or a commercial add-on. |
| [Codrops Webzibition](https://tympanus.net/codrops/webzibition/) | Curated examples of purposeful editorial hierarchy and interactions | **Adapt editorial principles**. Do not copy screenshots, layouts, scripts or distinctive visual assets. |

No upstream code is copied or vendored; names and URLs are retained to credit the
design references. There is no new package, CDN, tracking request, subscription,
build tool, runtime framework or cloud-agent dependency.

## Implemented visitor improvements

- Authored pages with **three or more H2/H3 headings** now provide a small
  linked section index. Headings already receive IDs from Python-Markdown's
  existing `toc` extension. The links work with JavaScript disabled.
- The index omits short pages, follows the author's section order, indents H3
  entries and switches from two columns to one on narrower screens.
- Heading targets receive a restrained accent marker. This is orientation, not
  an animated effect.
- Fenced code keeps original indentation and long lines instead of wrapping
  programming examples into misleading layouts. Keyboard users can focus and
  scroll the code block.
- Forum, Forerunner and Umbrella continue to use the existing theme tokens.

The work is deliberately **content-first**: no fake achievements, boilerplate
project cards, generic AI illustrations, auto-generated posts or fabricated
metrics. It preserves V5 authored Markdown, visitor URLs and the stable static
deployment architecture.

## Protocol for the next visual iteration

1. **Choose the task, not the aesthetic label.** Examine how a visitor finds
   C# notes, a project with source evidence, a blog post, or an anime entry.
   Work with real content and the actual first screen, not placeholder copy.
2. **Use three genuinely different proposals only when a redesign is needed.**
   Show the current site alongside directions derived from (a) classic forum
   editorial navigation, (b) Umbrella dossier classification and (c) Forerunner
   archival materials. Different layouts and type hierarchies matter more than
   swapping colour tokens. Keep the existing three user-selectable themes.
3. **Check relevant viewports and interactions.** At minimum review 390px,
   768px, 1280px, 1920px, 3440px and 5120px widths; explicitly exercise 4:3,
   5:4, 21:9 and 32:9 where possible, plus 200% zoom. Check keyboard,
   focus, reduced-motion, navigation, search, article anchors and code scroll.
4. **Respect measured budgets.** Keep first-party CSS + JavaScript below the
   existing 45 KiB uncompressed limit, avoid third-party browser requests,
   and run the Python and JavaScript suites, broken-link verification and
   actual Lighthouse/browser runs before declaring a visual improvement.
5. **Compare and subtract.** Any new border, panel, texture or animation must
   help hierarchy, legibility or wayfinding. Remove effects that do not.
   Preserve old routes and authored voice. Record evidence for the final build.

## Verification boundaries

The accompanying `successor/test_design_navigation.py` covers static section
navigation, heading IDs, HTML escaping, focusable code and CSS size constraints.
The existing `scripts/verify.py` and CI cover generated links and site
behaviour. These checks cannot certify mobile screenshots, layout reflow,
Lighthouse performance or the live production host. Record those separately;
do not conflate a pushed source change with a published website.
