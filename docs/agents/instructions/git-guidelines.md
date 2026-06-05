# Git Guidelines for Agents and Contributors

Purpose
- Standardize git workflows for humans and automation agents working in this repository.
- Ensure predictable commits, clear PRs, and safe collaboration with agents.

Branching
- Base branch: `main` (protected).
- Feature branches: `feature/<short-descriptor>`
- Bugfix branches: `bugfix/<short-descriptor>`
- Hotfix branches: `hotfix/<short-descriptor>`
- Use concise, hyphenated descriptors, keep branches small and focused.

Commit Messages
- Use conventional-style: `type(scope): short summary` (e.g., `feat(domain): add User entity`).
- Types: feat, fix, docs, chore, refactor, test, ci.
- Body: when needed, explain rationale and migration steps.
- Footer: reference issue/PR (e.g., `Closes #123`).
- Agent-created commits MUST include the Co-authored-by trailer:
  `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`

Pull Requests
- Open small PRs focused on a single concern.
- Ensure CI passes (tests, linters, type checks) before requesting review.
- Provide a clear description, bullet list of changes, and any migration steps.
- Require at least one approving reviewer for non-trivial changes.
- Prefer squash-and-merge for feature work unless history must be preserved.

Syncing and Rebase
- Keep branches up-to-date: rebase onto latest `main` (or merge `main`) before final review.
- Resolve conflicts locally, run tests, then push.
- Avoid force-pushing `main` or protected branches.

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
- Agents must run the repository's test suite and linters before committing.
- Agents must not push changes directly to remote; instead create a branch or draft PR for human review and let a human push or merge.
- When an agent opens a PR, include an automated checklist of steps taken (tests, linters, migrations).
- Agent commits should be minimal and reviewed by a human when possible.
- Agents must follow the same commit message format and include the Co-authored-by trailer.

Documentation
- Update AGENTS.md and relevant docs when changing agent behavior or adding new automation.

FAQ
- Q: Should I squash my commits? A: Yes for feature branches; keep main clean.
- Q: How to handle migrations? A: Add explicit migration steps in PR description and run migrations in a controlled environment.

Contact
- If unsure, ask a maintainer or open a draft PR for early feedback.

---
Last updated: 2026-06-05
