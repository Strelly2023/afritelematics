# AfriRide First Pilot Rollout Plan

Status: CONTROLLED FIELD ACTIVATION PLAN

Purpose: move from repository-proven trust pipeline to first real-world rider/driver evidence with minimum operational exposure.

## Pilot Objective

Prove that the authoritative AfriRide spine can support a real ride flow with:

- authenticated rider
- authenticated driver
- Postgres-backed trace persistence
- deterministic replay
- valid evidence
- reproducible receipt

This pilot does not prove public production readiness. It proves first controlled field execution.

## Pilot Scope

Initial rollout scope:

- 1 operator
- 1 driver
- 1 rider
- 1 geographic route or pickup zone
- 1 Postgres-backed backend instance
- observer present during the run

Excluded from first pilot:

- open signup
- payments
- surge pricing
- multi-driver dispatch contention
- large-area coverage

## Prerequisites

- Postgres runtime validation checklist passed
- cutover runbook completed successfully
- rollback path confirmed
- mobile or test clients can authenticate successfully
- operator dashboard or logs visible during run

## Pilot Roles

- `Operator`: watches the system and authorizes the run
- `Driver`: executes the transport leg
- `Rider`: requests and completes the ride
- `Observer`: records outcome and anomalies

## Pilot Flow

1. operator confirms system health
2. driver authenticates and sets online status
3. rider authenticates and requests ride
4. driver accepts ride
5. driver starts ride
6. driver completes ride
7. operator verifies:
   - replay
   - evidence
   - receipt
   - stored trace identity

## Success Criteria

The first pilot run is successful only if all are true:

- rider can request ride with valid auth
- driver can accept/start/complete with valid auth
- trace rows persist in Postgres
- replay returns expected ride state
- evidence returns `VERIFIED`
- receipt hash is produced
- receipt remains stable after process restart

## Evidence To Capture

For each pilot run capture:

- ride id
- trace event count
- replay response
- evidence response
- receipt response
- timestamps for each stage
- operator notes

These should be stored as field evidence for pilot certification, not just viewed interactively.

## Pilot Stop Conditions

Stop immediately if any occur:

- auth token cannot be issued or validated
- driver or rider action writes no trace event
- replay cannot reconstruct ride
- evidence returns `REJECTED`
- receipt endpoint fails
- identity in trace does not match authenticated actor

## Rollout Sequence

Stage 1. Dry operator simulation

- one operator runs the full flow using test clients

Stage 2. Controlled live run

- one real rider and one real driver complete one ride with operator present

Stage 3. Repeated controlled runs

- repeat same route or zone several times
- confirm proof outputs remain stable across multiple rides

Stage 4. Limited expansion

- add a second driver or second rider cohort only after repeated successful controlled runs

## Daily Pilot Checklist

- confirm database connectivity
- confirm token issuance
- confirm driver availability update works
- confirm replay/evidence/receipt endpoints respond
- confirm rollback plan still valid

## Pilot Exit Criteria

Exit the first-pilot phase only when:

- multiple controlled rides succeed end-to-end
- no replay mismatches occur
- no receipt mismatches occur
- no identity attribution anomalies occur
- operators can recover from a simple restart without proof drift

## What This Pilot Does Not Prove

Even if successful, this first rollout does not prove:

- mass-market reliability
- public production readiness
- high concurrency safety
- payments readiness
- large-scale dispatch behavior

It proves that the trust pipeline survives first contact with real users.
