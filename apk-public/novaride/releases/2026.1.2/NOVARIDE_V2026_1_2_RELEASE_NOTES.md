# NovaRide Mobile v2026.1.2 Public Pilot

## Scope

This release hardens Rider, Driver, Fleet Manager, and Operator public-pilot delivery. It does not enable General Availability, unrestricted public registration, real payments, or autonomous authority.

## Key Changes

- Release metadata updated to `2026.1.2` across all four apps.
- Release signing switched to the persistent NovaRide release keystore.
- Immutable APK release paths created for Rider, Driver, Fleet, and Operator.
- Release manifests, checksum generation, publication, and verification scripts updated for the new version.

## Authority Boundaries

- NovaID owns identity and authentication.
- NovaRide owns mobility workflows.
- NovaPay owns payment execution.
- NovaTrust owns evidence and receipts.
- NovaAI remains advisory only.

## Status

- `ga_allowed=false`
- `real_payments_enabled=false`
- Release approval remains blocked until the public download host serves the new immutable APKs instead of 404 responses.
- iOS IPA artifacts are not built in this release run.
