#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA_SQL="$ROOT_DIR/scripts/sql/afriride_postgres_schema_v1.sql"
MIGRATOR="$ROOT_DIR/scripts/afriride_sqlite_to_postgres_migrate.py"
DIFF_CHECKER="$ROOT_DIR/scripts/afriride_replay_diff_checker.py"
APP_MODULE="afriride_system.api.main:app"
HOST="${AFRIRIDE_RUNBOOK_HOST:-127.0.0.1}"
PORT="${AFRIRIDE_RUNBOOK_PORT:-8000}"
RIDE_ID="${AFRIRIDE_RUNBOOK_RIDE_ID:-ride-live-postgres-1}"
RIDER_ID="${AFRIRIDE_RUNBOOK_RIDER_ID:-rider-live-1}"
DRIVER_ID="${AFRIRIDE_RUNBOOK_DRIVER_ID:-driver-live-1}"
OPERATOR_ID="${AFRIRIDE_RUNBOOK_OPERATOR_ID:-operator-live-1}"
ARTIFACT_DIR="${AFRIRIDE_RUNBOOK_ARTIFACT_DIR:-$ROOT_DIR/reports/postgres_cutover_$(date +%Y%m%d_%H%M%S)}"
SERVER_PID=""

mkdir -p "$ARTIFACT_DIR"

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "FAIL: $*"
  exit 1
}

require_env() {
  local name="$1"
  [[ -n "${!name:-}" ]] || fail "required environment variable missing: $name"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    log "Stopping API server (pid=$SERVER_PID)"
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

http_json() {
  local output_file="$1"
  shift
  local status
  status="$(curl -sS -o "$output_file" -w '%{http_code}' "$@")"
  printf '%s' "$status"
}

expect_http_200() {
  local name="$1"
  local output_file="$2"
  shift 2
  local status
  status="$(http_json "$output_file" "$@")"
  [[ "$status" == "200" ]] || {
    cat "$output_file" >&2 || true
    fail "$name returned HTTP $status"
  }
}

json_extract() {
  local file="$1"
  local expr="$2"
  python - "$file" "$expr" <<'PY'
import json, sys
path = sys.argv[2].split(".")
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    value = json.load(fh)
for part in path:
    if part:
        value = value[part]
if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("null")
else:
    print(value)
PY
}

wait_for_server() {
  local attempts=30
  local url="http://$HOST:$PORT/docs"
  for _ in $(seq 1 "$attempts"); do
    if curl -sS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

issue_token() {
  local user_id="$1"
  local role="$2"
  local output_file="$3"
  expect_http_200 "token issuance for $role" "$output_file" \
    "http://$HOST:$PORT/auth/token" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$user_id\",\"role\":\"$role\"}"
  json_extract "$output_file" "token"
}

apply_schema() {
  log "Applying Postgres schema"
  psql "$AFRIRIDE_DATABASE_URL" -f "$SCHEMA_SQL" \
    >"$ARTIFACT_DIR/schema_apply.log" 2>&1 || {
      cat "$ARTIFACT_DIR/schema_apply.log" >&2 || true
      fail "schema apply failed"
    }
}

check_tables() {
  log "Checking required tables"
  psql "$AFRIRIDE_DATABASE_URL" -Atc "
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename IN (
        'drivers',
        'rides',
        'ride_events',
        'trace_events',
        'idempotency_records',
        'replay_snapshots',
        'evidence_records',
        'receipt_records'
      )
    ORDER BY tablename;
  " >"$ARTIFACT_DIR/table_check.txt"
  local count
  count="$(wc -l < "$ARTIFACT_DIR/table_check.txt" | tr -d ' ')"
  [[ "$count" == "8" ]] || {
    cat "$ARTIFACT_DIR/table_check.txt" >&2 || true
    fail "expected 8 required tables, found $count"
  }
}

run_migration() {
  log "Running SQLite -> Postgres migration with verification"
  python "$MIGRATOR" \
    --sqlite-path "$AFRIRIDE_SQLITE_SOURCE" \
    --postgres-url "$AFRIRIDE_DATABASE_URL" \
    --truncate-target \
    --verify \
    >"$ARTIFACT_DIR/migration.log" 2>&1 || {
      cat "$ARTIFACT_DIR/migration.log" >&2 || true
      fail "migration failed"
    }
}

run_diff_checker() {
  log "Running replay diff checker"
  python "$DIFF_CHECKER" \
    --source "$AFRIRIDE_SQLITE_SOURCE" \
    --target "$AFRIRIDE_DATABASE_URL" \
    >"$ARTIFACT_DIR/preboot_diff.json" || fail "replay diff checker failed"
  [[ "$(json_extract "$ARTIFACT_DIR/preboot_diff.json" "ok")" == "true" ]] || {
    cat "$ARTIFACT_DIR/preboot_diff.json" >&2 || true
    fail "pre-boot replay diff mismatch"
  }
}

start_server() {
  log "Starting Postgres-backed API"
  AFRIRIDE_DATABASE_URL="$AFRIRIDE_DATABASE_URL" \
    uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" \
    >"$ARTIFACT_DIR/api_server.log" 2>&1 &
  SERVER_PID="$!"
  wait_for_server || {
    cat "$ARTIFACT_DIR/api_server.log" >&2 || true
    fail "API server failed to start"
  }
}

restart_server() {
  cleanup
  SERVER_PID=""
  start_server
}

main() {
  require_env AFRIRIDE_SQLITE_SOURCE
  require_env AFRIRIDE_DATABASE_URL
  [[ -f "$AFRIRIDE_SQLITE_SOURCE" ]] || fail "SQLite source file not found: $AFRIRIDE_SQLITE_SOURCE"
  [[ -f "$SCHEMA_SQL" ]] || fail "schema file missing: $SCHEMA_SQL"
  [[ -f "$MIGRATOR" ]] || fail "migrator missing: $MIGRATOR"
  [[ -f "$DIFF_CHECKER" ]] || fail "diff checker missing: $DIFF_CHECKER"

  require_cmd python
  require_cmd curl
  require_cmd psql
  require_cmd uvicorn

  log "Artifacts will be stored in $ARTIFACT_DIR"
  log "Validating psycopg import"
  python - <<'PY' >/dev/null
import psycopg
PY

  apply_schema
  check_tables
  run_migration
  run_diff_checker
  start_server

  log "Issuing auth tokens"
  RIDER_TOKEN="$(issue_token "$RIDER_ID" "RIDER" "$ARTIFACT_DIR/rider_token.json")"
  DRIVER_TOKEN="$(issue_token "$DRIVER_ID" "DRIVER" "$ARTIFACT_DIR/driver_token.json")"
  OPERATOR_TOKEN="$(issue_token "$OPERATOR_ID" "OPERATOR" "$ARTIFACT_DIR/operator_token.json")"

  log "Setting driver online"
  expect_http_200 "driver status" "$ARTIFACT_DIR/driver_status.json" \
    "http://$HOST:$PORT/driver/status" \
    -X POST \
    -H "Authorization: Bearer $DRIVER_TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"driver_id\":\"$DRIVER_ID\",\"online\":true}"

  log "Requesting ride"
  expect_http_200 "request ride" "$ARTIFACT_DIR/request_ride.json" \
    "http://$HOST:$PORT/passenger/request-ride" \
    -X POST \
    -H "Authorization: Bearer $RIDER_TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"passenger_id\":\"$RIDER_ID\",\"pickup\":\"Pilot Pickup\",\"destination\":\"Pilot Destination\",\"ride_id\":\"$RIDE_ID\"}"
  [[ "$(json_extract "$ARTIFACT_DIR/request_ride.json" "status")" == "REQUESTED" ]] || \
    fail "ride request did not return REQUESTED"

  log "Accepting ride"
  expect_http_200 "accept ride" "$ARTIFACT_DIR/ride_accept.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/accept" \
    -X POST \
    -H "Authorization: Bearer $DRIVER_TOKEN"

  log "Marking driver arrived"
  expect_http_200 "driver arrived" "$ARTIFACT_DIR/ride_arrive.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/arrive" \
    -X POST \
    -H "Authorization: Bearer $DRIVER_TOKEN"

  log "Starting ride"
  expect_http_200 "start ride" "$ARTIFACT_DIR/ride_start.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/start" \
    -X POST \
    -H "Authorization: Bearer $DRIVER_TOKEN"

  log "Completing ride"
  expect_http_200 "complete ride" "$ARTIFACT_DIR/ride_complete.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/complete" \
    -X POST \
    -H "Authorization: Bearer $DRIVER_TOKEN"

  log "Fetching replay/evidence/receipt before restart"
  expect_http_200 "replay" "$ARTIFACT_DIR/replay_before.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/replay" \
    -H "Authorization: Bearer $OPERATOR_TOKEN"
  expect_http_200 "evidence" "$ARTIFACT_DIR/evidence_before.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/evidence" \
    -H "Authorization: Bearer $OPERATOR_TOKEN"
  expect_http_200 "receipt" "$ARTIFACT_DIR/receipt_before.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/receipt" \
    -H "Authorization: Bearer $OPERATOR_TOKEN"

  [[ "$(json_extract "$ARTIFACT_DIR/evidence_before.json" "verification_status")" == "VERIFIED" ]] || \
    fail "evidence before restart is not VERIFIED"
  local receipt_before
  receipt_before="$(json_extract "$ARTIFACT_DIR/receipt_before.json" "receipt_hash")"

  log "Inspecting trace rows in Postgres"
  psql "$AFRIRIDE_DATABASE_URL" -At -F $'\t' -c "
    SELECT event_id, sequence_id, actor_type, actor_id, ride_id, transition, COALESCE(previous_hash, ''), event_hash
    FROM trace_events
    WHERE ride_id = '$RIDE_ID'
    ORDER BY sequence_id;
  " >"$ARTIFACT_DIR/trace_rows.tsv"
  [[ -s "$ARTIFACT_DIR/trace_rows.tsv" ]] || fail "no trace rows persisted for $RIDE_ID"
  grep -q "$RIDER_ID" "$ARTIFACT_DIR/trace_rows.tsv" || fail "rider identity not found in trace rows"
  grep -q "$DRIVER_ID" "$ARTIFACT_DIR/trace_rows.tsv" || fail "driver identity not found in trace rows"

  log "Restarting API for durability validation"
  restart_server

  log "Fetching replay/evidence/receipt after restart"
  expect_http_200 "replay after restart" "$ARTIFACT_DIR/replay_after.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/replay" \
    -H "Authorization: Bearer $OPERATOR_TOKEN"
  expect_http_200 "evidence after restart" "$ARTIFACT_DIR/evidence_after.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/evidence" \
    -H "Authorization: Bearer $OPERATOR_TOKEN"
  expect_http_200 "receipt after restart" "$ARTIFACT_DIR/receipt_after.json" \
    "http://$HOST:$PORT/ride/$RIDE_ID/receipt" \
    -H "Authorization: Bearer $OPERATOR_TOKEN"

  [[ "$(json_extract "$ARTIFACT_DIR/evidence_after.json" "verification_status")" == "VERIFIED" ]] || \
    fail "evidence after restart is not VERIFIED"
  local receipt_after
  receipt_after="$(json_extract "$ARTIFACT_DIR/receipt_after.json" "receipt_hash")"
  [[ "$receipt_before" == "$receipt_after" ]] || fail "receipt hash changed across restart"

  log "Running final replay diff checker after live write"
  python "$DIFF_CHECKER" \
    --source "$AFRIRIDE_SQLITE_SOURCE" \
    --target "$AFRIRIDE_DATABASE_URL" \
    >"$ARTIFACT_DIR/postboot_diff.json" || fail "post-boot replay diff checker failed"

  log "Runbook completed successfully"
  cat <<EOF

PASS
- schema applied
- migration verified
- replay diff checker clean before boot
- Postgres-backed API booted
- authenticated live ride completed
- evidence VERIFIED before and after restart
- receipt hash stable across restart
- trace rows persisted with JWT-bound identities

Artifacts:
$ARTIFACT_DIR
EOF
}

main "$@"
