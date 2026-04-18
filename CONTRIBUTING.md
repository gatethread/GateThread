# Contributing to LLMGate

Thank you for contributing. This document explains the development workflow,
code standards, and PR process. Read it before opening a pull request.

---

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for the local dev stack)
- Ollama (for local LLM features) — [install here](https://ollama.com)
- Git

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_ORG/llmgate.git
cd llmgate
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

`-e` installs the package in editable mode — changes to source files take effect
immediately without reinstalling. `[dev]` includes ruff, pytest, and pip-audit.

### 4. Set up configuration

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your actual values. At minimum you need:
- `gateway.api_key` — generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `cloud.anthropic_api_key` — from [console.anthropic.com](https://console.anthropic.com)

### 5. Start the local dev stack

```bash
docker compose up -d
```

This starts PostgreSQL (with pgvector) and Redis. Check they are healthy:

```bash
docker compose ps
```

Both services should show `healthy` in the Status column.

### 6. Run database migrations

```bash
alembic upgrade head
```

This creates all tables. Run this whenever you pull changes that add new
migration files.

### 7. Start the development server

```bash
uvicorn app.main:app --reload --port 8000
```

`--reload` watches for file changes and restarts automatically.
The API is now available at `http://localhost:8000`.

---

## Running Tests

```bash
pytest
```

Run a specific file:

```bash
pytest tests/unit/test_smoke.py
```

Run with coverage (once pytest-cov is added):

```bash
pytest --cov=app
```

Tests must pass before a PR can be merged. CI runs the full suite on every PR.

---

## Linting and Formatting

We use `ruff` for both linting and formatting. It is configured in `pyproject.toml`.

**Check for lint errors:**

```bash
ruff check .
```

**Auto-fix lint errors where possible:**

```bash
ruff check . --fix
```

**Format code:**

```bash
ruff format .
```

Run both before every commit. CI will reject PRs that fail `ruff check`.

---

## Security Audit

```bash
pip-audit
```

Scans all installed packages against the PyPI advisory database. CI runs this
on every PR. A known critical vulnerability in a dependency blocks the build.

---

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/issue-N-short-description` | `feat/issue-3-gateway-api` |
| Bug fix | `fix/issue-N-short-description` | `fix/issue-4-redaction-false-positive` |
| Infrastructure | `infra/short-description` | `infra/terraform-ec2` |
| Documentation | `docs/short-description` | `docs/readme-quickstart` |

---

## Pull Request Process

1. **One issue per PR.** Do not bundle unrelated changes.
2. **All CI checks must pass** — ruff, pytest, pip-audit.
3. **All acceptance criteria from the issue must be met.** Verify each one
   explicitly in the PR description before requesting review.
4. **No secrets in the diff.** CI does not catch all leaks. Review your own
   diff before opening the PR.
5. **No direct commits to `main`.** Every change goes through a PR.
6. **PR reviewed before merge.** At least one approval required.

---

## Code Standards

The full quality bar is defined in [`.claude/criteria.md`](.claude/criteria.md).

The short version:
- Async everywhere on hot paths — no blocking I/O during request handling
- No raw prompt content in any persistent store — redact first, store second
- No secrets in code — environment variables or AWS SSM only
- No silent failures — every error must be surfaced explicitly
- Tests verify behavior, not implementation

---

## Common Issues

**`ModuleNotFoundError: No module named 'app'`**
You are running pytest from outside the project root, or you forgot `pip install -e .`.
Fix: `cd` to the project root and re-run.

**`docker compose ps` shows PostgreSQL as `unhealthy`**
Wait 30 seconds and check again — pgvector takes longer to initialize than plain PostgreSQL.
If it stays unhealthy: `docker compose logs postgres`.

**`ruff check` fails on import order**
Run `ruff check . --fix` — ruff can fix import ordering automatically.
