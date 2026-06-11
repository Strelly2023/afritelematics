#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${AFRIRIDE_SETUP_HOST:-127.0.0.1}"
PORT="${AFRIRIDE_SETUP_PORT:-8000}"
RUN_INSTALL=0
RUN_POSTGRES=0
BOOT_API=0
SERVER_PID=""

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "FAIL: $*"
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

wait_for_server() {
  local url="http://$HOST:$PORT/health"
  for _ in $(seq 1 30); do
    if curl -sS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

start_server() {
  log "Booting AfriRide API"
  uvicorn afriride_system.api.main:app --host "$HOST" --port "$PORT" >/tmp/afriride_phase1_setup.log 2>&1 &
  SERVER_PID="$!"
  wait_for_server || {
    cat /tmp/afriride_phase1_setup.log >&2 || true
    fail "API failed to boot"
  }
}

http_status() {
  curl -sS -o /tmp/phase1_setup_http.json -w '%{http_code}' "$@"
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --install-deps)
        RUN_INSTALL=1
        ;;
      --with-postgres)
        RUN_POSTGRES=1
        ;;
      --boot-api)
        BOOT_API=1
        ;;
      *)
        fail "unknown argument: $1"
        ;;
    esac
    shift
  done

  cd "$ROOT_DIR"

  require_cmd python3
  require_cmd curl
  require_cmd uvicorn

  log "Checking virtual environment guidance"
  python3 --version

  if [[ "$RUN_INSTALL" == "1" ]]; then
    log "Installing Python requirements"
    pip install -r requirements.txt
  else
    log "Skipping dependency installation (pass --install-deps to enable)"
  fi

  log "Validating psycopg import"
  python3 - <<'PY'
import psycopg
print("psycopg OK")
PY

  log "Validating governed setup runner contract"
  python3 -m afritech.guards.guard_phase1_runbook

  if [[ "$RUN_POSTGRES" == "1" ]]; then
    require_cmd psql
    [[ -n "${AFRIRIDE_DATABASE_URL:-}" ]] || fail "AFRIRIDE_DATABASE_URL is required for --with-postgres"
    log "Checking Postgres connectivity"
    psql "$AFRIRIDE_DATABASE_URL" -c '\conninfo'
    log "Applying governed Postgres schema"
    psql "$AFRIRIDE_DATABASE_URL" -f "$ROOT_DIR/scripts/sql/afriride_postgres_schema_v1.sql" >/tmp/phase1_setup_schema.log
  else
    log "Running in SQLite-baseline mode"
    export AFRIRIDE_DB_PATH="${AFRIRIDE_DB_PATH:-$ROOT_DIR/data/afriride.sqlite3}"
    mkdir -p "$(dirname "$AFRIRIDE_DB_PATH")"
  fi

  if [[ "$BOOT_API" == "1" ]]; then
    start_server
  else
    log "Skipping API boot (pass --boot-api to enable HTTP checks)"
  fi

  if [[ "$BOOT_API" == "1" ]]; then
    log "Checking /health"
    [[ "$(http_status "http://$HOST:$PORT/health")" == "200" ]] || fail "/health did not return 200"

    log "Checking /docs"
    [[ "$(http_status "http://$HOST:$PORT/docs")" == "200" ]] || fail "/docs did not return 200"

    log "Requesting auth token"
    [[ "$(http_status "http://$HOST:$PORT/auth/token" -H 'Content-Type: application/json' -d '{"user_id":"setup-rider","role":"RIDER"}')" == "200" ]] || fail "/auth/token did not return 200"

    TOKEN="$(python3 - <<'PY'
import json
with open("/tmp/phase1_setup_http.json", "r", encoding="utf-8") as fh:
    print(json.load(fh)["token"])
PY
)"

    log "Submitting minimal ride request"
    [[ "$(http_status "http://$HOST:$PORT/passenger/request-ride" \
      -H "Authorization: Bearer $TOKEN" \
      -H 'Content-Type: application/json' \
      -H 'Idempotency-Key: setup-request-1' \
      -d '{"passenger_id":"setup-rider","pickup":"A","destination":"B","ride_id":"setup-test-1"}')" == "200" ]] || fail "ride request did not return 200"
  fi

  log "Phase 1 setup contract PASSED"
}

main "$@"
