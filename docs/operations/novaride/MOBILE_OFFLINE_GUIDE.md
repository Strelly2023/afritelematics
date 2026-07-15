# NovaRide Mobile Offline Guide

Rider and driver apps use persistent queues backed by AsyncStorage with device-bound key material stored through Expo SecureStore.

Priority order:

1. SOS and safety
2. active-trip state
3. location updates
4. booking and dispatch acknowledgements
5. payment confirmations
6. receipts and ratings
7. analytics

Low-priority telemetry must never block safety operations. Sync requests require device ID, nonce, timestamp, and signed payload headers.
