# AfriRide First 3 Live Rides Execution Packet

STATUS: LIVE FIELD EXECUTION PACKET
CLASSIFICATION: FIRST REAL RIDES OPERATING SURFACE
GOVERNANCE MODE: ONE REHEARSAL, THEN LIVE RIDES

## Boundary

This packet is for executing the first 3 real AfriRide rides after exactly one
rehearsal pass.

It is not runtime authority, replay authority, regulatory approval, payment
licensing proof, production deployment proof, or evidence that the pilot has
already succeeded.

It must not create new architecture, new validators, new pillars, new launch
scope, or another rehearsal loop. Its job is to move the team into real rides
and make every live lesson traceable.

## Non-Negotiable Rule

```text
Run one rehearsal.
Then run live ride 1.
Do not rehearse endlessly.
```

If the rehearsal reveals a material blocker, pause only long enough to fix that
single blocker. Do not broaden the work.

## Live Ride Objective

The first 3 live rides must answer:

```text
Can a real driver complete the flow?
Can a real rider understand the promise?
Can pricing be explained plainly?
Can dispatch be explained plainly?
Can replay reconstruct what happened?
Can support handle confusion without guessing?
```

## Required Roles

Before live ride 1, name:

```text
pilot lead
driver coordinator
rider coordinator
support operator
replay operator
```

One person may hold multiple roles, but nobody may assume an unnamed role during
a live ride.

## Live Ride 1 - Controlled Real Ride

Purpose:

```text
prove one real ride can complete with a known driver and known rider
```

Requirements:

```text
known driver
known rider
bounded route
price explained before assignment
support operator online
replay operator ready
manual fallback available
```

After ride:

```text
driver fairness question answered
rider reliability question answered
replay receipt checked
pricing explanation checked
dispatch explanation checked
one lesson recorded
```

Pass condition:

```text
ride completes or fails with trace, replay, and plain-language explanation
```

## Live Ride 2 - Repeatability Check

Purpose:

```text
prove the first result was not accidental
```

Requirements:

```text
same route or same service zone
same driver or second ready driver
second rider if available
same support process
same replay review
```

After ride:

```text
compare ride 1 and ride 2 confusion points
compare pricing explanation clarity
compare dispatch explanation clarity
record whether driver confidence improved
record whether rider confidence improved
```

Pass condition:

```text
ride 2 produces no new unexplained pricing, dispatch, or replay issue
```

## Live Ride 3 - Confidence Check

Purpose:

```text
decide whether to proceed toward the first 10 rides
```

Requirements:

```text
real driver
real rider
support operator online
replay operator ready
operator decision prepared
```

After ride:

```text
review all three rides
count completed rides
count failed rides
count pricing anomalies
count replay mismatches
count support issues
choose go, pause, or narrow
```

Pass condition:

```text
team can explain all three rides without guessing
```

## Live Rider Confusion Handling

When the rider is confused, say:

```text
Thanks for saying that. We are running this pilot slowly so we can explain every ride clearly.
Let me check the trip record and explain what happened in plain language.
```

Then do:

```text
identify the ride
inspect the trip record
explain price if price is the issue
explain dispatch if pickup is the issue
explain status if timing is the issue
record whether the rider accepted the explanation
record what confused them
```

Do not:

```text
guess
blame the driver
blame the rider
promise a feature
change the truth manually
```

## When a Ride Goes Wrong

If a ride fails or creates concern:

```text
stop the next ride
record the issue
find the ride record
inspect replay
classify the issue
explain what happened
decide go, pause, or narrow
```

Issue classes:

```text
driver confusion
rider confusion
pricing explanation issue
dispatch explanation issue
pickup timing issue
payment record issue
support trace issue
replay proof issue
```

Pause immediately if:

```text
replay proof issue
price cannot be explained
dispatch cannot be explained
support issue has no trace
driver identity is uncertain
rider consent is missing
```

## First 3 Live Rides Log

Use:

```text
docs/operations/AfriRide_First_3_Live_Rides_Log_Template.csv
```

Required row per ride:

```text
ride_number
ride_id
driver_id
rider_id
route_type
status
price_explained
dispatch_explained
replay_receipt_checked
driver_fairness_response
rider_reliability_response
confusion_point
issue_class
operator_decision
next_action
```

## Proceed to First 10 Rides Only If

```text
at least 2 of 3 rides completed or failed with full trace
0 unexplained pricing issues
0 unexplained dispatch issues
0 replay proof gaps
driver feedback captured for every ride
rider feedback captured for every ride
operator decision recorded
```

## Referral After Ride 3

Ask for referrals only if the experience was good and explainable.

Driver:

```text
You completed one of the first AfriRide live rides. Do you know one driver who would value fair pricing and clear trip proof?
```

Rider:

```text
You completed one of the first AfriRide live rides. Do you know one person in this service zone who would value a fair ride that can be explained if something goes wrong?
```

Do not ask for public promotion before the first 10 rides are complete.

## Final Rule

```text
One rehearsal.
Three live rides.
Replay every ride.
Learn before scaling.
```
