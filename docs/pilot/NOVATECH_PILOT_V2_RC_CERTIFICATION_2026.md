# NovaTech Pilot V2 RC Certification 2026

Status: RELEASE CANDIDATE CERTIFICATION FRAMEWORK

Purpose: define the production-readiness review gates for the controlled real-device pilot after functional flows, LAN APK distribution, and basic end-to-end integration have been proven.

## RC Scope

This RC applies to:

- NovaID
- NovaRide
- NovaPay Consumer
- NovaPay Agent

It does not change product boundaries:

- NovaID authenticates and verifies identity.
- NovaRide handles mobility only.
- NovaPay executes financial services.
- NovaTrust records evidence and audit trails.
- NovaAI remains advisory only.

## RC Stages

### 1. Device Qualification

Goal: confirm target Android hardware is supported.

Exit criteria:

- target Android versions are installed and validated
- camera, GPS, biometrics, storage, and networking are usable on real devices
- APK install and launch succeed on each target class

### 2. Identity Certification

Goal: verify NovaID on real devices.

Exit criteria:

- passport OCR accuracy meets target
- selfie verification succeeds
- device binding persists across relaunch
- biometric login succeeds
- identity evidence is generated and verified

### 3. Mobility Certification

Goal: verify NovaRide end-to-end trip execution.

Exit criteria:

- rider request reaches driver queue
- driver accepts in time
- trip lifecycle transitions complete in order
- receipt and replay evidence are generated

### 4. Financial Certification

Goal: verify NovaPay wallet and agent operations.

Exit criteria:

- wallet creation succeeds
- transfers complete in pilot mode
- cash-in and cash-out succeed for agent flows
- ledger balances reconcile exactly
- duplicate transfer prevention is validated

### 5. Security Certification

Goal: verify authentication, token handling, and device controls.

Exit criteria:

- tokens expire correctly
- refresh tokens rotate
- expired sessions are rejected
- sensitive documents are encrypted on device
- debug builds cannot access production APIs

### 6. Performance Certification

Goal: verify the pilot remains responsive on real devices.

Exit criteria:

- startup time is within target
- memory usage remains stable
- battery impact is acceptable
- network retry behavior is stable

### 7. Recovery Certification

Goal: verify failures recover cleanly.

Exit criteria:

- offline recovery succeeds
- synchronization resumes correctly
- app restart does not corrupt state
- trip and payment retries do not duplicate actions

### 8. Production Readiness

Goal: formal review before RC freeze.

Exit criteria:

- no unresolved critical defects remain
- evidence package is complete
- rollback path is documented
- formal sign-off is recorded

## Quantitative Acceptance Gates

### NovaID

- Passport OCR accuracy >= 99%
- Selfie verification success >= 98%
- QR verification < 2 seconds
- Biometric login < 1 second
- Zero identity corruption

### NovaRide

- Rider request reaches driver queue < 2 seconds
- Driver acceptance < 3 seconds
- GPS refresh every 1-2 seconds
- Receipt generation < 5 seconds
- Replay evidence available for every completed trip

### NovaPay

- Wallet creation < 3 seconds
- Transfer completion < 5 seconds in pilot mode
- Ledger reconciliation = 100%
- Duplicate transfer prevention verified
- Receipt hash matches transaction
- No negative balances unless explicitly allowed

## Failure Injection

Exercise the following during pilot sessions:

- disable Wi-Fi during booking
- disable mobile data during payment
- switch between Wi-Fi and 4G/5G mid-transaction
- enable airplane mode
- simulate poor signal
- kill the app during identity verification
- kill the app during ride booking
- kill the app during payment
- reboot the phone during a trip
- rotate the screen repeatedly
- fill storage nearly full
- enable battery saver

Expected result:

- graceful recovery or controlled retry
- no data corruption
- no duplicated trip or payment actions

## Security Validation

Verify:

- tokens expire correctly
- refresh tokens rotate
- expired sessions are rejected
- screenshot protection works where intended
- sensitive documents are encrypted on device
- TLS certificates are validated
- rooted devices are handled according to policy
- debug builds cannot access production APIs

## Production Evidence Package

Capture:

- device model
- Android version
- APK version
- Git commit hash
- API version
- build number
- logs
- screenshots
- screen recordings
- transaction receipts
- replay evidence
- audit records
- performance metrics
- crash reports

## Final Production Gate

The pilot is complete only when all are true:

- all NovaID identity workflows pass
- NovaRide completes multiple successful end-to-end trips
- NovaPay Consumer and Agent complete all planned financial workflows in pilot mode
- no unresolved critical defects remain
- ledger reconciliation is correct
- replay and audit evidence exist for every transaction and ride
- performance targets are met
- security validation passes
- recovery testing passes
- a formal pilot report is signed off

At that point the next milestone is Release Candidate certification for controlled deployment review.

