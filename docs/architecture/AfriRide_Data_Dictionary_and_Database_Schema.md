# AfriRide Data Dictionary and Database Schema

STATUS: OPERATIONAL DATA DESIGN SURFACE
CLASSIFICATION: ISOLATED OPERATIONAL DATA DESIGN SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Document Classification

This document defines AfriRide operational data structures.

It does not redefine AfriTech constitutional truth, replay authority, or core admissibility law.

## 1. Core Entities

```text
Rider
Driver
Vehicle
Ride
RideEvent
FareEstimate
Payment
Notification
ScheduledRide
AuditReplayRecord
```

## 2. Database Schema

## 2.1 Rider

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Primary rider identifier |
| rider_id | string | Yes | Canonical rider reference |
| full_name | string | No | Rider display name |
| phone_number | string | No | Contact number |
| email | string | No | Contact email |
| payment_reference | string | No | External payment token/reference |
| status | string | Yes | ACTIVE, SUSPENDED, DELETED |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

## 2.2 Driver

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Primary driver identifier |
| driver_id | string | Yes | Canonical driver reference |
| full_name | string | No | Driver display name |
| phone_number | string | No | Contact number |
| availability_status | string | Yes | AVAILABLE, BUSY, OFFLINE |
| rating | decimal | No | Driver rating |
| status | string | Yes | ACTIVE, SUSPENDED, DELETED |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

## 2.3 Vehicle

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Primary vehicle identifier |
| driver_id | FK | Yes | Linked driver |
| make | string | Yes | Vehicle make |
| model | string | Yes | Vehicle model |
| year | integer | No | Vehicle year |
| color | string | No | Vehicle color |
| license_plate | string | Yes | Vehicle registration |
| status | string | Yes | ACTIVE, INACTIVE |

## 2.4 Ride

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Primary ride identifier |
| ride_id | string | Yes | Canonical ride reference |
| rider_id | FK/string | Yes | Rider reference |
| driver_id | FK/string | No | Assigned driver |
| origin | string | Yes | Pickup/origin location |
| destination | string | Yes | Destination |
| status | string | Yes | REQUESTED, MATCHED, ACCEPTED, STARTED, COMPLETED, CANCELLED, FAILED |
| fare_estimate_id | FK | No | Linked fare estimate |
| scheduled_time | datetime | No | Future ride time |
| started_at | datetime | No | Ride start time |
| completed_at | datetime | No | Ride completion time |
| cancelled_at | datetime | No | Cancellation time |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

## 2.5 RideEvent

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Event identifier |
| event_id | string | Yes | Canonical event reference |
| ride_id | FK/string | Yes | Linked ride |
| event_type | string | Yes | ride_created, driver_matched, ride_started, etc. |
| previous_status | string | No | Previous ride status |
| new_status | string | No | New ride status |
| actor_id | string | No | Rider, driver, or system actor |
| payload | JSON | No | Event metadata |
| created_at | datetime | Yes | Event timestamp |

## 2.6 FareEstimate

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Fare estimate identifier |
| ride_id | FK/string | No | Linked ride |
| origin | string | Yes | Origin |
| destination | string | Yes | Destination |
| distance_km | decimal | No | Estimated distance |
| duration_minutes | integer | No | Estimated duration |
| base_fare | decimal | Yes | Base fare |
| distance_fare | decimal | Yes | Distance component |
| time_fare | decimal | Yes | Time component |
| total_fare | decimal | Yes | Total estimate |
| currency | string | Yes | Currency code |
| created_at | datetime | Yes | Creation timestamp |

## 2.7 Payment

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Payment identifier |
| payment_id | string | Yes | Canonical payment reference |
| ride_id | FK/string | Yes | Linked ride |
| rider_id | FK/string | Yes | Paying rider |
| amount | decimal | Yes | Payment amount |
| currency | string | Yes | Currency |
| payment_status | string | Yes | PENDING, AUTHORIZED, PAID, FAILED, REFUNDED |
| provider_reference | string | No | External provider reference |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

## 2.8 Notification

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Notification identifier |
| notification_id | string | Yes | Canonical notification reference |
| recipient_id | string | Yes | Rider or driver recipient |
| recipient_type | string | Yes | RIDER, DRIVER, ADMIN |
| channel | string | Yes | SMS, EMAIL, PUSH, IN_APP |
| message | text | Yes | Notification content |
| status | string | Yes | PENDING, SENT, FAILED |
| created_at | datetime | Yes | Creation timestamp |

## 2.9 ScheduledRide

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Scheduled ride identifier |
| rider_id | FK/string | Yes | Rider reference |
| origin | string | Yes | Origin |
| destination | string | Yes | Destination |
| scheduled_time | datetime | Yes | Requested future time |
| status | string | Yes | SCHEDULED, ACTIVATED, CANCELLED, FAILED |
| created_at | datetime | Yes | Creation timestamp |

## 2.10 AuditReplayRecord

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | UUID / string | Yes | Audit record identifier |
| ride_id | FK/string | Yes | Linked ride |
| replay_hash | string | Yes | Replay verification hash |
| event_count | integer | Yes | Number of replayed events |
| replay_status | string | Yes | VALID, INVALID |
| generated_at | datetime | Yes | Replay record timestamp |

## 3. Key Relationships

```text
Rider 1 -> many Ride
Driver 1 -> many Ride
Driver 1 -> many Vehicle
Ride 1 -> many RideEvent
Ride 1 -> one/many FareEstimate
Ride 1 -> one/many Payment
Ride 1 -> many Notification
Ride 1 -> one/many AuditReplayRecord
Rider 1 -> many ScheduledRide
```

## 4. Ride Status Values

```text
REQUESTED
MATCHED
ACCEPTED
STARTED
COMPLETED
CANCELLED
FAILED
```

## 5. Event Types

```text
ride_created
driver_matched
ride_accepted
ride_started
ride_completed
ride_cancelled
ride_failed
fare_estimated
payment_authorized
payment_completed
notification_sent
continuity_recovered
```

## 6. Schema Constraints

AfriRide data must preserve:

```text
canonical identity
deterministic lifecycle lineage
replay-safe event history
immutable operational audit trail
closed-world execution boundaries
```

AfriRide data must not:

```text
treat UI state as authoritative truth
allow undocumented lifecycle states
mutate completed ride lineage silently
bypass replay/audit event generation
```

## 7. Safe Final Classification

```text
AfriRide data schema is a bounded operational persistence design
supporting deterministic ride coordination, replay-safe auditability,
and AfriTech constitutional admissibility constraints.
```
