# AfriRide Real Device Installation Path

Status: CONTROLLED FIELD PILOT INSTALLATION, LIVE PILOT NOT AUTHORIZED

This runbook explains how to install AfriRide on real devices for controlled pilot testing without public store release.

Current boundary:

```text
controlled_pilot_prepared = true
live_pilot_authorized = false
production = false
```

## Official Distribution References

- Android Debug Bridge can install APKs on connected Android devices using the `install` command: https://developer.android.com/tools/adb
- Google Play Console supports internal, closed, and open testing tracks: https://support.google.com/googleplay/android-developer/answer/9845334
- Apple TestFlight supports beta testing through App Store Connect before App Store release: https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/

## Repo Reality

The current AfriRide mobile surfaces are Flutter apps:

```text
afriride_system/flutter/driver_app
afriride_system/flutter/rider_app
```

Both currently include Android project files. No iOS Flutter target is present in these app folders at the time of this runbook, so iPhone installation requires adding iOS targets and Apple signing before TestFlight.

## Phase 1: Android Real Phone Install

Build Driver APK:

```bash
cd afriride_system/flutter/driver_app
flutter clean
flutter pub get
flutter analyze
flutter test
flutter build apk --release \
  --dart-define=AFRIRIDE_API_BASE_URL=https://afriride-api.onrender.com \
  --dart-define=AFRIRIDE_DEVICE_ROLE=driver \
  --dart-define=AFRIRIDE_PILOT_RUN_ID=live_pilot_001
```

Build Rider APK:

```bash
cd afriride_system/flutter/rider_app
flutter clean
flutter pub get
flutter analyze
flutter test
flutter build apk --release \
  --dart-define=AFRIRIDE_API_BASE_URL=https://afriride-api.onrender.com \
  --dart-define=AFRIRIDE_DEVICE_ROLE=rider \
  --dart-define=AFRIRIDE_PILOT_RUN_ID=live_pilot_001
```

Install by USB:

```bash
adb devices
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

Manual install is allowed only for known pilot devices:

1. Transfer APK to phone
2. Enable install from trusted file source
3. Install APK
4. Register device in `traces/pilot_runs/live_pilot_001/devices`

## Phase 2: iPhone TestFlight Path

Required before iPhone testing:

- Flutter iOS target exists
- Apple Developer Program account
- Bundle ID configured
- App Store Connect app entry
- Privacy Policy URL
- Support URL
- TestFlight build upload

TestFlight installation:

1. Archive in Xcode
2. Upload build to App Store Connect
3. Add tester email
4. Install via TestFlight

Until iOS targets exist in this repository, iPhone testing is `prepared_not_available`.

## Phase 3: Backend Gate

Real phone testing requires a reachable backend:

```text
GET https://afriride-api.onrender.com/health = 200 OK
POST /v1/events = 200/201
OPTIONS /rides/active = 200
```

If Render returns `503`, hold field execution.

## Phase 4: Device Registration

Required devices:

```text
driver_phone_001
rider_phone_001
operator_laptop_001
```

Each device must be registered before field testing:

```json
{
  "device_id": "driver_phone_001",
  "role": "driver",
  "pilot_run_id": "live_pilot_001",
  "signed_event_capable": true,
  "gps_capture_capable": true,
  "status": "registered"
}
```

## Phase 4.5: First Mobile Pilot Execution (Device + Token Lifecycle)

The first phone-backed pilot run must verify both device identity and token
discipline before any live ride action is accepted.

Required lifecycle:

1. Register the phone as a known pilot device.
2. Bind the phone to exactly one pilot role.
3. Issue a short-lived access token plus a refresh token.
4. Confirm the app submits events with `device_id`, `actor_id`, and `token_jti`.
5. Force one token refresh during the rehearsal window.
6. Confirm expired token rejection does not create trace mutations.
7. Revoke credentials if the phone is replaced, reset, or reassigned.

Minimum token rules:

```text
access token is short-lived
refresh token rotation is single-use
token_jti is audit-visible
expired token cannot mutate state
revoked device cannot resume with stale credentials
```

Required device and token evidence:

```text
device_registration_snapshot.json
token_issuance_audit.json
token_refresh_rotation_trace.json
expired_token_rejection_receipt.json
revoked_device_block_trace.json
```

Stop immediately if:

- device role does not match token role
- `token_jti` is missing from the authenticated session record
- expired token request writes any trace event
- refresh token can be reused
- revoked or reinstalled device is accepted without re-enrollment

## Phase 5: Controlled Ride Test

Do not use public riders.

Use:

- known driver
- known rider
- operator observer
- controlled route
- emergency contact

Flow:

```text
rider_request
driver_accept
driver_arrived
trip_start
trip_complete
receipt
replay_result
evidence_bundle
```

## Required Evidence

```text
signed_event_log.jsonl
ride_lifecycle_trace.json
receipt.json
replay_result.json
operator_observation_log.json
incident_log.json
evidence_bundle.json
```

## Stop Conditions

Stop immediately if:

- backend health fails
- event endpoint fails
- GPS permission fails
- wrong ride id is used
- proof receipt missing
- replay cannot verify
- operator cannot observe
- safety issue occurs

## Final Rule

Real device installation is allowed for controlled pilot testing. Public production release is not authorized by this runbook.
