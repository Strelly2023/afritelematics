# AfriRide Android Pilot Tester

STATUS: PHONE EVENT TEST CLIENT
CLASSIFICATION: DEVICE-BACKED REHEARSAL TOOL

This Flutter app lets an Android phone emit signed AfriRide mobile events to:

```text
POST /v1/events
```

It does not define replay truth, certify pilot completion, or make the run live
pilot evidence by itself.

## Use

Start the AfriTech pilot API on your Mac, then find your Mac LAN IP address.
The phone must use:

```text
http://<mac-lan-ip>:8000
```

not:

```text
http://localhost:8000
```

Open the app and set:

```text
API base URL: http://<mac-lan-ip>:8000
Device ID: ostrinov_phone_001
Ride ID: day_one_002_phone_trip_001
Pilot secret: pilot-secret
```

Then tap:

```text
Accept
Start
Location
Complete
```

or:

```text
Send Sequence
```

The app shows the `/v1/events` response:

```text
accepted=[...]
rejected=[...]
```

## Evidence Classification

If the phone sends accepted signed events, the run may be classified as:

```text
candidate live pilot evidence
```

only after the event receipts, trace hashes, post-pilot analysis, and
stakeholder report validators agree.

If the phone is merely listed in receipts but does not emit signed events, the
run remains:

```text
device-backed rehearsal
```

## Build

From this folder:

```text
flutter pub get
flutter run
```

For a physical Android phone, enable USB debugging or use Android Studio device
pairing.

## Boundary

Do not claim:

```text
pilot completed
production ready
public launch ready
regulatory approved
market validated
```
