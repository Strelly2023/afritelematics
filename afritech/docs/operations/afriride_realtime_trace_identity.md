# AfriRide Realtime, Trace, and Device Identity Surfaces

STATUS: PILOT IMPLEMENTATION EVIDENCE SLICE
CLASSIFICATION: OBSERVATION + EVIDENCE + TRUST BOUNDARY

## Realtime Rule

WebSockets are observation-only.

```text
event stream = source of truth
websocket update = projected observation
```

The implemented realtime surface is:

```text
afritech.api.realtime.ws_server.WebSocketHub
```

It publishes `STATE_UPDATE` messages to `ride_{ride_id}` channels with
projection-only authority.

## Trace Rule

Pilot traces must be recordable and replay-inspectable.

Implemented surfaces:

```text
afritech.trace.pilot_trace_recorder.PilotTraceRecorder
afritech.trace.replay_inspector.ReplayInspector
```

Trace records contain:

```text
trace_id
events
normalized_events
execution_states
witnesses
hash
```

## Device Identity Rule

No anonymous event authority.

Implemented surfaces:

```text
afritech.security.device_identity.DeviceIdentity
afritech.security.device_identity.DeviceRegistry
afritech.security.device_identity.PublicKeyAuthenticator
```

Each device binds:

```text
user_id -> device_id -> public_key
```

and event signatures are verified against the registered public key.

## Non-Claims

This artifact does not claim production WebSocket deployment, production key
custody, secure enclave integration, key rotation, device revocation, or a
completed pilot trace corpus.
