# AfriRide Phase 1 native mobile operations

The canonical apps are `rider_app` and `driver_app`. Phase 1 adds Expo push
registration (FCM/APNs), interactive native maps, rider GPS, driver background
GPS, external turn-by-turn navigation, idempotent offline queues, scheduled
background synchronization, device/runtime trust signals, and low-power-aware
location sampling.

## Required release configuration

1. Create separate Firebase Android apps for both package IDs and add each
   `google-services.json` through the EAS secret-file mechanism. Configure APNs
   credentials for both iOS bundle IDs in EAS.
2. Restrict Google Maps SDK keys to the Android package/signing certificate and
   iOS bundle ID. Supply keys through release-only Expo configuration; never
   commit provider keys.
3. Build development clients or store binaries. Expo Go cannot execute remote
   push delivery or production background-location behavior.
4. Configure the API base URL and ensure TLS. The backend route
   `POST /v1/mobile/devices/push` stores token registrations; production
   deployment must back this registry with the normal durable repository and
   connect it to the notification worker.
5. Enable Background Modes (`location`, background fetch, remote notification)
   in the Apple signing profile. Android permissions are declared in both Expo
   config and the checked-in native manifests.

## Privacy and lifecycle controls

Rider GPS is foreground-only. Driver background GPS starts only after the
driver starts a shift and stops when the driver goes offline. The Android
foreground-service notification and iOS location indicator remain visible.
Low Power Mode reduces driver sampling frequency and accuracy. Failed writes
are capped locally, replayed with idempotency keys, and retained until the API
acknowledges them.

The client device check is a risk signal, not cryptographic attestation.
Production enforcement must validate Google Play Integrity and Apple App
Attest assertions server-side before marking a device trusted; emulator/device
metadata alone must never authorize rides or payments.
