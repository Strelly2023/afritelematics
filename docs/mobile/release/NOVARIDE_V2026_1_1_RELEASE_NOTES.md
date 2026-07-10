# NovaRide Mobile v2026.1.1 Public Pilot

## Scope

This release hardens Rider and Driver public-pilot delivery. It does not enable General Availability, unrestricted public registration, real payments, or autonomous authority.

## Key Changes

- Dedicated static download routing for `download.afritechnology.com`.
- Immutable APK release paths under `/novaride/releases/2026.1.1/`.
- Public-pilot Rider and Driver metadata set to `2026.1.1`.
- Driver API diagnostics and server-confirmed dispatchability guardrails.
- Rider home refocused on pickup, destination, ride type, fare, request, trip, safety, payment, and receipt/support.
- Release manifests, checksum generation, provenance, publication, and public URL verification scripts.

## Authority Boundaries

- NovaID owns identity and authentication.
- NovaRide owns mobility workflows.
- NovaPay owns payment execution.
- NovaTrust owns evidence and receipts.
- NovaAI remains advisory only.

## Status

- `ga_allowed=false`
- `real_payments_enabled=false`
- Release approval is required before production publication.
- Current local APK artifacts are blocked from public-pilot approval because they were signed with the Android Debug certificate.
- Live API contract preflight reaches `https://api.afritechnology.com`, but `/ready` currently returns HTTP 503.
- The production download host must be redeployed with the dedicated static `download.afritechnology.com` NGINX block before immutable URLs can pass public verification.

## Planned iOS Artifacts

- `https://download.afritechnology.com/novaride/releases/2026.1.1/novaride-rider-v2026.1.1-public-pilot.ipa`
- `https://download.afritechnology.com/novaride/releases/2026.1.1/novaride-driver-v2026.1.1-public-pilot.ipa`

IPA files are not built in this release run and require Apple signing/provisioning validation before publication.
