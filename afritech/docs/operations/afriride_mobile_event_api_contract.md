# AfriRide Mobile Event API Contract

STATUS: PILOT INGRESS CONTRACT
CLASSIFICATION: STRICT EVENT ADMISSION BOUNDARY

## Boundary

The mobile event API is not a generic mutation API.

It accepts signed mobile event observations and forwards accepted events to the
normalization pipeline.

It must not perform direct runtime state mutation.

## Endpoint

```http
POST /v1/events
```

Request:

```json
{
  "events": [
    {
      "event_id": "evt_123",
      "event_type": "DRIVER_ACCEPTED_RIDE",
      "device_id": "driver_45",
      "entity_id": "ride_88",
      "timestamp": 123456,
      "logical_clock": 12,
      "payload": {
        "ride_id": "ride_88"
      },
      "signature": "abc123"
    }
  ],
  "received_at_ms": 1700000002000
}
```

Response:

```json
{
  "accepted": ["evt_123"],
  "rejected": []
}
```

## Required Event Fields

```text
event_id
event_type
device_id
entity_id
timestamp
logical_clock
payload
signature
```

## Minimal Pilot Event Types

```text
RIDER_REQUESTED_RIDE
RIDER_CANCELLED_RIDE
DRIVER_ACCEPTED_RIDE
DRIVER_ARRIVED
TRIP_STARTED
TRIP_COMPLETED
DRIVER_LOCATION_UPDATE
PAYMENT_TRIGGERED
```

## Strict Ingestion Order

```text
structure validation
-> signature verification
-> duplicate check
-> logical clock pre-check
-> forward to normalization pipeline
```

## Rejection Reasons

```text
invalid_request
invalid_structure
invalid_event_type
invalid_signature
duplicate_event
logical_clock_regression
forbidden_authority_field
```

## Non-Claims

This contract does not claim production API deployment, public mobile launch,
payment finality, identity verification, or completed pilot readiness.
