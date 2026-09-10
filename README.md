# Kaz's website — V5.2

The main website source lives in **Kazumi7884/Professional_website**, on **main**.

V5.2 adds a local writing desk and three high-contrast themes.
Run `python tools/site.py studio` to write posts in your browser.
See [the writing guide](docs/WRITING.md) for the complete workflow.
This is the refreshed V5 personal website: learning notebooks, blog posts,
project pages and distinct hobby sections. It builds ordinary HTML, CSS and
JavaScript. The web host does not need Python, Node, a database or containers.

Start with [the update guide](docs/UPDATING.md). It covers pulling, committing,
pushing, conflicts, Windows, Linux, OneDrive and small edits from a phone.

## First run on Windows

Install Python 3.11 or newer and Git, then open a terminal in the parent folder
where you want the project. You can use your OneDrive development folder.

```powershell
git clone https://github.com/Kazumi7884/Professional_website.git
cd Professional_website
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe tools/site.py preview
```

Open **http://localhost:8000**. Stop the preview with **Ctrl+C**. You do not need
to change PowerShell's execution policy or activate the environment.

## First run on Linux

Use your distribution's Python 3.11+ with virtual-environment support and Git.

```bash
git clone https://github.com/Kazumi7884/Professional_website.git
cd Professional_website
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/site.py preview
```

Open **http://localhost:8000**. Python environments are device-specific; rebuild
`.venv` on each device instead of copying one between Windows and Linux.

## Daily workflow

1. Finish any previous edit and check `git status`.
2. Pull with `git pull --ff-only` before starting new changes.
3. Edit Markdown in `content/`, styling in `assets/css/site.css`, or templates.
4. Run `tools/site.py check` using your environment's Python.
5. Preview, review the diff, commit and push.

The preview builds once at startup. After editing, run the build in another
terminal and refresh the browser, or restart preview.

## Commands

Replace `python` below with `.venv\Scripts\python.exe` on Windows or
`.venv/bin/python` on Linux if the environment is not activated.

| Command | What it does |
| --- | --- |
| `python tools/site.py studio` | Open the local writing desk at http://127.0.0.1:8000/__studio/ |
| `python tools/site.py build` | Generate `dist/` from the source |
| `python tools/site.py check` | Build and run 50 page-level review goals plus integrity checks |
| `python tools/site.py preview` | Build and serve on this device at port 8000 |
| `python tools/site.py preview --port 8001` | Use another local port |
| `python tools/site.py new "My first lesson" --section learning/c-sharp/posts` | Create a draft without replacing existing files |
| `python tools/site.py package` | Check and create `deploy/site-upload.zip` for your host |
| `python -m unittest discover -s tests -v` | Run build and content regression tests |

## Where to edit

| Folder/file | Purpose |
| --- | --- |
| `content/` | Authored Markdown pages and post metadata |
| `studio/` and `tools/studio.py` | Local browser editor; excluded from public builds |
| `templates/page.html` | Shared layouts and section rendering |
| `assets/css/site.css` | Theme colours, layout, mobile and print styling |
| `assets/js/` | Menus, theme preference, filters and search |
| `static/assets/images/` | Existing screenshots and charts |
| `static/data/anime.json` | Saved MyAnimeList list |
| `data/` | PC, Steam chart and Phasmophobia snapshots |
| `site.json` | Site name, author, URL and primary menu |
| `dist/` | Generated upload files; rebuild instead of editing |
| `docs/` | Workflow, migration and validation records |

See [writing posts](docs/WRITING.md), [publishing](docs/PUBLISHING.md),
[the overhaul record](docs/OVERHAUL.md) and [validation results](docs/VALIDATION.md).

The post layout resembles a classic forum. It is an authored website: it does
not invent public accounts, replies, visitor counts or a working discussion backend.

See [V5.2 design and repository decisions](docs/V5.2-DESIGN.md) for the theme system and evaluated open-source projects.
