#!/usr/bin/env bash
# Start both services for local development.
# - Backend: FastAPI on :8000
# - Frontend: vite dev (port chosen by @lovable.dev/vite-tanstack-config)
#
# Usage:  ./run.sh
# Stop:   Ctrl+C (both children are killed via trap)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── backend ─────────────────────────────────────────────────────────────────
pushd "$ROOT/backend" >/dev/null

if [[ ! -d .venv ]]; then
  echo "▶ Creating Python venv…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "▶ Installing backend deps…"
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  echo "⚠  backend/.env missing — copy ../.env.example and add your GOOGLE_SAFE_BROWSING_API_KEY"
fi

echo "▶ Starting FastAPI on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
popd >/dev/null

# ── frontend ────────────────────────────────────────────────────────────────
pushd "$ROOT/frontend" >/dev/null

if [[ ! -d node_modules ]]; then
  echo "▶ Installing frontend deps (first run only)…"
  if command -v bun >/dev/null 2>&1; then bun install
  elif command -v pnpm >/dev/null 2>&1; then pnpm install
  else npm install; fi
fi

echo "▶ Starting Vite dev server (proxying /api → http://localhost:8000)"
if command -v bun >/dev/null 2>&1; then bun run dev &
elif command -v pnpm >/dev/null 2>&1; then pnpm dev &
else npm run dev &
fi
FRONTEND_PID=$!
popd >/dev/null

cleanup() {
  echo ""
  echo "▶ Stopping services…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
