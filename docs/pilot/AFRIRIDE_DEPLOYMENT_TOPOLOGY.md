# AfriRide Deployment Topology

Status: TOPOLOGY BLUEPRINT

## Pilot Topology

```text
Driver App
  -> Backend API
  -> Protocol Node Cluster
  -> Ledger / State Service
  -> Operator Dashboard

Rider App
  -> Backend API
  -> Protocol Node Cluster
  -> Proof / Replay APIs
```

## Minimum Controlled Pilot

- Backend API: Render service
- Protocol cluster: 3-5 logical nodes
- Operator dashboard: observer-only
- Devices: one driver phone, one rider phone, one operator laptop
- Evidence storage: `traces/pilot_runs/live_pilot_001`

## Scale Topology

| Stage | Nodes | Scope |
| --- | ---: | --- |
| Stage 1 | 3-5 | controlled pilot |
| Stage 2 | 10 | expanded pilot |
| Stage 3 | 20 | adversarially simulated target |

## Edge Nodes

Future edge nodes may be added for local resilience, but they must remain protocol participants, not independent dispatch authorities.

## Authority Boundaries

- Mobile apps are interface-only.
- Operator dashboard is observer-only.
- Backend API brokers requests but must not bypass protocol evidence.
- Ledger and replay remain protocol-owned.
