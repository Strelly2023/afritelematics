# AfriRide Melbourne First Real Pilot Launch Plan

Status: READY-TO-RUN MELBOURNE PILOT LAUNCH PLAN
Classification: FIELD EXECUTION PLANNING SURFACE

Purpose: convert the current AfriRide rider and driver apps into a bounded first
real Melbourne pilot while preserving replay authority, evidence discipline, and
truthful product claims.

This plan does not claim that Melbourne execution has passed. Melbourne pilot
success can only be claimed after the Melbourne phase execution control contract
passes with preserved evidence.

## Pilot Objective

Run a small real-world mobility pilot in Melbourne that proves whether AfriRide
can preserve governed ride evidence under controlled field conditions.

Primary corridor:

```text
Melbourne CBD <-> Melbourne Airport
```

## Pilot Scope

```text
drivers: 3-5 trusted drivers
riders: 10-25 invite-only riders
duration: 7-14 days
trip_goal: 20-50 completed rides
payment_mode: observed payment event only unless compliance activation exists
claim_boundary: controlled pilot evidence, not production deployment
```

## Launch Sequence

### Step 1: Demo Freeze

- freeze rider and driver app demo build
- seed one clean demo ride fixture
- verify trust badge, receipt view, replay view, and evidence view
- record investor demo video from the frozen build

### Step 2: Operational Readiness

- assign one pilot operator
- assign backup operator
- register trusted drivers
- prepare rider invite list
- confirm support channel
- confirm hard-stop escalation owner

### Step 3: Evidence Readiness

- verify receipt generation
- verify replay hash generation
- verify evidence viewer
- verify public verification path
- verify audit package export
- prepare daily evidence folder

### Step 4: Field Execution

Run only bounded ride scenarios:

- normal ride completion
- driver reject cascade
- rider cancellation during matching
- network delay / timeout determinism
- payment failure observation without corrupting trip state

### Step 5: Daily Review

Each day must produce:

- ride count
- completed ride count
- failed ride count
- replay mismatch count
- evidence gap count
- driver feedback
- rider feedback
- operator decision log

## Hard Stops

Stop the pilot immediately if any occurs:

- replay mismatch
- missing receipt
- missing evidence for completed ride
- identity drift
- duplicate assignment
- post-cancel assignment
- payment state corrupts trip state
- public verification leaks private data

## Success Criteria

Melbourne pilot may be classified as passed only if:

- all selected Melbourne scenarios pass
- all completed rides have receipts
- all receipt replay hashes verify
- no hard-stop issue remains unresolved
- rider and driver states stay synchronized
- audit package export is available for pilot evidence
- operator decision log preserves all anomalies

## Investor Demo To Pilot Bridge

The investor demo video should show the same truth chain the pilot will test:

```text
request -> driver lifecycle -> receipt -> replay -> evidence -> public verification
```

The pilot must not rely on investor narrative. The pilot must rely on evidence.

## First Week Operating Rhythm

Day 0:

- dry run with internal accounts
- verify support and hard-stop procedure

Day 1:

- run 1-3 invite-only rides
- review every receipt manually

Days 2-3:

- expand to 5-10 rides per day if no hard stop occurs

Days 4-7:

- run controlled corridor trips
- produce daily evidence summary

Day 8:

- prepare pilot evidence review
- decide continue, pause, or harden

## Claim Boundary

Allowed after readiness:

- AfriRide is ready to run a bounded Melbourne pilot.
- AfriRide has an investor demo of trust-verifiable ride behavior.
- AfriRide has a planned evidence chain for Melbourne pilot execution.

Forbidden until evidence passes:

- Melbourne pilot completed
- production deployment ready
- regulatory approval achieved
- guaranteed real-world reliability
- large-scale marketplace proven
