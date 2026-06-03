# AfriRide Mobile Apps

STATUS: PHONE TEST IMPLEMENTATION SURFACE

These Expo apps are interface layers over the AfriRide FastAPI service.

They do not define AfriTech correctness and are not part of `afritech.demo.proof`.

The driver app is currently a simple signed phone-event tester for Android
rehearsals. It can emit signed AfriRide events to `/v1/events`.

It does not certify pilot completion or production readiness.

## API Base URL

Set `EXPO_PUBLIC_AFRIRIDE_API_URL` for device testing.

Default:

```text
http://127.0.0.1:8000
```

For Android emulator, use:

```text
http://10.0.2.2:8000
```

For a real Android phone, use your Mac LAN IP:

```text
http://<mac-lan-ip>:8000
```

Do not use `localhost` from a physical phone.

## Android Phone Test

From `afriride_system/mobile/driver_app`:

```text
npm install
npm start
```

Open the project in Expo Go on your Android phone.

In the app, set:

```text
API base URL: http://<mac-lan-ip>:8000
Device ID: ostrinov_phone_001
Ride ID: day_one_002_phone_trip_001
Pilot secret: pilot-secret
```

Tap:

```text
Send Sequence
```

The phone must show `/v1/events` results with accepted or rejected event IDs.

If signed events are accepted by the API, the run can be documented as:

```text
candidate live pilot evidence
```

until post-pilot analysis decides otherwise.

## Apps

```text
passenger_app/
driver_app/
```

Both apps use polling first. WebSockets are intentionally excluded from Phase 1.
