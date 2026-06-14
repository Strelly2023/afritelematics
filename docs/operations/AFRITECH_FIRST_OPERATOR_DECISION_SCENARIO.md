# AfriTech First Operator Decision Scenario

Status: READY FOR DECISION SIMULATION

Purpose: simulate the first operator decision event after the first live
pilot test run.

## Scenario A. GO

### Input

- zero-downtime deploy completed successfully
- HTTP health probe returned 200
- pilot dataset simulation validated
- field evidence runtime validated
- reconciliation divergence score is 0.0
- operator decision protocol validated
- no stop conditions are active

### Decision

```text
GO
```

### Required Record

- operator decision mode: go
- rationale: all governed evidence gates passed
- next action: proceed to bounded pilot operation

### Real Output Basis

This scenario matches the current known-good local outputs:

```text
AfriTech reconciliation validation PASSED
scenario_id=airport-zone-001 deployment_type=airport
operations=3 divergence_count=0
divergence_score=0.000000 recommendation=continue
```

```text
AfriTech operator decision protocol validation PASSED
adr=ADR-0044 rule=RULE-064 binding=BIND-042
```

```text
AfriTech live pilot execution validation PASSED
checklist=docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md
ec2_test_run=docs/operations/AFRITECH_EC2_FIRST_TEST_RUN.md
operator_scenario=docs/operations/AFRITECH_FIRST_OPERATOR_DECISION_SCENARIO.md
```

### GO Decision Record

```text
scenario_id=airport-zone-001
decision_mode=go
evidence_refs=reconciliation:divergence_score=0.0, operator_decision_protocol:passed, live_pilot_execution:passed
rationale=all governed evidence gates passed
next_action=proceed to bounded pilot operation
```

## Scenario B. STOP

### Input

- deploy health failed
- or reconciliation became authoritative
- or field evidence claimed truth authority
- or live money was attempted without approval

### Decision

```text
STOP
```

### Required Record

- operator decision mode: stop
- rationale: authority boundary breach or health gate failure
- next action: halt execution and isolate the failed artifact

### Example Stop Trigger

```text
deploy health failed
or reconciliation became authoritative
or field evidence claimed truth authority
or live money was attempted without approval
```

### STOP Decision Record

```text
scenario_id=airport-zone-001
decision_mode=stop
evidence_refs=deployment_health:failed or authority_boundary:breach
rationale=operator must halt when governed evidence fails or authority is breached
next_action=halt execution and isolate the failed artifact
```

## Operator Rule

The operator may choose only from the governed vocabulary:

- go
- continue
- refine
- stop
- rollback
- escalate

The operator may not redefine truth, replay, proof, reconciliation, or
dispatch.
