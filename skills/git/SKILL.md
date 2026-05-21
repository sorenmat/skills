---
name: git
description: Git flow rules and conventions. Load when performing any git operation - branching, committing, pushing, opening or merging pull requests, or discussing repository workflow. Enforces never pushing to master/main, never auto-merging PRs, branch-based development, PR-centric workflow, planning before non-trivial action, and test integrity.
---

# Git Flow

Procedural rules for working with git repositories. These are non-negotiable defaults; deviate only when the user explicitly asks for it.

## Core mandates

- **Never push to `master` or `main`.** Flag and discourage any direct commit or push to protected branches. If asked to push to one, stop and ask the user to confirm or to provide a feature branch name.
- **Never merge Pull Requests automatically.** Always leave the merge action to the user. You may open, update, comment on, and review PRs — not merge them.
- **Branch-based development.** All work happens on a dedicated `feature/`, `bugfix/`, `chore/`, or similarly-prefixed branch. If the user starts work on `main`/`master`, propose a branch name and switch before making changes.
- **PR-centric workflow.** Changes are integrated via Pull Requests. Mention peer review and CI checks as part of the suggested flow.
- **Plan before action.** For any non-trivial task, outline an implementation plan and present it for review before writing code or running destructive commands.
- **Test integrity.** It is fine to update tests to match intended code changes. Never remove a valid business validation just to make a test pass. If unsure whether a test assertion encodes real intent, ask the user.

## Inspection is safe; mutation needs intent

- Read-only git commands (`status`, `log`, `diff`, `branch`, `show`, `blame`, `remote -v`) are safe to run freely to gather context.
- Mutating commands (`commit`, `push`, `rebase`, `reset --hard`, `branch -D`, `tag`, `cherry-pick`) require a clear, user-stated intent. State what you are about to do before doing it.
- Never run `git push --force` or `git push --force-with-lease` without an explicit user instruction for *that specific* push.

## Commit hygiene

- Keep commit messages focused: subject line in imperative mood, body explaining *why* (not *what* — the diff shows what).
- One logical change per commit when practical. Avoid grab-bag commits.
- Do not commit generated files, secrets, large binaries, or local-only config. Check `.gitignore` first.

## When opening a PR

- Confirm the branch is not `main`/`master`.
- Summarize the change, link related issues, and call out anything reviewers should focus on (risk areas, migration steps, follow-ups).
- Note explicitly that the user — not the agent — performs the merge.
