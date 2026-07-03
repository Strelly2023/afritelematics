# AfriRide Phase 4 digital twin and Phase 5 trust-aware safety

## Fleet command center

`GET /v1/operations/digital-twin` returns the shared
`afriride.fleet_twin.v1` projection:

- current driver coordinates, heading, speed, battery and integrity;
- active and queued rides;
- demand heat cells and surge pressure;
- zone traffic derived from fleet speeds;
- durable safety alerts;
- online, stale-position and incident fleet health;
- ride and push queue lengths.

Telemetry and incidents use the authoritative AfriRide SQL storage, so every API
replica displays the same twin. The twin is projection-only and cannot mutate
rides. Redis mobility events continue to provide low-latency updates.

## Safety rules

Location ingestion deterministically evaluates:

- device/mock-location flags and physically impossible movement;
- speeds above 130 km/h;
- stops of at least ten minutes;
- route deviation of at least 500 metres;
- untrusted device state;
- GPS accuracy worse than 100 metres.

The safety sweep detects driver inactivity after two minutes. Rider distress
accepts SOS, silent SOS, unsafe-driver and medical signals.

Signals create idempotent durable incidents with one workflow:

- `driver_verification`
- `rider_verification`
- `operations_alert`
- `sos_handling`

Operators use
`POST /v1/operations/safety/incidents/{incident_id}/actions` to acknowledge,
record verification, dispatch SOS response or resolve. Every transition emits a
`SAFETY_WORKFLOW_UPDATED` event. Detection never automatically declares guilt,
contacts authorities or alters a trip.

## Runbook

Critical SOS events require immediate acknowledgement, rider contact through
approved channels, location validation and local emergency escalation policy.
Preserve telemetry, replay, device-integrity result and operator actions.

For suspected spoofing, hold automated dispatch, request driver verification
and compare independent network/device evidence. For unsafe speed or deviation,
prioritize rider welfare before fraud investigation. For stale telemetry,
confirm network and battery state before treating inactivity as a safety event.

Monitor telemetry age, incident creation rate, duplicate suppression, response
time, unresolved critical incidents, safety-rule false positives and command
center projection latency.
