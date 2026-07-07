# Private Development APK Testing

## Purpose

Validate APK metadata, checksums, release manifests, and LAN download paths before controlled pilot testing.

## Scope

- NovaRide Rider
- NovaRide Driver
- NovaRide Operator
- NovaRide Fleet
- NovaPay Consumer
- NovaPay Agent
- NovaPay Merchant
- NovaPay Business
- NovaID Personal
- NovaID Business
- NovaID Employee
- NovaID Partner
- NovaID Inspector

## Validation Steps

1. Confirm the APK exists.
2. Confirm the matching `.sha256` file exists.
3. Confirm the checksum matches the APK.
4. Confirm the release manifest exists.
5. Confirm the manifest includes the app name, version name, and version code.
6. Confirm the LAN download URL is documented.
7. Confirm the APK is marked for private development or local-only distribution.

## Failure Handling

If an artifact is missing, fail with a clear path-specific message.
If the checksum is invalid, fail immediately.
If the manifest claims production readiness, fail immediately.

