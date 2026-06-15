#!/usr/bin/env python3
"""Create and publish a GitHub issue using the create-issue skill templates and validator.

Usage:
  python create_issue_runner.py payload.json

Payload JSON fields (recommended):
  - title (required)
  - context (required)
  - gherkin (required): Gherkin scenarios text (Feature/Scenario/Given/When/Then)
  - labels (optional): list
  - assignees (optional): list

Publishing:
  - If environment variables `GITHUB_TOKEN` and `GITHUB_REPOSITORY` (owner/repo) are set,
    the script will attempt to create an issue via the GitHub REST API.
  - Otherwise it will write the generated markdown file under `docs/features/` and exit.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# Adjusted ROOT because this script now lives in /scripts
ROOT = Path(__file__).resolve().parents[1]
SKILL_TEMPLATES = ROOT / '.github' / 'skills' / 'create-issue' / 'templates'
VALIDATOR = ROOT / '.github' / 'skills' / 'create-issue' / 'scripts' / 'validate_issue.py'


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9-_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "issue"


def render_issue(title: str, context: str, gherkin: str) -> str:
    tmpl = (SKILL_TEMPLATES / 'issue.md').read_text(encoding='utf-8')
    content = tmpl
    content = content.replace('{{title}}', title)
    content = content.replace('{{context}}', context)
    placeholder = '{{gherkin scenarios ; each scenario must get a header with a number}}'
    content = content.replace(placeholder, gherkin)
    return content


def write_issue_file(title: str, content: str) -> Path:
    slug = slugify(title)
    feature_dir = ROOT / 'docs' / 'features' / slug
    feature_dir.mkdir(parents=True, exist_ok=True)
    file_path = feature_dir / f"{slug}.md"
    file_path.write_text(content, encoding='utf-8')
    return file_path


def validate_issue_file(path: Path) -> (bool, str):
    # Call the validator script
    proc = subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    ok = proc.returncode == 0
    return ok, out


def publish_github_issue(repo: str, token: str, title: str, body: str, labels=None, assignees=None):
    owner_repo = repo
    api_url = f"https://api.github.com/repos/{owner_repo}/issues"
    payload = {
        'title': title,
        'body': body,
    }
    if labels:
        payload['labels'] = labels
    if assignees:
        payload['assignees'] = assignees

    data = json.dumps(payload).encode('utf-8')
    req = Request(api_url, data=data, headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
    }, method='POST')

    try:
        with urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            return True, json.loads(resp_body)
    except HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            return False, json.loads(err_body)
        except Exception:
            return False, {'message': str(e)}


def publish_via_mcp_github_copilot(
    endpoint: str,
    token: str,
    owner_repo: str,
    title: str,
    body: str,
    labels=None,
    assignees=None,
) :
    """Publish issue via the GitHub Copilot MCP HTTP endpoint.

    Expected: POST {endpoint}/issues with JSON payload. Uses Bearer token auth.
    This is best-effort — actual MCP contract may differ; configure env vars accordingly.
    """
    api_url = endpoint.rstrip('/') + '/issues'
    payload = {
        'repository': owner_repo,
        'title': title,
        'body': body,
        'labels': labels or [],
        'assignees': assignees or [],
    }
    data = json.dumps(payload).encode('utf-8')
    req = Request(api_url, data=data, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }, method='POST')
    try:
        with urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            return True, json.loads(resp_body)
    except HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            return False, json.loads(err_body)
        except Exception:
            return False, {'message': str(e)}


def main():
    if len(sys.argv) != 2:
        print("Usage: python create_issue_runner.py payload.json")
        sys.exit(2)

    payload_path = Path(sys.argv[1])
    if not payload_path.exists():
        print(f"Payload file not found: {payload_path}")
        sys.exit(2)

    payload = json.loads(payload_path.read_text(encoding='utf-8'))
    title = payload.get('title')
    context = payload.get('context') or payload.get('body')
    gherkin = payload.get('gherkin')
    labels = payload.get('labels')
    assignees = payload.get('assignees')

    if not title or not context or not gherkin:
        print('ERROR: payload must include `title`, `context` (or `body`) and `gherkin`.')
        sys.exit(2)

    issue_markdown = render_issue(title, context, gherkin)
    issue_file = write_issue_file(title, issue_markdown)

    print(f"Wrote draft issue to {issue_file}")

    valid, validator_output = validate_issue_file(issue_file)
    print('Validator output:')
    print(validator_output)
    if not valid:
        print('Issue validation failed; not publishing.')
        sys.exit(3)

    # Attempt to publish via MCP (GitHub Copilot MCP) if configured, else fall back to GitHub API
    mcp_endpoint = os.environ.get('GITHUB_COPILOT_MCP_ENDPOINT')
    mcp_token = os.environ.get('GITHUB_COPILOT_MCP_TOKEN')
    gh_token = os.environ.get('GITHUB_TOKEN')
    gh_repo = os.environ.get('GITHUB_REPOSITORY')  # expected owner/repo

    if mcp_endpoint and mcp_token and gh_repo:
        print('Publishing via GitHub Copilot MCP...')
        success, resp = publish_via_mcp_github_copilot(
            mcp_endpoint,
            mcp_token,
            gh_repo,
            title,
            issue_markdown,
            labels,
            assignees,
        )
        if success:
            print('Published via MCP:')
            print(json.dumps(resp, indent=2))
            sys.exit(0)
        else:
            print('MCP publish failed; falling back to direct GitHub API. MCP response:')
            print(json.dumps(resp, indent=2))

    if gh_token and gh_repo:
        print('Publishing via GitHub REST API...')
        success, resp = publish_github_issue(gh_repo, gh_token, title, issue_markdown, labels, assignees)
        if success:
            print('Published issue:')
            print(json.dumps(resp, indent=2))
            sys.exit(0)
        else:
            print('Publish failed:')
            print(json.dumps(resp, indent=2))
            sys.exit(4)

    print('No publish configuration found; skipping publish.')
    print(json.dumps({'file': str(issue_file)}))
    sys.exit(0)


if __name__ == '__main__':
    main()
