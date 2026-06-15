# AfriRide App Store And Play Store Release Checklist

Status: APP STORE AND PLAY STORE RELEASE CHECKLIST
Classification: MOBILE_DISTRIBUTION_READINESS_SURFACE

Purpose: define the governed release checklist for the Expo-based AfriRide
mobile apps before partner demos, pilot distribution, TestFlight, or Play Store
submission.

This checklist is a distribution-readiness surface.
It is not proof that store publication is already complete.

## Covered Apps

- `rider_app`
- `driver_app`
- `dashboard`

The machine-readable release manifests live under `docs/mobile/release/` and
are exposed through:

```http
GET /public/afriride/mobile/release-readiness
```

## Release Goal

Ship the Expo / React Native app family through bounded channels while
preserving:

- replay-backed truth boundary
- mobile trace discipline
- idempotent request behavior
- correct API base URL handling

## Release Readiness Checklist

### 0. Release Contract

- run `python -m afritech.ci.afriride_mobile_release_validator`
- verify `/public/afriride/mobile/release-readiness`
- confirm `production_claim_allowed = false` until pilot evidence, legal review,
  store review, and operator approval are complete
- confirm Rider, Driver, and Operator Dashboard manifests are present
- confirm `production_blockers` are closed before any production store track

### 1. Build Targets

- verify `expo start --android`
- verify `expo start --ios`
- verify production app metadata in each `app.json`
- verify bundle identifiers / package names are intentional

### 2. Environment And Endpoint Discipline

- set `EXPO_PUBLIC_AFRIRIDE_API_URL` correctly per environment
- verify Android emulator path using `10.0.2.2`
- verify physical-device path using LAN or deployed URL
- confirm no demo build ships with `127.0.0.1` hard dependency

### 3. Authentication And Trace

- verify `/auth/token` flow
- verify mobile `client_event` envelope emission
- verify `local_timestamp` is present
- verify idempotency keys are sent for write actions

### 4. Permissions

- network permission
- GPS / location permission where needed
- notification or background permission only if actually used

### 5. Pilot Distribution Paths

- Android internal APK or Play internal testing
- iOS TestFlight
- operator installation instructions
- rollback path to previous known-good build

### 6. Store Listing Readiness

- app description reflects bounded pilot truthfully
- screenshots do not imply authority beyond replay-backed surfaces
- privacy text does not overclaim certification

## Mandatory Boundary

This checklist permits only this bounded claim:

```text
AfriRide has a concrete release checklist for Expo-based Android and iOS pilot
distribution
```

It does not permit this claim:

```text
all apps are already published in production stores
```
