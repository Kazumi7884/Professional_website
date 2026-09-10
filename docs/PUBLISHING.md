# Publishing the website

The repository contains editable source. The public host needs only the files
generated in `dist/`. GitHub commits and a Fasthosts upload are separate actions.

## Build the upload

Run with the Python executable from your virtual environment:

```bash
python tools/site.py package
```

The command rebuilds, checks the result and creates `deploy/site-upload.zip`.
It stops on failed checks. The archive contains public website files only,
without Git history, source tools, credentials or virtual environments.

## Fasthosts

1. Keep a backup of the currently published files before replacing them.
2. Open the website's document root, previously `/public`, in your hosting file
   manager or SFTP client. Confirm the actual root in your hosting account.
3. Upload and extract the **contents** of `site-upload.zip` there. The root must
   contain `index.html`, not a nested `dist/index.html` folder.
4. Include `.htaccess` if the host uses Apache. It configures the 404 page,
   compression, cache headers and basic browser protection.
5. Check the home page, a learning post, the personal sections and search.
6. Keep the previous upload until you have checked the new pages. Clear old
   orphaned files deliberately after that, using the backup if needed.

If Apache returns a 500 after upload, check the hosting error log. Some shared
hosts disallow individual `.htaccess` directives; remove only the unsupported
directive the log names. The site itself does not require PHP or server code.

## Another static host

Build command: `python -m pip install -r requirements.txt && python tools/site.py check`.
Output directory: `dist`. Python is needed at build time only. Keep the site at
the domain root: the public paths intentionally start with `/`.

Set `site.json` → `url` to the real HTTPS origin **without a trailing slash**
before deploying to a different domain. Rebuild to update canonical URLs, RSS,
the sitemap and structured data. A private preview should not replace the
production canonical origin in the main branch.

Apache headers are not automatically applied on every static host. Configure
the equivalent 404 handling and headers using that host's own settings.

## Repository checks

The supplied GitHub Actions workflow builds and tests on Windows and Linux and
provides an upload artifact. It does not log in to Fasthosts or deploy itself.
If hosted runners cannot start, the same check commands work locally; an
unstarted job is not a successful test.

## Roll back

Restore the previous verified upload on the host for a quick publication
rollback. Separately use `git revert` to undo the source change, then build and
package again. Source rollback and hosting rollback both need to happen if you
want them to match.
