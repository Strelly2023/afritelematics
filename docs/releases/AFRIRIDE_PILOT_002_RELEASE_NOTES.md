# AfriRide / NovaRide Pilot 002 Release Notes

Release date: 2026-07-05

This is a controlled pilot release package. It is not public production release readiness.

## Versioning

- Driver app
  - versionCode: 2
  - versionName: `0.2.0`

- Rider app
  - versionCode: 2
  - versionName: `0.2.0`

## Canonical release artifacts

- `apk/afriride-driver-live_pilot_002-release.apk`
- `apk/afriride-driver-live_pilot_002-release.apk.sha256`
- `apk/afriride-rider-live_pilot_002-release.apk`
- `apk/afriride-rider-live_pilot_002-release.apk.sha256`

## SHA256 checksums

- Driver APK: `51378823ea2d0592b805f4c681e49bbd7690e8737e44dbdf9d68348ad4049a29`
- Rider APK: `90337f6d6d45cdd65824b7ad436bc477bc2e23459da34a2f7ed0cbfe36cadeb8`

## Validation results

Completed during packaging:

- Android release builds: passed for driver and rider
- Application IDs preserved
  - Driver: `com.ostrinov23.afriridedrivertest`
  - Rider: `com.ostrinov23.afririderapp`

Pending at the time of this release-note draft:

- `npm --prefix driver_app run typecheck`
- `npm --prefix rider_app run typecheck`
- `python -m compileall afritech afriride_system`
- `pytest -q`
- `python -m afritech.ci.four_gate_validator`
- `python -m afritech.guards.guard_runtime_boundary_governance --fail-on-drift`
- `python -m afritech.ci.secret_scan`
- `python -m afritech.ci.docs_link_validator`
- `git diff --check`

This release note must be updated only after the full validation set is re-run and confirmed.

## Known operational dependencies

This pilot package still depends on operational readiness items that are outside source control:

- production-equivalent secrets and signing material
- notification credentials where live notifications are enabled
- map provider credentials where live maps are enabled
- pilot or production payment provider onboarding where applicable
- TLS certificates and DNS configuration
- monitoring, alerting, and incident response provisioning

These are operational requirements, not missing features.

## Pilot acceptance checklist

- [ ] APKs built and packaged
- [ ] APK checksums generated
- [ ] VersionCode and VersionName bumped to Pilot 002 values
- [ ] Application IDs preserved
- [ ] Driver and rider release artifacts copied into `apk/`
- [ ] Pilot 001 release APKs removed from `apk/`
- [ ] Full validation commands completed successfully
- [ ] Operational dependencies reviewed and documented
- [ ] Release treated as controlled pilot only

## Scope statement

This package supports a controlled pilot release of AfriRide / NovaRide for internal or bounded-field use.

It is not a public production launch artifact and must not be represented as such unless the full validation set, operational readiness requirements, and release approvals are all complete.
