# AfriRide Next-Gen Rider And Driver UI Wireframes

Status: FIGMA-LEVEL MOBILE WIREFRAME SPEC
Classification: TRUST-NATIVE MOBILE PRODUCT DESIGN SURFACE

Purpose: define the next-generation AfriRide Rider and Driver mobile interfaces
at implementation-ready fidelity while preserving the proof boundary.

The UI may explain trust, replay, receipts, and evidence. The UI must not claim
truth by itself. Truth remains owned by backend receipts, replay, evidence, and
public verification.

## Design System

### Visual Direction

- Dense, operational, premium mobility interface.
- Familiar ride-app ergonomics with visible trust status.
- Quiet background, high-contrast action areas, restrained trust color usage.
- Cards only for distinct repeated objects: ride request, trust summary, receipt, replay item.
- No decorative gradients, no marketing hero layout inside the app.

### Core Tokens

```text
background: #F6F8F7
surface: #FFFFFF
ink: #101820
muted: #63706A
trust: #168A5A
warning: #B7791F
danger: #C53030
line: #D8E0DA
radius: 8
spacing_unit: 8
```

### Shared Components

- `TrustBadge`: compact verified/review/failed trust status.
- `LifecycleRail`: horizontal or vertical state timeline.
- `ReceiptSummary`: receipt id, trust score, replay match, evidence completeness.
- `VerificationActions`: `View Receipt`, `View Replay`, `Verify this ride`, `Download Verification Package`.
- `SurfacePanel`: bounded panel for one object only.

## Rider App Wireframes

### Rider Home / Booking

```text
+------------------------------------------------+
| AfriRide                              Trust 91 |
|------------------------------------------------|
| Where to?                                      |
|                                                |
| Pickup                                         |
| [ Current location / Melbourne CBD          ]  |
|                                                |
| Destination                                    |
| [ Melbourne Airport                         ]  |
|                                                |
| Ride type                                      |
| [ Economy ] [ Premium ] [ Scheduled ] [Airport]|
|                                                |
| Ecosystem trust                                |
| Verified network: Ready                        |
| Public verification: Available                 |
|                                                |
| [ Request Ride ]                               |
+------------------------------------------------+
```

Required behavior:

- Pickup and destination fields stay visible above the fold.
- Ride type selection does not shift layout.
- Trust status is visible but not larger than the booking action.

### Rider Live Ride

```text
+------------------------------------------------+
| Ride ride-5bdca5bf                    Trust 92 |
|------------------------------------------------|
| Driver                                         |
| Djuma O                                        |
| Toyota Pilot                         ETA 3 min |
| Driver Trust Score: 94                         |
|                                                |
| REQUESTED -> ACCEPTED -> ARRIVED -> STARTED    |
|                                  -> COMPLETED  |
|                                                |
| Current status: IN TRIP                        |
|                                                |
| Verified Ride                                  |
| Replay match: pending                          |
| Evidence: collecting                           |
|                                                |
| [ View Receipt ] [ View Replay ]               |
| [ Verify this ride ]                           |
+------------------------------------------------+
```

Required behavior:

- Lifecycle rail is readable on one line on tablet and wraps cleanly on phone.
- Trust panel remains below operational status, not above driver identity.
- Verification button is disabled until a receipt id exists.

### Rider Receipt

```text
+------------------------------------------------+
| Ride Completed                                 |
|------------------------------------------------|
| Trust Score                              92/100 |
| Verification                            PASSED |
| Replay Match                              TRUE |
| Evidence Complete                         TRUE |
|                                                |
| Receipt ID                                     |
| rcpt-ride-5bdca5bf                            |
|                                                |
| Melbourne CBD -> Melbourne Airport             |
| Total: AUD 72.00                               |
|                                                |
| [ Download Receipt ] [ Verify ]                |
| [ Download Verification Package ]              |
+------------------------------------------------+
```

Required behavior:

- Receipt trust summary appears before fare details.
- Public verification never exposes private rider or driver data.
- Package button uses a manifest response, not locally generated files.

### Rider Replay

```text
+------------------------------------------------+
| Replay Timeline                                |
|------------------------------------------------|
| ride-5bdca5bf                                  |
| Replay verified                         TRUE   |
|                                                |
| 1  REQUESTED                         verified  |
| 2  DRIVER_ACCEPTED                  verified  |
| 3  ARRIVED                          verified  |
| 4  STARTED                          verified  |
| 5  COMPLETED                        verified  |
|                                                |
| Explanation                                    |
| Trip completion replay matched receipt hash.   |
+------------------------------------------------+
```

Required behavior:

- Show timeline as UI, not raw JSON.
- Keep event hashes hidden by default with optional expand behavior.
- Failed event appears with warning status and plain-language reason.

### Rider History

```text
+------------------------------------------------+
| Ride History                                   |
|------------------------------------------------|
| ride-5bdca5bf                                  |
| Completed                         Trust 92     |
| Verification: PASSED                           |
|                                                |
| ride-06c51759                                  |
| In trip                           Trust 88     |
| Verification: REVIEW_REQUIRED                  |
+------------------------------------------------+
```

Required behavior:

- Every history row shows trust context.
- Under-review rides must be visibly distinct from verified rides.

## Driver App Wireframes

### Driver Availability / Trust Profile

```text
+------------------------------------------------+
| AfriRide Driver                       Online   |
|------------------------------------------------|
| Djuma O                                        |
| Toyota Pilot                                   |
|                                                |
| Driver Trust Score                       94    |
| Verified rides                           152   |
| Replay consistency                       100%  |
| Status                           Trusted Driver|
|                                                |
| [ Go Offline ] [ Refresh Queue ]               |
+------------------------------------------------+
```

Required behavior:

- Availability state has one clear primary action.
- Trust profile is evidence-derived, not editable.

### Driver Ride Queue

```text
+------------------------------------------------+
| Ride Queue                                     |
|------------------------------------------------|
| Request ride-5bdca5bf                          |
| Pickup: Melbourne CBD                          |
| Dropoff: Melbourne Airport                     |
| Rider Trust Score: 91                          |
| Quote: AUD 72.00                       ETA 15m |
|                                                |
| [ Accept ] [ Reject ]                          |
+------------------------------------------------+
```

Required behavior:

- Rider trust appears as context, not as authority.
- Accept/reject actions require idempotency keys.

### Driver Trip Lifecycle

```text
+------------------------------------------------+
| Active Trip                           Trust 92 |
|------------------------------------------------|
| Rider: Rider 1                                  |
| Melbourne CBD -> Melbourne Airport             |
|                                                |
| ACCEPTED -> ARRIVED -> STARTED -> COMPLETED    |
|                                                |
| Replay verified: pending                       |
| Next: Drive to pickup                          |
|                                                |
| [ Arrived ]                                    |
+------------------------------------------------+
```

Required behavior:

- Only the valid next lifecycle action is primary.
- Invalid actions are hidden or disabled with explanation.
- Trust and replay status update after backend acknowledgement.

### Driver Earnings

```text
+------------------------------------------------+
| Earnings                                       |
|------------------------------------------------|
| This week                              AUD 120 |
| Rides                                      10  |
| Verified rides                            10  |
| Disputes                                   0  |
| Driver Trust Score                        94  |
|                                                |
| Source: core_system                            |
+------------------------------------------------+
```

Required behavior:

- Earnings remain distinct from settlement authority.
- Verified ride count is backend-derived.

### Driver Replay History

```text
+------------------------------------------------+
| Replay History                                 |
|------------------------------------------------|
| ride-5bdca5bf                         Trust 92 |
| REQUESTED -> ACCEPTED -> ARRIVED -> STARTED    |
|                                  -> COMPLETED  |
| Replay verified: TRUE                          |
+------------------------------------------------+
```

Required behavior:

- Same lifecycle truth as Rider app.
- Replay history cannot be edited locally.

## Accessibility Requirements

- Minimum touch target: 44 by 44 points.
- Trust color must be paired with text, never color-only.
- Buttons must fit labels at 320 px width.
- Timeline labels may wrap but must not overlap.
- Screen reader labels must include status and trust meaning.

## Figma Frame Inventory

```text
Rider / 01 Booking
Rider / 02 Waiting For Driver
Rider / 03 Live Ride
Rider / 04 Receipt
Rider / 05 Replay
Rider / 06 Ride History
Driver / 01 Availability
Driver / 02 Ride Queue
Driver / 03 Trip Lifecycle
Driver / 04 Earnings
Driver / 05 Trust Profile
Driver / 06 Replay History
Shared / TrustBadge States
Shared / LifecycleRail States
Shared / VerificationActions
```

## Boundary Copy

Use this copy in informational surfaces:

```text
AfriRide shows verification status from backend receipts, replay, and evidence.
The app displays proof results; it does not create proof authority.
```
