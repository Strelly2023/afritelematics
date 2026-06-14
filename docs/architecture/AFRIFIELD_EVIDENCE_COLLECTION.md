# AFRI Field Evidence Collection

Status: ACCEPTED REALITY INTERFACE

Classification: NON-AUTHORITATIVE FIELD EVIDENCE INGESTION SURFACE

Purpose: define the governed reality interface used by pilot and field
operations to capture external events as deterministic, replayable,
hash-verifiable evidence.

ADR-0042 introduces Field Evidence Collection as the AfriTech reality
interface. It captures real-world operational events as deterministic,
replayable evidence and binds them to governed dispatch output without granting
truth authority to the collection itself.

## Authority Chain

Field evidence is deliberately outside the authority chain.

```text
Constitution
        |
        v
Deterministic Truth
        |
        v
Replay
        |
        v
Proof
```

The chain means:

- Constitution defines authority.
- Deterministic Truth defines truth.
- Replay validates truth.
- Proof demonstrates truth.

Field evidence supplies reality-bound inputs for replay and proof. It does not
define authority, truth, replay outcome, proof outcome, dispatch, settlement, or
trust score.

## Responsibilities

- capture canonical event sequences for completed mobility operations
- bind field events to a dispatch decision, operation, and selected participant
- enforce hash stability, replay stability, and location plausibility
- preserve event ordering and event identity across export and verification
- produce invariant reports for IA-FIELD-001 through IA-FIELD-006
- export read-only proof artifacts for downstream custody, settlement, trust,
  and external audit surfaces

## Authority Boundary

- field evidence is input only
- field evidence does not define truth, proof, replay, dispatch, or settlement
- field evidence is reference-only and read-only
- field evidence cannot override a dispatch-selected participant
- field evidence cannot mutate operation state after capture
- field evidence cannot create live-money movement or settlement authority
- field evidence cannot certify itself externally

## Canonical Event Types

- GPS
- DRIVER_ACCEPT
- ARRIVAL
- PICKUP
- DROPOFF
- CUSTOMER_CONFIRM
- PAYMENT_CONFIRM

## Required Bindings

Every field evidence collection must bind to:

- `dispatch_id`
- `operation_id`
- `selected_participant_id`
- `event_sequence_id`
- `captured_at`
- `evidence_hash`

The binding is admissible only when the selected participant and operation
match the governed dispatch context.

## Scale-Trust Controls

Field evidence is trusted at scale only when all controls are present:

- deterministic serialization
- stable hashing
- dispatch participant binding
- operation identity binding
- ordered event sequence validation
- replay validation
- proof artifact generation
- read-only export
- invariant report generation
- full-system pilot verification runbook execution

## Verification Surfaces

- ADR: `afritech/governance/adr/ADR-0042-field-evidence-collection.yaml`
- Rule: `afritech/governance/rules/RULE-062-field-evidence-collection.yaml`
- Binding: `afritech/governance/bindings/BIND-040-field-evidence-collection.yaml`
- Implementation: `afritech/mobility/field_evidence.py`
- Runtime validator: `afritech/ci/afritech_field_evidence_runtime_validator.py`
- Tests: `afritech/tests/mobility/test_field_evidence.py`
- Runbook: `docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md`

## Pilot Use

Pilot deployment may use field evidence to demonstrate that real-world activity
was captured, bounded, hashed, replay-checked, and exported. Pilot deployment
must not use field evidence to bypass replay, override proof, override
settlement, or broaden authority.
