# AfriRide Use-Case Document

STATUS: OPERATIONAL REQUIREMENTS SURFACE
CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## System Classification

This document defines bounded operational behaviors for AfriRide on top of AfriTech constitutional execution and replay governance.

It does not redefine constitutional truth, replay admissibility, core enforcement semantics, or the current proof boundary.

## 1. Purpose

The purpose of AfriRide is to provide a deterministic, replay-governed mobility coordination platform enabling:

- rider trip requests
- driver matching
- trip lifecycle coordination
- fare estimation
- notifications
- payment coordination
- continuity during operational disruptions

while preserving:

```text
deterministic execution
replay admissibility
identity integrity
closed-world enforcement
constitutional boundaries
```

## 2. Actors

### Primary Actors

#### Rider

A user requesting transportation services.

#### Driver

A mobility provider accepting and completing rides.

#### System

AfriRide runtime and orchestration services operating under AfriTech constitutional enforcement.

### Secondary Actors

#### Payment Service

Processes payment authorization and settlement.

#### Notification Service

Sends ride lifecycle notifications.

#### Admin Operator

Monitors operational metrics and replay-safe audit visibility.

## 3. Core Use Cases

## UC-001 - Request Ride

### Goal

Allow a rider to request transportation.

### Primary Actor

Rider

### Preconditions

- rider identity exists
- rider account is admissible
- pickup and destination are valid

### Main Flow

1. Rider submits ride request.
2. System validates request payload.
3. System creates ride intent.
4. System assigns ride identifier.
5. System emits deterministic ride creation event.
6. Ride enters `REQUESTED` state.

### Postconditions

- ride intent exists
- ride is replay-addressable
- request is audit-visible

### Failure Conditions

- invalid payload
- invalid rider identity
- malformed coordinates
- closed-world validation failure

## UC-002 - Match Driver

### Goal

Assign an eligible driver to a ride.

### Primary Actor

System

### Preconditions

- ride exists
- ride state is `REQUESTED`
- eligible drivers available

### Main Flow

1. Matching engine evaluates drivers.
2. Deterministic selection logic executes.
3. Driver assigned.
4. Match event emitted.
5. Ride enters `MATCHED` state.

### Postconditions

- assigned driver recorded
- replay trace updated

### Failure Conditions

- no drivers available
- deterministic selection violation
- invalid driver identity

## UC-003 - Accept Ride

### Goal

Allow driver to accept assigned ride.

### Primary Actor

Driver

### Preconditions

- ride is `MATCHED`
- driver is assigned

### Main Flow

1. Driver accepts ride.
2. Acceptance validated.
3. Acceptance event emitted.
4. Ride enters `ACCEPTED` state.

### Postconditions

- ride legally accepted
- lifecycle updated deterministically

## UC-004 - Start Ride

### Goal

Begin active ride execution.

### Primary Actor

Driver

### Preconditions

- ride is `ACCEPTED`

### Main Flow

1. Driver starts trip.
2. Runtime validates lifecycle transition.
3. Ride enters `STARTED` state.
4. Tracking session begins.

### Postconditions

- active ride session exists
- deterministic tracking enabled

## UC-005 - Complete Ride

### Goal

Complete ride and finalize operational flow.

### Primary Actor

Driver

### Preconditions

- ride is `STARTED`

### Main Flow

1. Driver completes ride.
2. Runtime validates transition.
3. Fare finalized.
4. Completion event emitted.
5. Ride enters `COMPLETED` state.

### Postconditions

- ride immutable
- replay-valid completion state exists
- audit lineage complete

## UC-006 - Cancel Ride

### Goal

Cancel ride before completion.

### Primary Actors

Rider or Driver

### Preconditions

- ride not completed

### Main Flow

1. Cancellation requested.
2. Runtime validates cancellation legality.
3. Cancellation reason recorded.
4. Ride enters `CANCELLED`.

### Postconditions

- cancellation lineage preserved
- replay integrity maintained

## UC-007 - Fare Estimation

### Goal

Provide deterministic fare estimate before booking.

### Primary Actor

Rider

### Preconditions

- origin and destination valid

### Main Flow

1. Rider requests estimate.
2. Pricing service computes estimate.
3. Deterministic pricing rules applied.
4. Estimate returned.

### Postconditions

- estimate visible before booking

## UC-008 - Share ETA

### Goal

Allow rider to share trip progress.

### Primary Actor

Rider

### Main Flow

1. Rider enables ETA sharing.
2. System generates replay-safe tracking token.
3. Recipient receives live ETA updates.

### Postconditions

- tracking remains observational only
- no authority mutation occurs

## UC-009 - Scheduled Ride

### Goal

Allow future ride scheduling.

### Primary Actor

Rider

### Main Flow

1. Rider selects future time.
2. Ride request stored.
3. Activation scheduled.
4. Ride enters pending queue.

### Postconditions

- scheduled request preserved
- deterministic activation maintained

## UC-010 - Continuity During Disruption

### Goal

Preserve lawful ride continuity under operational disruption.

### Primary Actor

System

### Main Flow

1. Failure/disruption detected.
2. Recovery policies execute.
3. Replay lineage validated.
4. Deterministic convergence enforced.
5. Duplicate authority prevented.

### Postconditions

- identity preserved
- replay equivalence maintained
- continuity proof admissible within bounded validated scenarios

## 4. Lifecycle States

```text
REQUESTED
MATCHED
ACCEPTED
STARTED
COMPLETED
CANCELLED
FAILED
```

## 5. Constitutional Constraints

AfriRide operations must preserve:

```text
deterministic execution
closed-world execution
canonical identity resolution
replay admissibility
invariant preservation
claim discipline
```

AfriRide must not:

```text
redefine constitutional truth
introduce undeclared execution surfaces
permit observer-relative execution
bypass replay enforcement
```

## 6. Replay and Audit Requirements

All operationally significant actions must produce:

- replay-safe events
- deterministic lifecycle transitions
- immutable audit lineage
- replay reconstruction compatibility

## 7. Product Boundary

AfriRide is a bounded operational mobility layer operating within AfriTech constitutional enforcement.

Safe classification:

```text
AfriRide is a bounded replay-governed mobility coordination surface
validated under deterministic constitutional admissibility constraints.
```

This document does not claim global deployment readiness, unrestricted distributed systems readiness, universal validator completeness, or production marketplace readiness.
