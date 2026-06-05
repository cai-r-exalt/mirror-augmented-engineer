# Documentation Guidelines

Purpose
- Keep project documentation accurate, discoverable, and helpful for contributors and consumers.

Scope & Locations
- README.md: high-level project overview, quickstart.
- AGENTS.md: agent behaviors and usage.
- docs/agents/: process, testing, and architecture instructions.
- In-code: docstrings, module/package README where complex.

Style & Tone
- Audience-first: write for new contributors and maintainers.
- Be concise: prefer examples and copy-paste commands.
- Use active voice and present tense.

What to document
- Public API changes (update OpenAPI where applicable).
- Architectural decisions and motivations (short ADR-style notes).
- How to run, test, and debug the code locally.
- Any non-obvious operational steps (migrations, environment variables).

Docstrings & Code comments
- Docstrings for public modules, classes, and functions.
- Prefer short examples in docstrings showing typical usage.

PR & maintenance rules
- Update docs in same PR that changes behavior or public surface.
- Reviews must include a docs check: is there anything users need to know?
- Keep docs in sync with code; remove stale docs promptly.

Formatting & Tools
- Use Markdown for repo docs; keep sections short and linked.
- Prefer runnable examples and copyable commands.

Searchability & Navigation
- Use clear headings and links; add a short summary at top of long pages.

Checklist for doc changes
- [ ] Docs updated in the same PR
- [ ] Examples tested (where feasible)
- [ ] Links verified
- [ ] CI/docs build (if applicable) succeeds

