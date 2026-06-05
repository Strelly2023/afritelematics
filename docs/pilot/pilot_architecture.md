# Pilot Architecture

AfriRide pilot execution is a controlled, gated deployment of the AfriTech protocol.

## Devices

- `driver_phone_001`
- `rider_phone_001`
- `operator_laptop_001`

## Required Live Gates

- backend health
- event endpoint
- CORS
- WebSocket or fallback
- Driver APK
- Rider APK
- Operator dashboard
- signed event emission
- replay export
- emergency contact
- manual truth editing disabled

## Current Rule

Repository-side readiness does not authorize live pilot execution.
