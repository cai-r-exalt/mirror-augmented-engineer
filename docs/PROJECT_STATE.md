# Project State — Bel'Air's Buvette

Date: 2026-06-11

Short project overview

- Name: augmented-engineer-python-starter (Bel'Air's Buvette)
- Version: 0.1.0
- Architecture: Hexagonal (Ports & Adapters) with a FastAPI application layer, a pure Domain layer (entities, value objects, use cases) and Infrastructure adapters (persistence, external clients). Project structure follows app/application, app/domain, app/infrastructure with tests split across domain/application/infrastructure.

Recent changes

- Repository scaffold and developer guidance: README updated to include quickstart, development toolchain, and links to academy materials and FEATURES.md. The README emphasizes Python 3.13+, uv for tooling, and test/run commands.
- Formalized feature set: FEATURES.md now contains a comprehensive set of user stories and acceptance rules covering token economy, ordering rules, inventory and stock management, group orders, order lifecycle (change/acknowledge/cancel), transfer of tokens, and notification rules for hydration and safe drinking.
- Agent and contribution conventions: AGENTS.md details the assistant agent role, response markers, development guidelines, testing philosophies for each layer, and documentation/testing style expectations.
- Project metadata: pyproject.toml defines project name and version (0.1.0), Python requirement (>=3.13), dev dependencies (pytest, ruff), pytest testpaths and ruff linting configuration.

New features summary

The FEATURES.md file establishes the product requirements and new functional areas to implement:
- Token economy: two token types (drink, snack/food) with per-day allocations (9 food, 6 drink), no carryover, non-negative balances, and rules for transfers (max 3 tokens transferable) and group pooling.
- Ordering model: multi-item orders with token-based pricing (snacks=1, meals=3, non-alcoholic drinks=0, alcoholic normal=1, premium=2), checks for sufficient tokens, atomic validation against stock, ability to change or cancel unacknowledged orders, and acknowledgement flow with ETA computation.
- Inventory and stock: per-item stock tracking, non-negative quantities, stock decremented only on successful acknowledged orders, and order rejection when any requested item is out of stock.
- Notifications & safety: scheduled hydration reminders (hourly, or every 30 minutes for heavy drinkers) within defined daily windows and notifications upon order status changes.

Summary of documentation updates made

- Reviewed top-level files: README.md, FEATURES.md, AGENTS.md and pyproject.toml for current project state and version. No CHANGELOG/RELEASE files were found at the repository root.
- Added: docs/PROJECT_STATE.md (this file) summarizing the current state, recent changes, and feature highlights. If an existing PROJECT_STATE.md had existed, the file would have been appended instead (preserved prior content). This update does not alter other project files.

Notes and issues

- No top-level changelog or release notes found. If you maintain a CHANGELOG, consider adding it at the repository root to capture future releases.
- The new document is concise and intended as a snapshot; link targets in the doc assume existing docs/ subfolders described in AGENTS.md.

Prepared by: background documentation agent
