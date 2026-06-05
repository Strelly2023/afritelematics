# Diagrams

## Full System Flow

```mermaid
flowchart TD
    Client["Client / Application"] --> Network["Network Layer<br/>TLS, WSS, Handshake"]
    Network --> Gossip["P2P Gossip"]
    Gossip --> Kernel["Execution Kernel"]
    Kernel --> Proof["Proof Generation"]
    Proof --> Consensus["Consensus Engine"]
    Consensus --> Trust["Trust Evaluation"]
    Trust --> Ledger["Audit Ledger<br/>Execution Blocks"]
    Ledger --> Replay["Replay Verification"]
    Ledger --> State["State Machine"]
    State --> Service["Service Layer"]
    Service --> Observability["Observability<br/>Metrics, Traces, Exports"]
```

## Consensus Flow

```mermaid
flowchart LR
    Proofs["Proofs"] --> Validate["Validate"]
    Validate --> Aggregate["Aggregate by Result Hash"]
    Aggregate --> Quorum["Quorum Check"]
    Quorum --> Finalize["Finalize Accepted Proofs"]
    Finalize --> Commit["Commit Block"]
```

## Trust Flow

```mermaid
flowchart LR
    Node["Node"] --> Behavior["Proof / Behavior"]
    Behavior --> Valid{"Valid?"}
    Valid -->|yes| Reward["Consensus Match / Trust Stable"]
    Valid -->|no| Slash["Slashing Event"]
    Slash --> Score["Trust Score Down"]
    Score --> Firewall["Possible Peer Isolation"]
```

## State Projection

```mermaid
flowchart TD
    Ledger["Ledger Blocks"] --> Replay["Replay Blocks"]
    Replay --> Reducers["Contract Reducers"]
    Reducers --> Canonical["One Canonical Transition<br/>per Contract + Result Hash"]
    Canonical --> State["Global State"]
    State --> Services["Read-only Services"]
```

## Node Network

```mermaid
flowchart LR
    A["Node A"] <--> B["Node B"]
    B <--> C["Node C"]
    C <--> D["Node D"]
    D <--> E["Node E"]
    A <--> E
    B <--> D
```

## AfriRide Pilot Flow

```mermaid
flowchart TD
    Driver["Driver App"] --> API["Backend API"]
    Rider["Rider App"] --> API
    API --> Events["Signed Events"]
    Events --> Protocol["AfriTech Multi-node Protocol"]
    Protocol --> Blocks["Consensus Blocks"]
    Blocks --> RideState["Ride + Receipt State"]
    Blocks --> Evidence["Evidence Bundle"]
    Operator["Operator Dashboard"] --> Evidence
```

## Text Fallback

```text
Client -> Network -> P2P -> Execution -> Proof -> Consensus -> Ledger -> State -> Service
Proofs -> Validate -> Aggregate -> Quorum -> Finalize -> Commit Block
Invalid proof -> Slashing -> Trust score down -> Possible isolation
Ledger -> Replay -> Reducers -> Global State
```
