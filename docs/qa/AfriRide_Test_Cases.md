# AfriRide - Test Cases

## Document Classification

```text
STATUS: OPERATIONAL VALIDATION SURFACE
CLASSIFICATION: ISOLATED OPERATIONAL VALIDATION SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE
```

These test cases validate bounded AfriRide behavior under AfriTech constitutional admissibility constraints.

They do not prove:

```text
global deployment readiness
universal fault tolerance
complete state-space exhaustiveness
```

---

# 1. Ride Request Test Cases

## TC-001 - Create Ride Intent Successfully

| Field | Description |
| --- | --- |
| Requirement | FR-001 |
| Component | RideRequestService |
| Preconditions | Valid rider request data |
| Input | `rider_id`, `origin`, `destination` |
| Steps | Submit valid ride request |
| Expected Result | Ride is created with `REQUESTED` status |
| Priority | High |

---

## TC-002 - Reject Missing Rider ID

| Field | Description |
| --- | --- |
| Requirement | FR-002 |
| Component | RideRequestValidator |
| Input | Missing `rider_id` |
| Expected Result | `ValueError` raised |
| Priority | High |

---

## TC-003 - Reject Missing Origin

| Field | Description |
| --- | --- |
| Requirement | FR-002 |
| Component | RideRequestValidator |
| Input | Missing `origin` |
| Expected Result | `ValueError("Missing field: origin")` |
| Priority | High |

---

## TC-004 - Reject Missing Destination

| Field | Description |
| --- | --- |
| Requirement | FR-002 |
| Component | RideRequestValidator |
| Input | Missing `destination` |
| Expected Result | `ValueError("Missing field: destination")` |
| Priority | High |

---

# 2. Driver Matching Test Cases

## TC-005 - Assign Driver Successfully

| Field | Description |
| --- | --- |
| Requirement | FR-003 |
| Component | MatchingService |
| Preconditions | Ride exists in `REQUESTED` state |
| Steps | Call `assign_driver(ride)` |
| Expected Result | Driver is assigned |
| Priority | High |

---

## TC-006 - Driver Matching Is Deterministic

| Field | Description |
| --- | --- |
| Requirement | NFR-001 |
| Component | MatchingService |
| Steps | Run same matching input twice |
| Expected Result | Same driver selected |
| Priority | High |

---

# 3. Ride Lifecycle Test Cases

## TC-007 - REQUESTED to MATCHED

| Field | Description |
| --- | --- |
| Requirement | FR-003 |
| Component | RideLifecycleService |
| Initial State | `REQUESTED` |
| Action | transition to `MATCHED` |
| Expected Result | Ride status becomes `MATCHED` |
| Priority | High |

---

## TC-008 - MATCHED to ACCEPTED

| Field | Description |
| --- | --- |
| Requirement | FR-004 |
| Component | RideLifecycleService |
| Initial State | `MATCHED` |
| Action | transition to `ACCEPTED` |
| Expected Result | Ride status becomes `ACCEPTED` |
| Priority | High |

---

## TC-009 - ACCEPTED to STARTED

| Field | Description |
| --- | --- |
| Requirement | FR-006 |
| Component | RideLifecycleService |
| Initial State | `ACCEPTED` |
| Action | transition to `STARTED` |
| Expected Result | Ride status becomes `STARTED` |
| Priority | High |

---

## TC-010 - STARTED to COMPLETED

| Field | Description |
| --- | --- |
| Requirement | FR-007 |
| Component | RideLifecycleService |
| Initial State | `STARTED` |
| Action | transition to `COMPLETED` |
| Expected Result | Ride status becomes `COMPLETED` |
| Priority | High |

---

## TC-011 - Reject REQUESTED to COMPLETED

| Field | Description |
| --- | --- |
| Requirement | Lifecycle integrity |
| Component | RideLifecycleService |
| Initial State | `REQUESTED` |
| Action | transition to `COMPLETED` |
| Expected Result | Invalid transition rejected |
| Priority | Critical |

---

## TC-012 - Reject COMPLETED to CANCELLED

| Field | Description |
| --- | --- |
| Requirement | Lifecycle immutability |
| Component | RideLifecycleService |
| Initial State | `COMPLETED` |
| Action | transition to `CANCELLED` |
| Expected Result | Invalid transition rejected |
| Priority | Critical |

---

# 4. Full Ride Flow Test Cases

## TC-013 - Full Ride Flow Completes

| Field | Description |
| --- | --- |
| Requirement | End-to-end lifecycle |
| Components | RideRequestService, MatchingService, RideLifecycleService |
| Steps | `REQUESTED -> MATCHED -> ACCEPTED -> STARTED -> COMPLETED` |
| Expected Result | Ride ends in `COMPLETED` |
| Priority | Critical |

---

## TC-014 - Full Ride Flow Preserves Driver Assignment

| Field | Description |
| --- | --- |
| Requirement | Driver identity integrity |
| Steps | Assign driver, complete ride |
| Expected Result | Driver remains associated with ride |
| Priority | High |

---

# 5. Cancellation Test Cases

## TC-015 - Cancel Requested Ride

| Field | Description |
| --- | --- |
| Initial State | `REQUESTED` |
| Action | transition to `CANCELLED` |
| Expected Result | Ride status becomes `CANCELLED` |
| Priority | High |

---

## TC-016 - Cancel Accepted Ride

| Field | Description |
| --- | --- |
| Initial State | `ACCEPTED` |
| Action | transition to `CANCELLED` |
| Expected Result | Ride status becomes `CANCELLED` |
| Priority | High |

---

## TC-017 - Reject Cancel Completed Ride

| Field | Description |
| --- | --- |
| Initial State | `COMPLETED` |
| Action | transition to `CANCELLED` |
| Expected Result | Invalid transition rejected |
| Priority | Critical |

---

# 6. Pricing Test Cases

## TC-018 - Generate Fare Estimate

| Field | Description |
| --- | --- |
| Component | PricingService |
| Input | origin, destination |
| Expected Result | Fare estimate returned |
| Priority | Medium |

---

## TC-019 - Fare Estimate Is Deterministic

| Field | Description |
| --- | --- |
| Component | PricingService |
| Steps | Run same estimate twice |
| Expected Result | Same fare returned |
| Priority | High |

---

# 7. Notification Test Cases

## TC-020 - Send Ride Status Notification

| Field | Description |
| --- | --- |
| Component | NotificationService |
| Trigger | Ride lifecycle transition |
| Expected Result | Notification created/sent |
| Priority | Medium |

---

## TC-021 - Notification Failure Does Not Change Ride Status

| Field | Description |
| --- | --- |
| Component | NotificationService |
| Scenario | Notification delivery fails |
| Expected Result | Ride status remains authoritative |
| Priority | High |

---

# 8. Payment Test Cases

## TC-022 - Authorize Payment

| Field | Description |
| --- | --- |
| Component | PaymentService |
| Trigger | Ride accepted or completed |
| Expected Result | Payment enters `AUTHORIZED` or `PAID` state |
| Priority | Medium |

---

## TC-023 - Payment Failure Does Not Corrupt Replay Lineage

| Field | Description |
| --- | --- |
| Component | PaymentService |
| Scenario | Payment fails |
| Expected Result | Payment failure recorded; ride lineage remains intact |
| Priority | High |

---

# 9. Replay and Audit Test Cases

## TC-024 - Ride Event Is Recorded

| Field | Description |
| --- | --- |
| Component | RideEvent / Audit |
| Trigger | Lifecycle transition |
| Expected Result | Replay-safe event stored |
| Priority | Critical |

---

## TC-025 - Replay Reconstructs Ride Lifecycle

| Field | Description |
| --- | --- |
| Component | Replay/Audit |
| Input | Ride event history |
| Expected Result | Reconstructed status equals final ride status |
| Priority | Critical |

---

## TC-026 - Replay Detects Divergence

| Field | Description |
| --- | --- |
| Component | Replay validation |
| Scenario | Event history tampered |
| Expected Result | Replay invalid |
| Priority | Critical |

---

# 10. Continuity Test Cases

## TC-027 - Driver Dropout Recovery

| Field | Description |
| --- | --- |
| Scenario | Assigned driver drops out |
| Expected Result | Recovery occurs deterministically |
| Priority | Critical |

---

## TC-028 - Timeout Recovery

| Field | Description |
| --- | --- |
| Scenario | Driver does not respond |
| Expected Result | Timeout handled without duplicate authority |
| Priority | Critical |

---

## TC-029 - Deterministic Reassignment

| Field | Description |
| --- | --- |
| Scenario | New driver required |
| Expected Result | Same reassignment result under replay |
| Priority | Critical |

---

## TC-030 - Prevent Duplicate Authority

| Field | Description |
| --- | --- |
| Scenario | Two drivers attempt to control same ride |
| Expected Result | Only one authority accepted |
| Priority | Critical |

---

# 11. Governance Test Cases

## TC-031 - Claim Evidence Binding Exists

| Field | Description |
| --- | --- |
| Component | Claim discipline |
| Expected Result | Every implemented claim has evidence binding |
| Priority | Critical |

---

## TC-032 - Claim References Implemented Registry Entry

| Field | Description |
| --- | --- |
| Component | Claim discipline validator |
| Expected Result | `implementation_refs` exist in registry |
| Priority | Critical |

---

## TC-033 - Reject Claim Bound to Non-Implemented Surface

| Field | Description |
| --- | --- |
| Component | Claim discipline validator |
| Scenario | Claim references `PLANNED` surface |
| Expected Result | Validator fails |
| Priority | Critical |

---

## TC-034 - Documentation Remains Non-Authoritative

| Field | Description |
| --- | --- |
| Component | Governance tests |
| Expected Result | Docs cannot redefine proof truth |
| Priority | High |

---

# 12. API Test Cases

## TC-035 - Create Ride API Returns REQUESTED

| Field | Description |
| --- | --- |
| Endpoint | `POST /api/v1/rides` |
| Expected Result | `201 Created`, status `REQUESTED` |
| Priority | High |

---

## TC-036 - Create Ride API Rejects Missing Origin

| Field | Description |
| --- | --- |
| Endpoint | `POST /api/v1/rides` |
| Input | Missing `origin` |
| Expected Result | `400 Bad Request` |
| Priority | High |

---

## TC-037 - Ride Transition API Accepts Valid Transition

| Field | Description |
| --- | --- |
| Endpoint | `POST /api/v1/rides/{ride_id}/transition` |
| Expected Result | Status updated |
| Priority | High |

---

## TC-038 - Ride Transition API Rejects Invalid Transition

| Field | Description |
| --- | --- |
| Endpoint | `POST /api/v1/rides/{ride_id}/transition` |
| Scenario | `REQUESTED -> COMPLETED` |
| Expected Result | `400 Bad Request` |
| Priority | Critical |

---

# 13. Acceptance Criteria

AfriRide test execution is successful when:

```text
all critical tests pass
full ride flow passes
replay validation passes
continuity scenarios pass
claim-evidence-implementation validation passes
documentation boundary tests pass
```

---

# 14. Safe Final Classification

```text
AfriRide test cases validate bounded product behavior,
deterministic lifecycle execution,
replay-safe auditability,
and constitutional admissibility constraints.
```
