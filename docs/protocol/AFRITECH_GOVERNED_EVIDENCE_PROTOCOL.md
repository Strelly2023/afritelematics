# AfriTech Governed Evidence Protocol

The governed evidence protocol is the public contract that combines the
architecture anchor platform, evidence lifecycle semantics, governance
artifacts, and CI enforcement into one verifiable system.

## Classification

```text
GOVERNED_EVIDENCE_OPERATING_PROTOCOL
```

## Public Packet

```http
GET /public/architecture/evidence/protocol
```

The packet exposes:

- `protocol_version`
- `protocol_hash`
- `semantics_hash`
- `policy_hash`
- governance artifact hashes
- required validator list
- public evidence surfaces
- authority model

## Canonical Stack

```text
ADR
    -> RULE
    -> BIND
    -> Proof
    -> Blockchain Publication
    -> WebSocket Observation
    -> Anchor Index
    -> Cross-Network Reconciliation
    -> Evidence Policy
    -> Operational Semantics
    -> Mainnet Promotion Gate
    -> Explorer / Public Verification
```

## Authority Boundary

```text
Replay/Proof remains authority.
Blockchain remains publication evidence.
```

The protocol defines evidence behavior and integration rules. It does not
redefine truth, replay, proof, dispatch, settlement, or governance authority.

## Required Governance

- `ADR-0047`
- `RULE-067`
- `BIND-045`

## Required Validators

- `afritech.ci.afritech_blockchain_anchor_validator`
- `afritech.ci.afritech_blockchain_anchor_realtime_validator`
- `afritech.ci.afritech_governed_evidence_protocol_validator`

## Required Public Surfaces

- `/public/architecture/evidence/protocol`
- `/public/architecture/evidence/semantics`
- `/public/architecture/evidence/policy`
- `/public/architecture/anchors/reconciliation`
- `/public/architecture/anchors/reconciliation/resolution`
- `/public/architecture/anchors/stream/ws`
- `/public/architecture/anchors/stream/replay`
- `/public/architecture/anchors/mainnet-promotion-gate`
- `/public/architecture/anchors/explorer`
- `/public/architecture/adr/{adr_id}/contract-link`

## Failure Rule

```text
Missing protocol capability or governance artifact -> CI FAIL
```
