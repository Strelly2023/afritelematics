# NovaRide Mobile v2026.1.4 Public Pilot

## Scope

This release advances the NovaRide public-pilot line with secure logout, account switching, and a more complete Rider and Driver control surface. It remains a public-pilot release and does not enable General Availability, unrestricted public registration, real payments, or autonomous authority.

## Key Changes

- Secure logout and session isolation for Rider and Driver.
- Dedicated account/profile surfaces with logout access from multiple entry points.
- Rider booking flow tightened around pickup, destination, fare, request, ride lifecycle, payment, receipt, and replay.
- Driver shift flow tightened around shift start/end, GPS, availability, trip execution, and controlled logout.
- Immutable APK release paths under `/novaride/releases/2026.1.4/`.
- Public-pilot Rider and Driver metadata set to `2026.1.4`.
- Release manifests, checksum generation, provenance, publication, and public URL verification scripts advanced to the new release line.

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
- Public download verification must pass against the rebuilt 2026.1.4 APKs before this release can be treated as complete.

## Planned iOS Artifacts

- `https://download.afritechnology.com/novaride/releases/2026.1.4/novaride-rider-v2026.1.4-public-pilot.ipa`
- `https://download.afritechnology.com/novaride/releases/2026.1.4/novaride-driver-v2026.1.4-public-pilot.ipa`

IPA files are not built in this release run and require Apple signing/provisioning validation before publication.
