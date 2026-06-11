scripts/README.md

This folder contains helper scripts for repository maintenance.

publish_issues.py
- Purpose: publish markdown feature files under docs/features as GitHub issues.
- Usage:
    Set environment variables and run:

      setx GITHUB_TOKEN "<token>"  # Windows example
      setx GITHUB_REPOSITORY "owner/repo"
      python scripts/publish_issues.py

- Notes:
  - The script will skip files that already have a `published.json` alongside them.
  - The script checks existing issues in the repository to avoid duplicates.
  - Requires network access and a token with `repo` or `public_repo` scope depending on repo visibility.
