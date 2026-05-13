#!/usr/bin/env bash
# Run backend (uvicorn) and frontend (vite) concurrently. Localhost-only.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in keys." >&2
  exit 1
fi

cleanup() {
  echo
  echo "Shutting down..."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://127.0.0.1:8000..."
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend &

echo "Starting frontend on http://127.0.0.1:5173..."
cd frontend && npm run dev -- --host 127.0.0.1 &

wait
