# AfriTech Full-System Verification Runbook

Status: PILOT DEPLOYMENT VERIFICATION RUNBOOK

Classification: CONSTITUTIONALLY ENFORCED TRUST-AT-SCALE OPERATIONS SURFACE

Purpose: define the full verification sequence required before, during, and
after a bounded pilot deployment using the constitution, Eight Pillars,
ADR-0042 Field Evidence Collection, ADR-0043 reconciliation, ADR-0044 operator
decision protocol, replay, proof, CI, and operator closeout gates.

This runbook verifies readiness for a bounded pilot. It does not claim
unbounded production scale. Scale trust is earned by passing the same
constitutional checks repeatedly across controlled field operations.

## Authority Model

All verification uses the canonical authority chain:

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

Doctrine:

```text
Constitution defines authority.
Deterministic Truth defines truth.
Replay validates truth.
Proof demonstrates truth.

Execution performs actions.
Trust influences decisions.
Observability explains.
Intelligence advises.
Markets incentivize.
Federation connects.
Products consume governed capability.
```

Field evidence is a non-authoritative reality interface. It captures external
events for replay and proof. It does not define truth, dispatch, settlement,
trust, intelligence, or certification.

## Verification Goal

The pilot may proceed only when the system can demonstrate:

- constitutional doctrine is machine-checked
- Eight Pillars doctrine is enforced in CI
- ADR-0042 reality interface is accepted and bound to RULE-062 and BIND-040
- field evidence is deterministic, hash-stable, read-only, and replayable
- replay validates canonical truth
- proof demonstrates truth externally
- deployment scope is bounded and reversible
- operators can collect, review, export, and close evidence without bypassing authority

## Required Artifacts

- `afritech/constitution/AFRITECH_CONSTITUTION_V1.yaml`
- `docs/architecture/AFRITECH_OPERATING_MODEL.md`
- `afritech/ci/afritech_eight_pillars_validator.py`
- `afritech/governance/adr/ADR-0042-field-evidence-collection.yaml`
- `afritech/governance/rules/RULE-062-field-evidence-collection.yaml`
- `afritech/governance/bindings/BIND-040-field-evidence-collection.yaml`
- `docs/architecture/AFRIFIELD_EVIDENCE_COLLECTION.md`
- `afritech/mobility/field_evidence.py`
- `afritech/tests/mobility/test_field_evidence.py`
- `afritech/ci/constitutional_pipeline.py`
- `afritech/simulation/pilot_dataset.py`
- `docs/operations/AFRITECH_FIRST_LIVE_DEPLOYMENT_SCENARIO.md`
- `afritech/mobility/reconciliation.py`
- `docs/architecture/AFRISIMULATION_REALITY_RECONCILIATION.md`
- `afritech/ci/afritech_operator_decision_protocol_validator.py`
- `docs/architecture/AFRIOPERATOR_DECISION_PROTOCOL.md`
- `docs/operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md`
- `docs/operations/AFRITECH_DOMAIN_TLS_CUTOVER.md`
- `docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md`
- `docs/operations/AFRITECH_EC2_FIRST_TEST_RUN.md`
- `docs/operations/AFRITECH_FIRST_OPERATOR_DECISION_SCENARIO.md`
- `afritech/ci/afritech_live_pilot_execution_validator.py`

## Phase 0. Scope Lock

Objective: prevent accidental expansion before verification starts.

Required checks:

- pilot corridor is named
- pilot date window is named
- operator owner is named
- evidence reviewer is named
- deployment rollback owner is named
- product surfaces are bounded
- live-money movement is either disabled or explicitly governed by the AfriPay boundary

Exit gate:

```text
GO only if scope, owners, rollback path, and live-money boundary are explicit.
```

## Phase 1. Constitutional And Doctrine Verification

Run:

```bash
python -m afritech.ci.afritech_constitution_v1_validator
python -m afritech.ci.afritech_constitutional_pillars_validator
python -m afritech.ci.afritech_eight_pillars_validator
```

Required result:

- Constitution validates
- four constitutional pillars validate
- four ecosystem pillars validate
- authority chain prints as `Constitution -> Deterministic Truth -> Replay -> Proof`
- AfriTrust, AfriCloud, AfriAI, AfriPay, and AfriSync remain infrastructure capabilities

Exit gate:

```text
GO only if doctrine is enforced by CI.
```

## Phase 2. Reality Interface Verification

Run:

```bash
python -m afritech.ci.afritech_field_evidence_runtime_validator
python -m afritech.ci.afritech_pilot_dataset_simulation_validator
python -m afritech.ci.afritech_reconciliation_validator
python -m afritech.ci.afritech_operator_decision_protocol_validator
python -m afritech.ci.afritech_live_pilot_execution_validator
python -m pytest afritech/tests/mobility/test_field_evidence.py
```

Required result:

- ADR-0042 runtime validator passes
- airport pilot dataset simulation passes
- reconciliation passes in shadow mode
- operator decision protocol validates
- live pilot execution checklist validates
- first live deployment scenario is `airport-zone-001`
- first raw field signal becomes a non-authoritative field event
- field evidence happy path passes
- raw signal ingestion builds collection, proof, and invariant report artifacts
- participant mismatch is rejected
- authority injection is rejected
- missing event sequence is rejected
- exported evidence and proof are hash-stable
- invariant report validates IA-FIELD-001 through IA-FIELD-006
- field evidence does not mutate dispatch

Exit gate:

```text
GO only if field evidence remains read-only, replayable, hash-verifiable, and non-authoritative.
```

## Phase 3. Replay, Proof, And Evidence Verification

Run:

```bash
python -m afritech.ci.replay_authority_validator
python -m afritech.ci.replay_integrity_validator
python -m afritech.ci.proof_surface_validator
python -m afritech.ci.receipt_validator
python -m afritech.ci.trace_reconstruction_validator
```

Required result:

- replay authority validates
- replay integrity validates
- proof surface validates
- receipts validate
- traces reconstruct deterministically

Exit gate:

```text
GO only if replay validates truth and proof demonstrates truth without field evidence redefining either.
```

## Phase 4. Pilot Deployment Verification

Run:

```bash
python -m afritech.ci.afritech_pilot_dataset_simulation_validator
python -m afritech.ci.afritech_reconciliation_validator
python -m afritech.ci.afritech_operator_decision_protocol_validator
python -m afritech.ci.afriride_pilot_execution_checklist_validator
python -m afritech.ci.afriride_pilot_metrics_dashboard_validator
python -m afritech.ci.afriride_execution_grade_pilot_system_validator
python -m afritech.ci.afriride_field_execution_transition_boundary_validator
```

Required result:

- airport-zone-001 simulation validates
- reconciliation validates
- operator decision protocol validates
- pilot checklist validates
- metrics dashboard validates
- execution-grade pilot system validates
- field execution transition boundary validates

Exit gate:

```text
GO only if pilot execution is bounded, measured, and reversible.
```

## Phase 5. Full Constitutional Pipeline Registry Check

Before running the full pipeline, verify the registry shape:

```bash
python - <<'PY'
from afritech.ci.constitutional_pipeline import PIPELINE, validate_pipeline_registry
validate_pipeline_registry(PIPELINE)
print("pipeline registry valid", len(PIPELINE))
PY
```

Required result:

- no duplicate pipeline step names
- no duplicate pipeline commands
- phases remain deterministic
- `afritech_eight_pillars_validator` is present in the STATIC phase

Full run:

```bash
python -m afritech.ci.constitutional_pipeline
```

Exit gate:

```text
GO only if the constitutional pipeline completes.
```

## Phase 6. Field Operation Evidence Collection

First live scenario:

```text
Scenario ID: airport-zone-001
Scenario Type: airport
Zone: airport_pickup_dropoff_zone
Live Money: disabled by default
```

For each pilot operation:

1. record governed dispatch context
2. collect ordered field evidence events
3. validate selected participant binding
4. validate operation identity binding
5. validate canonical event sequence
6. build field evidence proof
7. export evidence, proof, and invariant report
8. attach evidence hash to the pilot evidence bundle
9. run simulation reality reconciliation in shadow mode

Required field event sequence:

- GPS
- DRIVER_ACCEPT
- ARRIVAL
- PICKUP
- DROPOFF
- CUSTOMER_CONFIRM
- PAYMENT_CONFIRM

Exit gate:

```text
GO only if every operation has deterministic evidence, proof, and invariant report artifacts.
```

## Phase 7. Operator Review

The evidence reviewer must confirm:

- no field evidence artifact claims authority
- no field evidence artifact overrides replay
- no field evidence artifact overrides dispatch
- no field evidence artifact overrides settlement
- no field evidence artifact mutates state
- all exported hashes are stable across repeated reads
- failed or missing evidence is isolated rather than silently repaired
- operator decision record is explicit and bounded

Exit gate:

```text
GO only if evidence failures are isolated and no authority boundary is breached.
```

## Phase 8. Pilot Closeout

Closeout package must include:

- command log for all verification commands
- constitutional pipeline result
- Eight Pillars validator output
- ADR-0042, RULE-062, and BIND-040 references
- ADR-0043, RULE-063, and BIND-041 references
- ADR-0044, RULE-064, and BIND-042 references
- field evidence exports
- field evidence invariant reports
- replay validation output
- proof surface output
- incidents and isolation decisions
- operator decision record
- go / refine / stop decision

Exit gate:

```text
Pilot is verified only when closeout artifacts prove bounded execution without authority drift.
```

## Stop Conditions

Stop the pilot immediately if:

- the authority chain changes
- field evidence is treated as truth authority
- replay integrity fails
- proof surface fails
- dispatch participant binding fails
- operation identity binding fails
- exported evidence is not hash-stable
- live-money movement occurs outside the governed AfriPay boundary
- operator review cannot isolate a failed evidence artifact

## Phase 9. Simulation Reality Reconciliation

Run:

```bash
python -m afritech.ci.afritech_reconciliation_validator
```

Required result:

- airport pilot simulation aligns with live field evidence
- divergence score is zero for the canonical simulation shadow run
- reconciliation recommendation is `continue`
- divergence report remains read-only

Exit gate:

```text
GO only if reconciliation confirms the live airport pilot still matches the governed simulation.
```

## Phase 10. Operator Decision Protocol

Run:

```bash
python -m afritech.ci.afritech_operator_decision_protocol_validator
```

Required result:

- operator decision surface validates
- zero-downtime deploy script is present
- TLS cutover bundle is present
- decision vocabulary remains bounded

Exit gate:

```text
GO only if operator decisions remain non-authoritative and bounded to governed evidence.
```

## Final Verification Statement

The system is trusted at pilot scale only when:

```text
doctrine is enforced
field evidence is bounded
replay validates truth
proof demonstrates truth
operators preserve authority boundaries
closeout artifacts are complete
```

This is the operational bridge from constitutionally enforced architecture to
field deployment that can be trusted at scale.
