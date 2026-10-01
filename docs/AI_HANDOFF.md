# Website maintenance handoff: 1 October 2026

Read `AGENTS.md`, the handbook reading contract, and its R19 runbook first.
Recheck `git status --short --branch` and `git rev-parse HEAD` before writing.
This is a dated checkpoint, not a running maintenance service.

## Source, preservation and current implementation

Repository: `Kazumi7884/Professional_website`, canonical branch `main`.
Windows source: `C:\Users\jamie\Professional_website`.
The initial checkout was `9bd2981`, 92 commits behind fetched main `a9d53ec`.
Its two modified validation reports were preserved on pushed branch
`rescue/local-validation-20261001` (commit `3d58826`) before fast-forwarding.
The local `professional_wesbite.zip` remains intact and is now ignored; it is
not an authoritative source or a publication package.

The current root README selects `successor/`, with generated output in `build/`.
The V5 tools and `dist/` remain the writing/recovery bridge. The September merge
record is historical; its earlier choice is not the current command routing.
Authored Markdown remains in `content/`. Do not replace authored writing with
model output or manufacture portfolio claims.

## Repairs and acceptance

- The successor could not build: education and experience linked to the removed
  `/projects/` index. A historical redirect to `/work/` now preserves those
  links, with generated fallback HTML and host redirect rules. Authored prose
  was not changed. The HTTP regression test follows the recovery route.
- The advertised local-only reviewer accepted remote URLs and proxy settings.
  It now requires literal loopback HTTP, refuses URL credentials and redirects,
  ignores environment proxies, caps generated tokens and reply bytes, and rejects
  empty replies. Existing draft files cannot be overwritten.
- The legacy test rejected every project even though the September consolidation
  restored two authored project pages. It now permits exactly those two routes,
  confirms their output files exist, and continues rejecting resource entries.
- Current branch instructions, implementation routing and local-AI documentation
  were corrected. No framework, hosting provider, authored claim or theme was
  replaced. Python file line-ending normalisation is incidental only.

## Windows evidence

| Check | Result |
| --- | --- |
| `python scripts/verify.py` | 141 behavioural tests passed |
| `node successor/runtime.test.cjs` | 32 browser-logic behaviours passed |
| `python tools/site.py check` | 2,000 route/goal checks, zero additional failures |
| `python -m unittest discover -s tests -v` | 83 tests passed |
| `node tests/runtime.cjs` | 39 tests passed |
| `python successor/package.py` | generated `deploy/successor-upload.zip` |
| Package inspection | 164 members; no Git, source tools, studio, handbook, secrets or internal build report |
| Successor output | 78 canonical pages; 3,621 internal references checked; CSS/JS 18,873 bytes |

The isolated, already-declared `jsdom@26.1.0` helper was installed in ignored
`.cache/runtime-tests`. No dependency was added to the public site.
Raw logs are local to the sibling FOSSLife checkout as `.website-*.log` and do
not travel through Git. Regenerate evidence on another device.

Real-browser verification is BLOCKED: agent-browser could not start its daemon,
and the connected browser tool reported no available browser. The JS tests use
jsdom, not an actual browser. No full visual, accessibility, viewport, or
Anti-Slop delivery-gate pass is claimed. Existing themes and authored copy were
preserved; this was a build/safety repair, not a visual redesign.
Linux/openSUSE execution and exact-candidate CI remain unverified locally.
GitHub reported existing dependency alerts during rescue push; their individual
advisories were not audited or resolved in this session.

## Public website and integration

HTTP observations at `https://kazumi7884.co.uk/`: home, search and learning
returned 200 with older page titles/assets. `/work/` returned 404. The served
home did not reference the successor stylesheet. The domain is NOT 1:1 with
this source. No Fasthosts upload, DNS change or Sites publication occurred.
The existing Sites project was only inventoried; it is not this domain's host.

The local candidate is prepared for main. Direct publication of the companion
FOSSLife reconciliation was blocked by automatic approval review; obtain approval
for the exact two source commits before publishing. Do not claim local commits
are already on origin. A source push is separate from a Fasthosts upload.

After approval, fetch both repositories and compare main before a non-force
push. If either moved, reconcile and rerun affected tests. Check exact-commit CI.
Use `docs/PUBLISHING.md` for the separately authorised hosting workflow and retain
the current host backup before any upload. Roll back source with `git revert`;
recover old local reports from the rescue branch without overwriting newer work.

## Local AI continuation

Use the installed Hermes profile through the governed endpoint `9080/v1`.
Read this handoff and applicable source into a fresh session; private chat memory
is not automatically transferred. Use one writer per checkout and the handbook's
bounded workflow. Do not start a scheduler, download models, or use cloud fallback.

For a read-only editorial draft, use the existing environment:

```powershell
.venv\Scripts\python.exe successor\local_review.py --endpoint http://127.0.0.1:9080/v1/chat/completions --model nano
```

This command reads editorial/snapshot files and prints a draft. An actual nano
request returned text, but it was repetitive and unsuitable for publication.
Connectivity is verified; useful editorial or coding quality is NOT. A subsequent
`general` model review timed out at the 90-second request limit; no draft or
source change resulted. Choose an
appropriate installed model, review its factual claims, and run normal checks
before accepting any change. Never auto-publish a generated draft.

Next eligible task: complete approved Git publication, inspect CI, then perform
real-browser review and a separately verified host update. No unattended runner
was enabled. After the timed-out request ended, llama-swap showed no running
models and the host passed all six endpoint checks plus the idle-compute check.
Inference resource pressure remains an unresolved follow-up, not a healthy
sustained-workload claim.
