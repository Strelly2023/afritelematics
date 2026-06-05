# AfriRide Real-World Activation Playbook

Status: PROCEDURAL PLAYBOOK, NOT LIVE AUTHORIZATION

## Step 1: Final Pre-Submission Check

```bash
python3 -m afritech.ci.afriride_app_store_deployment_validator
python3 -m pytest afritech/tests/distributed/test_afriride_app_store_deployment.py
python3 -m pytest afritech/tests/distributed/test_docs_and_tools_suite.py
python3 -m pytest afritech/tests/distributed/test_activation_scale_and_services.py
```

## Step 2: Build Release Candidates

Android Driver:

```bash
cd afriride_system/flutter/driver_app
flutter clean
flutter pub get
flutter analyze
flutter test
flutter build appbundle --release \
  --dart-define=AFRIRIDE_API_BASE_URL=https://afriride-api.onrender.com \
  --dart-define=AFRIRIDE_DEVICE_ROLE=driver \
  --dart-define=AFRIRIDE_PILOT_RUN_ID=live_pilot_001
```

Android Rider:

```bash
cd afriride_system/flutter/rider_app
flutter clean
flutter pub get
flutter analyze
flutter test
flutter build appbundle --release \
  --dart-define=AFRIRIDE_API_BASE_URL=https://afriride-api.onrender.com \
  --dart-define=AFRIRIDE_DEVICE_ROLE=rider \
  --dart-define=AFRIRIDE_PILOT_RUN_ID=live_pilot_001
```

iOS:

```text
Archive via Xcode after signing, privacy labels, support URL, and privacy policy URL are ready.
```

## Step 3: Testing Tiers

Do not skip stages:

1. Internal team testing
2. Closed testing
3. TestFlight external testing
4. Controlled pilot field execution

## Step 4: Pilot Activation Gates

Keep:

```text
go_authorized = false
```

Only authorize when:

- backend stable
- nodes connected
- observability live
- support channel active
- rollback strategy ready
- emergency contact ready
- evidence export ready

## Step 5: Controlled Pilot Launch

Initial pilot:

- 3-5 nodes
- small geographic area
- limited drivers
- limited riders
- operator observer present

## Step 6: Monitor

Watch:

- consensus stability
- proof integrity
- replay status
- network latency
- node trust changes
- ride lifecycle completion
- incident log

## Step 7: Scale

Scale only after evidence review:

```text
5 nodes -> 10 nodes -> 20 nodes
small route -> district -> larger region
```

## Stop Conditions

Immediately stop pilot if:

- backend health fails
- signed event path fails
- replay export fails
- wrong ride id is used
- evidence cannot be reconstructed
- safety incident requires escalation
