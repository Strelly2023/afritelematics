# NovaRide Mobile v2026.1.2 Public Pilot

## Scope

This release hardens Rider and Driver public-pilot delivery. Fleet Manager and Operator are treated as secure web products on `fleet.afritechnology.com` and `operator.afritechnology.com`. It does not enable General Availability, unrestricted public registration, real payments, or autonomous authority.

## Key Changes

- Release metadata updated to `2026.1.2` across all four apps.
- Release signing switched to the persistent NovaRide release keystore.
- Immutable APK release paths created for Rider and Driver. Fleet Manager and Operator are web products and do not require mandatory Public Pilot APK installation.
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
