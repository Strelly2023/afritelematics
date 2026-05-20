# AfriRide Mobile Apps

STATUS: FUTURE IMPLEMENTATION SURFACE

These Expo apps are interface layers over the AfriRide FastAPI service.

They do not define AfriTech correctness and are not part of `afritech.demo.proof`.

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

## Apps

```text
passenger_app/
driver_app/
```

Both apps use polling first. WebSockets are intentionally excluded from Phase 1.
