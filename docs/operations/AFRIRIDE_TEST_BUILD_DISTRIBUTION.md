# AfriRide GA Elite Test Build Distribution

Artifact Type: Execution-Enabling Deployment Runbook

Purpose: Build and distribute installable AfriRide Rider and Driver test apps for controlled field execution.

Classification:

```text
execution_enabling
legitimacy_effect: 0
wave7_effect: 0
```

## Required Backend

The backend must be publicly reachable over HTTPS before field distribution.

```text
EXPO_PUBLIC_AFRIRIDE_API_URL=https://your-backend-url
EXPO_PUBLIC_AFRIRIDE_TEST_MODE=true
```

Do not use localhost for field devices.

## Rider Test App

App:

```text
AfriRide Rider (Test)
```

Build:

```bash
cd rider_app
eas build -p android --profile test
eas build -p ios --profile test
```

Required behavior:

```text
request ride
view ride status
view receipt
view replay status
emit client_event envelope on every live request
fail if TEST_MODE is disabled
```

## Driver Test App

App:

```text
AfriRide Driver (Test)
```

Build:

```bash
cd driver_app
eas build -p android --profile test
eas build -p ios --profile test
```

Required behavior:

```text
view queue
accept or reject
start trip
complete trip
view earnings
emit client_event envelope on every live request
fail if TEST_MODE is disabled
```

## Operator Dashboard

Deploy the read-only dashboard to a tablet-accessible HTTPS URL.

Required environment:

```text
VITE_AFRIRIDE_API_URL=https://your-backend-url
VITE_AFRIRIDE_TEST_MODE=true
```

Required panels:

```text
active rides
replay health
evidence pipeline
guard violations
trace integrity
```

## Distribution

Android:

```text
send APK to testers
install via Android internal testing or direct APK install
```

iOS:

```text
use TestFlight or internal/ad hoc distribution
```

Field team package:

```text
driver app link
rider app link
operator dashboard URL
driver IDs
rider IDs
observer checklist
backend URL
```

Optional portable download page:

```text
docs/operations/afriride-test-apps-download.html
```

Replace the placeholder APK, TestFlight, and dashboard URLs after EAS builds complete, then host the file on GitHub Pages, Vercel, Netlify, or any static HTTPS server.

## Hard Rules

```text
test mode must remain enabled
no production store release
no non-test backend
no uninstrumented field run
no success claim from installability
```

Installable apps are execution-enabling only. They do not produce operational legitimacy until field execution is captured, replayed, and validated.
