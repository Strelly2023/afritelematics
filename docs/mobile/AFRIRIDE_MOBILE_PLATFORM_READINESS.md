# AfriRide Mobile Platform Readiness

Status: MOBILE PLATFORM READINESS
Classification: CROSS_PLATFORM_MOBILE_EXECUTION_SURFACE

Purpose: define the real mobile-platform support boundary for the AfriRide
mobile clients and the checklist required before a first partner demo or pilot.

This document is a mobile readiness and claim-boundary surface.
It is not proof that app-store publication or production mobile rollout is
already complete.

## Current Mobile Surface Split

The codebase currently contains two mobile client families:

- Expo / React Native execution apps in `afriride_system/mobile/`
- Flutter pilot clients in `afriride_system/flutter/`

These do not carry the same readiness claim.

## Expo / React Native Apps

The following apps are built as Expo / React Native clients:

- `afriride_system/mobile/passenger_app`
- `afriride_system/mobile/driver_app`
- `afriride_system/mobile/operator_app`

These apps use:

- `expo start`
- `expo start --android`
- `expo start --ios`

This permits the bounded claim that the Expo app family is designed as a single
cross-platform codebase for Android and iOS execution surfaces.

## Flutter Pilot Clients

The following pilot clients exist in:

- `afriride_system/flutter/rider_app`
- `afriride_system/flutter/driver_app`

These are controlled pilot scaffolds.

They are event-producer clients and observation clients.
They are not the current primary cross-platform production mobile claim.

In the present repo state, the checked-in platform scaffolding visible for these
Flutter clients is Android.

Therefore this document does not permit the claim that the Flutter pilot
surfaces are fully evidenced in-repo for both Android and iOS packaging.

## What Is Safe To Claim Now

Safe claim:

```text
The Expo mobile apps are designed as Android + iOS cross-platform clients over
the authoritative AfriRide API.
```

Safe claim:

```text
The Flutter rider and driver pilot clients are bounded pilot surfaces with
Android scaffolding visible in the repo.
```

Unsafe claim:

```text
all mobile surfaces are already app-store-ready on both Android and iOS
```

## Technical Checklist Before First Partner Demo

### 1. Platform Targets

- verify Android launch through Expo
- verify iOS launch through Expo
- verify API base URL switching for emulator, simulator, and physical device

### 2. Permissions

- network access
- location / GPS access where required
- background execution behavior if used

### 3. Time And Trace Discipline

Because the mobile layer emits trace-linked events, verify:

- client timestamp generation
- local clock normalization assumptions
- event ordering behavior under delay

### 4. Offline / Weak Network Handling

Verify:

- idempotency key reuse safety
- delayed request retry behavior
- reconnection after poor connectivity
- no client-side authority override during offline periods

### 5. Pilot UX Discipline

Verify:

- rider status flow remains understandable
- driver lifecycle actions remain clear
- operator mobile view does not imply truth authority

## Distribution Boundary

This document permits only this bounded claim:

```text
AfriRide has a cross-platform Expo mobile client family and a bounded mobile
readiness checklist for real device and partner-demo preparation
```

It does not permit this claim:

```text
all mobile clients are already published to the App Store and Play Store
```

