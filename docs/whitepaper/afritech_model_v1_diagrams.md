# AfriTech Model v1 Diagrams

## Purpose

These diagrams visualize the canonical model without introducing new concepts.

All diagram elements map to the v1 vocabulary:

- Execution
- Environment
- Optimization
- Replay

## Definition Mapping

```mermaid
flowchart LR
    DAG["DAG"] --> Execution["Execution"]
    Scheduler["Scheduler"] --> Execution
    Scheduler --> Optimization["Optimization"]
    GraphOptimizer["Graph Optimizer"] --> Optimization
    Fabric["Distributed Fabric"] --> Environment["Environment"]
    DistributedOS["Distributed OS"] --> Environment
    Trace["Trace"] --> Replay["Replay"]
    ReplayValidator["Replay Validator"] --> Replay
```

## Execution Flow

```mermaid
flowchart TD
    OS["Distributed OS"] --> Fabric["Distributed Fabric"]
    Fabric --> DAG["Canonical DAG"]
    DAG --> Optimizer["Graph Optimizer"]
    Optimizer --> Scheduler["Locality Scheduler"]
    Scheduler --> Execution["Execution"]
    Execution --> Trace["Trace"]
    Trace --> Replay["Replay Validation"]
```

## Architecture Stack

```mermaid
flowchart TD
    Concept["Concept"] --> Invariant["Invariant"]
    Invariant --> Rule["Rule"]
    Rule --> Guard["Guard"]
    Guard --> Scheduler["Scheduler"]
    Scheduler --> Optimizer["Graph Optimizer"]
    Optimizer --> Fabric["Distributed Fabric"]
    Fabric --> OS["Distributed OS"]
    OS --> Trace["Trace"]
    Trace --> Replay["Replay"]
    Replay --> CI["CI"]
```

## Truth Separation

```mermaid
flowchart LR
    Optimization["Optimization"] --> Execution["Execution"]
    Environment["Environment"] --> Execution
    Execution --> Output["Output"]
    Execution --> Trace["Trace"]
    Trace --> Replay["Replay"]
    Output --> Replay
    Replay --> Truth["Truth Authority"]
```

## Constraint

These diagrams are illustrative only.

They must not be used to introduce new definitions, roles, or authority boundaries.
