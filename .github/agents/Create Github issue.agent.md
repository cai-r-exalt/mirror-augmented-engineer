---
name: Create Github issue agent
description: Background agent that drafts an issue using the `create-issue` skill and publishes it to the repository's GitHub via the configured MCP.
argument-hint: |
	Provide an issue payload containing at least a `title` and `body`. Optional fields: `labels`, `assignees`, `files` (paths to include), `issue_template`.
tools: ['read/readFile', 'search', 'edit/createFile', 'edit/editFiles', 'agent/runSubagent', 'github/issue_write', 'github/issue_read', 'github/*', 'mcp_context7_get-library-docs', 'mcp_serena_write_memory', 'upstash/context7/*']
model: GPT-5 mini (copilot)

---

# Create Github issue agent

This agent automates the creation of GitHub issues by: 1) drafting the issue using the `create-issue` skill found at `.github/skills/create-issue`, and 2) publishing the drafted issue to GitHub using the repository's MCP integration.

## Behavior

1. Validate the incoming argument payload. Require `title` and `body`.
2. If `files` are provided, read the files and include their contents (or extracts) when drafting the issue.
3. Invoke the `create-issue` skill (use the skill files under `.github/skills/create-issue`) to produce a final issue markdown. Prefer the `templates/issue.md` template when present.
4. Validate the generated issue with `scripts/validate_issue.py` from the skill folder; if validation fails, return the errors and do not publish.
5. Publish the validated issue to GitHub using the repository's MCP or the agent-exposed GitHub MCP server tools when configured. Publishing preference (highest to lowest):
	- Agent MCP tool (preferred): call the `io_github_github_github-mcp-server-issue_write` tool with `owner`, `repo`, `title`, `body`, `labels`, and `assignees`.
	- MCP HTTP endpoint: set `GITHUB_COPILOT_MCP_ENDPOINT` and `GITHUB_COPILOT_MCP_TOKEN` so the runner can call the MCP HTTP API.
	- Direct API mode: set `GITHUB_TOKEN` and `GITHUB_REPOSITORY` (fallback). The runner will use the GitHub REST API if no MCP tool is available.
6. On success, return a JSON with `url`, `number`, `title`, and `body`.

## Implementation notes for the agent runner

- Prefer calling the skill locally first (format + validation) before calling any external MCP API.
- Use `runSubagent` to execute the skill pipeline if the runner supports subagents. Otherwise, read and execute the skill template files directly from `.github/skills/create-issue`.
- Use `mcp_context7_resolve-library-id` / `mcp_context7_get-library-docs` only if you need to resolve or fetch MCP-specific docs; primary publishing should use the repository's configured MCP interface exposed to agents (for example `upstash/context7/*`).

## Input example

```json
{
	"title": "Bug: incorrect total in place-order",
	"body": "Steps to reproduce...\nExpected...\nActual...",
	"labels": ["bug", "priority:high"],
	"assignees": ["maintainer-username"],
	"files": ["tests/application/test_place_order.py"]
}
```

## Output format

Return a JSON object:

```json
{
	"url": "https://github.com/org/repo/issues/123",
	"number": 123,
	"title": "...",
	"body": "..."
}
```

## Failure handling

- If validation fails, return `{ "errors": [...] }` and do not publish.
- If publish fails, include the MCP error payload in `{ "mcp_error": ... }`.

## Example run steps for a runner

1. Validate input payload.
2. Read required files with `read/readFile`.
3. Run the skill (either via `runSubagent` or by executing the skill's `scripts/validate_issue.py`).
4. If valid, call the MCP publish API exposed to the agent environment (preferred) or fall back to the GitHub REST API and return the resulting issue URL/number.

