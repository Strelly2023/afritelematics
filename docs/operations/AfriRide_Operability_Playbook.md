# AfriRide Operability Playbook

## Purpose

AfriRide is now a replay-governed deterministic application core. The next challenge is human operability: making the system understandable, debuggable, and evolvable without weakening replay authority.

This playbook defines the operability layer around AfriRide. It does not change the computational model, domain primitives, replay rules, or evidence-store authority boundaries.

## Authority Rule

```text
Core terms remain canonical.
Operational terms are translations only.
Replay remains the sole authority of truth.
```

Any tool, user interface, guide, or workflow introduced by this playbook must expose or explain existing artifacts. It must not create a new truth surface.

## Operational Vocabulary

The canonical AfriTech terms stay unchanged in code and model documents. Operational language may be used in docs, onboarding, UI copy, and support workflows to reduce cognitive load.

| Canonical term | Operational term | Meaning |
| --- | --- | --- |
| Replay | Verification | Recompute and validate the execution record. |
| Trace | Execution record | The canonical causal record of a ride. |
| Witness | Proof artifact | Hash-bound evidence used during verification. |
| Admissibility | Valid input rules | Requirements an input must satisfy before execution. |
| Ontology | System schema | The declared structure of the system. |
| Optimization | Decision proposal | Deterministic matching, routing, or pricing output. |
| Evidence store | Verified archive | Stored artifacts that must pass replay before use. |

Operational terms are not replacements. They are teaching labels.

## Golden Path

The first operator workflow is intentionally narrow.

```text
1. Create Ride
2. Optimize Ride
3. Execute Lifecycle Transitions
4. Build Trace
5. Replay
6. Inspect Audit Report
```

### Create Ride

Declare ride inputs and receive a canonical ride hash.

Expected artifact:

```text
ride_hash
```

### Optimize Ride

Compute deterministic matching, routing, and pricing artifacts from declared inputs.

Expected artifacts:

```text
assignment_hash
route_hash
price_hash
```

### Execute Lifecycle Transitions

Submit explicit transition requests and receive ordered execution steps.

Expected artifact:

```text
execution_steps_hash
```

### Build Trace

Assemble the ride hash, DAG hash, optimization hashes, and execution steps into a canonical execution record.

Expected artifact:

```text
trace_hash
```

### Replay

Recompute all artifacts from declared inputs and compare them to the trace.

Expected result:

```text
replay_valid = true
```

### Inspect Audit Report

Use the admin UI or audit endpoint to inspect the ride, optimization artifacts, execution steps, trace, replay report, and explanation.

## Ladder of Understanding

AfriRide should be learned in layers.

| Level | Audience goal | Required understanding |
| --- | --- | --- |
| 1 | Use the system | Proof API golden path |
| 2 | Verify a ride | Trace, replay report, audit UI |
| 3 | Debug a failure | Hash mismatch, drift, invalid evidence |
| 4 | Extend safely | Change classes and replay contract tests |
| 5 | Reason formally | AfriTech model, invariants, authority boundaries |

No onboarding path should require Level 5 knowledge before a user can run the golden path.

## Tooling Roadmap

### Replay Inspector

Shows:

```text
Ride -> DAG -> Assignment -> Route -> Price -> Execution Steps -> Trace -> Replay
```

Required behavior:

1. Highlight matching and mismatching hashes.
2. Show replay failure reasons.
3. Never allow mutation from the inspector.

### Trace Visualizer

Shows the lifecycle path:

```text
REQUESTED -> MATCHED -> DRIVER_ACCEPTED -> IN_PROGRESS -> COMPLETED
```

Required behavior:

1. Render execution steps in canonical order.
2. Overlay assignment, route, and price artifacts.
3. Mark missing or non-contiguous transitions as invalid.

### Proof Artifact Viewer

Shows canonical JSON and hashes for:

```text
ride
assignment
route
price
execution_steps
trace
```

Required behavior:

1. Expand canonical JSON without rewriting it.
2. Copy hashes for support and audit workflows.
3. Make clear that hashes are evidence, not authority without replay.

### Replay Failure Dashboard

Shows:

```text
trace_hash
failure_reason
failed_component
expected_hash
actual_hash
```

Required behavior:

1. Group failures by component.
2. Distinguish invalid input from storage drift.
3. Route all truth claims through replay output.

### CLI

The CLI should provide fast developer feedback without bypassing the Proof API or domain replay rules.

Initial command shape:

```bash
afriride-proof audit bundle.json
afriride-proof replay bundle.json
afriride-proof explain bundle.json
afriride-proof verify-store trace_hash
```

Required behavior:

1. Accept declared input bundles.
2. Print canonical hashes.
3. Exit nonzero on replay failure.
4. Never read hidden local state unless explicitly passed as input.

## Safe Evolution Framework

AfriRide can evolve, but changes must be classified before implementation.

### Class 1: Safe Changes

Examples:

1. UI layout changes
2. Read-only visualizations
3. Documentation and onboarding
4. Explanation wording derived from existing artifacts

Rules:

```text
No domain behavior change.
No replay behavior change.
No stored artifact schema change.
```

### Class 2: Bounded Changes

Examples:

1. New deterministic optimization layer
2. New declared pricing config field
3. New audit projection
4. New evidence-store adapter

Rules:

```text
Declared inputs required.
Trace integration required.
Replay validation required.
Contract tests required.
```

### Class 3: Core Changes

Examples:

1. Ride identity model
2. Lifecycle DAG semantics
3. Replay validator semantics
4. Canonical hash representation

Rules:

```text
Versioned semantics required.
Migration plan required.
Old traces must still replay under their original version.
Model review required before implementation.
```

## Replay Contract Tests

Every change that touches Class 2 or Class 3 behavior must preserve historical replay.

Minimum contract:

```text
For every stored fixture trace:
  replay(trace, declared_inputs) must produce the expected replay report.
```

Required fixture categories:

1. Valid ride with matching, routing, pricing, execution, and trace.
2. Matching drift.
3. Routing drift.
4. Pricing drift.
5. Execution-step drift.
6. Evidence-store corruption.

## Versioned Semantics

Future semantic changes must be versioned instead of overwriting truth.

```text
execution_v1 trace -> replay_v1
execution_v2 trace -> replay_v2
```

Rules:

1. A trace must declare its semantic version.
2. Replay must select rules by trace version.
3. New semantics may not invalidate older valid traces.

## Experimental Zones

Experiments are allowed only when isolated.

```text
sandbox artifacts may be generated
sandbox artifacts may be inspected
sandbox artifacts may not enter verified evidence storage
```

Promotion rule:

```text
sandbox idea -> declared input model -> trace integration -> replay validation -> evidence eligibility
```

## Non-Negotiable Checks

Every operability addition must answer yes to all four questions:

1. Does it improve clarity?
2. Does it preserve replay authority?
3. Does it avoid implicit behavior?
4. Does it keep the model vocabulary intact?

If any answer is no, the change is rejected or redesigned.

## Status

This playbook defines the first operability boundary for AfriRide. It surrounds the replay-governed core with clarity systems while preserving the existing authority chain:

```text
UI observes.
API exposes.
Domain computes.
Replay judges.
Evidence stores only after verification.
```
