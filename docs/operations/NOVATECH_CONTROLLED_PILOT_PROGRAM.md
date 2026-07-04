# NovaTech Controlled Pilot Program

Version: 1.0

This document is the operational reference for controlled pilot execution across
the NovaTech platform. It formalizes the boundary between repository evidence,
controlled field use, operational readiness, and commercial launch.

## 1. Executive Summary

NovaTech supports two controlled pilots on a shared governed platform:

- NovaRide Controlled Pilot
- NovaPay Controlled Pilot

Both pilots exercise the same platform services:

- NovaID
- NovaPower
- NovaTrust
- NovaAI
- Notifications
- Audit
- Monitoring
- Operations

The pilot stage validates real-world execution with bounded participant counts,
explicit approval paths, and verifiable evidence. It does not imply commercial
launch or unrestricted production operation.

## 2. Governance Model

The governance model is intentionally staged:

```text
Repository implementation
    ≠
Operational activation

Operational activation
    ≠
Commercial launch

Controlled pilot
    ≠
Public production
```

Pilot decisions must remain governed by:

- NovaID identity and role claims
- NovaPower authorization and approval workflows
- NovaTrust evidence, receipts, replay, and signatures
- NovaAI advisory only, with no autonomous execution authority

## 3. NovaRide Pilot

### Objective

Validate trusted mobility operations in a controlled environment.

### Participants

| Role | Target |
| --- | ---: |
| Drivers | 25–50 |
| Riders | 100–300 |
| Dispatch operators | 3–5 |
| Support staff | 2–4 |
| Operations managers | 2 |

### Applications

- Rider App
- Driver App
- Operations Dashboard
- Customer Support Console
- NovaTrust Explorer

### Pilot Scope

- account registration
- identity verification
- ride booking
- driver matching
- live GPS tracking
- navigation handoff
- ride lifecycle
- digital receipts
- replay verification
- support workflows

### Pilot KPIs

- ride completion rate ≥ 95%
- API availability ≥ 99%
- dispatch latency within pilot SLA
- GPS update latency within pilot SLA
- replay verification succeeds for sampled rides
- no unresolved critical incidents

## 4. NovaPay Pilot

### Objective

Validate digital payments and governed financial operations in a controlled
commercial environment.

### Participants

| Role | Target |
| --- | ---: |
| Consumers | 100–500 |
| Merchants | 20–100 |
| Agents | 10–30 |
| Finance users | 3–5 |
| Compliance officers | 2–3 |
| Support staff | 2–4 |

### Applications

- NovaPay Wallet
- Business Wallet
- Merchant App
- Agent App
- Finance Portal
- Compliance Portal
- Partner Portal
- Inspector Portal
- NovaTrust Explorer

### Pilot Scope

- wallet onboarding
- KYC / KYB
- QR payments
- merchant acceptance
- cash-in / cash-out
- refunds
- settlement reporting
- receipt verification
- compliance review
- finance reconciliation

### Pilot KPIs

- transaction success rate ≥ 99%
- settlement completed within pilot SLA
- receipt verification available
- merchant onboarding complete
- finance reconciliation complete
- compliance review complete

## 5. Shared Platform Services

The pilots should exercise the shared platform once, rather than duplicating
validation across product surfaces:

- NovaID authentication and MFA
- NovaPower authorization and approvals
- NovaTrust receipts, replay, signatures, and verification
- notification delivery
- audit logging
- monitoring and dashboards
- operations workflows
- NovaAI advisory summaries

## 6. Entry Gates

### Repository validation gates

Before admitting pilot users, the following repository checks must pass:

- four-gate validation
- runtime-boundary validation
- documentation validation
- secret scan
- targeted regression suites
- architecture validation

### Operational readiness gates

The following are external operational dependencies and are not source control
features:

- production-equivalent secrets
- TLS certificates
- monitoring and alerting
- pilot provider credentials
- push notification credentials
- map provider credentials where enabled

These remain documented in `docs/operations/PRODUCTION_READINESS_REQUIREMENTS.md`.

## 7. Pilot Execution

Pilot execution should be run as a daily operational cycle:

1. admit controlled participants
2. verify identity and policy eligibility
3. execute the pilot workflow
4. capture evidence
5. reconcile support, finance, and compliance outcomes
6. review incidents and exceptions
7. retain replay and audit artifacts

Operational teams should maintain:

- daily support triage
- incident response
- finance reconciliation
- compliance review
- evidence archiving

## 8. Evidence Collection

Each pilot cycle should generate an evidence package with:

| Area | Evidence |
| --- | --- |
| Governance | four-gate validation report |
| Runtime | runtime-boundary validation report |
| Trust | replay verification report |
| Operations | health dashboard snapshot |
| NovaRide | ride completion and dispatch metrics |
| NovaPay | transaction success and settlement metrics |
| Finance | reconciliation report |
| Compliance | AML / KYC review summary |
| Support | incident and resolution summary |
| Security | vulnerability review summary |

### Evidence separation

Repository evidence and operational evidence are related but distinct:

| Category | Evidence |
| --- | --- |
| Repository evidence | CI validation, architecture validation, tests, documentation validation |
| Operational evidence | Pilot metrics, monitoring, support outcomes, finance reconciliation, compliance reviews, operational incidents |

## 9. Pilot Decision Matrix

Operators should use the following matrix when deciding how to proceed at the
end of a pilot cycle or after a material incident:

| Pilot outcome | Required action | Approval |
| --- | --- | --- |
| All KPIs achieved, no critical incidents | Promote to Operational Readiness review | Pilot Manager + Operations Lead |
| KPIs achieved with minor issues | Continue pilot with corrective actions | Pilot Manager |
| KPIs partially achieved | Extend pilot for another cycle | Governance Board |
| Critical defect affecting safety, payments, identity, or trust | Pause affected workflows until resolved | Operations Lead + Governance |
| Governance validation fails | Suspend pilot immediately | Governance Authority |
| External dependency unavailable (payment provider, push service, maps, etc.) | Continue unaffected scenarios or suspend impacted workflows | Operations Lead |

## 10. Pilot Completion Report

Every pilot cycle should end with a standardized completion report.

Suggested structure:

```text
Pilot ID
Pilot Name
Cycle Number
Start Date
End Date

Participants
-----------
Drivers
Riders
Consumers
Merchants
Agents

KPIs
----
Ride completion
Transaction success
Settlement success
Support SLA
Compliance SLA

Governance
----------
Four-gate validation
Runtime validation
Replay validation
Security review

Operational Summary
-------------------
Incidents
Corrective actions
Known risks

Recommendation
--------------
Continue Pilot
Extend Pilot
Promote to Operational Readiness
Stop Pilot

Approvals
---------
Pilot Manager
Operations Lead
Compliance Lead
Engineering Lead
```

## 11. Exit Gates

### From Controlled Pilot Ready to Operationally Ready

Promotion requires:

- pilot KPIs consistently achieved
- no unresolved critical defects
- governance validation continues to pass
- operational documentation complete
- production readiness requirements satisfied
- operational approval recorded

### From Operationally Ready to Commercial Launch

Promotion requires:

- production credentials provisioned
- live provider onboarding completed
- monitoring and disaster recovery verified
- app store / Play Console approvals completed
- executive go-live approval recorded

## 12. Current Classification

| Domain | Status |
| --- | --- |
| Architecture | Complete |
| Implementation | Complete |
| Governance | Complete |
| Trust | Complete |
| Portal ecosystem | Complete |
| Documentation | Complete |
| Controlled pilot | Ready |
| Operational readiness | External activation required |
| Commercial launch | Pending operational approvals |

## 13. Notes

The repository evidence referenced by this program is the implementation and
validation work in source control. Operational evidence is produced by the live
environment during pilot execution.

The transcript that informed this document noted that a full repository-wide
`pytest -q` run was still in progress at the time of capture. This document does
not claim that unconfirmed regression state as completed evidence.
