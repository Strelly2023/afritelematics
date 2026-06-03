# AfriRide:
# Reference Implementation of the AfriTech Model

## Purpose

AfriRide is the first application realization of the AfriTech model.

It is not defined as a conventional ride-hailing application. It is defined as a deterministic, replay-auditable mobility execution system.

AfriRide demonstrates that the AfriTech model can govern a real-world domain where execution, environment, optimization, and replay must remain distinct.

## Model Mapping

| AfriTech Definition | AfriRide Realization |
| --- | --- |
| Execution | Ride lifecycle |
| Environment | City zones, drivers, vehicles, platform constraints |
| Optimization | Driver matching, routing, pricing, locality scheduling |
| Replay | Ride reconstruction, dispute audit, decision verification |

## Core Principle

Every ride is a governed execution unit.

```text
Ride = declared inputs + canonical lifecycle DAG + bounded optimization + replay trace
```

No ride decision may depend on undeclared input, randomness, or realtime-only authority.

## Ride Execution Model

### Canonical Ride Data

```yaml
Ride:
  id
  passenger_id
  pickup_location
  dropoff_location
  requested_at
  assigned_driver
  route_plan
  price_plan
  status
```

Required constraints:

1. Driver assignment must be explicit.
2. Matching must be deterministic.
3. Routing inputs must be declared.
4. Pricing inputs must be declared.
5. State transitions must be replayable.

## Ride Lifecycle DAG

```text
Request Ride
    ↓
Match Driver
    ↓
Calculate Route
    ↓
Calculate Price
    ↓
Driver Acceptance
    ↓
Ride Start
    ↓
Ride End
```

The lifecycle is the canonical execution structure for a ride.

No hidden transition may alter ride state outside this DAG.

## AfriTech Surface Mapping

| AfriTech Surface | AfriRide Use |
| --- | --- |
| Distributed OS | Declares city execution constraints, resource limits, and hardware/runtime context |
| Distributed Fabric | Places ride execution by city zone and partition |
| Execution Graph Optimizer | Structures ride lifecycle, route planning, and price planning as replay-safe DAGs |
| Locality Scheduler | Performs zone-local matching and locality-aware dispatch |
| Trace | Records request, match, route, price, lifecycle, and environment decisions |
| Replay | Reconstructs the ride and validates outcome plus decision structure |

## Locality Model

AfriRide partitions execution by pickup zone.

```text
City
 ├── Zone A → partition
 ├── Zone B → partition
 └── Zone C → partition
```

Locality rules:

1. A ride belongs to its pickup partition.
2. Same-zone driver candidates are preferred by deterministic ordering.
3. Cross-zone assignment must be explicit and traceable.
4. Cross-zone execution must preserve replay-equivalent outcome.

## Matching Model

Driver matching is a scheduling decision, not an opaque heuristic.

Inputs:

1. Ride request
2. Declared pickup partition
3. Candidate drivers
4. Driver availability
5. Deterministic distance or locality score

Forbidden:

1. Random driver selection
2. Hidden ranking signals
3. Realtime-only assignment state
4. Assignment without trace evidence

Output:

```text
driver_match = deterministic_scheduler_decision
```

## Routing and Pricing

Routing and pricing are optimization surfaces.

They may improve efficiency or cost calculation, but they may not define truth.

Required:

1. Map graph inputs must be declared.
2. Traffic inputs must be declared if used.
3. Pricing inputs must be declared.
4. Route and price plans must be included in the ride trace.

## Ride Trace

Every ride must emit a trace sufficient for replay.

```yaml
ride_trace:
  request
  environment:
    city
    zone
    resource_contract
  driver_match
  route_plan
  price_plan
  lifecycle_steps
  scheduler_trace
  graph_optimizer_trace
  fabric_trace
  os_trace
```

Replay must reconstruct both:

1. The final ride outcome.
2. The decision structure that produced the outcome.

## MVP Implementation Order

1. Canonical ride model
2. Ride lifecycle DAG
3. Deterministic driver matching
4. Basic deterministic routing
5. Ride trace and replay
6. Zone partitioning through distributed fabric
7. OS constraints and resource contracts
8. Passenger, driver, and admin surfaces

## Application Rule

AfriRide must remain an application of the AfriTech model.

If an AfriRide feature cannot be expressed through execution, environment, optimization, or replay, it must not be added until the model is explicitly reviewed.

## Positioning

AfriRide is the reference implementation and product entry point for AfriTech.

Its purpose is to prove that deterministic distributed computation can govern a real-world mobility system without sacrificing auditability, locality, or optimization.
