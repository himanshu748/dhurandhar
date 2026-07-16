#!/bin/sh
set -eu

# The published image is a judge-facing evidence viewer. Keep that boundary
# fail-closed even when a hosting service retains stale environment values.
if [ "${DHURANDHAR_PUBLIC_REPLAY:-true}" = "true" ]; then
  export DHURANDHAR_EVENT_LOG=/app/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl
  export DHURANDHAR_SEED_DEMO=false
  export DHURANDHAR_RUNTIME=deterministic
  export DHURANDHAR_ENABLE_CODEX_RUNTIME=false
  export DHURANDHAR_CODEX_APPLY_CHANGES=false
  unset DHURANDHAR_OPERATOR_TOKEN
fi

exec uvicorn app.main:app \
  --app-dir backend \
  --host "${APP_HOST:-0.0.0.0}" \
  --port "${PORT:-${APP_PORT:-8000}}"
