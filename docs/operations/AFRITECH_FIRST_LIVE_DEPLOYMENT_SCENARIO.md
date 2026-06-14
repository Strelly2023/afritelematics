# AfriTech First Live Deployment Scenario

Status: FIRST LIVE OPERATION SCENARIO

Classification: GOVERNED AIRPORT PILOT DEPLOYMENT SURFACE

Purpose: define the first bounded live deployment scenario that moves AfriTech
from architecture and simulation into controlled live operation.

## Scenario

```text
Scenario ID: airport-zone-001
Scenario Type: airport
Zone: airport_pickup_dropoff_zone
Live Money: disabled by default
Authority Boundary: live_deployment_scenario_reference_only
```

The first deployment scenario is an airport controlled pickup and dropoff pilot.
This is the preferred first live scenario because an airport zone has bounded
geography, clear pickup/dropoff events, visible operator oversight, strong
identity expectations, and simple stop conditions.

Operator decisions for the pilot are governed by
`docs/operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md`.

The live pilot execution checklist is defined in
`docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md`.

The first EC2 test run is described in
`docs/operations/AFRITECH_EC2_FIRST_TEST_RUN.md`.

The first operator decision simulation is described in
`docs/operations/AFRITECH_FIRST_OPERATOR_DECISION_SCENARIO.md`.

## Authority Chain

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

Field evidence remains non-authoritative. It may enter the system only as
bounded reality evidence through ADR-0042 runtime ingestion.

## Deployment Goal

Validate that AfriTech can run a bounded real-world mobility operation where:

- dispatch selects a verified participant
- raw field signals are ingested through ADR-0042
- field signals become deterministic field events
- field events become a hash-stable collection
- proof and invariant reports are generated
- operators review evidence without bypassing replay authority
- live-money movement remains disabled unless explicitly governed

## Pilot Dataset Simulation

Before live operation, generate the deterministic airport pilot dataset:

```bash
python -m afritech.ci.afritech_pilot_dataset_simulation_validator
```

The simulation produces:

- scenario manifest for `airport-zone-001`
- three governed airport operations by default
- seven field signals per operation
- field evidence collection hash per operation
- proof hash per operation
- ingestion hash per operation
- deterministic dataset hash

## Shadow Reconciliation

Before the first live operation is declared operationally viable, run the
simulation reality reconciliation layer in shadow mode:

```bash
python -m afritech.ci.afritech_reconciliation_validator
```

The reconciliation layer compares the airport pilot simulation with the live
field evidence outputs and classifies divergence without overriding authority.

## Required Gates

Run:

```bash
python -m afritech.ci.afritech_eight_pillars_validator
python -m afritech.ci.afritech_trusted_scale_infrastructure_validator
python -m afritech.ci.afritech_field_evidence_runtime_validator
python -m afritech.ci.afritech_pilot_dataset_simulation_validator
python -m afritech.ci.afritech_reconciliation_validator
python -m afritech.ci.afritech_operator_decision_protocol_validator
python -m afritech.ci.afritech_live_pilot_execution_validator
```

Required result:

- authority chain remains `Constitution -> Deterministic Truth -> Replay -> Proof`
- ADR-0042 runtime validates
- pilot dataset simulation validates
- reconciliation validates
- operator decision protocol validates
- live pilot execution checklist validates
- airport scenario remains reference-only
- field evidence remains non-authoritative
- live-money movement remains disabled by default

## Operator Roles

- pilot lead
- airport zone operator
- driver support
- evidence reviewer
- rollback owner

## Live Operation Sequence

1. lock pilot scope and operator roles
2. run the full-system verification runbook
3. run the airport pilot dataset simulation
4. select one verified airport-zone driver
5. execute one bounded pickup/dropoff operation
6. ingest GPS, driver accept, arrival, pickup, dropoff, customer confirm, and payment confirm signals
7. export field evidence, proof, invariant report, and ingestion report
8. run simulation reality reconciliation in shadow mode
9. validate the operator decision protocol
10. validate the live pilot execution checklist
11. review hashes, divergence, and stop conditions
12. record go / refine / stop decision

## Stop Conditions

Stop the pilot immediately if:

- authority chain changes
- field evidence is treated as truth authority
- dispatch participant mismatch occurs
- event sequence is missing
- evidence hash is unstable
- proof hash is unstable
- unapproved live-money movement occurs
- operator cannot isolate a failed evidence artifact
- operator decision record is explicit and bounded

## Success Criteria

The first live deployment scenario is successful only when:

```text
simulation passes
runtime ingestion passes
one live operation is bounded
field evidence is exported
replay/proof checks pass
operator closeout is complete
operator decision is recorded
no authority drift occurs
```

This scenario is the transition point from governed architecture to controlled
live operation.
