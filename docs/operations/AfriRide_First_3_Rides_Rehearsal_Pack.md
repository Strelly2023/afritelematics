# AfriRide First 3 Rides Rehearsal Pack

STATUS: PRE-LIVE REHEARSAL PACK
CLASSIFICATION: DRIVER CONVERSATION AND FIRST-RIDE SIMULATION SURFACE
GOVERNANCE MODE: PRACTICE BEFORE LIVE, REPLAY EVERY LESSON

## Boundary

This pack prepares the team for the first 3 controlled-live rides.

It is not runtime authority, replay authority, regulatory approval, payment
licensing proof, production deployment proof, or evidence that a pilot ride has
already succeeded.

It must not add architecture, new validators, new pillars, or new launch scope.
Its job is to help operators speak clearly, rehearse safely, handle predictable
problems, and move into the first real rides faster.

## Day-One Outcome

The first day should produce:

```text
5 driver conversations
3 qualified driver leads
1 ready driver
1 ready rider
1 completed rehearsal ride
1 replay-backed lesson
```

If a real ride is not safe yet, run a controlled rehearsal ride and record why
the live ride was paused.

## Word-for-Word Driver Conversation

### Opening

```text
Hi, my name is [name]. I am helping launch AfriRide in one city with a small driver group.
We are not asking you to switch platforms today.
We are testing a fair ride system where pricing is clear and every trip can be proven if there is a dispute.
Can I ask you four quick questions about what is unfair in ride apps today?
```

### Four Questions

```text
1. What makes ride platforms unfair for you today?
2. When does pricing feel unclear or wrong?
3. What causes pickup, cancellation, or payment problems?
4. What would make you trust a new ride system enough to test it?
```

### Simple AfriRide Explanation

```text
AfriRide is built around one promise: fair rides with proof.
If a trip is questioned, we do not guess.
We replay the trip record and explain pricing, dispatch, pickup, dropoff, or failure clearly.
```

### Pilot Ask

```text
We are starting with 10-50 drivers, not a public launch.
The first step is one controlled test ride.
You try the flow, we show the replay receipt, and you tell us what felt fair or confusing.
Would you be willing to do one controlled test ride this week?
```

### If Driver Says Yes

```text
Great. I need your name, phone, vehicle type, service zone, and best availability window.
After the test ride I will ask two things: did the price feel fair, and would you accept another ride?
```

### If Driver Hesitates

```text
That is fair. You do not need to commit today.
What is the one concern you would need answered before testing one ride?
```

### If Driver Says No

```text
No problem. Before I go, what should a fair ride system never do to drivers?
```

## First 3 Rides Simulation Plan

### Ride 1 - Operator Rehearsal

Purpose:

```text
prove the team can run the flow without a real user depending on it
```

Actors:

```text
operator as rider
ready driver or internal driver
support operator
replay operator
```

Steps:

```text
request ride
confirm expected price
assign driver
accept ride
confirm pickup
confirm dropoff
generate replay receipt
ask driver fairness question
ask rider reliability question
record one blocker
```

Pass condition:

```text
ride completes with replay receipt and pricing explanation
```

### Ride 2 - Driver Training Ride

Purpose:

```text
test whether a real driver understands the flow
```

Actors:

```text
real driver
operator rider
support operator
replay operator
```

Steps:

```text
driver receives assignment
driver accepts
driver confirms pickup
driver confirms dropoff
operator explains replay receipt
driver explains back what replay means
driver names one confusing step
```

Pass condition:

```text
driver can complete the ride and explain why replay proof matters
```

### Ride 3 - First Invited User Rehearsal

Purpose:

```text
test whether a first invited user understands the promise
```

Actors:

```text
invited user
ready driver
support operator
replay operator
```

Steps:

```text
user requests or schedules ride
operator confirms pickup and dropoff
price is explained before assignment
driver accepts
ride completes or fails with trace
user sees simple explanation if needed
operator records trust response
```

Pass condition:

```text
user can say whether the ride felt fair, reliable, and understandable
```

## Problem Scenario Response Cards

Use the response card template:

```text
docs/operations/AfriRide_First_Ride_Response_Cards.csv
```

Required scenarios:

```text
driver asks about pay fairness
driver worries about hidden pricing
driver does not understand replay
user asks why price is different
pickup is delayed
driver cancels
user cancels
payment record is unclear
support issue has no trace
replay receipt is missing
```

## Replay Habit

After every rehearsal or ride:

```text
find trip record
inspect replay receipt
explain price
explain dispatch
record driver reaction
record user reaction
choose one lesson
```

Do not move to the next ride if the current ride produced a material issue that
replay cannot explain.

## Referral Prompt After a Good Ride

Only ask after a driver or user has a good experience.

Driver prompt:

```text
You just completed a replay-backed AfriRide test ride.
Do you know one driver who cares about fair pricing and would give honest feedback?
```

User prompt:

```text
You just tried the AfriRide pilot.
Do you know one person in this service zone who would value a fair, reliable ride with proof if something goes wrong?
```

Do not ask for broad promotion before the first 10 rides are complete.

## End-of-Rehearsal Decision

Choose one:

```text
go: run first live ride
pause: fix one blocker before live ride
narrow: reduce route, driver set, or user set
```

The decision must be based on:

```text
driver readiness
user clarity
pricing explainability
dispatch explainability
replay receipt availability
support traceability
```

## Final Rule

```text
Say it simply.
Run it slowly.
Replay it immediately.
Learn before scaling.
```
