# AfriCPPT Protocol Specification

Status: AFRICPPT PROTOCOL SPECIFICATION
Classification: EXTERNAL_INTEGRATION_PROTOCOL_SURFACE

Purpose: extract the AfriCPPT layer from the unified AfriTech architecture into
an external protocol surface that partners, regulators, and integrators can
implement against.

This protocol document is an integration surface.
It is not a transfer of truth authority.

## Extraction Source

This document is extracted from:

- `docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md`

The architecture explains how AfriCPPT fits into the larger system.
This protocol specifies how external systems may integrate with that layer.

## Protocol Role

AfriCPPT is the cross-platform proof protocol layer.

It standardizes:

- proof exchange standards
- external verification APIs
- multi-party validation
- federation / partner trust
- SDK / integration adapters

It does not standardize a second truth engine.

## External Integration Goal

External parties should be able to:

- receive replay-linked trust packets
- verify bounded evidence against published APIs
- inspect registry and network verification records
- consume anchored export integrity artifacts
- integrate the results into audit, compliance, claims, and mobility workflows

without gaining runtime mutation authority.

## Canonical Integration Objects

- trace hash
- replay hash
- evidence bundle
- receipt record
- anchor commitment
- registry publication record
- witness quorum record
- conformance profile
- dependent system declaration

## Integration Flows

### 1. Verification Request Flow

```text
partner request
-> verification API
-> replay-linked packet lookup
-> bounded verification result
-> partner decision workflow
```

### 2. Registry Publication Flow

```text
replay-backed packet
-> publication envelope
-> trust registry entry
-> external visibility
```

### 3. Network Verification Flow

```text
registry packet
-> witness participants
-> quorum review
-> verification network record
```

### 4. Audit Export Flow

```text
receipt + evidence + anchor
-> legal / audit export bundle
-> partner retention workflow
```

### 5. Dependency Declaration Flow

```text
external adopter
-> conformance profile lookup
-> dependency declaration
-> registry / network dependency visibility
```

## Required External Integration Rules

Rule 1. Replay remains truth authority.

Rule 2. External APIs may expose verification outcomes, but may not mutate trace
or replay truth.

Rule 3. Registry publication indexes evidence only.

Rule 4. Anchor commitments prove export integrity only.

Rule 5. SDK ergonomics may simplify transport, but may not reinterpret verdicts.

Rule 6. Multi-party verification may record verifier alignment, but may not
override replay.

Rule 7. External systems must treat verification packets as bounded evidence, not
as sovereign execution state.

Rule 8. Declared dependent systems may rely on protocol surfaces, but may not
reinterpret those surfaces as sovereign truth.

## Required Integration Surfaces

- `POST /v1/partner/verify`
- `GET /v1/partner/anchors/{anchor_id}`
- `GET /v1/trust/registry`
- `POST /v1/trust/registry/publish`
- `POST /v1/trust/network/verify`
- `GET /v1/trust/standards/profile`
- `POST /v1/trust/dependents/register`
- `GET /v1/trust/dependents`

## Authority Boundary

This protocol permits only this bounded claim:

```text
external systems can integrate with replay-linked proof, registry, and network
verification surfaces without becoming truth authority
```

It does not permit this claim:

```text
partner systems can define truth
registry publication certifies runtime state
SDK output replaces replay
```
