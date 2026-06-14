# AfriTech Operator Decision Protocol Runbook

Status: READY FOR PILOT DECISION EXECUTION

Purpose: define the operator-facing procedure for making go/no-go,
continue/refine, stop, rollback, and escalate decisions during pilot
execution.

## Protocol

1. Collect the reconciliation report.
2. Collect the pilot dataset validation report.
3. Collect the field evidence validation report.
4. Check deployment health.
5. Check TLS cutover state if the domain cutover is active.
6. Check zero-downtime deploy result.
7. Check runbook step status.
8. Check stop conditions.
9. Record one decision from the bounded vocabulary.
10. Record the next action.

## Live Pilot Execution Use

The live pilot execution checklist documents the full step-by-step path for
the first real EC2 test run and the first bounded operator decision.

## Decision Modes

- go: all required gates are green and pilot execution may proceed
- continue: execution remains within bounds and no operator intervention is required
- refine: execution is viable but should be tuned before scaling
- stop: execution must halt immediately
- rollback: the latest deploy or cutover must be reversed
- escalate: the issue needs higher-privilege review or external intervention

## Stop Conditions

Stop or rollback if any of the following are true:

- authority chain changes
- reconciliation becomes authoritative
- replay or proof validation fails
- deployment health fails
- TLS cutover fails certificate or DNS checks
- zero-downtime deploy health gate fails
- live money movement is attempted without explicit approval

## Decision Record

Record:

- scenario id
- timestamp
- decision mode
- evidence references
- rationale
- next action
- rollback readiness

## Output

Write the decision record into the operator log and preserve it as pilot evidence.
