# AfriRide Mobile Apps

STATUS: MOBILE EXECUTION SURFACES

These Expo apps are interface layers over the AfriRide FastAPI service.

They do not define AfriTech correctness and are not part of `afritech.demo.proof`.

The rider, driver, and operator apps now execute against the authoritative
AfriRide API. They remain non-authoritative clients over replay, evidence,
receipt, and operational read surfaces.

The earlier signed phone-event tester concept is retained only as a historical
claim boundary, not as the current driver-app implementation.

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
Driver ID: driver-1
Ride ID: live-smoke-ride-001
```

Use the real lifecycle controls:

```text
Go online
Accept ride
Driver arrived
Start ride
Complete ride
```

If mobile execution succeeds against the live API, the run can still only be documented as:

```text
candidate live pilot evidence
```

until post-pilot analysis decides otherwise.

## Apps

```text
passenger_app/
driver_app/
operator_app/
```

Both apps use polling first. WebSockets are intentionally excluded from Phase 1.
