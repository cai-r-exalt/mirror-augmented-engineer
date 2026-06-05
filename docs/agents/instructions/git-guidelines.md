# Git Guidelines for Agents and Contributors

<<<<<<< HEAD
Purpose
- Standardize git workflows for humans and automation agents working in this repository.
- Ensure predictable commits, clear PRs, and safe collaboration with agents.

Branching
=======
## Purpose
- Standardize git workflows for humans and automation agents working in this repository.
- Ensure predictable commits, clear PRs, and safe collaboration with agents.

## Branching
>>>>>>> 248d305 (docs(guidelines): add git-guidelines with session commits cleanup)
- Base branch: `main` (protected).
- Feature branches: `feature/<short-descriptor>`
- Bugfix branches: `bugfix/<short-descriptor>`
- Hotfix branches: `hotfix/<short-descriptor>`
- Use concise, hyphenated descriptors, keep branches small and focused.

<<<<<<< HEAD
Commit Messages
=======
## Commit Messages
>>>>>>> 248d305 (docs(guidelines): add git-guidelines with session commits cleanup)
- Use conventional-style: `type(scope): short summary` (e.g., `feat(domain): add User entity`).
- Types: feat, fix, docs, chore, refactor, test, ci.
- Body: when needed, explain rationale and migration steps.
- Footer: reference issue/PR (e.g., `Closes #123`).
- Agent-created commits MUST include the Co-authored-by trailer:
  `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`

<<<<<<< HEAD
Pull Requests
=======
## Session Commits Cleanup
- Agents create multiple intermediate commits during a session (e.g., "WIP", "fix", "review feedback").
- **Before opening a PR, clean up session commits** by squashing or rebasing them into logical, well-described commits.
- Use `git rebase -i` or `git reset --soft HEAD~N` to consolidate commits and craft meaningful messages following the Commit Messages section above.
- The final commit(s) in the PR should represent completed, reviewable units of work—not development breadcrumbs.
- This keeps the repository history clean and makes it easier to understand what changed and why.

## Pull Requests
>>>>>>> 248d305 (docs(guidelines): add git-guidelines with session commits cleanup)
- Open small PRs focused on a single concern.
- Ensure CI passes (tests, linters, type checks) before requesting review.
- Provide a clear description, bullet list of changes, and any migration steps.
- Require at least one approving reviewer for non-trivial changes.
- Prefer squash-and-merge for feature work unless history must be preserved.

<<<<<<< HEAD
Syncing and Rebase
=======
## Syncing and Rebase
>>>>>>> 248d305 (docs(guidelines): add git-guidelines with session commits cleanup)
- Keep branches up-to-date: rebase onto latest `main` (or merge `main`) before final review.
- Resolve conflicts locally, run tests, then push.
- Avoid force-pushing `main` or protected branches.

<<<<<<< HEAD
Merging & Releases
- Merge only when CI green and reviewers approve.
- Tag releases with semantic versioning where appropriate.

Testing & Pre-merge Checks
- Run unit/integration tests and linters locally or via CI.
- Use existing pre-commit hooks; don’t bypass them.
- For infra/migration changes, include a rollback plan in PR description.

Large or Risky Changes
- Split into multiple PRs (API + migration + refactor) where possible.
- Use feature flags for incremental rollout of risky features.

Security & Secrets
- Never commit secrets or credentials. Use environment/config management and vaults.
- If a secret is committed accidentally, rotate it immediately and create a security PR to remove it from history.

Agent-specific notes
=======
## Merging & Releases
- Merge only when CI green and reviewers approve.
- Tag releases with semantic versioning where appropriate.

## Testing & Pre-merge Checks
- Run unit/integration tests and linters locally or via CI.
- Use existing pre-commit hooks; don't bypass them.
- For infra/migration changes, include a rollback plan in PR description.

## Large or Risky Changes
- Split into multiple PRs (API + migration + refactor) where possible.
- Use feature flags for incremental rollout of risky features.

## Security & Secrets
- Never commit secrets or credentials. Use environment/config management and vaults.
- If a secret is committed accidentally, rotate it immediately and create a security PR to remove it from history.

## Agent-specific notes
>>>>>>> 248d305 (docs(guidelines): add git-guidelines with session commits cleanup)
- Agents must run the repository's test suite and linters before committing.
- Agents must not push changes directly to remote; instead create a branch or draft PR for human review and let a human push or merge.
- When an agent opens a PR, include an automated checklist of steps taken (tests, linters, migrations).
- Agent commits should be minimal and reviewed by a human when possible.
- Agents must follow the same commit message format and include the Co-authored-by trailer.
<<<<<<< HEAD

Documentation
- Update AGENTS.md and relevant docs when changing agent behavior or adding new automation.

FAQ
- Q: Should I squash my commits? A: Yes for feature branches; keep main clean.
- Q: How to handle migrations? A: Add explicit migration steps in PR description and run migrations in a controlled environment.

Contact
=======
- **Agents MUST clean up all session commits** (see Session Commits Cleanup section) before opening a PR for human review.

## Documentation
- Update AGENTS.md and relevant docs when changing agent behavior or adding new automation.

## FAQ
- Q: Should I squash my commits? A: Yes for feature branches; keep main clean.
- Q: How to handle migrations? A: Add explicit migration steps in PR description and run migrations in a controlled environment.
- Q: How do I clean up my session commits? A: Use `git rebase -i HEAD~N` (where N is the number of commits to consolidate) to squash and reorder commits into logical units with descriptive messages.

## Contact
>>>>>>> 248d305 (docs(guidelines): add git-guidelines with session commits cleanup)
- If unsure, ask a maintainer or open a draft PR for early feedback.

---
Last updated: 2026-06-05
