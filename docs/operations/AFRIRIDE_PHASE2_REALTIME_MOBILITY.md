# AfriRide Phase 2 real-time mobility

## Contract

`afriride.mobility.v1` is the single mobile stream contract. Clients connect to
`/ws/mobility/{actor_id}` with a JWT, persisted `cursor`, and optional
`ride_id`. Frames are server projections and never bypass HTTP lifecycle
authority.

Events:

- `SESSION_READY` — authenticated session and heartbeat policy
- `HEARTBEAT_ACK` / `DRIVER_PRESENCE_UPDATED` — presence and last-seen state
- `DISPATCH_REQUESTED` — new demand for available drivers
- `RIDE_STATE_UPDATED` — accepted, arrived, started, completed or cancelled
- `DRIVER_LOCATION_UPDATED` — coordinates plus recalculated distance and ETA
- `SERVER_PUSH_EVENT` — foreground socket equivalent of a background push

Clients persist the highest sequence, reconnect with exponential backoff and
jitter, and request replay after that cursor. Existing HTTP polling remains a
degraded-mode fallback.

## Runtime topology

The in-process hub is suitable for local and single-instance pilot operation.
Commercial multi-instance deployment must replace its event deque and presence
map with Redis Streams (or Kafka plus Redis presence), while preserving the
same contract and sequence semantics. Use a shared consumer/outbox so database
commit, WebSocket publication and push fallback cannot diverge.

Set `AFRIRIDE_PUSH_DELIVERY_ENABLED=true` only after FCM/APNs credentials are
configured in EAS. Push registrations are Expo tokens; background delivery is
sent through the Expo gateway. All attempts are recorded in the server outbox.

## Operational targets

- heartbeat: 15 seconds
- presence expiry: 45 seconds
- replay retention: 10,000 process-local events in pilot
- reconnect: exponential 1–30 seconds with jitter
- REST polling: retained at 4 seconds only as fallback during migration
- socket payloads: observation-only; ride mutation remains API-authorized

Monitor connection count, replay depth, heartbeat lag, event-to-device
latency, reconnect rate, push retry rate and sequence gaps before increasing
city traffic.

## Phase 2B production configuration

Set `AFRIRIDE_REALTIME_BACKEND=redis` and `AFRIRIDE_REDIS_URL`. Startup fails
instead of silently falling back when Redis configuration is invalid. Redis
Streams use `mobility:{target}` and presence uses `presence:{actor_id}` with a
45-second TTL. Numeric pilot cursors remain accepted; new clients persist Redis
`stream_id` values.

`mobile_push_outbox` and `mobile_push_devices` are created by both SQLite and
PostgreSQL schemas. Driver assignment, its ride event, and the push outbox row
commit on one database connection. Run the retry worker separately:

```bash
python -m afriride_system.workers.mobile_push_worker
```

The reference multi-instance topology is
`deploy/novaride/docker-compose.realtime.yml`. Production should use managed
PostgreSQL/Redis, encrypted Redis transport, ACLs, backups, stream retention
monitoring, and a single schema migration job before scaling API replicas.
