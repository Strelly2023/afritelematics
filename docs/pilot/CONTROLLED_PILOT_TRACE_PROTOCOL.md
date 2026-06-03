# CONTROLLED_PILOT_TRACE_PROTOCOL

## Status

```text
Classification:
CONTROLLED PILOT EVIDENCE PROTOCOL

Purpose:
Generate bounded live evidence for AfriRide execution.

Authority:
Non-authoritative operational protocol.

This document does not redefine system truth.
Replay verification remains the source of execution truth.
```

---

# 1. Objective

The purpose of this protocol is to collect admissible pilot evidence from a controlled AfriRide execution run.

The protocol verifies:

```text
device
    ↓
event
    ↓
API
    ↓
receipt
    ↓
replay
    ↓
observation
```

within a bounded operational environment.

---

# 2. Scope

## Included

```text
Driver App
AfriRide API
Receipt Evidence
Replay Evidence
Observation Capture
Pilot Reporting
```

## Excluded

```text
Production readiness claims
Commercial readiness claims
Global deployment claims
Market adoption claims
Performance benchmarking claims
```

---

# 3. Pilot Classification

Successful execution of this protocol permits only:

```text
Controlled Pilot Evidence Collected
```

It does NOT permit:

```text
Production Proven
Production Validated
GA++++
Globally Ready
```

---

# 4. Required Environment

## Device

At least one bound driver device.

Example:

```json
{
  "device_id": "driver_phone_001",
  "role": "driver_device",
  "signed_event_capable": true
}
```

## Driver

At least one identified driver participant.

## API

Live API endpoint reachable.

Example:

```json
{
  "environment": "pilot",
  "api_status": "reachable"
}
```

---

# 5. Required Pilot Trace Directory

```text
traces/
└── pilot_runs/
    └── day_one_003/
        ├── device_registration_snapshot.json
        ├── live_api_config.json
        ├── signed_event_sequence.json
        ├── api_response_receipts.json
        ├── replay_verification_result.json
        ├── driver_app_observation.json
        └── stakeholder_evidence_report.md
```

---

# 6. Pilot Execution Sequence

The following sequence must be observed.

```text
accept
start
location
complete
```

### Accept

Driver accepts assigned ride.

### Start

Driver begins ride.

### Location

Location observation emitted.

### Complete

Driver completes ride.

---

# 7. Evidence Requirements

## Event Evidence

Each event must include:

```text
event_id
ride_id
driver_id
timestamp
signature
```

---

## API Evidence

Each accepted event must produce:

```text
response_code
response_timestamp
request_identifier
```

---

## Receipt Evidence

A completed ride must produce:

```text
receipt_id
ride_id
status=completed
```

---

## Replay Evidence

Replay verification must produce:

```text
replay_id
replay_verified=true
```

---

# 8. Driver App Verification

The Driver App must demonstrate visibility of:

```text
assigned ride
receipt evidence
replay evidence
earnings evidence
```

The Driver App must NOT:

```text
compute pricing
assign drivers
generate receipts
mutate replay
approve replay
authorize payouts
```

---

# 9. Failure Handling

Pilot evidence is invalid if:

```text
receipt missing
replay missing
replay unverified
event rejected without trace
evidence artifact missing
```

---

# 10. Success Criteria

The pilot run succeeds only if:

```text
✓ signed event emitted

✓ API accepted event

✓ receipt generated

✓ replay verified

✓ Driver App displayed evidence

✓ trace artifacts captured

✓ stakeholder report generated
```

---

# 11. Stakeholder Evidence Report

The stakeholder report must contain:

```text
pilot identifier
date
device list
event count
receipt count
replay status
observations
limitations
```

---

# 12. Claim Discipline

Successful execution permits:

```text
Controlled pilot evidence collected.
```

Successful execution does NOT permit:

```text
Production proven.
Production validated.
Globally deployed.
GA++++ certified.
```

---

# 13. Final Classification

If all protocol requirements are satisfied:

```text
Driver App Surface
GA+++ VERIFIED+

Pilot Evidence
CONTROLLED PILOT EVIDENCE COLLECTED
```

If any required artifact is missing:

```text
Pilot Evidence
INCOMPLETE
```

and no evidence claim may be made.

---

# 14. Constitutional Boundary

Final authority remains:

```text
Execution generates behavior.

Replay authorizes truth.
```

Pilot observation may collect evidence.

Pilot observation may not redefine truth.
