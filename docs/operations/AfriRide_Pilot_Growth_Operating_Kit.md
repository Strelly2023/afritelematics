# AfriRide Pilot Growth Operating Kit

STATUS: FIELD EXECUTION KIT
CLASSIFICATION: DRIVER AND FIRST-USER ACQUISITION SURFACE
GOVERNANCE MODE: REAL PEOPLE, REAL RIDES, REPLAY-BACKED TRUST

## Boundary

This kit is for Week 1-4 field execution.

It is not runtime authority, replay authority, regulatory approval, payment
licensing proof, production deployment proof, or evidence that the pilot has
already succeeded.

It translates the launch plan into daily conversations, intake records, and
metrics. It must not introduce new architecture, new pillars, new ecosystem
scope, or a new validation program.

## Daily Rule

Every day must produce one of these outcomes:

```text
new driver conversation
new driver onboarded
new invited user
new completed ride
new replay-backed lesson
```

If none of those happened, the day stayed in system mode.

## Driver Acquisition Script

### Opening

```text
Hi, I am helping launch AfriRide in one city with a small driver group.
The goal is simple: fair rides, predictable pricing, and every trip can be proven if there is a dispute.
We are inviting 10-50 drivers for the controlled pilot.
```

### Driver Pain Questions

Ask:

```text
What makes ride platforms unfair for you today?
When do you feel pricing is unclear?
What causes your biggest pickup or cancellation problems?
What would make you trust a new ride system?
```

Record answers exactly. Do not reinterpret complaints into architecture terms.

### Trust Pitch

Say:

```text
AfriRide is different because every trip has a replay record.
If pricing, dispatch, or a dispute is questioned, we can reconstruct what happened instead of guessing.
```

### Pilot Ask

Say:

```text
We are not asking you to switch everything.
We are asking you to join a controlled pilot, complete test rides, and tell us where the system feels fair or unfair.
```

### Close

Confirm:

```text
driver name
phone
city zone
vehicle type
availability window
platforms currently used
top complaint
pilot interest: yes, maybe, no
next action
```

## Driver Onboarding Checklist

Required before live user rides:

```text
identity record captured
vehicle record captured
service zone confirmed
availability window confirmed
driver accept flow tested
pickup flow tested
dropoff flow tested
support path explained
fair pricing explanation completed
replay receipt shown
driver complaint channel confirmed
```

Readiness gate:

```text
driver can complete a controlled test ride and explain why replay proof matters
```

## First 100 Users Growth Plan

Target users:

```text
airport transfer riders
commuters in the pilot corridor
students with repeat routes
healthcare or shift workers
small business operators
friends and family referrals inside the service zone
```

Invite message:

```text
AfriRide is running a small invite-only ride pilot.
The promise is fair pricing, reliable pickup, and every trip can be proven if something goes wrong.
We are inviting the first 100 users in one service zone.
```

User intake fields:

```text
user name
phone
usual pickup area
usual destination area
ride frequency
biggest ride problem today
preferred ride time
pilot consent
first ride target date
```

Activation rule:

```text
an invited user is not activated until they complete one ride or one scheduled ride attempt
```

## First 50 Rides Target

Minimum success after four weeks:

```text
50+ real rides
10+ active drivers
100+ invited users
zero unexplained pricing anomalies
all completed rides replay-backed
all disputes trace-backed
```

Ride mix:

```text
20 controlled corridor rides
15 repeat rider rides
10 driver reliability test rides
5 edge-case rides with support observation
```

## Daily Metrics Capture

Use the daily metrics template:

```text
docs/operations/AfriRide_Pilot_Daily_Metrics_Template.csv
```

Required fields:

```text
date
city
drivers_contacted
drivers_onboarded
drivers_active
users_invited
users_activated
rides_requested
rides_completed
rides_failed
booking_time_median_seconds
pickup_reliability_rate
ride_success_rate
pricing_anomaly_count
replay_mismatch_count
dispatch_unexplained_count
dispute_count
refund_case_count
driver_complaint_count
user_complaint_count
replay_explained_incident_count
top_driver_complaint
top_user_complaint
operator_decision
```

## Daily Review Questions

Ask every evening:

```text
Did real drivers move closer to trusting AfriRide?
Did real users move closer to trusting AfriRide?
Did any ride fail in a way replay could not explain?
Did pricing feel fair to drivers and users?
What is the single blocker to fix tomorrow?
```

## Support Response Rule

When a rider or driver raises a concern:

```text
acknowledge the issue
find the trip record
run or inspect the replay
explain pricing, dispatch, cancellation, or failure in plain language
record whether the explanation was accepted
fix only if the trace reveals a product blocker
```

## Weekly Decision

At the end of each week, decide one:

```text
go: continue pilot as scoped
pause: stop live rides until a trust blocker is fixed
narrow: reduce zone, driver group, or user group
```

Do not expand unless:

```text
rides are happening
drivers remain active
users are activating
pricing anomalies are explained or zero
replay proof remains intact
support issues are trace-backed
```

## Field Discipline

Allowed:

```text
talk to drivers
invite users
complete rides
observe failures
review replay
fix ride blockers
improve onboarding
improve support response
```

Blocked:

```text
new ecosystem expansion
new pillar work
abstract validator work
multi-city launch work
architecture polishing unrelated to rides
```

## Final Field Rule

```text
Talk to drivers.
Invite users.
Complete rides.
Replay failures.
Fix trust blockers.
```
