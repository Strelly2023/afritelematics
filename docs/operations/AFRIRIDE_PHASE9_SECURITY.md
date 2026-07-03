# Phase 9 — Mobile and API Security

## Controls

- Android Play Integrity and Apple App Attest use a server-issued, device-bound,
  single-use nonce. Production verification is delegated to configured verifier
  services and fails closed when a verifier is absent.
- Mobile bearer tokens are stored with `expo-secure-store`, restricted to the
  current device and unlocked keychain. Restored production sessions require
  biometric authentication.
- Android Network Security Configuration and iOS ATS pin the production API
  certificate chain. Cleartext traffic and Android application backups are disabled.
- Every mobile mutation carries a timestamp and unique nonce. Production rejects
  missing, stale, and replayed nonces.
- Per-identity request windows protect anonymous and authenticated API traffic and
  return `429` with `Retry-After`.
- Attested sessions have opaque identifiers and explicit revocation state.

HTTP mutations remain authoritative, idempotency remains enabled, and these controls
do not change ride, payment, realtime, or offline synchronization contracts.

## Production configuration

Set:

```text
AFRIRIDE_ENV=production
AFRIRIDE_PLAY_CLOUD_PROJECT_NUMBER=<google-cloud-project-number>
AFRIRIDE_PLAY_INTEGRITY_VERIFIER_URL=https://<internal-verifier>/play-integrity
AFRIRIDE_APP_ATTEST_VERIFIER_URL=https://<internal-verifier>/app-attest
AFRIRIDE_ENFORCE_REPLAY_PROTECTION=true
AFRIRIDE_ENFORCE_RATE_LIMITING=true
```

Both Android applications include a native Play Integrity bridge using Google's
Play Integrity 1.5.0 SDK. The iOS release bridge must register its App Attest token
provider through `registerAttestationTokenProvider`; production builds fail closed
if the native provider is absent. Test builds intentionally skip attestation when no
native provider exists.

## Certificate rotation

The checked pins were measured from `api.afritechnology.com` on 2026-07-04:

- leaf SPKI: `5YKPKI8dH/EpgQSe8awrtQJZXs9bDXL5wamTdcE9l9E=`
- Let's Encrypt YE1 intermediate SPKI:
  `brzvtCELCIZUo4sD/qPX0ccRtPsd3DY6RfmxpOU9oB4=`

Android pin expiry is 2027-07-01. Operations must validate and deploy replacement
primary and backup pins before certificate-chain or expiry changes. Pin changes
require tested native releases for both apps.

## Validation

```bash
python -m pytest afriride_system/tests/test_phase9_security.py
cd rider_app && npm run typecheck
cd ../driver_app && npm run typecheck
```
