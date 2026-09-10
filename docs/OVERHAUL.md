# V5.1 overhaul record

Base content: `Professional_website_V5_FIXED_2026-08-11.zip` (78 Markdown pages).
Destination: `Kazumi7884/Professional_website`, branch `main`.

## Five overhaul passes

| Pass | Work implemented | Evidence |
| --- | --- | --- |
| 1. Personal-site styling | Compact masthead, flat purple/green panels, quieter headings, topic rows, author profiles and original screenshots; removed decorative background imagery and glow-based styling | Shared template and stylesheet; 78 authored routes |
| 2. Authored posts and hobby sections | Forum-style author rail, dates, contents, signatures, older/newer posts; journal typography, anime shelf, Steam chart gallery, PC inventory and expandable investigation notes | Content regression and filtering tests |
| 3. Runtime and loading | Static first render, short separate scripts, guarded theme storage, menu focus restoration, filter caching, deferred search, retry handling, safe text rendering, lazy images and non-autoplay audio | 15 DOM behaviour tests; JavaScript syntax checks |
| 4. Structure and discoverability | Route migration, original-repository redirects, scoped learning lists, project/resource aggregation, canonicals, metadata, RSS, sitemap, labels and keyboard targets | 50 automated review goals × 78 authored routes = 3,900 route/goal checks |
| 5. Build and maintenance | Python build/preview/check/package/new-post command, draft handling, overwrite/traversal protection, pinned dependencies, Windows/Linux CI and practical Git/OneDrive instructions | 19 Python regression tests; reproducible public upload package |

These passes describe the implemented areas. The separate 50-goal report is an
automated review, not a claim that 1,500 independent feature edits or 50 human
visual redesigns were completed. Each goal records outcomes for all 78 authored
routes. Shared-template improvements apply throughout those routes.

## Media recovery

The V5 packages contained damaged binary data in the 15 Steam WebP charts,
favicon and audio. Intact copies were recovered from the user's original
`Professional_website_V2(1).zip`. Chart files and the favicon decode successfully.
The audio file was restored byte-for-byte from that archive. No charts were
regenerated or their numerical content invented.

The C# screenshot is retained. Anime covers use the existing MyAnimeList URLs
with text links and descriptions alongside them. Remote cover availability is
not guaranteed by the local build.

## Size and dependency changes

| Source payload | V5 archive | V5.1 |
| --- | ---: | ---: |
| CSS files combined | 140,805 bytes | 18,899 bytes |
| JavaScript files combined | 52,506 bytes | 9,336 bytes |

These are uncompressed source totals, not live network or Lighthouse results.
The 3,077-byte search script loads only on the search route. The main stylesheet
and JavaScript are fingerprinted for safe long-term caching. HTML and JSON
revalidate. Audio is about 6 MB but uses `preload="none"` and never autoplays.

The old generator, templates, Node build stack, generated TypeScript copy,
duplicate startup script, unused webfonts and old deployment tooling are absent
from the working source. Production needs static hosting only. Node/jsdom are
optional test dependencies installed into an ignored directory; they do not
build or run the published site.

## Preserved boundaries

- Authored Markdown remains the source of truth. Existing body text is retained
  except obsolete workflow/tool references and the updated site changelog.
- Publication dates and hobby snapshots are retained rather than fabricated.
- The website does not become a live discussion server. Forum styling does not
  imply working visitor accounts, comments or reply counters.
- Saved PC and game data are not verified as current hardware/game facts.
- Git history before this replacement remains available for recovery.
- The upload package contains no Git metadata, credentials or source tooling.

## Verification limits

The local build, 3,900 static checks, 19 Python tests and 15 DOM behaviour tests
passed. DOM tests use jsdom, not a browser rendering engine. Browser visual QA,
Lighthouse/Core Web Vitals, external-link availability, live hosting headers and
Windows execution were not verified locally. The CI workflow requests Windows
and Linux runs; their actual remote outcome must be checked in GitHub Actions.

No Fasthosts credentials were used and a Fasthosts upload was not performed by
this change. Follow `PUBLISHING.md` after pulling the source.
