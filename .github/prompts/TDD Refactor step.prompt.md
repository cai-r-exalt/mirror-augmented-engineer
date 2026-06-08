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

1. Move the test class and any related test code to the appropriate production code file. The class should be renamed adequately. For example, if the test is for a domain use case, it should be in `app/domain/`, if it's for an application use case, it should be in `app/application/`, and so on.
2. Refactor the test code to improve readability, maintainability, and adherence to best practices while ensuring that the test still passes. Such as no code duplication, clear variable and functions naming.
3. Code should conform to coding style and project guidelines.
4. Do not change the behavior of the test or the assertions, only refactor the structure and organization of the code.
5. After refactoring, run the test to confirm it still passes: `uv run pytest tests/<test-file-path> -v`.
6. All tests should stay green after the refactor, no new failing tests should be introduced.
7. Work incrementally, making small refactorings and testing frequently to ensure the test remains passing throughout the process.
8. Do not add test fixtures or any code that usually exists in testing files. The refactor goal is to write production code.
9. Do not add any comments about test or TDD in the code, only refactor the test code into production code with clear naming and structure. Do not touch any comments that were already present in the test files.
10. Clean the test files by removing dead code or dead imports.

## Examples


Example 1 — Move domain use-case test into production use case

- Input (Green-step JSON):

```json
{
  "modified_files": ["tests/test_domain.py"]
}
```

- Expected output (what the refactor step should do):

- Move the minimal passing code from the test into `app/domain/use_cases/place_order.py` as a properly named class `PlaceOrder` or function `place_order()` while keeping behavior identical.
- Rename the test helper class to a clearer test name (e.g., `TestPlaceOrderSuccess`) and update imports to reference the production `PlaceOrder` class.
- Remove duplicated setup code by extracting a small private helper in the production module if the test previously contained logic that belongs to domain behaviour.
- Keep assertions and external behaviour unchanged.


Example 2 — Extract and remove duplication from an application-layer test

- Input (Green-step JSON):

```json
{
  "modified_files": ["tests/test_application.py"]
}
```

- Expected output (what the refactor step should do):

- Identify duplicated mock setup and move the core orchestration code into `app/application/use_cases/validate_order.py` as `validate_order()`.
- Replace duplicated inline mocks in the test with focused, single-line mocks and use clear variable names for the arrangement phase.
- Ensure the test imports the new `validate_order` and still asserts the same interactions with the stock service.
- Run the specific test to confirm it remains green.

Notes:
- Examples show the kind of structural changes expected: move production code out of tests, rename artifacts for clarity, and remove duplication while preserving test assertions.
- Do small, verifiable refactors and run the test frequently.

## Output requirements

The output of this prompt should be in JSON format so that downstream steps can parse it. The JSON MUST contain the following field:
- `modified_files`: a list of file paths that were modified in this refactor step. Include any production or test files changed (for example, `app/domain/use_cases/place_order.py` or `tests/test_domain.py`).

Example output:

```json
{
	"modified_files": ["app/domain/use_cases/place_order.py", "tests/test_domain.py"]
}
```