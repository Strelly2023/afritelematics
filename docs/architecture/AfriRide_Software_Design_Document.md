# AfriRide Software Design Document

STATUS: OPERATIONAL DESIGN SURFACE
CLASSIFICATION: ISOLATED OPERATIONAL DESIGN SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Document Classification

This SDD defines the bounded software design of AfriRide as an operational product layer under AfriTech constitutional execution governance.

This document does not redefine:

```text
constitutional truth
replay admissibility
core invariants
execution legality
identity ontology
proof authority
```

## 1. Purpose

The purpose of this document is to describe how AfriRide software components are designed to support:

```text
ride requests
driver matching
ride lifecycle execution
pricing coordination
notifications
payment coordination
audit visibility
continuity validation
```

while preserving deterministic execution, replay safety, and constitutional admissibility.

## 2. Design Scope

### Included

```text
Django application structure
ride request service design
driver matching design
ride lifecycle design
pricing service design
notification service design
payment coordination design
API design
test design
replay/audit alignment
```

### Excluded

```text
global marketplace scaling guarantees
complete distributed consensus
unbounded dispatch optimization
production payment settlement guarantees
formal completeness proof
```

## 3. High-Level Design

AfriRide is designed as a bounded product system:

```text
Client / API
-> Django API layer
-> application services
-> domain models
-> persistence layer
-> replay/audit visibility
-> AfriTech constitutional validation
```

Core rule:

```text
AfriRide may execute operational mobility behavior,
but may not redefine AfriTech truth.
```

## 4. Package Structure

Recommended structure:

```text
afriride_system/
  django_app/
    api/
      v1/
        ride/
          urls.py
          views.py

    apps/
      ride_request/
        services/
          ride_request_service.py
        validators/
          input_validator.py

      ride_matching/
        services/
          matching_service.py

      ride_lifecycle/
        services/
          lifecycle_service.py

      rider/
        models/
          rider.py

      driver/
        models/
          driver.py

      pricing/
        services/
          pricing_service.py

      payments/
        services/
          payment_service.py

      notifications/
        services/
          notification_service.py

    tests/
```

## 5. Component Design

## 5.1 Ride Request Service

### Responsibility

Creates validated ride intents.

### Input

```text
rider_id
origin
destination
```

### Output

```text
Ride object
status = REQUESTED
```

### Design Rules

```text
validate input before creation
reject missing fields
create deterministic ride intent
do not perform driver matching here
do not perform payment settlement here
```

## 5.2 Ride Request Validator

### Responsibility

Reject invalid ride request payloads.

### Required Fields

```text
rider_id
origin
destination
```

### Failure Mode

```python
raise ValueError("Missing field: <field>")
```

## 5.3 Matching Service

### Responsibility

Assign an eligible driver to a ride.

### Design Rules

```text
matching must be deterministic
driver assignment must be reproducible
driver identity must be explicit
matching must not mutate constitutional truth
```

### Output

```text
Driver object or assignment reference
```

## 5.4 Ride Lifecycle Service

### Responsibility

Enforce legal ride status transitions.

### Valid States

```text
REQUESTED
MATCHED
ACCEPTED
STARTED
COMPLETED
CANCELLED
FAILED
```

### Valid Transitions

```text
REQUESTED -> MATCHED
MATCHED -> ACCEPTED
ACCEPTED -> STARTED
STARTED -> COMPLETED
REQUESTED -> CANCELLED
MATCHED -> CANCELLED
ACCEPTED -> CANCELLED
```

### Failure Mode

```python
raise ValueError("Invalid transition")
```

## 5.5 Pricing Service

### Responsibility

Calculate deterministic fare estimate.

### Inputs

```text
origin
destination
distance
duration
```

### Output

```text
fare_estimate
currency
```

### Constraint

Pricing is operational. It must not redefine replay truth or lifecycle legality.

## 5.6 Notification Service

### Responsibility

Notify riders and drivers about lifecycle changes.

### Constraint

Notifications are observational only.

```text
notification delivery failure must not mutate ride truth
```

## 5.7 Payment Service

### Responsibility

Coordinate payment authorization and settlement.

### Constraint

Payment processing is operationally isolated from constitutional proof truth.

```text
payment failure may affect ride operation
but must not corrupt replay lineage
```

## 6. Data Design

## 6.1 Ride Model

```python
class Ride:
    ride_id: str
    rider_id: str
    driver_id: str | None
    origin: str
    destination: str
    status: str
    created_at: datetime
    updated_at: datetime
```

## 6.2 Driver Model

```python
class Driver:
    driver_id: str
    availability_status: str
    vehicle_information: dict
    rating: float
```

## 6.3 Rider Model

```python
class Rider:
    rider_id: str
    profile_information: dict
    payment_reference: str | None
```

## 7. API Design

## 7.1 Create Ride

```text
POST /api/v1/rides
```

### Request

```json
{
  "rider_id": "rider_001",
  "origin": "Melbourne CBD",
  "destination": "Melbourne Airport"
}
```

### Response

```json
{
  "ride_id": "ride_001",
  "status": "REQUESTED"
}
```

## 7.2 Get Ride

```text
GET /api/v1/rides/{ride_id}
```

## 7.3 Transition Ride

```text
POST /api/v1/rides/{ride_id}/transition
```

### Request

```json
{
  "status": "STARTED"
}
```

## 8. State Design

Ride lifecycle state machine:

```text
REQUESTED
   |
   v
MATCHED
   |
   v
ACCEPTED
   |
   v
STARTED
   |
   v
COMPLETED
```

Cancellation path:

```text
REQUESTED -> CANCELLED
MATCHED -> CANCELLED
ACCEPTED -> CANCELLED
```

Forbidden examples:

```text
REQUESTED -> COMPLETED
MATCHED -> STARTED
COMPLETED -> CANCELLED
CANCELLED -> STARTED
```

## 9. Error Handling Design

### Validation Errors

```text
missing rider_id
missing origin
missing destination
```

### Lifecycle Errors

```text
invalid transition
transition after completion
transition from cancelled ride
```

### Matching Errors

```text
no eligible driver
invalid driver identity
```

### Payment Errors

```text
authorization failed
settlement failed
```

### Notification Errors

```text
delivery failed
```

Notification failures must be isolated from authoritative ride state.

## 10. Replay and Audit Design

Operationally significant actions should be traceable:

```text
ride_created
driver_matched
ride_accepted
ride_started
ride_completed
ride_cancelled
```

Each event should include:

```text
event_id
ride_id
event_type
previous_status
new_status
timestamp
actor_id
```

Replay/audit design must preserve:

```text
deterministic ordering
identity integrity
immutable lineage
reconstruction compatibility
```

## 11. Test Design

### Unit Tests

```text
RideRequestValidator rejects missing fields
RideRequestService creates REQUESTED ride
MatchingService assigns deterministic driver
RideLifecycleService accepts valid transitions
RideLifecycleService rejects invalid transitions
```

### Integration Tests

```text
full ride flow:
REQUESTED -> MATCHED -> ACCEPTED -> STARTED -> COMPLETED
```

### Governance Tests

```text
documentation remains non-authoritative
AfriRide product layer remains isolated
claim-evidence-implementation bindings remain valid
```

### Continuity Tests

```text
driver dropout
timeout
reassignment
duplicate authority prevention
replay equivalence
```

## 12. Security Design

The system must enforce:

```text
explicit identity
validated inputs
no undeclared runtime surfaces
no direct constitutional bypass
no observer-relative lifecycle mutation
```

## 13. Design Constraints

AfriRide must preserve:

```text
deterministic execution
replay admissibility
closed-world execution
canonical identity resolution
invariant preservation
claim discipline
```

AfriRide must not:

```text
redefine constitutional truth
bypass replay validation
create undeclared execution surfaces
treat documentation as proof authority
```

## 14. Traceability Matrix

| Requirement | Design Component |
| --- | --- |
| Ride request | RideRequestService |
| Input validation | RideRequestValidator |
| Driver matching | MatchingService |
| Lifecycle transitions | RideLifecycleService |
| Pricing | PricingService |
| Notifications | NotificationService |
| Payments | PaymentService |
| Replay audit | Replay/Audit event design |
| Continuity | Continuity tests |
| Constitutional boundary | Governance tests |

## 15. Safe Final Classification

```text
AfriRide is a bounded operational mobility software design
implemented as a Django product layer
under AfriTech replay-governed constitutional admissibility constraints.
```
