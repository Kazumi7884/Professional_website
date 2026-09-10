---
title: Writing desk
description: Create and edit posts with the local writing desk, then publish through the usual Git workflow.
noindex: true
searchable: false
---

The writing desk gives me one place to write posts, save drafts and preview the result. It runs on my own computer.

## Open the writing desk

From the website folder, use the command for your computer.

### Windows

```powershell
.venv\Scripts\python.exe tools/site.py studio
```

### Linux

```bash
.venv/bin/python tools/site.py studio
```

Open **http://127.0.0.1:8000/__studio/** in your browser. First-time setup is in the repository README.

## Write, preview, save

1. Choose **New post**, a title and a section.
2. Write using the formatting buttons. Choose **Preview** to check your post.
3. Choose **Save draft** to keep it out of the public site.
4. When finished, choose **Ready for publishing** and save. **Build site** updates the local website.
5. Check the result, then commit and push your changes using the update guide.

Saving and building do not upload anything to the public website. Drafts stay out of the build, search and RSS feed.
