# Writing posts in V5.2

## First-time setup

Use the Windows or Linux setup commands in README.md once. The writing desk
uses the same Python environment and requirements as the website build.

## Open the writing desk

From your website folder on Windows:

```powershell
.venv\Scripts\python.exe tools/site.py studio
```

On Linux:

```bash
.venv/bin/python tools/site.py studio
```

Open **http://127.0.0.1:8000/__studio/**. Keep the terminal running while you
write. Stop it with Ctrl+C. If port 8000 is busy, add `--port 8001` and open the
address printed in the terminal. Zen/Firefox works with the native controls;
there is no browser-specific file-picker API or extra Node setup.

## Create a post

1. Click **New post**.
2. Enter a title. The filename fills itself in; edit it before the first save
   if you want a different address.
3. Select a section. Use **blog** for a general blog post,
   **personal/misc/writing/posts** for your journal, or a learning track's
   **posts** folder for technical notes.
4. Write a short summary, choose a date and add comma-separated tags.
5. Write your text. Select text and use **Bold**, **Italic**, **Link** or the
   other formatting buttons. The code button inserts a fenced block; replace
   `text` after its opening backticks with `csharp`, `ruby`, `r` or your language.
6. Use **Preview** or **Side by side** to check the article. The theme selector
   previews the same three colour systems used by the website.
7. Click **Save draft**, or use Ctrl+S (Cmd+S on macOS).

The template menu inserts an outline at your cursor without replacing your
existing text. Markdown stays editable in any text editor.

## Edit an existing page

Search by title or folder in the left-hand list, then click a page. The desk
preserves existing aliases, custom URLs, layouts and other metadata that is
not shown in the form. Existing filenames are locked to avoid breaking links.
For a deliberate rename, use Git and add a redirect/alias as described below.

The catalogue includes pages, resources and projects as well as posts. Preview
shows the article text; specialised anime, hardware and games layouts should
also be checked with **Build site**, then **View site**.

## Draft recovery and file conflicts

Changes are copied to this browser's local storage while you type. These
recovery copies are not committed, are not synced by OneDrive and can be lost
if browser data is cleared. **Save** is the step that writes your Markdown to
the website folder. **Download Markdown** creates a portable backup.

If a recovery copy exists when the desk opens, choose **Restore unsaved work**.
If another editor or OneDrive changes a file after you opened it, the desk
rejects the save instead of overwriting that newer version. Download your
Markdown, reopen the page, compare the versions and copy your changes back.
Work on one device at a time and let OneDrive finish syncing before switching.

## Make a post publish-ready

1. Add the summary, date and post text.
2. Change Status to **Ready for publishing** and click **Save ready post**.
3. Click **Build site**, then **View site**. Drafts remain excluded from the
   generated website, search index and RSS feed.
4. Run your usual check command and review the diff before committing.

With your environment activated, the shared workflow is:

```bash
python tools/site.py check
git status --short
git diff -- content/
git add content/
git commit -m "Add my new post"
git push
```

Without activation, replace `python` with `.venv\Scripts\python.exe` on Windows
or `.venv/bin/python` on Linux. See UPDATING.md for pulling and resolving conflicts.
Saving, marking ready and building are local actions; they do not upload or
publish the website. See PUBLISHING.md for uploading the generated site.

## Manual editing still works

```bash
python tools/site.py new "My first lesson" --section learning/c-sharp/posts
```

A minimal post file looks like this:

```yaml
---
title: My first lesson
description: What I learned about console input.
date: '2026-09-10'
entryType: post
draft: true
tags:
  - C#
  - learning
---
```

Write Markdown after the closing `---`. Set `draft: false` when ready.
You do not need to edit menus, HTML, an index or the RSS feed for a new post.

For a renamed post, keep the old URL under `aliases` in its metadata, for
example `aliases: [/learning/c-sharp/posts/old-title/]`. Build and check before
publishing. Do not reuse an alias that belongs to another page.
