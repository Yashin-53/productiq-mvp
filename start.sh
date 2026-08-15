#!/usr/bin/env bash
# Convenience launcher for local development.
set -e
echo "Starting backend on :8000 ..."
(cd backend && pip install -r requirements.txt --quiet && python3 -m uvicorn app.main:app --reload --port 8000) &
BACK_PID=$!
echo "Starting frontend on :5173 ..."
(cd frontend && npm install --silent && npm run dev -- --port 5173) &
FRONT_PID=$!
trap "kill $BACK_PID $FRONT_PID" EXIT
wait
