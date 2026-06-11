#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://afriride-api.onrender.com}"

if command -v uuidgen >/dev/null 2>&1; then
  RUN_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"
else
  RUN_ID="$(date +%s%N)"
fi

idempotency_key() {
  printf 'live-smoke-%s-%s' "$RUN_ID" "$1"
}

echo "Testing AfriRide live system: $BASE_URL"
echo

check() {
  name="$1"
  shift
  echo "==> $name"
  "$@"
  echo
}

check "Health" \
  curl -i "$BASE_URL/health"

OPERATOR_TOKEN="$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"operator-1","role":"OPERATOR"}' | jq -r '.token')"

RIDER_TOKEN="$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"rider-1","role":"RIDER"}' | jq -r '.token')"

DRIVER_TOKEN="$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"driver-1","role":"DRIVER"}' | jq -r '.token')"

check "Active rides" \
  curl -i "$BASE_URL/rides/active" \
  -H "Authorization: Bearer $OPERATOR_TOKEN"

check "Replay health" \
  curl -i "$BASE_URL/system/replay/health" \
  -H "Authorization: Bearer $OPERATOR_TOKEN"

check "Evidence summary" \
  curl -i "$BASE_URL/system/evidence" \
  -H "Authorization: Bearer $OPERATOR_TOKEN"

check "System guards" \
  curl -i "$BASE_URL/system/guards" \
  -H "Authorization: Bearer $OPERATOR_TOKEN"

check "Driver online" \
  curl -i -X POST "$BASE_URL/driver/status" \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(idempotency_key driver-online)" \
  -d '{"driver_id":"driver-1","online":true}'

echo "Creating test ride..."
RIDE_ID="live-smoke-ride-$RUN_ID"
RIDE_RESPONSE="$(curl -s -X POST "$BASE_URL/passenger/request-ride" \
  -H "Authorization: Bearer $RIDER_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(idempotency_key request-ride)" \
  -d "{\"passenger_id\":\"rider-1\",\"pickup\":\"Point A\",\"destination\":\"Point B\",\"ride_id\":\"$RIDE_ID\"}")"

echo "$RIDE_RESPONSE" | jq .
RIDE_ID="$(echo "$RIDE_RESPONSE" | jq -r '.ride_id // .data.ride_id // empty')"

if [ -z "$RIDE_ID" ]; then
  echo "No ride_id returned. Ride-level proof checks skipped."
  exit 1
fi

check "Assigned rides" \
  curl -i "$BASE_URL/driver/driver-1/rides/assigned" \
  -H "Authorization: Bearer $DRIVER_TOKEN"

check "Ride accept" \
  curl -i -X POST "$BASE_URL/ride/$RIDE_ID/accept" \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(idempotency_key accept)" \
  -d '{"driver_id":"driver-1"}'

check "Driver arrived" \
  curl -i -X POST "$BASE_URL/ride/$RIDE_ID/arrive" \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(idempotency_key arrive)" \
  -d '{"driver_id":"driver-1"}'

check "Ride start" \
  curl -i -X POST "$BASE_URL/ride/$RIDE_ID/start" \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(idempotency_key start)" \
  -d '{"driver_id":"driver-1"}'

check "Ride complete" \
  curl -i -X POST "$BASE_URL/ride/$RIDE_ID/complete" \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(idempotency_key complete)" \
  -d '{"driver_id":"driver-1"}'

check "Ride replay" \
  curl -i "$BASE_URL/ride/$RIDE_ID/replay" \
  -H "Authorization: Bearer $RIDER_TOKEN"

check "Ride evidence" \
  curl -i "$BASE_URL/ride/$RIDE_ID/evidence" \
  -H "Authorization: Bearer $RIDER_TOKEN"

check "Ride receipt" \
  curl -i "$BASE_URL/ride/$RIDE_ID/receipt" \
  -H "Authorization: Bearer $RIDER_TOKEN"

check "Ride ledger receipt" \
  curl -i "$BASE_URL/ride/$RIDE_ID/ledger-receipt" \
  -H "Authorization: Bearer $RIDER_TOKEN"

echo "Live smoke test completed."
