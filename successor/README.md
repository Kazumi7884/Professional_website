# Kaz's personal site successor

This is a new implementation. V5 supplies authored Markdown, saved snapshots,
images and historical URLs. No V5 Python, template, CSS or JavaScript module is
used by the new build. The old tools remain a recovery/authoring bridge, not the
new public implementation.

## Build and preview

Use the environment created with the repository's pinned requirements.

Windows PowerShell:

```powershell
.venv\Scripts\python.exe successor/build.py
.venv\Scripts\python.exe successor/serve.py --port 8765
```

Linux (including fish):

```text
.venv/bin/python successor/build.py
.venv/bin/python successor/serve.py --port 8765
```

The server binds to 127.0.0.1 only. Public output is `build/`; it needs no server
runtime. The default canonical origin remains the approved `site.json` domain.
Use `--origin https://your-host` only when building for that host.

## Clone, update and keep a local copy

Clone the repository, create the pinned Python environment, install the existing
requirements, then run the build and verification commands above. The complete
site source is in the clone: `content/` is the writing, `successor/` is the new
site generator, `static/` contains carried-forward images and data, and `build/`
is generated output. Do not edit `build/` by hand.

For a normal update after pulling changes:

```powershell
.venv\Scripts\python.exe successor\refresh.py
.venv\Scripts\python.exe successor\build.py
.venv\Scripts\python.exe scripts\verify.py
```

`refresh.py` only refreshes the selected public repository facts. It does not
write a blog post, change a project description, or publish anything. Review
`successor/repositories.json` before committing it. That keeps a repository push
from turning into a claim about experience.

The GitHub workflow checks that same allowlist three times a day and opens or
updates one `automation/repository-snapshot` pull request when the facts change.
It builds and verifies before pushing the branch. It never merges its own pull
request or force-push over branch changes. Merge the reviewed change to put the
new dated facts on the site. If someone changes that review branch directly,
the scheduled update stops instead of replacing their work; resolve or merge the
review before the next update.

## Optional local AI review

`local_review.py` works with an OpenAI-compatible endpoint on your own machine.
It reads only the editorial project file and the public repository snapshot, then
prints a review draft for you to decide on. It cannot edit source files unless
you explicitly give it `--output`, and even then it writes a separate draft only.

```powershell
.venv\Scripts\python.exe successor\local_review.py --endpoint http://127.0.0.1:11435/v1/chat/completions --model simple
```

For a different local model service, pass its local chat-completions endpoint and
model name. Read the draft against the repositories and your own notes before
changing `projects.json` or authored Markdown. This is a review aid, not an
automatic writer or publisher.

## Writing and recovery

Authored sources remain in `content/`. Existing post bodies are unchanged.
Use the established V5 writing desk to edit/save Markdown, then run the successor
build above. Its old Build/View controls still preview V5, so use the successor
preview URL for the new design. This bridge is explicit: the V5 writing desk
has not been rewritten or certified as a clean-room component.

Drafts are excluded. New published pages are indexed at build time. A failed
build leaves the last successful output intact. The builder refuses to replace
an unmarked directory. Keep source backups in Git and copy any unsaved desk work
before switching tools. Reverting the successor changes restores the old build
workflow; restoring an uploaded site is a separate host-backup operation.

## Course evidence

`courses.json` records seven owned courses observed in the signed-in Udemy
learning library on 30 September 2026. The connector has no enrolment/progress
API, so this is a browser-verified snapshot. Archived courses were not verified.
No password, account identity, receipt or session data belongs in this file.

Progress is not proficiency. Related project links are subject connections,
not a claim that a project was completed for the course. Unstarted courses keep
null progress rather than an invented zero. Review the library before changing
the observation date. Course renames should preserve IDs and page slugs.

## Curated repository updates

`projects.json` is the editorial allowlist and contribution narrative.
`repositories.json` holds machine facts. `python successor/refresh.py` fetches
only allowlisted public repos using unauthenticated GitHub requests. Private or
mismatched responses, timeouts and malformed data fail without replacing the
last good snapshot. A missing licence is recorded as unknown, not open source.

The scheduled workflow refreshes only this file and opens a review pull request
when there is a real change. Review the diff, run the local checks if you have
made other edits, and merge through the normal path. It never changes narratives
or publishes a website by itself. No source-repository token, webhook, cross-repo
write permission or extra service is needed.

The repository inventory was inspected through GitHub. Coursework has direct
public source evidence and is included. Earlier portfolio repositories, the
desktop fork and private repositories are not promoted into public achievement
pages. FOSSLife is excluded as required by the website's authorship policy.

## Verification and publication

Run `python scripts/verify.py` for behavioural tests and link validation.
Run `node successor/runtime.test.cjs` after installing the existing jsdom helper
under `.cache/runtime-tests`. Real-browser checks remain additional.

`python successor/package.py` creates `deploy/successor-upload.zip` from a fresh
validated build. Inspect its contents; it contains public output only. It does
not deploy. Apache uses `.htaccess`; compatible static hosts can use `_redirects`.
Other hosts need equivalent redirect and 404 rules. Browser-side fallback pages
remain available where redirect configuration is unsupported.

Offline caching stores core pages and up to 100 same-origin responses. New
content changes the cache revision. Activation removes only this site's known
old cache prefixes. Optional storage failure does not prevent online reading.
No analytics, remote fonts, embeds or browser API credentials are introduced.

