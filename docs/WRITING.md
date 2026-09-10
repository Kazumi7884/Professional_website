# Writing posts and editing pages

Posts live in `content/`. A file called `_index.md` introduces a section; another
Markdown filename becomes a page. For example,
`content/learning/c-sharp/posts/my-first-lesson.md` becomes
`/learning/c-sharp/posts/my-first-lesson/`.

Create a draft with your environment's Python:

```bash
python tools/site.py new "My first lesson" --section learning/c-sharp/posts
```

For a personal journal entry:

```bash
python tools/site.py new "A weekend on the bike" --section personal/misc/writing/posts
```

The command never overwrites an existing file. New drafts are excluded from the
published site, search and feeds. Set `draft: false` when ready, then build.

## Metadata

```yaml
---
title: My first lesson
description: What I learned while making a small console program.
date: '2026-09-10'
lastmod: '2026-09-10'
entryType: post
draft: false
tags:
  - c-sharp
  - learning
---
```

Use the real original publication date for `date`. Change `lastmod` when you
make a meaningful update. The imported archive contains migration-era dates;
check them against your original notes before correcting historical posts.

Use `entryType: project` for a project and `entryType: resource` for a useful
link or reference. These automatically populate Projects and Resources.

## Article body

Write Markdown below the second `---`. Start body headings with `##` because the
template supplies the page's `h1`. Use `###` for a subsection. The contents list
is generated from these headings.

Put code in fenced blocks and name the language, such as `csharp`, `python`,
`javascript`, `css` or `html`. Keep HTML, CSS and JavaScript examples in separate
blocks. Explain what a block does in the paragraph beside it.

Images belong in `static/assets/images/your-topic/`. Link to them from Markdown
using the public path, for example:

```markdown
![Console output showing the calculated total](/assets/images/your-topic/console-output.webp)
```

Use your own screenshots and photographs when possible. Keep captions factual;
do not present generated examples as work you personally completed. The build
checks image files and records their dimensions automatically.

## Rename a post without breaking old links

Rename the Markdown file, then add the old public address to its metadata:

```yaml
aliases:
  - /learning/c-sharp/posts/old-name/
  - /learning/c-sharp/posts/old-name.html
```

The old addresses become redirects. Update internal links to the new path;
the build also canonicalises known aliases.

## Hobby data

The anime list is a dated snapshot in `static/data/anime.json`. PC data lives in
`data/pc.json`, Steam chart captions in `data/steam.json`, and game notes in
`data/phasmophobia/`. Keep snapshot dates honest. Refreshing the site alone does
not fetch a new list or verify current game mechanics.

The original optional MyAnimeList sync tool is retained:

```bash
python tools/sync_myanimelist.py
```

Set `MAL_USERNAME` and `MAL_CLIENT_ID` in your ignored `.env.local` first. Keep
that file off GitHub. This step contacts the official API; ordinary builds use
the existing snapshot and need no credentials. After a successful sync, review
`static/data/anime.json`, build/check, then commit the changed snapshot.

The public post layout looks like a forum, but posting is done through these
source files. There is no public discussion server or pretend reply counter.
