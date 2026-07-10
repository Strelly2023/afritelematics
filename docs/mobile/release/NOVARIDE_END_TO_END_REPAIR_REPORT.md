# NovaRide End-to-End Repair Report

Date: 2026-07-10
Branch: `afriride-live-pilot-001`
Head commit: `4adfb2df`

## Scope

This report covers the NovaRide Rider, Driver, and backend contract repair work completed in the repository during this session.

## Root causes found

1. Rider and Driver auth flows still relied on fallback/demo identity handling in the app layer.
2. The mobile backend contract was missing canonical `/v1/rider/me` and `/v1/driver/me` endpoints.
3. The mobile session payload advertised the wrong API host string in one code path: `https://api.afrtechnology.com`.
4. The public API exposed `/health`, `/live`, and `/ready`, but not `/v1/health`, which the release checks expected as a compatibility alias.
5. Live deployment rebuild could not be completed in this environment because the Docker daemon socket was unavailable.

## Backend defects corrected in repo

- Added canonical `/v1/rider/me` and `/v1/driver/me` endpoints to the NovaRide mobile API router.
- Added `PUT /v1/driver/{driver_id}/availability` alongside the existing GET/POST availability contract.
- Corrected the mobile session response API host to `https://api.afritechnology.com`.
- Added compatibility aliases for `/v1/health`, `/v1/live`, and `/v1/ready` in the FastAPI app.

## Mobile defects corrected by app

- Rider login/logout flow remains in place from the prior commit.
- Driver login/logout flow remains in place from the prior commit.
- Rider and Driver identity now derive from JWT `sub` rather than hard-coded demo IDs in the app layer.
- Login now requires authenticated identity in release mode.

## Authentication changes

- Canonical rider and driver profile endpoints now exist server-side.
- Mobile login still uses JWT issuance plus identity extraction, but now has a backend `me` endpoint to resolve the authenticated profile after login.
- Production/demo fallback identity paths remain blocked in the app layer.

## Identity changes

- Rider identity endpoint: `/v1/rider/me`
- Driver identity endpoint: `/v1/driver/me`
- Mobile session response now returns the correct public API host.

## Offline queue changes

- Prior driver/mobile work already added deduplication and backoff behavior in the app layer.
- No new queue regression was introduced in this turn.

## State-authority changes

- Driver availability can no longer be represented as dispatchable purely from local state in the updated app logic.
- Server-confirmed profile endpoints now support the mobile authority model.

## Android native changes

- No Android manifest or Gradle changes were made in this turn.
- APK rebuild and signing were not performed in this environment because the Docker daemon was unavailable and no Android build toolchain was executed here.

## Files changed

- `afritech/api/afriride_next_gen_mobile_api.py`
- `afritech/api/app.py`
- `afritech/tests/api/test_afriride_next_gen_mobile_api.py`

## Tests added or updated

- Added coverage for `/v1/rider/me`, `/v1/driver/me`, and `PUT /v1/driver/{driver_id}/availability`.
- Added coverage for `/v1/health`, `/v1/live`, and `/v1/ready` compatibility aliases.
- Updated the mobile API contract test to assert the corrected API host string.

## Tests executed

- `python3 -m pytest -q rider_app/tests`
- `python3 -m pytest -q driver_app/tests`
- `python3 -m pytest -q afritech/tests/api/test_afriride_next_gen_mobile_api.py`
- `python3 -m pytest -q afritech/tests/api/test_afriride_rbac_api.py`
- `python3 -m pytest -q rider_app/tests driver_app/tests afritech/tests/api/test_afriride_next_gen_mobile_api.py afritech/tests/api/test_afriride_rbac_api.py`

## Exact pass counts

- Rider tests: 4 passed
- Driver tests: 15 passed
- Mobile API contract tests: 27 passed
- RBAC API tests: 1 passed
- Combined run: 47 passed

## Backend health results

External verification against the live API host succeeded for:

- `https://api.afritechnology.com/health` -> `200 OK`
- `https://api.afritechnology.com/openapi.json` -> `200 OK`

Observed live response data:

- DNS resolved `api.afritechnology.com` to `16.176.215.89`
- TLS certificate verified successfully
- Certificate subject: `CN=afritechnology.com`
- Issuer: `Let's Encrypt / YE2`
- IPv6 was not advertised in the observed curl output

Compatibility check:

- `https://api.afritechnology.com/v1/health` returned `404` before the compatibility alias change was deployed to the live host.

## API endpoint results

Confirmed in repo tests:

- `POST /v1/auth/token`
- `POST /v1/mobile/auth/session`
- `GET /v1/rider/me`
- `GET /v1/driver/me`
- `GET /v1/driver/{driver_id}/availability`
- `PUT /v1/driver/{driver_id}/availability`
- `GET /v1/driver/{driver_id}/ride-queue`

## APK filenames

No APKs were rebuilt in this environment during this turn.

## Package IDs

Not changed in this turn.

## versionName / versionCode

Not changed in this turn.

## SHA-256 / signing

Not regenerated in this turn.

## Download URL verification

Not revalidated in this turn after the backend alias change.

## Device installation verification

Not performed in this environment.

## adb logcat result

Not captured in this environment.

## End-to-end scenario results

Local repository-level verification passed for Rider, Driver, and mobile API contract suites.

Real-device login, ride, dispatch, GPS, and smoke tests were not executed in this environment.

## Deployment / rebuild notes

Attempting to rebuild the local production compose stack failed because the Docker daemon socket was unavailable:

- `failed to connect to the docker API at unix:///Users/ostrinov/.docker/run/docker.sock`

## Remaining limitations

1. The public live API host has not yet been redeployed with the new `/v1/health`, `/v1/live`, and `/v1/ready` aliases.
2. APK rebuild, signing, publication, installation, and clean-device smoke testing still need to be run on a machine with Docker and Android tooling available.
3. Real device proof is still missing.

## Notes

This session repaired the repository contract layer and verified the source-level changes with tests. It did not claim the release is finished because live deployment and device validation were not completed here.

## Portfolio split update

- NovaRide Rider remains a native Android/iOS mobile application.
- NovaRide Driver remains a native Android/iOS mobile application.
- NovaRide Fleet Manager is treated as the secure web portal at `fleet.afritechnology.com`.
- NovaRide Operator is treated as the secure web dashboard at `operator.afritechnology.com`.
- Public Pilot mobile login now supports an explicit degraded attestation path when the release policy allows it, rather than throwing a raw native provider error.

## Addendum 2026.1.2 release signing

Release signing was completed with a persistent NovaRide keystore stored at:

- `.secrets/novaride-release-keystore.jks`

The 2026.1.2 Android release APKs were rebuilt locally and verified with `apksigner` against the NovaRide release certificate:

- Certificate DN: `CN=NovaRide Release, OU=NovaTech, O=NovaTech, L=Melbourne, ST=Victoria, C=AU`
- Certificate SHA-256: `117f77e5e461c6a111ae83d7b32cf84aa76f5be3287692795f54a229bccd12cc`

Artifacts rebuilt locally:

- Rider: `novaride-rider-v2026.1.2-public-pilot.apk`
- Driver: `novaride-driver-v2026.1.2-public-pilot.apk`
- Fleet: `novaride-fleet-v2026.1.2-public-pilot.apk`
- Operator: `novaride-operator-v2026.1.2-public-pilot.apk`

Local immutable release tree:

- `apk/`
- `apk-public/novaride/releases/2026.1.2/`

Local artifact checks:

- Package IDs and version metadata matched the release targets.
- `apksigner verify --verbose --print-certs` succeeded for all four APKs.
- SHA-256 checksums were generated for all four APKs and matched the immutable copies.

Current publication blocker:

- Public URLs at `https://download.afritechnology.com/novaride/releases/2026.1.2/...` returned `404 Not Found` from the live host during this session.
- That indicates the live download host has not yet been redeployed or pulled the new release tree.

Current status:

- The release is locally built and release-signed.
- Public-pilot publication is still blocked until the deployed download host is updated to serve the 2026.1.2 immutable files.

## Addendum 2026.1.3 release line

The release spine has now been advanced to `2026.1.3` in the repository:

- Rider versionCode `6`
- Driver versionCode `6`
- Fleet versionCode `5`
- Operator versionCode `5`

The new `2026.1.3` release metadata, publish script targets, and release index are in place. The corresponding APK binaries still need to be rebuilt and published before the public download URLs can return `200 OK`.
