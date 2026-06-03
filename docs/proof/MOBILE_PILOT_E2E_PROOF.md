# Mobile Pilot End-to-End Proof

## Document Classification

```text
STATUS: PRODUCTION PROOF GATE 7
CLASSIFICATION: MOBILE PILOT E2E EVIDENCE SURFACE
ROLE: PROVE MOBILE SUBMISSION CAN COMPLETE A REPLAY-VALID TRIP WITHOUT GRANTING CLIENT AUTHORITY
BOUNDARY: MOBILE CLIENTS MAY SUBMIT EVENTS; MOBILE CLIENTS MAY NOT DEFINE TRUTH
```

This report documents Production Proof Gate 7.

The mobile pilot proof validates that rider and driver client entropy enters
through controlled envelopes, server-side normalization, deterministic
execution, persistent evidence, and replay validation.

## Required Flow

```text
rider request
→ mobile envelope
→ adapter
→ normalization
→ ingestion
→ persistent event store
→ driver candidate selection
→ trip accepted
→ trip tracked
→ ETA shared
→ replay hash verified
→ same trip replayed deterministically
```

## Required Rejection Cases

```text
client timestamp authority
client-computed fare authority
client-computed driver match authority
client replay hash authority
duplicate mobile request
spoofed rider/driver event
out-of-order mobile update
tampered trip status
```

## Enforcement Surface

```text
ecosystems/afriride/simulation/mobile_pilot_proof.py
afriride_system/tests/e2e/test_mobile_pilot_e2e.py
afritech/ci/mobile_pilot_e2e_validator.py
docs/proof/MOBILE_PILOT_E2E_PROOF.md
```

Mobile clients may observe, request, and submit events.

Mobile clients may not define identity, fare, match result, replay hash, trip
legitimacy, final truth, or server-side deterministic execution artifacts.

## Current Gate

```bash
python3 -m afritech.ci.mobile_pilot_e2e_validator
```

Passing this gate means AfriRide mobile pilot can complete a rider/driver trip
flow end-to-end, persist event evidence, replay the trip deterministically, and
verify the same trip hash without rider or driver clients becoming truth
authorities.
