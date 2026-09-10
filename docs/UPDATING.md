# Pull, edit, commit and update

Repository: https://github.com/Kazumi7884/Professional_website

Branch: `main`. Keep this repository as the source of truth. Your OneDrive copy
can remain the working location; Git records the changes you choose to publish.

## What the Git words mean

| Word | Meaning |
| --- | --- |
| Clone | Download a repository, including its change history, for the first time |
| Pull | Bring remote changes into your existing working copy |
| Status | See your branch and changed/untracked files |
| Diff | Read the exact line changes before saving them |
| Add / stage | Choose changes for the next commit |
| Commit | Make a named local checkpoint |
| Push | Upload your local commits to GitHub |
| Branch | Work on a change separately before integrating it |
| Revert | Make a new commit that undoes an earlier commit |

## Update an existing working copy

Open the **repository folder**, not its parent. If you already cloned it, do not
clone another copy over the same files.

```bash
git remote -v
git status --short --branch
git pull --ff-only
```

The remote should name `Kazumi7884/Professional_website`. If status shows local
edits, commit them first or use the unfinished-work steps below. `--ff-only`
stops if the histories need reconciling instead of making a surprise merge.

## Save and upload an edit

Make the changes, run the site check, then read what will be uploaded.

```bash
git diff
git status --short
```

Stage the files you intentionally changed. These are examples; use your real
filenames. A content-only edit does not require staging the stylesheet.

```bash
git add content/learning/c-sharp/posts/my-first-lesson.md
git add assets/css/site.css
git diff --staged
git commit -m "Add first C# lesson and improve notebook spacing"
git push origin main
```

If Git asks for your identity, configure your own name and your GitHub no-reply
email in this repository. Copy the no-reply address from GitHub's email settings.

```bash
git config user.name "YOUR NAME"
git config user.email "YOUR GITHUB NO-REPLY EMAIL"
```

Those are placeholders: replace them before running the commands. For sign-in,
use Git Credential Manager's browser prompt or GitHub Desktop. Do not put a
password or token in a file, remote URL or commit.

## Branches for larger changes

Start from a clean working tree and an updated main branch.

```bash
git switch main
git pull --ff-only
git switch -c improve-learning-layout
```

Edit, check and commit normally, then publish the branch:

```bash
git push -u origin improve-learning-layout
```

Open GitHub and create a pull request from that branch into `main`. Review the
diff and test results, merge it, then update your local main branch:

```bash
git switch main
git pull --ff-only
```

## Pulling while you have unfinished work

Prefer a small work-in-progress commit on your own branch. For a short pause,
you can temporarily stash tracked and untracked changes:

```bash
git stash push -u -m "Before pulling website updates"
git pull --ff-only
git stash pop
```

If applying the stash reports conflicts, the stash is retained. Resolve the
files and check the site before removing it. Ignored files such as `.venv/` and
`.env` are not included by `-u`.

## A push is rejected because GitHub has newer commits

With your own changes committed and status clean:

```bash
git fetch origin
git rebase origin/main
```

If a conflict occurs, open the named file. Compare both versions, keep the
intended combined result and remove the `<<<<<<<`, `=======` and `>>>>>>>`
markers. Then:

```bash
git add path/to/the-resolved-file
git rebase --continue
```

Repeat only for files Git names. To return to where you were before rebasing:

```bash
git rebase --abort
```

After the rebase succeeds, run the site check and `git push origin main`.
Do not use force-push to resolve ordinary website update conflicts.

## Recover an older version

Look at the recent history:

```bash
git log --oneline -12
```

To undo a published commit, copy its short hash and substitute it below:

```bash
git revert COMMIT_HASH
git push origin main
```

This keeps the history. To inspect an older version without changing main,
create a recovery branch at the chosen hash:

```bash
git switch -c inspect-old-site COMMIT_HASH
```

To restore just one file into your current working copy:

```bash
git restore --source COMMIT_HASH -- path/to/file
git diff
```

Check it, then stage and commit the restoration normally. Do not run
`git reset --hard` or `git clean -fd` as routine update commands; they discard work.

## OneDrive and multiple devices

- Keep your chosen project folder in OneDrive and make it available offline.
- Finish the edit, commit and push on device A; allow OneDrive to finish before
  opening that same working copy on device B. Avoid simultaneous Git operations.
- Run `git status` and `git pull --ff-only` when switching devices.
- Use a separate Python virtual environment per device; Windows and Linux
  environments are not interchangeable. The environment may live outside
  OneDrive while the site source stays inside it.
- If OneDrive produces a conflict copy, keep both versions until you compare
  them with the last Git commit. Never resolve a conflict by blindly deleting
  one of the files.

## GitHub Desktop and phone edits

In GitHub Desktop, select the repository, choose **Fetch origin**, then **Pull
origin** when offered. Review the changed-file checkboxes, write a commit
summary, choose **Commit to main**, then **Push origin**. Preview and check with
the Python commands from the README.

On a phone, open a Markdown file on GitHub, use the pencil/Edit control, make a
small change and use **Commit changes**. For a bigger edit, open the repository
in GitHub's web editor with the `.` shortcut or `github.dev`. Prefer a new
branch for edits you cannot preview on the phone. Pull those commits on your
PC before resuming local work.

Committing website source does not automatically upload it to Fasthosts. The
[publishing guide](PUBLISHING.md) explains that separate step.

## V5.2: write from the browser

After pulling and installing the existing requirements, run `python tools/site.py studio`
with your virtual environment's Python. Open http://127.0.0.1:8000/__studio/.
The writing desk saves into `content/`; include those files in your normal commit.
`Build site` refreshes `dist/`, which remains generated output.

For this redesign branch, fetch and switch with a clean working tree:

```bash
git fetch origin
git switch --track origin/codex/v5.2-writing-themes
```

If the branch already exists locally, use `git switch codex/v5.2-writing-themes`.
After the pull request is merged, switch back to main and run `git pull --ff-only`.
