# AFRIID Unified Mobility Participant Model

STATUS: FUTURE GOVERNED SPECIFICATION
CLASSIFICATION: ISOLATED PRODUCT ARCHITECTURE SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines the Gen-3 AfriID participant model as a governed specification surface. It does not claim deployment, operational legitimacy, or truth authority.

AfriID is a reference identity layer. It may support verification and continuity, but it does not redefine replay truth, proof truth, payment truth, or runtime authority.

## Related Governance

- ADR: `ADR-0024`
- Rule: `RULE-044`
- Binding: `BIND-022`

## Purpose

AfriID provides a unified mobility participant model for the Gen-3 mobility stack.

```text
one participant
multiple operational roles
bounded identity authority
replay-linked evidence
```

## Participant Model

```text
MobilityParticipant:
  participant_id
  display_name
  roles
  verification_status
  trust_score
  evidence_links
  metadata
```

### Allowed Roles

- rider
- driver
- courier
- merchant
- fleet
- institution

### Verification States

- unverified
- pending
- verified
- suspended

## Core Invariants

### INV-ID-001

```text
a participant may hold multiple operational roles
```

### INV-ID-002

```text
identity is reference-only and never truth authority
```

### INV-ID-003

```text
roles and evidence links must be deterministic and replay-stable
```

### INV-ID-004

```text
trust score may influence operational selection but cannot override proof or replay
```

## Authority Boundary

AfriID may answer:

- who is the participant
- which roles are declared
- what verification state is recorded
- which evidence links are associated

AfriID may not answer:

- what is replay truth
- what is proof truth
- what is payment truth
- what is runtime admissibility

## Downstream Use

AfriID may feed:

- trust-aware dispatch
- fleet federation
- support workflows
- settlement references
- evidence bundles

It must remain externally isolated from constitutional truth.

## Replay Requirement

Identity operations must be replay-stable.

If a participant model cannot be deterministically reconstructed, it is not admissible as a governed participant surface.

## Implementation Expectations

The implementation should provide:

- immutable participant objects
- canonical serialization
- strict role validation
- explicit authority boundary markers
- evidence link normalization
- validator-safe tests

