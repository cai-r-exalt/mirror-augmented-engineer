#!/usr/bin/env python3
"""Publish feature markdown files under docs/features as GitHub issues.

Usage:
  GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo python scripts/publish_issues.py

Behavior:
 - Scans docs/features recursively for .md files.
 - Skips files that already contain a `published.json` in the same folder.
 - Uses GITHUB_TOKEN and GITHUB_REPOSITORY to call the GitHub REST API.
 - Avoids duplicate issues by checking existing open+closed issues for the same title.
 - Writes docs/features/<feature>/published.json with the created issue number and url.

This is intentionally dependency-free (urllib).
"""

from pathlib import Path
import os
import sys
import json
import time
import urllib.parse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = ROOT / 'docs' / 'features'

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY')  # owner/repo

if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
    print('ERROR: set GITHUB_TOKEN and GITHUB_REPOSITORY (owner/repo) in environment')
    sys.exit(2)

API_BASE = 'https://api.github.com'

# Optional MCP HTTP endpoint
MCP_ENDPOINT = os.environ.get('GITHUB_COPILOT_MCP_ENDPOINT')
MCP_TOKEN = os.environ.get('GITHUB_COPILOT_MCP_TOKEN')

# Build headers for GitHub REST (if token provided)
HEADERS = {}
if GITHUB_TOKEN:
    HEADERS = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
    }

# MCP headers (if MCP token provided)
MCP_HEADERS = {}
if MCP_TOKEN:
    MCP_HEADERS = {
        'Authorization': f'Bearer {MCP_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def list_repo_issues_via_github(owner_repo):
    issues = {}
    page = 1
    while True:
        url = f"{API_BASE}/repos/{owner_repo}/issues?state=all&per_page=100&page={page}"
        req = Request(url, headers=HEADERS, method='GET')
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except HTTPError as e:
            print('Failed to list issues via GitHub API:', e)
            return issues
        if not data:
            break
        for it in data:
            title = it.get('title')
            if title:
                issues[title.strip()] = {'number': it.get('number'), 'url': it.get('html_url')}
        page += 1
        if page > 10:
            break
    return issues


def list_repo_issues_via_mcp(owner_repo):
    issues = {}
    if not MCP_ENDPOINT:
        return issues
    # Best-effort: GET {endpoint}/issues?repository=owner/repo&state=all
    url = MCP_ENDPOINT.rstrip('/') + f"/issues?repository={urllib.parse.quote(owner_repo)}&state=all"
    req = Request(url, headers=MCP_HEADERS, method='GET')
    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print('Failed to list issues via MCP endpoint:', e)
        return issues
    if not isinstance(data, list):
        return issues
    for it in data:
        title = it.get('title')
        if title:
            issues[title.strip()] = {'number': it.get('number'), 'url': it.get('html_url')}
    return issues


def list_repo_issues(owner_repo):
    # Prefer GitHub REST if available, else try MCP, else return empty
    if GITHUB_TOKEN:
        return list_repo_issues_via_github(owner_repo)
    if MCP_ENDPOINT and MCP_TOKEN:
        return list_repo_issues_via_mcp(owner_repo)
    return {}


def create_issue_via_github(owner_repo, title, body):
    url = f"{API_BASE}/repos/{owner_repo}/issues"
    payload = {'title': title, 'body': body}
    data = json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers=HEADERS, method='POST')
    try:
        with urlopen(req) as resp:
            return True, json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        try:
            err = e.read().decode('utf-8')
            return False, json.loads(err)
        except Exception:
            return False, {'message': str(e)}


def create_issue_via_mcp(owner_repo, title, body):
    if not MCP_ENDPOINT or not MCP_TOKEN:
        return False, {'message': 'MCP endpoint/token not configured'}
    url = MCP_ENDPOINT.rstrip('/') + '/issues'
    payload = {
        'repository': owner_repo,
        'title': title,
        'body': body,
        'labels': [],
        'assignees': [],
    }
    data = json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers=MCP_HEADERS, method='POST')
    try:
        with urlopen(req) as resp:
            return True, json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        try:
            err = e.read().decode('utf-8')
            return False, json.loads(err)
        except Exception:
            return False, {'message': str(e)}


def create_issue(owner_repo, title, body):
    # Prefer MCP if configured, else GitHub REST
    if MCP_ENDPOINT and MCP_TOKEN:
        return create_issue_via_mcp(owner_repo, title, body)
    if GITHUB_TOKEN:
        return create_issue_via_github(owner_repo, title, body)
    return False, {'message': 'No publish configuration'}


def scan_and_publish():
    existing = list_repo_issues(GITHUB_REPOSITORY)
    if not FEATURES_DIR.exists():
        print('No docs/features directory found; nothing to publish.')
        return

    md_files = list(FEATURES_DIR.rglob('*.md'))
    if not md_files:
        print('No markdown files found under docs/features')
        return

    for md in sorted(md_files):
        # skip test dirs or files that are not feature issues
        parent = md.parent
        published_file = parent / 'published.json'
        if published_file.exists():
            print(f'Skipping {md} (already published according to {published_file})')
            continue

        text = md.read_text(encoding='utf-8')
        # Extract title (first markdown H1)
        title = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('# '):
                title = line[2:].strip()
                break
        if not title:
            print(f'Skipping {md} (no H1 title found)')
            continue

        if title in existing:
            print(f'Skipping {md} (issue already exists: {existing[title]["url"]})')
            # write small published.json so future runs skip
            published_file.write_text(json.dumps({'number': existing[title]['number'], 'url': existing[title]['url']}, indent=2), encoding='utf-8')
            continue

        print(f'Creating issue for {md} -> "{title}"')
        ok, resp = create_issue(GITHUB_REPOSITORY, title, text)
        if ok:
            num = resp.get('number')
            url = resp.get('html_url')
            print(f'Created issue #{num}: {url}')
            published_file.write_text(json.dumps({'number': num, 'url': url}, indent=2), encoding='utf-8')
            # Be polite to API
            time.sleep(1)
        else:
            print(f'Failed to create issue for {md}:', resp)


if __name__ == '__main__':
    scan_and_publish()
