# Testing Guidelines

Purpose
- Ensure correctness across Hexagonal layers (Domain, Application, Infrastructure).
- Make tests fast, deterministic, and valuable.

Principles
- Prefer behavior-focused unit tests for Domain.
- Use integration tests for Application and Infrastructure.
- Follow TDD where practical: Red → Green → Refactor.
- Keep tests readable and small.

Testing Pyramid
- Unit (fast, many) — Domain entities, value objects, pure logic.
- Integration (moderate) — Use cases, repositories (with test doubles where possible).
- End-to-end / Infra (few) — DB migrations, external integrations, Testcontainers.

Layer-specific guidance
- Domain
  - No external I/O; use pure objects and deterministic inputs.
  - Use descriptive test names and examples.
- Application
  - Use FastAPI TestClient for router-level tests.
  - Override dependencies for isolation; include one set of integration tests that exercise use-case wiring.
- Infrastructure
  - Use Testcontainers or ephemeral DB instances for realistic integration tests.
  - Run migrations in test setup; seed minimal fixtures.

Test quality
- Aim for >80% coverage but focus on meaningful coverage.
- Tests must be deterministic and avoid sleeps/time-based heuristics.
- Mark truly flaky tests and fix or quarantine them.

Fixtures & Factories
- Centralize factories/fixtures in tests/conftest.py or tests/factories/.
- Use small, explicit fixtures and avoid global mutable state.

CI & PR requirements
- All tests must pass on CI before merging.
- Add/Update tests for new features or bug fixes.
- Include test instructions in PR description when non-obvious.

Running tests
- Use pytest; keep tests runnable locally and in CI.
- Prefer flags: pytest -q --maxfail=1

Failure handling
- Investigate failures promptly; do not re-run to hide issues.

Short checklist for contributors
- [ ] Tests added/updated
- [ ] CI green
- [ ] No flaky tests introduced
- [ ] Docs updated if behavior changed

