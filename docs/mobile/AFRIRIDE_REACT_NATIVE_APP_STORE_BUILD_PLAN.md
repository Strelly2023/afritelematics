# AfriRide React Native App Store Build Plan

Status: APP STORE READY BUILD PLAN
Classification: REACT_NATIVE_MOBILE_RELEASE_SURFACE

Purpose: define the release path for `rider_app` and `driver_app` as
Expo/React Native applications for internal testing, TestFlight, Play internal
testing, and eventual store submission.

This plan is a build-readiness surface. It does not claim that the apps are
already published or approved by Apple or Google.

## Covered Apps

```text
rider_app  -> AfriRide Rider
driver_app -> AfriRide Driver
```

## Build Philosophy

- Release small, bounded pilot builds first.
- Keep production claims disabled until pilot evidence passes.
- Preserve API base URL discipline per environment.
- Keep rider and driver bundles separate.
- Require trust, replay, receipt, and evidence screens before external testing.

## Required Preflight Checks

Rider:

```bash
cd rider_app
npm run typecheck
```

Driver:

```bash
cd driver_app
npm run typecheck
```

Python surface tests:

```bash
pytest -q rider_app/tests driver_app/tests
```

Diff hygiene:

```bash
git diff --check -- rider_app driver_app
```

## Environment Matrix

```text
local_android_emulator: http://10.0.2.2:8000
local_ios_simulator: http://127.0.0.1:8000
pilot_staging: https://api.afrtechnology.com
production_candidate: disabled until pilot evidence approval
```

Required variable:

```text
EXPO_PUBLIC_AFRIRIDE_API_URL
```

No build may ship with a hardcoded local-only API URL.

## Android Build Path

Internal APK for pilot install:

```bash
cd rider_app
npx expo run:android --variant release

cd ../driver_app
npx expo run:android --variant release
```

Play internal testing AAB:

```bash
cd rider_app
npx eas build --platform android --profile preview

cd ../driver_app
npx eas build --platform android --profile preview
```

Required Android artifacts:

- package name reviewed
- release keystore controlled
- app icon present
- splash screen present
- network permission present
- location permission only if used
- privacy policy URL ready
- support URL ready
- account deletion path ready

## iOS Build Path

Simulator validation:

```bash
cd rider_app
npm run ios

cd ../driver_app
npm run ios
```

TestFlight build:

```bash
cd rider_app
npx eas build --platform ios --profile preview

cd ../driver_app
npx eas build --platform ios --profile preview
```

Required iOS artifacts:

- bundle identifier reviewed
- app icon present
- launch screen present
- location usage copy present if location is enabled
- privacy nutrition labels prepared
- support URL ready
- privacy policy URL ready
- account deletion path ready

## Store Listing Copy

Short description:

```text
AfriRide is a pilot mobility app with replay-backed ride receipts, verification
status, and trust-aware rider and driver experiences.
```

Long description:

```text
AfriRide helps riders and drivers coordinate trips while showing verification
signals from governed ride receipts, replay, and evidence. During pilot phases,
trust features are shown as bounded verification information and may evolve as
field evidence expands.
```

Forbidden copy:

```text
production-proven
guaranteed real-world reliability
regulatory approved
fully autonomous trust authority
```

## Screenshot Set

Rider screenshots:

- booking with ride options
- live ride with lifecycle rail
- verified ride trust panel
- receipt trust summary
- replay timeline
- ride history with trust scores

Driver screenshots:

- availability dashboard
- operator dashboard with Fleet Trust, Pilot Evidence, Replay Exceptions,
  Driver Trust Trends, and Public Verification Status
- driver trust profile
- ride queue with rider trust
- trip lifecycle
- earnings with verified rides and disputes
- replay history

## App Store Submission Assets

Required visual assets:

- 1024 x 1024 app icon for AfriRide Rider
- 1024 x 1024 app icon for AfriRide Driver
- iPhone 6.7 inch screenshots for Rider booking, live ride, receipt, replay,
  verification package, and ride history
- iPhone 6.7 inch screenshots for Driver operator dashboard, availability,
  ride queue, lifecycle, earnings, and replay history
- Android phone screenshots matching the same Rider and Driver surfaces
- launch screen images using the AfriRide name and plain brand color only

Required listing assets:

- privacy policy URL
- support URL
- account deletion URL
- pilot reviewer notes with test rider and driver credentials
- demo receipt ID for public verification review
- statement that verification data is bounded pilot evidence, not regulatory
  approval

Required review notes:

```text
AfriRide Rider and AfriRide Driver are pilot mobility apps connected to the
AfriRide API. Verification surfaces display backend-generated receipts, replay,
evidence, and public verification status. Mobile clients do not create or alter
trust scores.
```

Required App Privacy inputs:

- location data: used for ride coordination when enabled
- identifiers: used for rider, driver, and device sessions
- diagnostics: used for pilot evidence, latency, and crash evidence
- financial info: limited to ride fare and driver earnings summaries when shown

Required Google Data Safety inputs:

- data is encrypted in transit
- account deletion path is available before public release
- public verification redacts private rider, driver, and precise location data
- pilot diagnostics are used for app functionality, safety, and fraud prevention

## Privacy And Data Safety Inputs

Data categories:

- account identifiers
- approximate or precise location when used for ride coordination
- ride history
- support messages
- verification metadata

Data boundary:

```text
Public verification must redact private rider, driver, location precision, and
support data unless explicitly approved for public disclosure.
```

## Release Channels

### Channel 1: Internal Engineering

- local simulator/emulator
- internal APK
- developer devices only

### Channel 2: Pilot Testers

- TestFlight internal/external group
- Google Play internal testing
- invite-only rider and driver accounts

### Channel 3: Partner Demo

- frozen demo data
- no production claims
- verification endpoints read-only

### Channel 4: Store Candidate

Requires:

- legal review complete
- pilot evidence review complete
- production blockers closed
- support and deletion URLs live
- release manifests updated
- operator approval recorded

## Hard Stops

Do not submit if any condition exists:

- API base URL points to local-only host
- receipt screen unavailable
- replay screen unavailable
- verification button unavailable
- account deletion path missing
- privacy policy URL missing
- app copy claims production proof before pilot evidence
- public verification leaks private data

## App Store Readiness Claim

Allowed:

```text
AfriRide has a React Native App Store and Play Store build plan for bounded
pilot distribution.
```

Forbidden:

```text
AfriRide is already approved for public production release.
```
