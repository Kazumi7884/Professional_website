# Default website audit workflow

Kaz requested this workflow on 14 October 2026 for future site work. Apply it
to the actual stack. This repository builds a static public site from
`successor/`; `tools/studio.py` is a separate local-only authoring backend.

1. Confirm source, branch, clean/dirty state, authored content, build path and
   hosting identity. Read AGENTS and the applicable handbook sections.
2. Build the production output before changing source. Select home and the two
   or three slowest representative pages by measured screening, considering
   image-heavy pages and long listings. Keep the selected routes fixed.
3. Run Lighthouse three times per route in mobile mode with cold storage and
   the same browser/version, CPU/network profile and serving method. Save raw
   reports, tool versions, source identity and per-metric medians. Separate
   simulated lab results from real-device or live-host claims. Null scores,
   missing screenshots or failed audits are BLOCKED, never converted to zero.
4. Delegate four read-only audits: images/fonts/scripts; frontend; database/API;
   servers/network. Use medium effort, with high for database/API. Reviewers
   identify source file, affected page, priority, evidence and the smallest fix.
   They do not edit CSS or any source. Only one owner implements the combined
   findings. Runtime model names are not evidence of test quality.
5. Preserve content, themes and features. Ask before dependency removal,
   deployment-region changes or database changes. Ordinary verified fixes use
   the existing authorization. Do not add a framework or database for N/A tips.
6. Repeat the same production measurements after fixes. Report improvements,
   regressions and noise honestly. Repeat affected functional checks after
   subsequent code changes; source checks cannot substitute for browser work.

| Review group | Checks and applicability |
| --- | --- |
| Images, fonts, scripts | Modern formats; useful responsive sizes; lossless fidelity for code/screenshots; intrinsic dimensions; measured critical-image priority; below-fold lazy loading; local or framework font loading; limited font families; defer genuinely optional third-party scripts. Preserve original full-size evidence. SVG and icons need not be rasterized. |
| Frontend | Measure byte/gzip breakdown or framework bundles; selective imports; defer heavy optional components; prerender initial content; stream AI answers and show meaningful loading/error/empty states when such features exist. Avoid invented skeletons on static content. |
| Database/API | Read real queries and authorization first; justify indexes; inspect RLS and repeated identity checks; N+1; paginate long datasets; isolate public/user caches; background heavy jobs. No database change without approval. Static-site N/A does not exempt local authoring APIs. |
| Servers/network | Verify deployed compression, cache policy, security headers, HTTPS, redirects and 404s; co-locate runtime and database only when they exist; static/ISR eligibility; API waterfalls; test main flows with low-end Android/slow-4G emulation. |

Security: scan tracked source and public output without logging keys; exclude
drafts, environments, source tools, studio files and Git metadata from upload
packages. Exercise unauthenticated and malformed API requests. Check
Host/Origin/CSRF, path and symlink confinement, escaped Markdown/search output,
SSRF destination/redirect/pagination boundaries and dependency advisories. SQL
injection is N/A only after confirming there is no SQL/database path.

Accessibility: use axe plus keyboard testing, visible focus and focus recovery,
semantic landmarks/headings, forms/status announcements, image alternatives and
complex-chart descriptions, all themes, contrast, reduced motion and 200% zoom.
Test mobile, 4:3, 5:4, 21:9, 32:9 and 5120×2160 viewports. Automated results do
not establish complete WCAG conformance or physical-device testing.

Additional checks: offline quota/storage-denial recovery, cache privacy and real
bounds, complete cache-version invalidation, slow-network timeout recovery,
source-derived search/no-results/failure/retry, broken internal links and anchors,
canonical/feed/sitemap/draft checks, supply-chain scans, archive member inspection
and a rollback record. Keep blocked and N/A items separate from pass counts.

Run existing checks plus these security/offline gates from the repository root:

```text
python -m pip install -r requirements-security.txt
python -m pip_audit -r requirements.txt --progress-spinner=off
python scripts/security_scan.py
node --test successor/worker.test.cjs
```

These scanner dependencies are development tools. Nothing is installed on the
public host. Source integration, CI status, upload-package creation and host
publication are separate results. Follow docs/PUBLISHING.md for the real host.

Reproducible Lighthouse runner (requires installed Chrome):

```text
npm install --prefix .cache/performance lighthouse@13.5.0 chrome-launcher@1.2.2 --ignore-scripts --no-audit --no-fund
python successor/build.py
node scripts/lighthouse.mjs before
```

After changing and rebuilding source, use `node scripts/lighthouse.mjs after`.
Each label retains twelve raw reports and four medians in `.cache/lighthouse/`.
The optional third argument selects another built checkout as a baseline.
Set `CHROME_PATH` only if automatic discovery cannot find Chrome. The dedicated
pull-request workflow runs both the base commit and candidate on the same hosted
runner; it publishes the reports as a CI artifact, without publishing the site.
Both samples use the current preview adapter, including gzip for public text,
to match the existing deployment compression policy. The adapter reads each
checkout's generated files; it does not change or rebuild the baseline source.
