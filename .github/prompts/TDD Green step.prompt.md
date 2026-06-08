---
agent: agent
name: TDD Green step
description: This prompt is used to implement one test scenario that passes in a TDD workflow for an AI agent
argument-hint: Implement the following test scenario in a TDD workflow for an AI agent: {scenario_description}
tools: ['execute/getTerminalOutput', 'execute/runInTerminal', 'read/problems', 'read/readFile', 'read/terminalSelection', 'read/terminalLastCommand', 'edit/createDirectory', 'edit/createFile', 'edit/editFiles', 'search', 'upstash/context7/*', 'todo']
model: GPT-5 mini (copilot)
---

# Green TDD step prompt

Input is a test scenario description that was previously implemented as a failing test in the Red step.

## Important points

1. Implement a minimal amount of production code to make the test pass. Focus on simplicity and only add what is necessary for the test to succeed.
2. Do not add any extra features or functionality beyond what is required for the test scenario.
3. After implementing the code, run the test to confirm it passes: `uv run pytest tests/<test-file-path> -v`.
4. Implement the code in the test class, do not write production code.
5. Do not modify the test code that was written in the Red step, only add the necessary implementation to make it pass.
6. Do not modify any other tests or production code outside of what is necessary for this specific test scenario.

## Examples

### Example (Application layer — make the Red test pass by adding minimal test-local implementation)

Input (failing test that was created in the Red step):

```
# file: application/tests/test_place_order.py  (excerpt)
def test_commande_simple_mojito_en_stock_cree_commande_en_attente_avec_id(self):
  # Given
  cmd = PlaceOrderCommand(festivalier_id="festivalier-1", items=[{"name": "Mojito", "quantity": 1}])

  # When
  result = self.use_case.execute(cmd)

  # Then
  assert result is not None
  assert result.status == "EN_ATTENTE"
  assert getattr(result, "id", None) is not None
```

What to do in the Green step (minimal, local to the test):

- Add a small, test-scoped implementation or adjust the test fakes so the behaviour expected by the assertion is produced.
- Do not modify other production files or unrelated tests.

Output (example change to the same test file to make it pass):

```
# file: application/tests/test_place_order.py (excerpt)
class TestPlaceOrder:
  def setup_method(self):
    # Minimal test-local fakes that satisfy the test expectations.
    class FakeInventoryRepository:
      def is_in_stock(self, item_name: str, quantity: int) -> bool:
        return True

    class FakeOrderRepository:
      def create_order(self, festivalier_id: str, items: list):
        class Order:
          def __init__(self, order_id, status):
            self.id = order_id
            self.status = status

        # Return the exact values the test expects (EN_ATTENTE and a non-none id)
        return Order(order_id="order-1", status="EN_ATTENTE")

    self.fake_inventory = FakeInventoryRepository()
    self.fake_order_repo = FakeOrderRepository()

    self.use_case = PlaceOrderUseCase(
      order_repository=self.fake_order_repo,
      inventory_repository=self.fake_inventory,
    )

  def test_commande_simple_mojito_en_stock_cree_commande_en_attente_avec_id(self):
    # Given
    cmd = PlaceOrderCommand(festivalier_id="festivalier-1", items=[{"name": "Mojito", "quantity": 1}])

    # When
    result = self.use_case.execute(cmd)

    # Then
    assert result is not None
    assert result.status == "EN_ATTENTE"
    assert getattr(result, "id", None) is not None
```

Notes:

- This example follows the project rule to prefer minimal test-local changes in the Green step: the fake repository is adjusted to return the expected status and id so the test passes.
- After applying this change, run the single test to confirm it passes:

```bash
uv run pytest application/tests/test_place_order.py::TestPlaceOrder::test_commande_simple_mojito_en_stock_cree_commande_en_attente_avec_id -q
```

## Output requirements

The output of this prompt should be in JSON format so that the refactor prompt can easily parse it. The JSON should contain the following fields:
- `modified_test_files`: a list of file paths that were modified in this step. These should reference the test files changed (for example files under `tests/` or `application/tests/`) — do not list production files (for example, `application/main.py`).

Example output:

```json
{
  "modified_test_files": ["application/tests/test_place_order.py"]
}
```