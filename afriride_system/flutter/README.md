# AfriRide Flutter Pilot Clients

STATUS: CONTROLLED PILOT SCAFFOLD
CLASSIFICATION: EVENT PRODUCER CLIENTS

These Flutter clients are minimal pilot surfaces for producing signed mobile
events against the AfriTech ingestion contract.

They are not production mobile apps, app-store artifacts, payment clients, KYC
clients, or runtime authority surfaces.

## Boundary

```text
Flutter client
-> local event buffer
-> deterministic send order
-> POST /v1/events
-> edge normalization
-> constitutional execution
```

WebSocket tracking is observation-only:

```text
execution projection -> /ws/{ride_id} -> rider display
```

The event stream remains the source of truth.
