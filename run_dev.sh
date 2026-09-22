#!/usr/bin/env bash
# Runs the FastAPI backend (:8000, internal) and the Next.js frontend (:3000) together for local dev.
# Open ONLY http://localhost:3000 - Next.js proxies /api/* to the backend server-side (see
# frontend/next.config.ts), so the whole app lives on one localhost URL with no CORS involved.
# Requires: python -m roadmind.train && python -m roadmind.evaluate already run once.
set -euo pipefail
cd "$(dirname "$0")"
trap 'kill 0' EXIT
.venv/bin/uvicorn backend.main:app --reload --port 8000 &
(cd frontend && npm run dev -- --port 3000) &
wait
