#!/usr/bin/env sh
set -eu

API_URL="${API_URL:-http://localhost:8000}"
printf '1. Checking TraceFrame...\n'
curl --fail --silent "$API_URL/health"
printf '\n2. Generating a provenance-tracked image...\n'
RESULT="$(curl --fail --silent -X POST "$API_URL/api/generations" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"A refillable trail bottle on warm stone at sunrise, editorial product photography"}')"
printf '%s\n' "$RESULT"
RUN_ID="$(printf '%s' "$RESULT" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
printf '3. Replaying %s...\n' "$RUN_ID"
curl --fail --silent -X POST "$API_URL/api/generations/$RUN_ID/replay" \
  -H 'Content-Type: application/json' -d '{}'
printf '\n4. Provenance history...\n'
curl --fail --silent "$API_URL/api/generations"
printf '\n'
