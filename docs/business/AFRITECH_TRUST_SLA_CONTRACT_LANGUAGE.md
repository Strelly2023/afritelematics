# AfriTech Trust SLA Contract Language

Status: TRUST SLA CONTRACT LANGUAGE
Classification: COMMERCIAL_AND_LEGAL_RUNTIME_BOUNDARY_SURFACE

Purpose: define bounded contract language for commercial use of the trust SLA
surface exposed by the AfriRide runtime.

This document is a contract-language support surface.
It is not legal advice and is not a signed contract.

## Clause Goal

Translate runtime trust observability into commercial language without claiming
that contractual wording replaces replay, evidence, or receipt proof.

## Recommended Clause

```text
AfriTech will make available a trust-state surface that reports current
trust_score, replay failure count, hash-chain failure count, guard violation
count, and current SLA status through a bounded runtime interface.

The trust-state surface is an operational reporting layer. It explains current
system health and threshold adherence. It does not replace the replay-backed
evidence, signed receipt, or verification packet surfaces that remain the
authority for post-event verification.
```

## SLA Status Language

Recommended operational states:

- `GREEN`: trust score meets the highest declared threshold and no replay or hash-chain failures are present
- `WATCH`: trust score is below the highest threshold but above the minimum review threshold
- `BREACH`: trust score falls below the minimum review threshold or a critical integrity condition is open

## Service Language

Recommended support wording:

```text
AfriTech will notify the Partner of runtime trust-state degradation visible
through the trust SLA surface and will review replay, evidence, and guard
signals during the agreed support window.
```

## Exclusion Language

Recommended exclusion wording:

```text
SLA status is an operational threshold surface only.
It does not certify legal outcome, business outcome, or universal system
correctness outside the bounded replay-backed workflow.
```

## Mandatory Boundary

Any commercial agreement using trust SLA language must preserve:

- replay remains truth authority
- signed receipt remains the portable proof artifact
- external verification remains bounded evidence exchange
- SLA explains threshold adherence only

