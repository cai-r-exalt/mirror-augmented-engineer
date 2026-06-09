---
agent: agent
name: TDD Red step
description: This prompt is used to implement one test scenario that fails in a TDD workflow for an AI agent
argument-hint: Implement the following test scenario in a TDD workflow for an AI agent: {scenario_description}
tools: ['execute/getTerminalOutput', 'execute/runInTerminal', 'read/problems', 'read/readFile', 'read/terminalSelection', 'read/terminalLastCommand', 'edit/createDirectory', 'edit/createFile', 'edit/editFiles', 'search', 'upstash/context7/*', 'todo']
model: GPT-5 mini (copilot)
---

# Red TDD step prompt

## Instructions
1. Analyze the provided scenario description carefully.
2. Check if a test file already exists for the scope of this test scenario. 
   - If it exists, append the new test case.
   - If not, create a new test file in `tests/{layer}/`.
3. Write the test so it accurately reflects the scenario and is expected to fail:
    - for the domain layer: `docs/agents/instructions/domain-testing.instructions.md`
    - for the application layer: `docs/agents/instructions/application-testing.instructions.md`
    - for the infrastructure layer: `docs/agents/instructions/infrastructure-testing.instructions.md`
4. Run the test to confirm it fails: `uv run pytest tests/<test-file-path> -v`.
5. Test should expose the given/when/then behavior clearly in the test code structure and assertions.
6. There is no need to test the existence of a class or function, the test should focus on the expected behavior and outcomes of the scenario.

## Requirements
- **CRITICAL**: **NEVER** implement any production code. Your ONLY goal is to write a failing test.
- Use pytest with `assert` statements.
- Use `FakeRepository` pattern for domain tests (subclass the abstract port).

### Avoid — example of what **not** to do

Do not implement production code as part of the Red step. For example, avoid adding a use-case or repository implementation in the repository while writing the failing test:

```python
# BAD: do NOT add production code here during the Red step
# file: app/application/use_cases/place_order.py
class PlaceOrderUseCase:
    def __init__(self, order_repository, inventory_repository):
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository

    def execute(self, command):
        # Creating orders or persisting to the database belongs to a later step
        order = self.order_repository.create_order(command.festivalier_id, command.items)
        return order
```

This is exactly what the Red TDD step must avoid — only create tests that fail, do not add production implementations.

## Examples

### Domain test example

Input:
Scenario: Successfully export contacts
Given a user with 20 contacts
When ExportContactsUseCase is executed
Then it returns a result with all 20 contacts

Expected Output — new file `tests/domain/test_export_contacts_use_case.py`:

```python
import pytest
from app.domain.use_cases.export_contacts import ExportContactsUseCase, ExportContactsQuery
from tests.domain.fakes.fake_contact_repository import FakeContactRepository


class TestExportContactsUseCase:
    def setup_method(self):
        self.fake_repo = FakeContactRepository()
        self.use_case = ExportContactsUseCase(self.fake_repo)

    def test_given_20_contacts_when_export_then_returns_all_contacts(self):
        # Given
        for i in range(20):
            self.fake_repo.add_contact(id=f"c-{i}", name=f"Contact {i}", email=f"c{i}@example.com")
        # When
        result = self.use_case.execute(ExportContactsQuery(user_id="user-1"))
        # Then
        assert result is not None
        assert len(result.contacts) == 20
```