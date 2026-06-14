# AfriTech Live Pilot Execution Checklist

Status: READY FOR REAL PILOT EXECUTION

Classification: GOVERNED OPERATIONAL CHECKLIST

Purpose: define the step-by-step live execution checklist for the first
bounded AfriTech pilot on EC2.

## Phase 0. Scope Lock

1. Confirm the pilot scenario is `airport-zone-001`.
2. Confirm live money is disabled by default.
3. Confirm the operator roles are assigned.
4. Confirm the rollback owner is present.
5. Confirm the evidence reviewer is present.

Exit condition:

```text
GO only if scope, owners, and rollback path are explicit.
```

## Phase 1. Repo Sync

1. Pull the latest repository changes on EC2.
2. Confirm `deploy/production/.env.production` is present.
3. Confirm no placeholder secrets remain.
4. Confirm the pilot HTTP Caddyfile is active.

## Phase 2. Build and Start

1. Run the zero-downtime deploy script.

```bash
./scripts/deploy_production_zero_downtime.sh --base-url http://<host>
```

2. Wait for the API health gate.
3. Confirm the dashboard container starts.
4. Confirm the edge container starts.

## Phase 3. Health Probe

1. Run the production probe.

```bash
./scripts/run_local_production_probe.sh http://<host>
```

2. Confirm `/health` returns OK.
3. Confirm `/public/verify/health` returns OK.
4. Confirm `/public/registry` returns the public registry payload.

## Phase 4. Pilot Simulation

1. Run the pilot dataset validator.

```bash
python -m afritech.ci.afritech_pilot_dataset_simulation_validator
```

2. Confirm the airport simulation passes.
3. Confirm the dataset hash is stable.

## Phase 5. Reality Ingestion

1. Run the field evidence runtime validator.

```bash
python -m afritech.ci.afritech_field_evidence_runtime_validator
```

2. Confirm the first live field signal is accepted.
3. Confirm field evidence remains non-authoritative.

## Phase 6. Reconciliation

1. Run the reconciliation validator.

```bash
python -m afritech.ci.afritech_reconciliation_validator
```

2. Confirm divergence is zero in the canonical shadow run.
3. Confirm the recommendation is `continue`.

## Phase 7. Operator Decision

1. Run the operator decision protocol validator.

```bash
python -m afritech.ci.afritech_operator_decision_protocol_validator
```

2. Run the live pilot execution validator.

```bash
python -m afritech.ci.afritech_live_pilot_execution_validator
```

3. Record one bounded decision from the approved vocabulary.
4. Record the rationale and next action.

## Phase 8. GO / STOP Decision

1. If every gate passed, record `GO`.
2. If any authority boundary failed, record `STOP`.
3. If the system is viable but needs tuning, record `REFINE`.
4. If rollback is required, record `ROLLBACK`.
5. If escalation is required, record `ESCALATE`.

## Stop Conditions

- authority chain changes
- field evidence becomes truth authority
- replay or proof validation fails
- reconciliation becomes authoritative
- deploy health fails
- TLS cutover is attempted without the TLS bundle
- live money moves without explicit approval

## Evidence Bundle

- deploy output
- health probe output
- pilot dataset validation output
- field evidence runtime output
- reconciliation output
- operator decision record

## Final Rule

Do not claim pilot success until the evidence bundle is complete and the
operator decision is recorded.
