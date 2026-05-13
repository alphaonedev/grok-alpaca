.PHONY: dev backend frontend install test lint fmt clean openapi gen-types

install:
	uv sync --all-extras
	cd frontend && npm install

dev:
	@./scripts/run-dev.sh

backend:
	uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend

frontend:
	cd frontend && npm run dev

openapi:
	@uv run python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > frontend/openapi.json
	@echo "Wrote frontend/openapi.json"

gen-types: openapi
	cd frontend && npx openapi-typescript openapi.json -o src/api/types.ts

test:
	uv run pytest backend/tests -v
	cd frontend && npm test -- --run

lint:
	uv run ruff check backend
	uv run black --check backend
	uv run mypy backend/app
	cd frontend && npm run lint
	@echo "Checking no live-trading imports..."
	@! grep -r "from alpaca.trading" backend/app || (echo "FAIL: alpaca.trading imported (read-only project)"; exit 1)
	@! grep -r "TradingClient" backend/app || (echo "FAIL: TradingClient referenced (read-only project)"; exit 1)

fmt:
	uv run ruff check --fix backend
	uv run black backend
	cd frontend && npm run format

clean:
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	rm -rf .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
