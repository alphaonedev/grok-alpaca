# Prompt 15 — Tests + CI

## Goal
A green CI pipeline that runs backend tests, frontend tests, type checks, lint, and a playwright e2e smoke test.

## Tasks
1. Backend
   - `pytest` config in `pyproject.toml`: `asyncio_mode = "auto"`, `testpaths = ["backend/tests"]`, custom marker `integration`.
   - Unit tests for every service module (mock external HTTP with `respx` for Alpaca and a fake xAI client).
   - Coverage threshold ≥ 80% on `backend/app/services/`.

2. Frontend
   - `vitest` for hooks/components.
   - `@playwright/test` e2e: app loads, send a chat message against a mocked `/api/v1/chat` SSE endpoint, assert chart + markdown rendered.

3. CI: `.github/workflows/ci.yml`
   - Matrix: `python-version: ["3.11", "3.12"]`, `node-version: ["20", "22"]`.
   - Steps:
     - Checkout
     - Setup uv, `uv sync --all-extras`
     - `uv run ruff check backend`
     - `uv run black --check backend`
     - `uv run mypy backend/app`
     - `make lint` (also runs the no-trading-imports grep)
     - `uv run pytest --cov=backend/app --cov-report=xml`
     - Setup Node, `cd frontend && npm ci`
     - `npm run lint`
     - `npm test -- --run`
     - `npx playwright install --with-deps chromium`
     - `npm run e2e`
     - Upload coverage to Codecov (optional, only if `CODECOV_TOKEN` is configured).

4. Pre-commit: `.pre-commit-config.yaml` with ruff, black, eslint, prettier.

## Acceptance
- `make test` exits 0 locally.
- A push to a branch + `gh pr create` runs CI green.
