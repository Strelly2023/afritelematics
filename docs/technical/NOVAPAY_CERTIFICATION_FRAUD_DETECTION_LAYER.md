# NovaPay Certification and Fraud Detection Layer

Status: design bound to deterministic implementation

NovaPay certification and fraud detection is a projection-only control layer for financial operations. It evaluates identity binding, tenant alignment, role scope, ownership, compliance, fraud signals, trust score, and proof coverage before a payment is certified for execution or review.

## 1. Authority Boundary

The layer never mutates ledger, wallet, route, provider, settlement, or treasury state.

It may emit:
- fraud assessment evidence
- certification evidence
- review recommendations
- audit-ready hashes
- regulator reporting fields

It may not emit:
- ledger entries
- settlement confirmation
- provider callback truth
- payment success state
- treasury reservation state

## 2. Execution Flow

Request -> NovaID -> tenant binding -> RBAC scope -> resource guard -> fraud assessment -> certification evidence -> NovaPower authorization -> payment execution -> NovaTrust proof

Certification is an input to execution control. It is not financial truth.

## 3. Fraud Signal Model

Fraud scoring is deterministic and replayable.

Required signal classes:
- identity binding failure
- tenant mismatch
- invalid payment scope
- resource ownership mismatch
- large amount
- repeated payee velocity
- large offline payment
- KYC or AML review requirement
- party risk score escalation
- trust score degradation
- proof coverage degradation

Fraud levels:
- LOW: score below 0.30
- MEDIUM: score from 0.30 to below 0.60
- HIGH: score from 0.60 to below 0.85
- CRITICAL: score from 0.85 and above

## 4. Fail-Closed Rules

The assessment must return blocked when any of these are false:
- tenant_aligned
- identity_bound
- scope_valid
- resource_owner_valid

The assessment must also block:
- CRITICAL fraud score
- high party risk from compliance controls

The assessment must return review when:
- HIGH fraud score is present
- trust_score is below 70
- proof_coverage is below 75
- compliance requires manual review but does not block

## 5. Certification Tiers

NOVAPAY_CERTIFIED:
- decision is allowed
- trust_score is at least 85
- proof_coverage is at least 90
- fraud_score is below 0.30

NOVAPAY_REVIEW_CONTROLLED:
- decision is not blocked
- trust_score is at least 70
- proof_coverage is at least 75
- manual review or controlled execution may be required

NOVAPAY_PROVISIONAL:
- decision is not blocked
- evidence is incomplete or trust/proof coverage is below certification target
- execution requires explicit NovaPower escalation

NOVAPAY_BLOCKED:
- tenant, identity, scope, ownership, critical fraud, or high party risk failed
- execution is forbidden

## 6. Certification Evidence Contract

Every certification record must include:
- certification_id
- organization_id
- transaction_reference
- tier
- status
- issuer_role
- assessment_hash
- certification_hash
- controls.identity_bound
- controls.tenant_aligned
- controls.scope_valid
- controls.ownership_valid
- controls.fraud_reviewed
- controls.proof_ready

The hash must be canonical and deterministic.

## 7. NovaPower Gate

NovaPower may authorize payment execution only when:
- assessment decision is allowed, or controlled review has explicitly approved review
- certification tier is not NOVAPAY_BLOCKED
- issuer authority is explicit
- identity and tenant controls are true
- fraud evidence is attached to the audit chain

High-value payments should add:
- minimum trust_score of 80
- multi-approval
- explicit reviewer identity
- anomaly note
- regulator export flag when required

## 8. NovaTrust Audit Binding

NovaTrust must preserve:
- assessment_hash
- certification_hash
- actor identity
- organization identity
- fraud reasons
- certification tier
- proof coverage
- trust score

This creates a replayable evidence trail for auditors, regulators, partners, and internal incident review.

## 9. Implementation Binding

The deterministic implementation lives in:

- `afritech/afripay/certification_fraud.py`

The implementation is intentionally framework-neutral so it can be used from Django, FastAPI, Celery, regulator exports, or offline audit replay.

## 10. System Guarantee

No NovaPay certification may be issued as clean when identity, tenant, scope, or ownership controls fail.

No NovaPay certification may define financial truth.

No NovaPay certification may bypass NovaPower execution authority.

No NovaPay fraud decision may be non-deterministic.
