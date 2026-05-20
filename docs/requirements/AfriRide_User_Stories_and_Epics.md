# AfriRide User Stories and Epics

STATUS: OPERATIONAL REQUIREMENTS
CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines AfriRide user stories and epics as an operational product requirements surface.

It does not define constitutional truth, does not expand the AfriTech proof surface, does not claim global deployment readiness, and does not modify the constitutional enforcement contract.

Capability status is classified as:

```text
[Implemented] -> backed by tested system behavior in the current bounded implementation surface
[In Development] -> partially implemented, not yet fully validated
[Planned] -> product direction, not yet implemented
[Exploratory] -> conceptual, no execution commitment
```

All planned and exploratory stories are isolated from the current proof surface until executable evidence, validator coverage, and claim discipline bindings exist.

## Epic 1 - Ride Request and Intent Capture

### Goal

Allow riders to create a deterministic ride intent.

### Create Ride Request

Status: [Implemented]

```text
As a rider,
I want to request a ride with origin and destination,
so that the system can begin ride coordination.
```

### Validate Ride Inputs

Status: [Implemented]

```text
As the system,
I want to validate ride request data,
so that only admissible inputs enter execution.
```

### Assign Unique Ride Identity

Status: [Implemented]

```text
As the system,
I want every ride to have a unique ID,
so that it can be tracked and replayed deterministically.
```

## Epic 2 - Ride Lifecycle Management

### Goal

Ensure rides follow a strict, replay-safe state machine.

### Transition Ride States

Status: [Implemented]

```text
As the system,
I want to enforce valid ride state transitions,
so that execution remains consistent and admissible.
```

### Prevent Invalid Transitions

Status: [Implemented]

```text
As the system,
I want to block illegal state transitions,
so that no invalid execution path exists.
```

### Complete Ride Execution

Status: [Implemented]

```text
As a rider and driver,
I want to complete a ride,
so that the trip lifecycle reaches a valid terminal state.
```

## Epic 3 - Driver Matching

### Goal

Assign drivers in a deterministic and replay-safe way.

### Assign Driver to Ride

Status: [In Development]

```text
As the system,
I want to assign an available driver,
so that rides can be executed.
```

### Ensure Deterministic Matching

Status: [In Development]

```text
As the system,
I want matching to be deterministic,
so that replay produces identical outcomes.
```

### Handle No Available Driver

Status: [Planned]

```text
As a rider,
I want to be notified if no driver is available,
so that I can retry or cancel.
```

## Epic 4 - Pricing and Fare Calculation

### Goal

Provide deterministic, transparent pricing.

### Calculate Fare

Status: [Implemented]

```text
As the system,
I want to calculate trip fare based on distance,
so that pricing is predictable and reproducible.
```

### Display Upfront Pricing

Status: [Planned]

```text
As a rider,
I want to see the estimated fare before confirming,
so that I can make an informed decision.
```

### Support Pricing Categories

Status: [Planned]

```text
As the system,
I want different ride types with pricing tiers,
so that users can choose service levels.
```

## Epic 5 - API and System Interaction

### Goal

Expose safe, controlled entry points.

### Submit Ride Request via API

Status: [Implemented]

```text
As a client application,
I want to send ride requests via API,
so that users can interact with the system.
```

### Enforce API Compliance

Status: [In Development]

```text
As the system,
I want to validate API requests through middleware,
so that all interactions remain admissible.
```

### Ensure Idempotent Requests

Status: [Planned]

```text
As the system,
I want duplicate requests to be safely handled,
so that execution remains deterministic.
```

## Epic 6 - Safety and Trust Layer

### Goal

Introduce governance-bound participation controls.

### Enable PIN Verification

Status: [Planned]

```text
As a rider,
I want to confirm the correct driver using a PIN,
so that pickup is secure.
```

### Track Ride Status

Status: [Implemented]

```text
As a rider,
I want to see ride status updates,
so that I know the trip progress.
```

### Share Ride Information

Status: [Planned]

```text
As a rider,
I want to share my trip details,
so that others can monitor my safety.
```

## Epic 7 - Replay and Traceability

### Goal

Ensure bounded ride execution remains replay-verifiable where it participates in the current validated proof surface.

### Generate Execution Trace

Status: [Implemented]

```text
As the system,
I want to log ride execution steps,
so that replay is possible.
```

### Validate Replay Consistency

Status: [Implemented]

```text
As the system,
I want to verify replay equivalence,
so that execution integrity is maintained.
```

### Link Execution to Proof

Status: [Implemented]

```text
As the system,
I want ride execution to align with proof validation,
so that admissibility is enforced.
```

## Epic 8 - Future Experience Layer

### Goal

Expand rider ecosystem capabilities without treating planned product features as current proof truth.

### Schedule Rides

Status: [Planned]

```text
As a rider,
I want to schedule rides in advance,
so that I can plan ahead.
```

### Multi-stop Trips

Status: [Planned]

```text
As a rider,
I want to add multiple stops,
so that I can complete complex trips.
```

### Fare Splitting

Status: [Exploratory]

```text
As a rider,
I want to split fares with others,
so that group travel is easier.
```

### Membership - AfriRide One

Status: [Exploratory]

```text
As a rider,
I want subscription benefits,
so that I can access discounts and rewards.
```

## Structural View

Core implemented surface:

- ride request
- lifecycle management
- deterministic pricing
- replay validation
- API entry

Growth surface:

- rider UX features
- marketplace extensions
- safety features
- ecosystem integrations

## Boundary Clause

Implemented stories identify tested operational behavior inside the current bounded implementation surface. They do not imply global production readiness, unrestricted distributed systems readiness, or universal validator completeness.

Planned and exploratory stories are isolated product requirements and are not part of the current proof surface.

## Final Product Constraint

```text
AfriRide user behavior is defined and constrained
by constitutionally admissible execution,
not informal feature expectations.
```

