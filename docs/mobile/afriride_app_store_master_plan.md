# AfriRide App Store Deployment Master Plan

Status: APP-STORE CANDIDATE PREPARATION, PILOT GATED

## Product Positioning

AfriRide is a sovereign, replay-governed mobility platform entering controlled pilot release.

Do not claim:

- production-proven operation
- guaranteed real-world performance
- immutable real-world truth

Allowed positioning:

- replay-governed pilot system
- controlled mobility pilot
- experimental distributed infrastructure under evaluation

## App Surfaces

- AfriRide Rider: public app candidate
- AfriRide Driver: public app candidate
- Operator dashboard: internal observer-only control surface

## Actual Repo Implementation

The repository currently contains Flutter apps:

- `afriride_system/flutter/rider_app`
- `afriride_system/flutter/driver_app`

The abstract mobile architecture remains:

```text
apps/rider
apps/driver
shared/services/api
shared/services/proof
shared/services/auth
screens
components
```

## Store Compliance

Required legal URLs:

- Privacy Policy
- Terms of Service
- Support Page
- Account deletion request page

Official references:

- Apple App Privacy requires a publicly accessible privacy policy URL and supports pages where users can request data deletion or changes: https://developer.apple.com/app-store/app-privacy-details/
- Google Play requires Data safety disclosures, a privacy policy, and account deletion paths for apps that allow account creation: https://support.google.com/googleplay/android-developer/answer/10787469 and https://support.google.com/googleplay/android-developer/answer/13327111

## Permission Copy

Location:

```text
AfriRide uses location data to match riders and drivers in real time.
```

Camera, if enabled:

```text
Camera may be used for identity verification and trip evidence.
```

Notifications:

```text
Notifications are used for ride updates and safety alerts.
```

## Required App Features

- account creation and login
- in-app account deletion request
- data removal confirmation
- support contact
- safety flow
- privacy and terms access
- proof receipt display
- replay status display
- trip evidence display

Proof feature disclaimer:

```text
This feature provides verifiable execution information during pilot phase and may evolve over time.
```

## Backend + Protocol API

Required:

```text
POST /auth/register
POST /auth/login
DELETE /account
POST /rides/request
POST /rides/accept
POST /rides/start
POST /rides/complete
GET /rides/:id
GET /proof/:ride_id
GET /replay/:ride_id/status
POST /support/ticket
GET /ledger/:ride_id
GET /state/ride/:id
GET /trust/node/:id
```

## Build Validation

Flutter:

```bash
cd afriride_system/flutter/driver_app
flutter analyze
flutter test
flutter build apk --release

cd ../rider_app
flutter analyze
flutter test
flutter build apk --release
```

AfriTech gates:

```bash
python3 -m afritech.ci.app_surface_validator
python3 -m afritech.ci.mobile_pilot_e2e_validator
python3 -m afritech.ci.afriride_live_pilot_protocol_validator
python3 -m afritech.ci.afriride_day_one_runbook_validator
python3 -m afritech.ci.afriride_post_pilot_analysis_validator
python3 -m afritech.ci.afriride_app_store_deployment_validator
pytest -q
```

## Google Play

- App name: AfriRide
- Package: `com.afritech.afriride`
- Release order: internal testing -> closed testing -> production
- Required: AAB, screenshots, feature graphic, privacy policy URL, Data safety form

## Apple App Store

- Bundle ID: `com.afritech.afriride`
- Release order: TestFlight -> external testers -> review -> release
- Required: screenshots, privacy labels, support URL, privacy policy URL

## Proof System Disclosure

Use this language:

```text
AfriRide uses a replay-governed execution model to provide verifiable coordination signals during pilot phases. This system is under controlled evaluation and may evolve.
```

## Final Rule

App-store preparation may proceed. Live public production claims may not.
