# NovaTech Real Device Pilot Sequence 2026

Status: CONTROLLED PILOT SEQUENCE

Purpose: define the recommended real-device pilot order for NovaID, NovaRide, NovaPay Consumer, and NovaPay Agent after APK distribution is confirmed on the LAN.

## Pilot Boundaries

- Use only pilot devices you control.
- Use only pilot data stored outside Git.
- Use simulated or pilot payment modes until live operations are explicitly authorized.
- Keep NovaID as the identity layer, NovaRide as mobility only, NovaPay as financial execution, NovaTrust as evidence, and NovaAI advisory only.

## Preflight

1. Confirm the APK server root is `~/afritelematics/apk`.
2. Confirm every APK returns `HTTP 200 OK` from the LAN URL.
3. Confirm the pilot device set is registered.
4. Confirm screen recording and logs are enabled.
5. Confirm each app opens on a real Android device.

## Recommended Sequence

### Phase 1: NovaID

Validate identity first so the same trusted profile can be reused across the rest of the pilot.

Run:

- account registration
- passport upload
- driver licence upload
- selfie and liveness
- device binding
- biometric login
- consent management
- digital ID display

Pass criteria:

- OCR succeeds on the passport and licence
- face match succeeds
- trust profile is generated
- biometric login succeeds after restart
- device binding survives relaunch

### Phase 2: NovaRide

Validate ride operations only after identity is stable.

Run:

- rider requests ride
- driver comes online
- driver sees request in queue
- driver accepts ride
- driver arrives
- trip starts
- trip completes
- rider receives receipt
- replay evidence is available

Pass criteria:

- rider request reaches the driver queue
- driver can accept without refresh loops
- ride transitions follow the expected lifecycle
- receipt and replay are generated
- driver and rider evidence align

### Phase 3: NovaPay Consumer

Validate wallet and transfer execution after identity and ride surfaces are stable.

Run:

- wallet activation
- NovaID linkage
- add recipient
- transfer in pilot mode
- QR payment
- receipt download
- history review

Pass criteria:

- wallet state updates correctly
- transfer receipt is produced
- transaction history reflects the action
- no production payment credentials are needed

### Phase 4: NovaPay Agent

Validate cash-in/cash-out and support operations last.

Run:

- agent login
- customer verification
- cash in
- cash out
- float review
- reconciliation
- commission review

Pass criteria:

- customer verification works with NovaID
- wallet and float balances update correctly
- reconciliation matches recorded transactions
- commission reporting is consistent

## Device Matrix

- Primary Android phone: NovaID and NovaPay Consumer
- Secondary Android phone: NovaRide rider or driver
- Optional tablet: operator or agent dashboard

## Network Matrix

- Wi-Fi
- 4G or 5G
- weak signal
- offline retry
- Wi-Fi to mobile handoff

## Evidence To Capture

- APK download link used
- device model and OS version
- screenshots
- screen recordings
- request and response logs
- receipts
- replay evidence
- crash logs
- operator notes

## Stop Conditions

Stop the pilot immediately if any occur:

- a device cannot install the correct APK
- NovaID fails to bind the device
- NovaRide requests do not appear in the driver queue
- NovaPay cannot create a wallet or complete a pilot transfer
- receipts are missing
- replay evidence fails
- crash or data loss occurs

## Exit Criteria

The pilot is complete only when:

- NovaID passes real-device identity verification
- NovaRide completes at least one full controlled ride
- NovaPay Consumer completes at least one controlled wallet transfer
- NovaPay Agent completes at least one controlled cash-in/cash-out cycle
- no critical crashes or proof mismatches occur
- all evidence is exported and reviewed

