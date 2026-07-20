# NovaRide MVP scope

## Outcome

The MVP proves that a verified rider can request a trip, a verified and approved driver can accept and complete it, payment can be recorded safely, and operations can monitor and support the full journey.

## P0 capabilities

1. **Rider identity:** phone/email registration, OTP, login/logout, profile, emergency contact, consent and NovaID session integration.
2. **Driver onboarding:** identity, licence, vehicle/documents, approval/rejection and online/offline state.
3. **Location/maps:** current location, pickup/destination, route preview, driver updates, trip map, ETA and navigation handoff.
4. **Deterministic quote:** base, distance, time, booking fee, vehicle class, total and expiry.
5. **Ride request:** pickup, destination, ride type, payment method, submit/cancel and status.
6. **Dispatch:** eligible nearby-driver ranking, offer, accept/decline, timeout, reassignment and double-assignment prevention.
7. **Trip lifecycle:** `REQUESTED`, `SEARCHING`, `DRIVER_ASSIGNED`, `ACCEPTED`, `DRIVER_ARRIVING`, `ARRIVED`, `IN_PROGRESS`, `COMPLETED`; terminal alternatives `CANCELLED`, `EXPIRED`, `FAILED`.
8. **Driver execution:** offer, pickup, navigation, arrived/start/complete and earnings record.
9. **Rider live experience:** verified driver/vehicle details, ETA, call/chat entry, status and completion summary.
10. **Payments:** cash, sandbox card or approved NovaPay pilot; idempotent status, receipt and trip linkage. Unrestricted real payments remain disabled until both release gates pass.
11. **Notifications:** acceptance, assignment, approach/arrival, start/completion, payment, cancellation and support updates.
12. **Safety:** verified driver/vehicle, SOS, sharing, emergency contact, incident, operations alert and audit trail.
13. **Ratings:** bilateral rating, optional comment and issue flag.
14. **History/receipts:** completed/cancelled trips, detail, fare, payment and receipt.
15. **Operations:** live rides/drivers, search, timeline, policy-controlled cancel/reassign, incidents, support and payment status.
16. **Administration:** driver approval, people/vehicle management, region/pricing configuration, suspension, audit and roles.
17. **Support:** trip-linked issues, status, lost property and payment/fare cases.
18. **Security/audit:** RBAC, tenant isolation, privileged MFA, secure tokens, validation, rate limits, TLS, audit and redaction.
19. **Monitoring:** health, dispatch/payment errors, crashes, active trips, queue backlog and notification failures.

## Required MVP surfaces

- NovaRide Rider Android application
- NovaRide Driver Android application
- Operations web console
- Platform administration portal
- Shared backend APIs

Rider/driver iOS, support console and basic fleet portal follow immediately after MVP stabilisation.

## Release-boundary journey

```text
Rider registers
  -> Driver registers and is approved
  -> Driver goes online
  -> Rider requests a trip
  -> Dispatch assigns exactly one eligible driver
  -> Driver accepts
  -> Rider tracks arrival
  -> Driver starts and completes the trip
  -> Payment is recorded idempotently
  -> Receipt is generated
  -> Rider and driver can rate
  -> Operations can inspect the complete evidence trail
```

Failure, cancellation, timeout, offline recovery, incident and support paths are part of the boundary rather than optional polish.
