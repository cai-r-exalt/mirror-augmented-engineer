# The Bel'Air's Buvette : building a backend for eXalt famous festival drinks and snacks bar. With Python, AI, and love.

Version française : [README_fr.md](README_fr.md)  
Version española : [README_es.md](README_es.md)

>[!note]
> 
> This project is part of the eXalt IT augmented engineer learning path, located in its [academy](https://example.com).

Hello there and welcome to the Bel'Air's Buvette project repository!

This project is your playground to create a robust backend system for managing the drinks and snacks!

You will build the most fantastic backend using Python.

But more importantly, your new best friend: Github Copilot, your new rubber ducky / overenthusiastic intern pair programmer buddy!

## Project Structure

```
augmented-engineer-python-starter/
 application/      # Entry point — wires domain and infrastructure together
 domain/           # Core business logic and domain model
 infrastructure/   # Adapters, persistence, external integrations
```

## Packages

### `domain`

The heart of the application. Contains all business logic, entities, value objects and domain services.  
This package has **zero** internal dependencies — it's pure Python, no framework required.

### `application`

The entry point. Orchestrates use cases by coordinating domain objects.  
It defines the **ports** (abstract classes / protocols) the infrastructure layer must implement (e.g. repositories, external service contracts).  
Depends only on `domain`.

### `infrastructure`

Provides concrete implementations of the ports defined in `application`.  
This is where persistence (database, filesystem), external API clients, messaging and other technical concerns live.  
Depends on `domain` and `application`.

## Installing the Toolchain

| Tool | Version | Documentation |
|------|---------|---------------|
| Python | 3.13+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| Git | latest | [git-scm.com](https://git-scm.com/downloads) |

> Install uv via `pip install uv` or the [official install script](https://docs.astral.sh/uv/getting-started/installation/).

## Getting Started

### Prerequisites

- Python 3.13+
- uv
- Git

### Fork & Clone

Fork this repository to your own Gitlab account (main branch only), then clone it:

```bash
git clone <YOUR_FORK_URL>
cd augmented-engineer-python-starter
```

### Mirror to GitHub

To properly use advanced AI features with Copilot, mirror this repository to your GitHub account:

```bash
git remote add github <the URL of your new GitHub repository>
git branch -M main
git push -u github main
```

### Install dependencies

```bash
uv sync
```

### Run the tests

```bash
uv run pytest
```

### Run the application

```bash
uv run python -m application.main
```

## Next Steps

Start by following the formation material in the [academy](https://example.com).

Read [FEATURES.md](./FEATURES.md) for the list of user stories and acceptance criteria.

Happy coding!
