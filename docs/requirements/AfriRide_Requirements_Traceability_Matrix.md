# AfriRide - Requirements Traceability Matrix

## Document Classification

```text
STATUS: OPERATIONAL TRACEABILITY SURFACE
CLASSIFICATION: ISOLATED OPERATIONAL TRACEABILITY SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE
```

This matrix traces AfriRide business, software, design, test, and governance requirements.

It does not redefine:

```text
constitutional truth
replay authority
execution legality
core invariants
```

---

# 1. Traceability Scope

This matrix links:

```text
BRD objectives
SRS requirements
SAD components
SDD design elements
test cases
governance constraints
```

---

# 2. Requirement Traceability Matrix

| Requirement ID | Requirement | Source | Design / Component | Test Case(s) | Status |
| --- | --- | --- | --- | --- | --- |
| BR-001 | Reliable ride coordination | BRD | RideRequestService, RideLifecycleService | TC-001, TC-013 | Covered |
| BR-002 | Deterministic lifecycle management | BRD / SRS | RideLifecycleService | TC-007-TC-013 | Covered |
| BR-003 | Transparent fare estimation | BRD / SRS | PricingService | TC-018, TC-019 | Covered |
| BR-004 | Operational continuity | BRD / SAD | Continuity validation layer | TC-027-TC-030 | Covered |
| BR-005 | Rider and driver identity integrity | BRD / SRS | Rider, Driver, MatchingService | TC-014, TC-030 | Covered |
| BR-006 | Replay-safe auditability | BRD / SAD | RideEvent, AuditReplayRecord | TC-024-TC-026 | Covered |
| FR-001 | Create ride intent | SRS | RideRequestService | TC-001, TC-035 | Covered |
| FR-002 | Validate ride request payload | SRS | RideRequestValidator | TC-002-TC-004, TC-036 | Covered |
| FR-003 | Deterministic driver matching | SRS | MatchingService | TC-005, TC-006 | Covered |
| FR-004 | Driver accepts ride | SRS | RideLifecycleService | TC-008 | Covered |
| FR-005 | Driver rejects ride | SRS | MatchingService / LifecycleService | Future rejection test | Partial |
| FR-006 | Start ride | SRS | RideLifecycleService | TC-009 | Covered |
| FR-007 | Complete ride | SRS | RideLifecycleService | TC-010, TC-013 | Covered |
| FR-008 | Cancel ride | SRS | RideLifecycleService | TC-015-TC-017 | Covered |
| FR-009 | Fare estimation | SRS | PricingService | TC-018, TC-019 | Covered |
| FR-010 | ETA sharing | SRS / UI | NotificationService / Tracking UI | Future ETA test | Partial |
| FR-011 | Scheduled rides | SRS | ScheduledRide | Future scheduled ride test | Partial |
| FR-012 | Notifications | SRS | NotificationService | TC-020, TC-021 | Covered |
| FR-013 | Replay reconstruction | SRS | Replay / Audit services | TC-025, TC-026 | Covered |
| FR-014 | Continuity recovery | SRS / SAD | Continuity scenarios | TC-027-TC-030 | Covered |
| NFR-001 | Deterministic execution | SRS | MatchingService, LifecycleService, PricingService | TC-006, TC-019, TC-025 | Covered |
| NFR-002 | Replay safety | SRS / SAD | RideEvent, AuditReplayRecord | TC-024-TC-026 | Covered |
| NFR-003 | Identity integrity | SRS / SAD | Rider, Driver, Ride identity model | TC-014, TC-030 | Covered |
| NFR-004 | Closed-world enforcement | SRS / SAD | AfriTech constitutional validation | TC-031-TC-034 | Covered |
| NFR-005 | Audit visibility | SRS / SAD | RideEvent, AuditReplayRecord | TC-024, TC-025 | Covered |
| NFR-006 | Failure containment | SRS / QA | Continuity and replay tests | TC-023, TC-027-TC-030 | Covered |
| NFR-007 | Observational isolation | SRS / UI / SAD | Notifications, UI, dashboards | TC-021, TC-034 | Covered |
| GOV-001 | Claim-evidence binding | Governance | CLAIM_EVIDENCE_BINDINGS.yaml | TC-031 | Covered |
| GOV-002 | Claim references implementation registry | Governance | implementation_registry.yaml | TC-032 | Covered |
| GOV-003 | Reject non-implemented claim refs | Governance | claim_discipline_validator.py | TC-033 | Covered |
| GOV-004 | Documentation non-authoritative boundary | Governance / Docs | Documentation boundary tests | TC-034 | Covered |
| API-001 | Create ride API | SRS / API | `POST /api/v1/rides` | TC-035, TC-036 | Covered |
| API-002 | Ride transition API | SRS / API | `POST /api/v1/rides/{ride_id}/transition` | TC-037, TC-038 | Covered |

---

# 3. Coverage Summary

| Category | Covered | Partial | Missing |
| --- | ---: | ---: | ---: |
| Business Requirements | 6 | 0 | 0 |
| Functional Requirements | 11 | 3 | 0 |
| Non-Functional Requirements | 7 | 0 | 0 |
| Governance Requirements | 4 | 0 | 0 |
| API Requirements | 2 | 0 | 0 |

---

# 4. Partial Coverage Items

| Requirement | Reason | Required Follow-Up |
| --- | --- | --- |
| FR-005 - Driver rejects ride | Rejection scenario not explicitly mapped to a concrete test | Add driver rejection lifecycle test |
| FR-010 - ETA sharing | UI/notification behavior defined, but no concrete test case yet | Add ETA sharing token/test |
| FR-011 - Scheduled rides | Data and UX defined, but no lifecycle activation test yet | Add scheduled ride activation test |

---

# 5. Governance Traceability

```text
claim
-> evidence
-> implementation_refs
-> implementation_registry
-> admissibility validation
-> CI enforcement
```

Traceability rules:

```text
every implemented claim must have evidence
every implemented claim must reference implementation
referenced implementation must be IMPLEMENTED
referenced implementation must be replay admissible
referenced implementation must be proof admissible
referenced implementation must be deterministic
```

---

# 6. Validation Commands

```bash
python3 -m afritech.ci.claim_discipline_validator
python3 -m afritech.ci.constitutional_validation
python3 -m afritech.demo.proof
pytest -q
```

---

# 7. Acceptance Criteria

Traceability is acceptable when:

```text
all critical requirements map to test cases
all implemented claims map to implementation registry entries
all governance tests pass
all replay and continuity requirements remain bounded
all documentation surfaces remain non-authoritative
```

---

# 8. Safe Final Classification

```text
AfriRide traceability matrix provides bounded requirement-to-test coverage
for replay-governed mobility coordination under AfriTech constitutional
admissibility constraints.
```
