# System Overview

AfriTech is composed of layered components:

1. Network Layer
2. P2P and Gossip Layer
3. Execution Layer
4. Proof Layer
5. Consensus Layer
6. Trust Layer
7. Ledger Layer
8. Replay Layer
9. State Layer
10. Service Layer
11. Observability Layer

## Flow

```text
Client -> Node -> Gossip -> Execution -> Proof -> Consensus -> Ledger -> State
```

## Classification

AfriTech is an execution-centric sovereign ledger protocol. It is not a classical blockchain; the block payload is accepted execution proof, and state is projected from committed execution history.
