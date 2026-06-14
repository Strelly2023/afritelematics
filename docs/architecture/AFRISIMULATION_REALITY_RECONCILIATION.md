# AfriTech Simulation Reality Reconciliation

Status: ACCEPTED RECONCILIATION BOUNDARY

Classification: NON-AUTHORITATIVE OPERATIONAL FEEDBACK SURFACE

Purpose: define the governed layer that compares pilot simulation outputs with
live field evidence outputs and produces divergence reports, calibration
signals, and operator review traces without granting authority to simulation,
reality, or reconciliation.

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

Simulation and reality are compared under this chain. Neither becomes authority.
The reconciliation layer explains divergence only.

## Responsibilities

- compare simulation dataset hashes with live ingestion hashes
- compare simulation operation hashes with live collection, proof, and ingestion hashes
- classify divergence by severity
- produce operator-readable calibration notes
- recommend continue, shadow more, investigate, or stop

## Authority Boundary

- reconciliation is input only
- reconciliation does not define truth
- reconciliation does not mutate replay, proof, dispatch, or settlement
- reconciliation does not repair divergence
- reconciliation does not override pilot decisions

## Required Inputs

- simulation dataset hash
- simulation operation hashes
- live ingestion hashes
- live collection hashes
- live proof hashes
- scenario id
- operation ids

## Required Outputs

- reconciliation report
- divergence score
- calibration notes
- operator review trace
- stop or continue recommendation

## Pilot Use

The first live airport scenario uses reconciliation as a shadow mode control to
compare what the simulation expected with what the live field evidence produced.
If divergence is detected, the report is reviewed. It does not silently
reclassify the system.
