# AfriTech Operator Decision Protocol

Status: READY FOR PILOT DECISION SURFACE

Classification: NON-AUTHORITATIVE OPERATOR DECISION LAYER

Purpose: define the governed operator decision surface used for pilot
execution, zero-downtime deployment, and domain TLS cutover.

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

Operator decisions consume evidence from this chain. They do not alter it.

## Decision Vocabulary

- go
- continue
- refine
- stop
- rollback
- escalate

## Required Inputs

- reconciliation report
- pilot dataset validation report
- field evidence validation report
- deployment health
- TLS cutover state
- zero-downtime deploy result
- runbook step status
- stop conditions

## Required Outputs

- operator decision record
- decision rationale
- execution trace
- escalation trace
- rollback trace
- next action

## Decision Rules

- decisions are read-only with respect to truth, replay, proof, dispatch,
  settlement, and reconciliation
- decisions must cite governed evidence
- decisions must use the bounded vocabulary above
- stop and rollback conditions must be explicit
- the decision surface must remain non-authoritative

## Zero-Downtime Deployment Use

The zero-downtime deploy script updates the API, dashboard, and edge in a
sequenced way and then validates the edge before probe execution.

## TLS Cutover Use

The TLS cutover uses a domain-only Caddy configuration and a separate TLS
compose bundle. It does not reuse the pilot HTTP edge file.

## Operator Record

Each decision should be recorded with:

- timestamp
- scenario id
- decision mode
- evidence references
- stop condition state
- rollback readiness
- next action

## Failure Policy

If evidence is inconsistent, the protocol defaults to `stop` or `rollback`
instead of inventing a new authority path.
