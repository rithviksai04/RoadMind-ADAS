#!/usr/bin/env bash
# Runs the FastAPI backend (port 8000) and the Next.js frontend (port 3000) together for local dev.
# Requires: python -m roadmind.train && python -m roadmind.evaluate already run once.
set -euo pipefail
cd "$(dirname "$0")"
trap 'kill 0' EXIT
.venv/bin/uvicorn backend.main:app --reload --port 8000 &
(cd frontend && npm run dev -- --port 3000) &
wait
