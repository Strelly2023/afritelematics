# ADR-402: Adversarial Integrity Layer

STATUS: IMPLEMENTED EVIDENCE SLICE

## Decision

AfriRide admits mutation candidates only after deterministic security
enforcement:

```text
AUTHENTICITY
-> STRUCTURE
-> LINEAGE
-> ADMISSIBILITY
```

Any failure rejects before mutation eligibility.

## Implemented Surface

```text
afritech.security.event_authenticator
afritech.security.mutation_guard
afritech.security.adversarial_engine
afritech.security.integrity_trace
afritech.ci.security_integrity_validator
```

## Proven In This Slice

```text
invalid signatures are rejected
payload tampering after signing is rejected
timestamp tampering after signing is rejected
nested witness/replay authority injection is rejected
untrusted lineage is rejected
duplicate replay mutation attempts are rejected
admitted events receive stable integrity hashes
admitted events emit authenticity -> structure -> lineage -> admissibility traces
```

## Non-Claims

This ADR does not claim production key custody, external identity proofing,
hardware-backed signing, universal fraud detection, or complete attack-space
exhaustiveness.

It proves an executable, deterministic integrity gate for mutation candidates
before they become eligible to mutate state.
