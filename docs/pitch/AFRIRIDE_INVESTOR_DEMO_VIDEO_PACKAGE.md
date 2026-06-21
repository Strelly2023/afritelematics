# AfriRide Investor Demo Video Package

Status: INVESTOR-READY DEMO VIDEO PACKAGE
Classification: ISOLATED INVESTOR COMMUNICATION SURFACE

Purpose: turn the current rider and driver app flows into a short investor demo
video that shows AfriRide as an observable, replayable, trust-verifiable
mobility system.

This package is a communication surface. It does not claim completed Melbourne
pilot execution, production scale, regulatory approval, or guaranteed market
capture.

## Core Demo Thesis

AfriRide is not only a ride app.

AfriRide is a governed mobility transaction system where each ride can emit:

- a receipt
- a replay trace
- evidence state
- a trust score
- a public verification path

Investor line:

```text
Traditional ride platforms say a trip happened.
AfriRide can show the governed proof that it happened.
```

## Target Runtime

```text
total_length: 2:30 to 3:30
audience: investors, mobility partners, enterprise operators
format: screen recording with voiceover
claim_boundary: demo of available system behavior, not proof of completed pilot scale
```

## Shot List

1. Title frame: AfriRide - trust-verifiable mobility.
2. Rider login: show API Base URL, rider identity, session role.
3. Rider request: enter pickup and destination, submit ride request.
4. Driver availability: show driver online and queue refresh.
5. Driver lifecycle: accept, arrive, start, complete.
6. Rider tracking: show synchronized ride status and assigned driver.
7. Receipt view: show `receipt_id`, `trust_score`, `replay_hash`, and governed output.
8. Replay visualization: show lifecycle timeline from REQUESTED to COMPLETED.
9. Evidence viewer: show completed ride evidence and payment observation.
10. Public verification: show the path for `GET /public/trust/{receipt_id}` or equivalent verification surface.
11. Closing frame: every ride can become a verifiable trust artifact.

## Voiceover Script

```text
AfriRide starts like a familiar mobility app.

A rider requests a trip. A driver accepts it. The ride moves through a normal
operational lifecycle.

The difference is what happens underneath.

Every important transition is recorded as governed execution. The rider and
driver see the same state. The system emits a receipt, a replay hash, evidence,
and a trust score.

That means a completed ride is not just a database row. It is a verifiable
trust artifact.

For riders, this creates transparency. For drivers, it creates non-fakeable
reputation. For operators, it creates auditability. For partners and regulators,
it creates an external verification surface.

AfriRide is mobility with proof: observable, replayable, and trust-verifiable.
```

## On-Screen Captions

- Request ride
- Driver accepts
- Trip state synchronized
- Receipt emitted
- Replay proves lifecycle
- Evidence binds reality
- Public verification ready
- Mobility with proof

## Demo Data Contract

Use one clean fixture across the whole video:

```json
{
  "rider_id": "rider-1",
  "driver_id": "driver-1",
  "ride_id": "ride-5bdca5bf",
  "receipt_id": "5bdca5bf",
  "trust_score": 92,
  "pickup": "Melbourne CBD",
  "destination": "Melbourne Airport"
}
```

## Required Product Upgrades Before Recording

- Trust badge: `Verified Ride (Trust Score: 92)`
- Public verification button: `Verify this ride`
- Replay timeline UI: `REQUESTED -> DRIVER_ACCEPTED -> ARRIVED -> STARTED -> COMPLETED`
- Driver trust score: `Driver Trust Score: 94`
- Audit package button: `Download Verification Package`

## Recording Checklist

- Use seeded demo data only.
- Keep API base URL visible only if it is the intended demo environment.
- Hide secrets, tokens, local admin panels, and internal database views.
- Show both rider and driver views in one continuous narrative.
- Do not say the Melbourne pilot has passed unless the Melbourne control contract has passed.
- End with the bounded product truth: AfriRide demonstrates trust-verifiable mobility behavior.
