# AfriTech Live Partner Demo Flow

Status: LIVE PARTNER DEMO FLOW
Classification: RUNTIME_LINKED_COMMERCIAL_DEMO_SURFACE

Purpose: define the exact live partner demo flow using the runtime proof,
external verification, signed receipt, and trust streaming endpoints now
available in the AfriRide system.

This demo flow is a bounded commercial demonstration surface.
It is not by itself a proof of production-scale deployment.

## Demo Goal

Show a partner that AfriTech can:

- complete a real bounded ride flow
- produce signed proof
- expose independent verification
- stream live trust state
- attach an operational trust threshold to the system

## Demo Assets

- `GET /ride/{ride_id}/replay`
- `GET /ride/{ride_id}/receipt`
- `GET /ride/{ride_id}/evidence`
- `POST /system/external-verify/{ride_id}`
- `GET /system/trust-sla`
- `WS /ws/system/trust`

## Live Demo Sequence

### 1. Set The Frame

Say:

```text
You do not need to trust our dashboard. We will show you the replay, the signed
receipt, the independent verification surface, and the live trust stream.
```

### 2. Show Replay

Call:

- `GET /ride/{ride_id}/replay`

Explain:

- replay reconstructs the ride deterministically
- replay verification fails if event ordering, hash chain, or lifecycle rules break

### 3. Show Signed Receipt

Call:

- `GET /ride/{ride_id}/receipt`

Point to:

- `receipt_hash`
- `signature_validation.signature_mode`
- `signature_validation.all_signatures_valid`

Explain:

- the receipt is a portable trust artifact
- receipt signing prevents silent proof forgery

### 4. Show External Verification

Call:

- `POST /system/external-verify/{ride_id}`

Point to:

- `verification_packet.verification_status`
- `verification_packet.authority_boundary`
- `receipt_signature_validation`

Explain:

- an external reviewer can verify the ride without direct database access
- partner verification remains bounded by replay-backed authority

### 5. Show Trust SLA

Call:

- `GET /system/trust-sla`

Point to:

- `sla_status`
- `trust_score`
- `thresholds`

Explain:

- trust thresholds are operational guarantees
- SLA explains runtime readiness but does not replace replay truth

### 6. Show Live Trust Stream

Connect:

- `WS /ws/system/trust`

Point to:

- `trust_score`
- `replay_failures`
- `hash_chain_failures`
- `sla_status`
- `alerts`

Explain:

- live trust is observable continuously
- the system can surface drift or integrity degradation in real time

## Close

Use:

```text
If this matters to your workflow, the next step is one bounded pilot where your
team verifies one real evidence path live, using the same replay, receipt,
external verification, and trust SLA surfaces shown here.
```

## Authority Boundary

This demo flow permits only this bounded claim:

```text
AfriTech can demonstrate runtime proof, signed receipts, external verification,
and live trust thresholds in one bounded partner session
```

