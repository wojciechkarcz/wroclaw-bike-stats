- Always read SPECS.md and the latest section of CHANGELOG.md before starting work.

- When I say “start working on issue #<n>”:
    1) Ensure that the `main` branch is up to date with the remote. If not, switch to `main` and run `git pull`:
    2) Fetch the issue JSON:
       - Run: `gh issue view <n> --json number,title,body`
    3) If the command exits non-zero:
       - Capture and surface stderr.
       - If the error contains “401” or “token_expired”, reply: “My session token expired. Please sign in again.”
    4) Check if a branch named `issue-<n>` exists:
       - If not, create it: `git checkout -b issue-<n> main`
       - If yes, switch to it: `git checkout issue-<n>`
    5) Treat the issue body as the task brief and instructions.
    6) Make all changes in this branch only.

- When I say “continue working on issue #<n>”:
    1) Ensure you're on issue's branch `issue-<n>`. If not, checkout to the branch: `git checkout issue-<n>`
    2) Fetch the issue body and all comments for context:
       ```
       gh issue view <n> --json number,title,body,comments --template '
       #{{.number}} {{.title}}

       {{.body}}

       --- Comments ---
       {{range .comments -}}
       {{.createdAt}}  
       {{.body}}

       {{end}}
       '
       ```
    3) Switch to branch `issue-<n>` (create from `main` if missing).
    4) Resume work based on the combined context of issue + comments.

- When I say “update issue #<n>”:
    1) Commit all local changes in branch `issue-<n>`:
       - `git add -A && git commit -m "<commit message> (#<n>)"`
    2) Push changes to GitHub:
       - `git push -u origin issue-<n>`
    3) Summarize the current progress in a short changelog entry (concise list of changes, decisions, or blockers) in a temp file `comment.md`
    4) Add that summary as a GitHub issue comment:
       - `gh issue comment <n> --body-file comment.md`.
       - after executing that command without errors, remove a temp file `comment.md`
    5) This ensures the codebase, branch, and issue discussion are always in sync.

- When I say “create a pr for issue #<n>”:
    1) Commit all local changes in branch `issue-<n>`:
       - `git add -A && git commit -m "<commit message> (#<n>)"`
    2) Push to GitHub:
       - `git push -u origin issue-<n>`
    3) Create a pull request with title `#<n> - <issue title or short summary>` and description containing:
       - The issue body
       - A summary of the work done
       - Any important decisions or notes
       Example:  
       `gh pr create --fill --title "#<n> - <summary>" --body "<description>"`

- General rules:
    - Only modify files inside the repo; do not invent or rely on external services.
    - Do not commit or push any changes unless explicitly instructed. 
    - Keep diffs small and focused on the issue’s scope.
    - After creation of PR to each issue, update CHANGELOG.md:
       - Append new section at top with issue number and title, date, summary, and key decisions/assumptions.
    - Use standard library whenever possible; add minimal dependencies only when justified.
    - Provide small, reproducible test snippets in commit messages if helpful.
    - Ensure consistent branch naming: always `issue-<n>`.
    - Use always conventional commit messages starting with a type: fix, feat, chore, build, ci, docs, test, style, refactor
