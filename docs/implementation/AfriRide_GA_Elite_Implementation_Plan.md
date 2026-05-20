# AfriRide GA Elite Implementation Plan

STATUS: IMPLEMENTATION PLAN
CLASSIFICATION: ISOLATED OPERATIONAL IMPLEMENTATION SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This implementation plan describes an isolated operational build path for AfriRide. It does not define proof truth, does not claim global deployment readiness, and does not classify planned product capabilities as currently implemented.

Implementation planning must preserve or isolate all claims.

## Governing Rule

```text
preserve internal truth
or remain fully external
```

AfriRide implementation must remain separated into two planes:

```text
Plane 1: Constitutional Core (AfriTech) -> PRESERVE
Plane 2: Product and Operations (AfriRide) -> ISOLATE
```

The constitutional core is a protected surface. Product and operational work may evolve only while remaining fully external to sealed truth, invariant definitions, proof authority, and enforcement integrity.

## Phase Structure

AfriRide implementation is organized into six controlled product phases:

```text
Phase 0 -> System Foundation (already active)
Phase 1 -> Mobility Core Kernel
Phase 2 -> Ride Lifecycle Engine
Phase 3 -> Marketplace and Pricing Layer
Phase 4 -> Rider Experience Layer
Phase 5 -> Safety and Support Systems
Phase 6 -> Ecosystem Expansion
```

These phases are operational planning surfaces. They do not expand proof scope beyond the bounded AfriRide continuity domain.

## Phase 0 - Constitutional Foundation

Status: [Implemented / In Development]

Current active foundation:

- deterministic runtime
- replay engine
- invariant enforcement
- four-gate validator
- enforcement-integrity validator
- constitutional validation pipeline
- proof surface
- bounded AfriRide continuity proof behavior

Constraint:

```text
DO NOT TOUCH protected constitutional surfaces for product implementation.
```

Output:

```text
current governed infrastructure foundation
```

## Phase 1 - Mobility Core Kernel

Status: [Planned]

Objective:

```text
create the minimum admissible mobility execution layer
```

Systems to implement:

- ride intent model with rider identity, origin, destination, timestamp, and constraints
- deterministic matching engine
- driver availability registry
- trip state machine

Initial trip states:

```text
REQUESTED -> MATCHED -> ACCEPTED -> STARTED -> COMPLETED -> VERIFIED
```

Constraints:

- must be replay-safe
- must generate trace logs
- must pass replay reconstruction
- must not use probabilistic assignment as an authority source

Output:

```text
minimal ride execution flow for internal testing only
```

## Phase 2 - Ride Lifecycle Engine

Status: [Planned]

Objective:

```text
make rides executable, traceable, and verifiable
```

Systems to implement:

- ride execution engine
- enforced start and end trip logic
- deterministic state transitions
- replay binding for execution traces
- deterministic log structure
- witness-ready structure
- pricing skeleton
- rider and driver identity binding

Pricing skeleton:

```text
base fare + distance * factor
```

Output:

```text
replay-verifiable ride execution
```

## Phase 3 - Marketplace and Pricing Layer

Status: [Planned]

Objective:

```text
introduce controlled commercial logic
```

Systems to implement:

- deterministic pricing engine v1
- simple ride categories
- deterministic matching heuristics
- local marketplace simulation

Initial ride categories:

- AfriRideS
- AfriRideL

Not allowed in this phase:

- machine-learning pricing
- dynamic surge pricing
- probabilistic matching
- unbounded commercial claims

Output:

```text
functional local marketplace simulation
```

## Phase 4 - Rider Experience Layer

Status: [Planned]

Objective:

```text
expose safe and isolated product features
```

Initial user-facing surfaces:

- upfront pricing UI
- ride request UI
- basic ETA sharing
- trip status tracking

Required interaction model:

```text
app -> API -> isolated product layer -> deterministic operational response
```

Still planned beyond this phase:

- multi-stop routing
- scheduled rides
- fare split
- AI coordination

Output:

```text
first user-facing AfriRide MVP
```

## Phase 5 - Safety and Support Systems

Status: [Planned]

Objective:

```text
introduce trust layers without breaking determinism
```

Systems to implement:

- PIN verification
- ride logs
- lost item reporting
- support workflow tracking

Not yet included:

- anomaly detection AI
- predictive safety
- emergency automation claims

Output:

```text
baseline trust and support layer
```

## Phase 6 - Ecosystem Expansion

Status: [Exploratory]

Objective:

```text
introduce advanced features as isolated systems only
```

Possible future systems:

- scheduling engine
- fare split system
- membership layer (AfriRide One)
- logistics integrations
- delivery integrations
- AI ride coordination

Rule:

```text
all ecosystem expansion must remain externally isolated
no change to core admissibility is allowed
```

Output:

```text
isolated ecosystem expansion candidates
```

## Implementation Architecture View

Potential product modules:

```text
afriride_system/
├── ride_kernel/
├── lifecycle_engine/
├── pricing_engine/
├── matching_engine/
├── api_layer/
├── mobile_app/
└── integration_layer/
```

These module names are planning targets unless implemented and validator-backed in the repository.

## Data Flow

```text
User request
   ↓
API layer
   ↓
Ride kernel (deterministic)
   ↓
Lifecycle engine
   ↓
Replay logs
   ↓
Response to UI
```

Product data flow may expose operational behavior, but it may not redefine sealed truth or admissibility.

## Mandatory Validation Integration

Every implementation phase must pass:

```bash
python3 -m afritech.ci.enforcement_integrity_validator
python3 -m afritech.ci.four_gate_validator
python3 -m afritech.demo.proof
python3 -m afritech.ci.constitutional_validation
```

Phase claims remain invalid until the relevant implementation and tests pass.

## Drift Detection Rules

Immediate rejection if implementation introduces:

- randomness as core authority
- replay inconsistency
- validator bypass
- UI logic as truth
- API logic as core decision authority
- undocumented state mutation
- hidden execution paths
- proof-scope expansion

## Delivery Model

Each phase must deliver:

```text
executable system
replay-valid traces
passing validators
bounded claims
```

If a phase cannot provide these, it remains planned or exploratory.

## DFM Integration

Operational implementation must obey:

```text
operations optimize reproducibility
but never redefine admissibility
```

Operational tooling may include:

- replay visualizer
- validator dashboard
- trace explorer
- onboarding flows

These tools are DFM surfaces. They improve reproducibility and human operability without acquiring authority over admissibility.

## Final Implementation Truth

```text
If a feature cannot be replay-verified,
it is not part of AfriRide's admitted execution surface.
```

## Final Compression

```text
Build mobility systems
as deterministic, replay-verifiable,
constitutionally constrained workflows
before exposing user features.
```

## Boundary Clause

This implementation plan is an isolated operational planning surface. It does not modify `afritech.demo.proof`, `FIVE_INVARIANT_CONTRACT.yaml`, or the enforcement chain. It does not expand proof scope beyond the bounded AfriRide domain. It does not claim global deployment readiness, a deployed consumer marketplace, or implemented rider features beyond the current validator-backed system surface.
