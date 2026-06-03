# AfriRide GA eLive Layered Architecture Diagram

This document captures the GA eLive architecture as a layered, enforceable system model aligned with the AfriTech deterministic execution pipeline.

## Artifact Classification

```text
Artifact Type:
EXECUTIVE ARCHITECTURE ARTIFACT

NOT:
Proof Artifact
NOT:
Runtime Authority Surface
```

```text
Diagram explains.
Validators enforce.
Replay proves.
```

## Executive Diagram

```mermaid
flowchart TB
    subgraph L1["1. Presentation Layer"]
        rider["Rider Mobile App"]
        driver["Driver Mobile App"]
        admin["Admin Dashboard"]
        public_web["Public Web App"]
    end

    subgraph L2["2. API and Gateway Layer"]
        api["afritech.api.app"]
        auth["Authentication"]
        ws["HTTP / WebSocket Entry"]
    end

    subgraph L3["3. Edge Layer"]
        adapter["edge.adapter.runtime_adapter"]
        validation["edge.adapter.validation"]
        normalizer["edge.normalization.normalizer"]
        edge_guard["guards.edge_input_guard"]
    end

    subgraph L4["4. Ingestion Layer"]
        ingestor["edge.ingestion.queue_ingestor"]
    end

    subgraph L5["5. Execution Layer"]
        queue["execution.queue.*"]
        router["execution.partition.router"]
        workers["execution.worker.worker_pool"]
        core["core.engine"]
        matching["core.matching_engine"]
    end

    subgraph L6["6. State and Storage Layer"]
        event_log["storage.event_log"]
        event_schema["storage.event_schema"]
    end

    subgraph L7["7. Replay Layer"]
        replay["storage.replay_engine"]
        trace["trace.trace_reconstructor"]
    end

    subgraph L8["8. Proof and Witness Layer"]
        receipt["proof.constitutional_receipt"]
        witnesses["proof.witness.*"]
    end

    subgraph L9["9. Observability Layer"]
        dashboards["Dashboards"]
        analytics["Analytics"]
        monitoring["Monitoring"]
    end

    subgraph L10["10. Governance and CI Layer"]
        validators["afritech.ci.*"]
        claims["Claim Discipline"]
        gates["Four-Gate Validation"]
        enforcement["Enforcement Integrity"]
    end

    subgraph L11["11. Integration Layer"]
        payments["Payments"]
        maps["Maps"]
        sms["SMS"]
    end

    subgraph L12["12. Runtime and Distributed Layer"]
        partitions["Partition System"]
        distributed_workers["Distributed Workers"]
        fabric["Execution Fabric"]
    end

    rider --> api
    driver --> api
    admin --> api
    public_web --> api

    ws --> auth --> api
    api --> adapter --> validation --> normalizer --> edge_guard --> ingestor
    ingestor --> queue --> router --> workers --> core --> matching
    matching --> event_log
    core --> event_log
    event_log --> event_schema --> replay --> trace --> receipt --> witnesses

    event_log -. "read-only" .-> dashboards
    replay -. "read-only" .-> analytics
    receipt -. "read-only" .-> monitoring

    validators -. "blocks drift" .-> api
    validators -. "blocks drift" .-> adapter
    validators -. "blocks drift" .-> core
    validators -. "blocks drift" .-> replay

    payments --> adapter
    maps --> adapter
    sms --> adapter

    router --> partitions
    workers --> distributed_workers
    core --> fabric
```

## Critical Flow

```mermaid
sequenceDiagram
    participant UI as Presentation Layer
    participant API as API Gateway
    participant Edge as Edge Adapter / Normalizer
    participant Ingest as Queue Ingestion
    participant Exec as Deterministic Execution
    participant Store as Immutable Event Log
    participant Replay as Replay Engine
    participant Proof as Receipt + Witness
    participant Obs as Read-only Views
    participant CI as Governance / CI

    UI->>API: User action
    API->>Edge: Route request
    Edge->>Edge: Validate and normalize
    Edge->>Ingest: Admit canonical event
    Ingest->>Exec: Queue event
    Exec->>Store: Append resulting event
    Store->>Replay: Reconstruct truth
    Replay->>Proof: Emit verified evidence
    Proof-->>UI: Receipt / replay / explanation
    Store-->>Obs: Read-only projections
    CI-->>API: Enforce no business logic
    CI-->>Edge: Enforce adapter-normalizer-ingestor order
    CI-->>Exec: Enforce determinism
    CI-->>Replay: Enforce replay safety
```

## Enforcement Boundaries

```mermaid
flowchart LR
    ui["Presentation"]
    api["API"]
    edge["Edge"]
    queue["Ingestion Queue"]
    execution["Execution Core"]
    storage["Event Log"]
    replay["Replay"]
    proof["Proof"]

    ui -->|"request/display only"| api
    api -->|"no direct execution"| edge
    edge -->|"canonical event only"| queue
    queue -->|"ordered admission"| execution
    execution -->|"append-only results"| storage
    storage -->|"replay input"| replay
    replay -->|"truth verification"| proof
    proof -->|"evidence surfaces"| ui

    forbidden_ui["Forbidden in UI: pricing, dispatch, replay mutation, direct core access"]
    forbidden_api["Forbidden in API: business logic, direct execution"]
    forbidden_obs["Forbidden in Observability: state mutation"]

    forbidden_ui -.-> ui
    forbidden_api -.-> api
    forbidden_obs -.-> storage
```

## Layer Responsibility Matrix

| Layer | Role | Primary Modules | Constraint |
| --- | --- | --- | --- |
| Presentation | User interaction | Rider app, Driver app, Admin Dashboard, Public Web | Display/request only |
| API | Entry point | `afritech.api.app` | No business logic, no direct execution |
| Edge | Input control | `edge.adapter.*`, `edge.normalization.*`, `guards.edge_input_guard` | Adapter to normalization to ingestion only |
| Ingestion | Event admission | `edge.ingestion.queue_ingestor` | Everything becomes an event |
| Execution | Deterministic processing | `execution.queue.*`, `execution.worker.*`, `core.engine`, `core.matching_engine` | Replay-stable output |
| Storage | Immutable state | `storage.event_log`, `storage.event_schema` | Append-only event truth |
| Replay | Truth engine | `storage.replay_engine`, `trace.trace_reconstructor` | Truth equals replay result |
| Proof | Audit evidence | `proof.constitutional_receipt`, `proof.witness.*` | Full traceability |
| Observability | Read-only intelligence | Dashboards, analytics, monitoring | Explain only |
| Governance | Enforcement | `afritech.ci.*` | Blocks drift |
| Integration | External systems | Payments, maps, SMS | Normalize before influence |
| Runtime | Distributed scale | Partitions, distributed workers, execution fabric | Deterministic convergence |

## System Law

```text
Request -> Event -> Deterministic Execution -> Replay -> Proof -> Truth
```

## Enforceable System Law

All admissible system truth MUST satisfy:

```text
1. Request MUST be converted into a canonical event.
2. Event MUST be normalized and hashed deterministically.
3. Execution MUST be performed only through queued worker execution.
4. Execution MUST produce a replayable trace.
5. Replay MUST reconstruct the exact execution deterministically.
6. Proof MUST bind replay output to invariant validation.
7. ONLY replay output constitutes admissible truth.
```

Canonical identity law:

```text
Truth = Replay(Event -> Deterministic Execution)
```

```text
No direct execution from API.
No business logic in presentation surfaces.
No mutation from observability.
No truth without replay.
```

## Forbidden Violations

```text
FORBIDDEN:

- Truth derived from API response.
- Truth derived from UI state.
- Truth derived from logs only.
- Truth derived from receipts without replay validation.
- Any execution bypassing queue ingestion.
- Any non-deterministic execution path.
```

## Frozen Enforcement Boundaries

```text
Boundary 1:
API -> Core
FORBIDDEN

Boundary 2:
Edge -> Core (direct)
FORBIDDEN

Boundary 3:
Execution outside queue
FORBIDDEN

Boundary 4:
Truth outside replay
FORBIDDEN
```

## Final Closure Statement

```text
AfriRide GA eLive architecture is now formally defined as a replay-governed
deterministic execution system where:

- architecture defines structure,
- validators enforce discipline,
- replay defines truth.

The system enforces a strict execution law:

Request -> Event -> Deterministic Execution -> Replay -> Proof -> Truth

All authority remains bounded below replay, preventing upstream layers
from defining or mutating truth.

This constitutes an executive architectural artifact with full CI
enforcement and invariant alignment.

Controlled pilot readiness remains unproven and is intentionally isolated
from architectural completion claims.
```
