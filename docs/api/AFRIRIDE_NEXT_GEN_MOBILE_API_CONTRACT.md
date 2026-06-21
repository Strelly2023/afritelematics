# AfriRide Next-Gen Mobile API Contract

Status: NEXT-GEN RIDER AND DRIVER API CONTRACT
Classification: MOBILE_BACKEND_INTERFACE_SPECIFICATION

Purpose: define the backend endpoints required by the next-generation
trust-native AfriRide Rider and Driver React Native apps.

This contract keeps mobile apps as interface-only clients. Dispatch, pricing,
state admission, replay, receipts, evidence, trust scoring, certificates, and
public verification remain server/protocol owned.

## Core Rules

- Mobile write actions must send an idempotency key.
- Mobile state transitions must be admitted by the backend state machine.
- Trust scores must be derived by backend evidence and replay services.
- Public verification must expose bounded proof data only.
- Rider and driver views must read from the same ride truth source.
- Mobile apps must never finalize receipts, replay hashes, ledger truth, or trust scores locally.

## Shared Types

### Trust Summary

```json
{
  "trust_score": 92,
  "verification_status": "PASSED",
  "replay_match": true,
  "evidence_complete": true,
  "receipt_id": "rcpt-ride-5bdca5bf",
  "public_verification_url": "/public/trust/rcpt-ride-5bdca5bf"
}
```

### Replay Timeline Event

```json
{
  "label": "DRIVER_ACCEPTED",
  "verified": true,
  "event_hash": "sha256:...",
  "sequence": 2
}
```

Allowed labels:

```text
REQUESTED
DRIVER_ACCEPTED
ARRIVED
STARTED
COMPLETED
CANCELLED
FAILED
```

### Verification Package Manifest

```json
{
  "package_id": "vpkg-ride-5bdca5bf",
  "receipt_id": "rcpt-ride-5bdca5bf",
  "ride_id": "ride-5bdca5bf",
  "files": [
    "receipt.json",
    "replay.json",
    "evidence.json",
    "certificate.json"
  ],
  "offline_verification": true
}
```

## Authentication

### POST /v1/mobile/auth/session

Creates a rider or driver session.

Request:

```json
{
  "actor_id": "rider-1",
  "role": "RIDER",
  "device_id": "device-ios-001",
  "app_version": "1.0.0",
  "platform": "ios"
}
```

Response:

```json
{
  "session_id": "sess-rider-1",
  "actor_id": "rider-1",
  "role": "RIDER",
  "expires_at": "2026-07-01T00:00:00Z",
  "api_base_url": "https://api.afrtechnology.com"
}
```

## Rider Endpoints

### POST /v1/rider/rides

Requests a ride.

Headers:

```text
Idempotency-Key: ride-request-rider-1-001
Authorization: Bearer <token>
```

Request:

```json
{
  "rider_id": "rider-1",
  "pickup": "Melbourne CBD",
  "dropoff": "Melbourne Airport",
  "ride_type": "Airport",
  "client_event": {
    "local_timestamp": "2026-06-21T09:00:00Z",
    "device_id": "device-ios-001"
  }
}
```

Response:

```json
{
  "ride_id": "ride-5bdca5bf",
  "status": "requested",
  "quoted_total": "AUD 72.00",
  "currency": "AUD",
  "ride_type": "Airport",
  "confirmation_token": "confirm-ride-5bdca5bf",
  "trust_score": 91
}
```

### GET /v1/rider/rides/{ride_id}

Returns the rider status snapshot.

Response:

```json
{
  "ride_id": "ride-5bdca5bf",
  "status": "in_progress",
  "driver_name": "Djuma O",
  "vehicle_label": "Toyota Pilot",
  "eta_text": "3 min",
  "location_text": "Approaching pickup",
  "driver_trust_score": 94,
  "trust_score": 92,
  "trust_summary": {
    "trust_score": 92,
    "verification_status": "PASSED",
    "replay_match": true,
    "evidence_complete": true,
    "receipt_id": "rcpt-ride-5bdca5bf",
    "public_verification_url": "/public/trust/rcpt-ride-5bdca5bf"
  }
}
```

### GET /v1/rider/rides/{ride_id}/receipt

Returns the trust-native receipt summary shown in the Rider app.

Response:

```json
{
  "ride_id": "ride-5bdca5bf",
  "receipt_id": "rcpt-ride-5bdca5bf",
  "status": "completed",
  "distance_text": "22.4 km",
  "total_text": "AUD 72.00",
  "started_at": "2026-06-21T09:12:00Z",
  "completed_at": "2026-06-21T09:45:00Z",
  "trust_score": 92,
  "verification_status": "PASSED",
  "replay_match": true,
  "evidence_complete": true
}
```

### GET /v1/rider/rides/{ride_id}/replay

Returns the rider replay visualization contract.

Response:

```json
{
  "ride_id": "ride-5bdca5bf",
  "replay_id": "rply-ride-5bdca5bf",
  "replay_verified": true,
  "route_summary": "Melbourne CBD to Melbourne Airport",
  "timeline_events": [
    {"label": "REQUESTED", "verified": true, "sequence": 1},
    {"label": "DRIVER_ACCEPTED", "verified": true, "sequence": 2},
    {"label": "ARRIVED", "verified": true, "sequence": 3},
    {"label": "STARTED", "verified": true, "sequence": 4},
    {"label": "COMPLETED", "verified": true, "sequence": 5}
  ],
  "explanation_steps": [
    "Ride request was admitted",
    "Driver acceptance matched assignment state",
    "Trip completion replay matched receipt hash"
  ]
}
```

### GET /v1/rider/rides/history

Returns trust-aware ride history.

Response:

```json
{
  "items": [
    {
      "ride_id": "ride-5bdca5bf",
      "status": "completed",
      "trust_score": 92,
      "verification_status": "PASSED"
    },
    {
      "ride_id": "ride-06c51759",
      "status": "in_progress",
      "trust_score": 88,
      "verification_status": "REVIEW_REQUIRED"
    }
  ]
}
```

## Driver Endpoints

### GET /v1/driver/{driver_id}/availability

Returns driver availability and trust profile summary.

Response:

```json
{
  "driver_id": "driver-1",
  "status": "available",
  "updated_at": "2026-06-21T09:00:00Z",
  "trust_score": 94,
  "verified_rides": 152,
  "replay_consistency_pct": 100
}
```

### POST /v1/driver/{driver_id}/availability

Updates availability.

Request:

```json
{
  "status": "available",
  "client_event": {
    "local_timestamp": "2026-06-21T09:00:00Z",
    "device_id": "driver-device-001"
  }
}
```

Response:

```json
{
  "driver_id": "driver-1",
  "status": "available",
  "updated_at": "2026-06-21T09:00:01Z",
  "trust_score": 94,
  "verified_rides": 152,
  "replay_consistency_pct": 100
}
```

### GET /v1/driver/{driver_id}/ride-queue

Returns available ride requests with rider trust context.

Response:

```json
{
  "items": [
    {
      "ride_id": "ride-5bdca5bf",
      "pickup_text": "Melbourne CBD",
      "dropoff_text": "Melbourne Airport",
      "rider_name": "Rider 1",
      "rider_trust_score": 91,
      "status": "pending",
      "quoted_total_text": "AUD 72.00",
      "eta_text": "15 min"
    }
  ]
}
```

### POST /v1/driver/rides/{ride_id}/accept

Accepts a ride assignment.

Request:

```json
{
  "driver_id": "driver-1",
  "client_event": {
    "local_timestamp": "2026-06-21T09:03:00Z",
    "device_id": "driver-device-001"
  }
}
```

Response:

```json
{
  "ride_id": "ride-5bdca5bf",
  "status": "accepted",
  "rider_name": "Rider 1",
  "pickup_text": "Melbourne CBD",
  "dropoff_text": "Melbourne Airport",
  "next_instruction": "Drive to pickup",
  "trust_score": 92,
  "replay_verified": true
}
```

### POST /v1/driver/rides/{ride_id}/arrive

Marks driver arrival. Response shape matches `TripSnapshot`.

### POST /v1/driver/rides/{ride_id}/start

Starts the trip. Response shape matches `TripSnapshot`.

### POST /v1/driver/rides/{ride_id}/complete

Completes the trip and triggers receipt/replay/evidence finalization.

Response:

```json
{
  "ride_id": "ride-5bdca5bf",
  "status": "completed",
  "rider_name": "Rider 1",
  "pickup_text": "Melbourne CBD",
  "dropoff_text": "Melbourne Airport",
  "next_instruction": "Receipt ready",
  "trust_score": 92,
  "replay_verified": true
}
```

### GET /v1/driver/{driver_id}/earnings

Returns trust-aware earnings.

Response:

```json
{
  "driver_id": "driver-1",
  "period_label": "This week",
  "total_text": "AUD 120.00",
  "ride_count": 10,
  "source": "core_system",
  "verified_ride_count": 10,
  "dispute_count": 0,
  "trust_score": 94
}
```

### GET /v1/driver/{driver_id}/replay-history

Returns driver replay history.

Response:

```json
{
  "items": [
    {
      "ride_id": "ride-5bdca5bf",
      "replay_id": "rply-ride-5bdca5bf",
      "replay_verified": true,
      "completed_at": "2026-06-21T09:45:00Z",
      "trust_score": 92,
      "timeline_events": ["REQUESTED", "ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"]
    }
  ]
}
```

## Operator Dashboard Endpoints

Operator endpoints are read-only dashboard surfaces for pilot leads and fleet
operators. They must aggregate existing receipts, replay, evidence, and public
verification status without allowing the operator UI to mutate proof data.

### GET /v1/operator/dashboard

Returns the high-level trust operations dashboard.

Response:

```json
{
  "fleet_trust_score": 96,
  "active_drivers": 12,
  "verified_rides_today": 48,
  "evidence_packets_today": 212,
  "open_replay_exceptions": 1,
  "replay_exception_rate_pct": 0.8,
  "driver_trust_trend": [
    {"label": "Mon", "score": 93},
    {"label": "Tue", "score": 94},
    {"label": "Wed", "score": 95},
    {"label": "Thu", "score": 96}
  ],
  "public_verification": {
    "status": "operational",
    "checks_today": 37,
    "pass_rate_pct": 100
  },
  "pilot_evidence": {
    "shift_count": 7,
    "gps_signal_loss_events": 0,
    "route_deviation_events": 1,
    "latency_breaches": 0
  }
}
```

UI bindings:

- Fleet Trust -> `fleet_trust_score`, `active_drivers`
- Pilot Evidence -> `evidence_packets_today`, `pilot_evidence`
- Replay Exceptions -> `open_replay_exceptions`, `replay_exception_rate_pct`
- Driver Trust Trends -> `driver_trust_trend[]`
- Public Verification Status -> `public_verification`

### GET /v1/operator/replay-exceptions

Returns the exception queue when the dashboard count is non-zero.

Response:

```json
{
  "items": [
    {
      "ride_id": "ride-06c51759",
      "receipt_id": "rcpt-ride-06c51759",
      "severity": "review",
      "reason": "timeline_event_pending",
      "assigned_team": "pilot-ops"
    }
  ]
}
```

### GET /v1/operator/public-verification/status

Returns health and public proof availability for external verification.

Response:

```json
{
  "status": "operational",
  "last_success_at": "2026-06-21T09:45:00Z",
  "checks_today": 37,
  "pass_rate_pct": 100,
  "private_data_redaction": "enabled"
}
```

## Public Trust Endpoints

### GET /public/trust/{receipt_id}

Returns public verification for a receipt.

Response:

```json
{
  "receipt_id": "rcpt-ride-5bdca5bf",
  "verified": true,
  "trust_score": 92,
  "replay_match": true,
  "evidence_complete": true,
  "certificate_chain_verified": true,
  "private_data_redacted": true
}
```

### GET /public/trust/{receipt_id}/package

Returns the downloadable verification package manifest.

Response:

```json
{
  "mode": "portable_verification_package",
  "package_id": "vpkg-ride-5bdca5bf",
  "receipt_id": "rcpt-ride-5bdca5bf",
  "files": [
    "receipt.json",
    "replay.json",
    "evidence.json",
    "certificate.json"
  ],
  "offline_verification": true
}
```

## Error Contract

All endpoints must use structured errors:

```json
{
  "error": {
    "type": "state_transition_rejected",
    "message": "Trip cannot be completed before it starts.",
    "ride_id": "ride-5bdca5bf",
    "retryable": false
  }
}
```

Required error types:

- `auth_required`
- `role_forbidden`
- `idempotency_conflict`
- `state_transition_rejected`
- `receipt_not_found`
- `verification_failed`
- `public_data_redacted`
- `backend_unavailable`
