# AfriRide Device Certification Test Plan

Status: DEVICE CERTIFICATION TEST PLAN
Classification: MOBILE_FIELD_VALIDATION_SURFACE

Purpose: define the device-level test plan required before first partner demo,
field pilot, or multi-device rollout.

This plan is a field-validation surface.
It is not proof that certification has already been completed across all device
classes.

## Device Certification Goal

Verify that real devices preserve:

- API connectivity
- timestamp discipline
- idempotent writes
- understandable rider and driver UX
- no authority drift under weak network conditions

## Minimum Device Matrix

- one Android emulator
- one physical Android phone
- one iOS simulator or iPhone
- one operator device for observability checks

## Required Test Areas

### 1. Connectivity

- API base URL switching works
- authentication succeeds
- protected routes succeed with correct role

### 2. Event Integrity

- write actions emit `client_event`
- timestamps are present
- idempotency keys are attached
- ride actions do not duplicate after retry

### 3. Weak Network

- airplane-mode interruption rehearsal
- delayed reconnect
- repeated timeout handling
- queue flush behavior after recovery

### 4. UX Discipline

- rider understands pending vs completed state
- driver understands accept / arrive / start / complete flow
- operator view does not overclaim truth

### 5. Proof Surfaces

- receipt fetch succeeds
- replay fetch succeeds
- evidence fetch succeeds
- trust metrics remain readable on operator surface

## Certification Exit Rule

The device run passes only if:

- no duplicate committed action appears from retry behavior
- no client-side authority override is observed
- proof surfaces remain consistent after recovery

