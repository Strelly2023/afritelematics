#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://afritechnology.com}"
COMPOSE_FILE="${COMPOSE_FILE:-deploy/production/docker-compose.trust-node.yml}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

pass() { echo "[PASS] $1"; }
warn() { echo "[WARN] $1"; }
fail() { echo "[FAIL] $1"; exit 1; }

check_http() {
  local label="$1"
  local url="$2"
  local expected_status="$3"
  local expected_type="$4"
  local body="$TMP_DIR/${label// /_}.body"
  local headers="$TMP_DIR/${label// /_}.headers"
  local result
  result="$(curl -ksS -D "$headers" -o "$body" -w '%{http_code} %{content_type}' "$url")"
  local status="${result%% *}"
  local content_type="${result#* }"
  echo "$label => HTTP=$status TYPE=$content_type"
  [[ "$status" == "$expected_status" ]] || fail "$label expected HTTP $expected_status but got $status"
  [[ "$content_type" == "$expected_type"* ]] || fail "$label expected type $expected_type but got $content_type"
  if [[ "$expected_type" == "application/json" ]]; then
    python3 -m json.tool "$body" >/dev/null || fail "$label did not return valid JSON"
  fi
}

echo "NCP-008 deployment verification"
echo "Base URL: $BASE_URL"
echo

if command -v docker >/dev/null 2>&1; then
  pass "docker available"
  docker compose -f "$COMPOSE_FILE" config >/dev/null
  pass "docker compose config valid"
  docker exec production-nginx-1 nginx -t >/dev/null
  pass "nginx config valid"
  docker compose -f "$COMPOSE_FILE" ps
else
  warn "docker unavailable; skipping compose and container health checks"
fi

check_http "Portal route" "$BASE_URL/novacodepro/operations" "200" "text/html"
check_http "Runtime JSON" "$BASE_URL/novacodepro/config/runtime.json" "200" "application/json"
check_http "Operations overview guard" "$BASE_URL/api/v1/operations/overview" "401" "application/json"
check_http "Operations incidents guard" "$BASE_URL/api/v1/operations/incidents" "401" "application/json"
check_http "Operations actions guard" "$BASE_URL/api/v1/operations/actions" "401" "application/json"

curl -ksS "$BASE_URL/novacodepro/config/runtime.json" > "$TMP_DIR/runtime.json"
python3 -m json.tool "$TMP_DIR/runtime.json" >/dev/null
pass "runtime JSON validated"

docker exec production-afritech-api-1 curl -fsS http://127.0.0.1:8000/openapi.json > "$TMP_DIR/openapi.json"

OPENAPI_JSON="$TMP_DIR/openapi.json" python3 - <<'PY'
import json
import os
from pathlib import Path

document = json.loads(Path(os.environ["OPENAPI_JSON"]).read_text())
paths = sorted(document.get("paths", {}))
operations = [path for path in paths if path.startswith("/api/v1/operations/")]
if not operations:
    raise SystemExit("No NCP-008 operation paths found")
required = [
    "/api/v1/operations/overview",
    "/api/v1/operations/incidents",
    "/api/v1/operations/actions",
    "/api/v1/operations/environments",
]
missing = [path for path in required if path not in paths]
if missing:
    raise SystemExit(f"Missing operations paths: {missing}")
operation_ids = []
for path, methods in document.get("paths", {}).items():
    if not path.startswith("/api/v1/operations/"):
        continue
    for method in methods.values():
        operation_ids.append(method.get("operationId"))
if len(operation_ids) != len(set(operation_ids)):
    raise SystemExit("Duplicate NCP-008 operation IDs detected")
print(f"Operations paths: {len(operations)}")
PY
pass "openapi routes validated"

echo
echo "Live verification summary"
echo "deployment verification: passed"
echo "authenticated functional verification: not-run"
echo "external-provider verification: not-run"
echo "browser E2E: not-run"
echo "accessibility verification: not-run"
echo "resilience verification: not-run"

pass "NCP-008 live verification completed"
