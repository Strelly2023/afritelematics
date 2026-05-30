# AfriRide First 10 Rides Runbook

STATUS: DAY-ONE FIELD RUNBOOK
CLASSIFICATION: FIRST REAL RIDES EXECUTION SURFACE
GOVERNANCE MODE: HUMAN-OPERATED, REPLAY-BACKED, TRUST-FIRST

## Boundary

This runbook is for the first 10 real or controlled-live AfriRide rides.

It is not runtime authority, replay authority, regulatory approval, payment
licensing proof, production deployment proof, or evidence that the pilot has
already succeeded.

It must not create new architecture, new ecosystem scope, new validators, or a
new product roadmap.

Its job is to help operators complete rides, capture proof, and learn from
reality.

## Success Definition

The first 10 rides are successful only if:

```text
drivers understand the flow
users understand the promise
rides complete or fail with trace
pricing is explainable
dispatch is explainable
replay evidence exists
support issues are recorded
one blocker is chosen for the next day
```

## Roles

Minimum team:

```text
pilot lead
driver coordinator
user coordinator
support operator
replay operator
```

One person may hold multiple roles, but every role must be named before the
first ride starts.

## Pre-Ride Setup

Before ride 1:

```text
confirm service zone
confirm driver roster
confirm first user list
confirm support phone or chat
confirm manual fallback path
confirm pricing explanation
confirm replay receipt path
open daily metrics template
open incident log
```

No ride starts until the operator can answer:

```text
who is the driver
who is the user
where is pickup
where is dropoff
what is the expected price
how will replay be captured
who handles support
```

## Ride Execution Checklist

For each ride:

```text
1. record ride_id
2. record driver_id
3. record user_id
4. record pickup area
5. record dropoff area
6. show or confirm price before trip
7. assign driver
8. confirm driver accepted
9. confirm pickup
10. confirm dropoff
11. record completion or failure
12. attach replay receipt
13. ask driver: did this feel fair?
14. ask user: did this feel reliable?
15. record one lesson
```

## First 10 Ride Sequence

```text
Ride 1: internal operator ride
Ride 2: driver training ride
Ride 3: repeat controlled corridor ride
Ride 4: first invited user ride
Ride 5: second invited user ride
Ride 6: different driver, same corridor
Ride 7: repeat user ride if possible
Ride 8: support-observed ride
Ride 9: driver reliability ride
Ride 10: trust review ride
```

The sequence may adapt to reality, but the first 10 rides must include:

```text
at least 3 drivers
at least 3 users
at least 2 repeat corridor rides
at least 1 support-observed ride
10 replay receipt checks
10 price explanation checks
```

## Plain-Language Driver Check

After each ride, ask the driver:

```text
Did the price feel fair?
Did the pickup assignment make sense?
Was any step confusing?
Would you accept another ride?
What is the one thing to fix?
```

## Plain-Language User Check

After each ride, ask the user:

```text
Was booking clear?
Did pickup feel reliable?
Did the price feel fair?
Would you use this again?
What is the one thing to fix?
```

## Replay Review

For each ride, the replay operator records:

```text
replay receipt exists
pricing explanation exists
dispatch explanation exists
completion or failure reason exists
support issue linked if any
```

If replay cannot explain a material issue, stop live rides until the issue is
understood.

## First 10 Metrics

Record these after every ride:

```text
ride_id
driver_id
user_id
requested_at
assigned_at
accepted_at
pickup_confirmed_at
dropoff_confirmed_at
status
price_explained
replay_receipt
driver_fairness_response
user_reliability_response
support_issue
lesson
```

Use the KPI dashboard template:

```text
docs/operations/AfriRide_Pilot_KPI_Dashboard_Template.csv
```

## Stop Rules

Pause immediately if:

```text
driver identity is uncertain
user consent is missing
price cannot be explained
dispatch cannot be explained
replay receipt is missing
support issue has no trace
operator changes truth manually
```

## End-of-Day Review

At the end of the day:

```text
count completed rides
count failed rides
count replay-backed rides
count pricing anomalies
count driver complaints
count user complaints
choose one blocker
choose tomorrow's first action
```

Decision:

```text
go: run the next rides
pause: stop until blocker is fixed
narrow: reduce zone, drivers, or users
```

## Final Rule

```text
Do not optimize before the first 10 rides teach you what is real.
```
