---
agent: agent
name: TDD Refactor step
description: This prompt is used to refactor a test scenario that passes in a TDD workflow for an AI agent
argument-hint: Refactor the following test scenario in a TDD workflow for an AI agent: {scenario_description}
tools: ['execute/getTerminalOutput', 'execute/runInTerminal', 'read/problems', 'read/readFile', 'read/terminalSelection', 'read/terminalLastCommand', 'edit/createDirectory', 'edit/createFile', 'edit/editFiles', 'search', 'upstash/context7/*', 'todo']
model: GPT-5 mini (copilot)
---

# Green TDD step prompt

## Input

The input is the JSON output of the Green step. This JSON contains the file paths of the test files that were modified in the Green step.

## Important points

1. Move the test class and any related test code to the appropriate test file if it was not already in the correct location. For example, if the test is for a domain use case, it should be in `tests/domain/`, if it's for an application use case, it should be in `tests/application/`, and so on.
2. Refactor the test code to improve readability, maintainability, and adherence to best practices while ensuring that the test still passes. Such as no code duplication, clear variable and functions naming.
3. Code should conform to coding style and project guidelines.
4. Do not change the behavior of the test or the assertions, only refactor the structure and organization of the code.
5. After refactoring, run the test to confirm it still passes: `uv run pytest tests/<test-file-path> -v`.
6. All tests should stay green after the refactor, no new failing tests should be introduced.
7. Work incrementally, making small refactorings and testing frequently to ensure the test remains passing throughout the process.

## Examples

Example 1 — simple fixture extraction

Input (JSON from Green step):

```json
{ "modified_test_files": ["tests/application/test_place_order.py"] }
```

Before (extracted from `tests/application/test_place_order.py` after Green step):

```python
class TestPlaceOrder:
	def setup_method(self):
		self.user_id = 1
		self.product_id = 42

	def test_place_order_creates_record(self):
		repo = InMemoryOrderRepository()
		service = PlaceOrderService(repo)
		order = Order(user_id=self.user_id, product_id=self.product_id, quantity=1)
		service.place(order)
		assert repo.count() == 1

	def test_place_order_reduces_stock(self):
		repo = InMemoryOrderRepository()
		inventory = InMemoryInventory()
		service = PlaceOrderService(repo, inventory)
		order = Order(user_id=self.user_id, product_id=self.product_id, quantity=1)
		service.place(order)
		assert inventory.get_stock(self.product_id) == 9
```

Problems in this version:
- Duplication of repo/service creation across tests
- Setup uses instance attributes instead of fixtures

After refactor (moved to `tests/application/test_place_order.py` with fixtures):

```python
import pytest

@pytest.fixture
def user_id():
	return 1

@pytest.fixture
def product_id():
	return 42

@pytest.fixture
def repo():
	return InMemoryOrderRepository()

@pytest.fixture
def inventory():
	inv = InMemoryInventory()
	inv.set_stock(42, 10)
	return inv

@pytest.fixture
def service(repo, inventory):
	return PlaceOrderService(repo, inventory)

def build_order(user_id, product_id, quantity=1):
	return Order(user_id=user_id, product_id=product_id, quantity=quantity)

def test_place_order_creates_record(service, repo, user_id, product_id):
	order = build_order(user_id, product_id)
	service.place(order)
	assert repo.count() == 1

def test_place_order_reduces_stock(service, inventory, user_id, product_id):
	order = build_order(user_id, product_id)
	service.place(order)
	assert inventory.get_stock(product_id) == 9
```

Refactor notes:
- Extracted `repo`, `inventory`, and `service` into `pytest` fixtures for reuse.
- Replaced `setup_method` attributes with explicit `pytest` fixtures (`user_id`, `product_id`).
- Added `build_order` helper to make test intent clearer and avoid inline construction duplication.
- Kept assertions and behavior unchanged — only improved structure and readability.

Verification:
- Run the test after refactor: `uv run pytest tests/application/test_place_order.py -v`
- Ensure all tests remain green; no behavior was changed.

Example 2 — moving tests to correct module and parametrize

Input (JSON from Green step):

```json
{ "modified_test_files": ["tests/test_place_order.py"] }
```

Before (`tests/test_place_order.py`):

```python
def test_place_order_happy_path():
	repo = InMemoryOrderRepository()
	service = PlaceOrderService(repo)
	order = Order(user_id=1, product_id=10, quantity=2)
	service.place(order)
	assert repo.count() == 1

def test_place_order_insufficient_stock():
	repo = InMemoryOrderRepository()
	service = PlaceOrderService(repo)
	order = Order(user_id=1, product_id=10, quantity=99)
	with pytest.raises(OutOfStockError):
		service.place(order)
```

Refactor goals:
- This is an application-level test and should live under `tests/application/`.
- Reduce duplication and use `pytest.mark.parametrize` to cover multiple scenarios.

After refactor (moved to `tests/application/test_place_order.py`):

```python
import pytest

@pytest.fixture
def repo():
	return InMemoryOrderRepository()

@pytest.fixture
def service(repo):
	return PlaceOrderService(repo)

@pytest.mark.parametrize(
	"quantity,expect_error",
	[
		(2, None),
		(99, OutOfStockError),
	],
)
def test_place_order_various_quantities(service, repo, quantity, expect_error):
	order = Order(user_id=1, product_id=10, quantity=quantity)
	if expect_error:
		with pytest.raises(expect_error):
			service.place(order)
	else:
		service.place(order)
		assert repo.count() == 1
```

Refactor notes:
- Moved tests to `tests/application/` to match the application scope.
- Combined related scenarios using `parametrize` to make intent explicit and avoid duplicated setup.
- Preserved assertions and exception expectations.

Verification:
- Run `uv run pytest tests/application/test_place_order.py -v` and confirm green.
