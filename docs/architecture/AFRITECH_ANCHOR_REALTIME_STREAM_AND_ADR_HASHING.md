# AfriTech Anchor Realtime Stream and ADR Hashing

AfriTech exposes a websocket-based anchor stream, cross-network reconciliation,
and governed ADR hashing as a read-only publication evidence layer.

## Architecture

```text
AfriTech API
    -> Anchor Stream Hub
    -> WebSocket clients
    -> Anchor index store
    -> Cross-network reconciliation
    -> ADR hashing helper
    -> ArchitectureAnchor contract
    -> Public explorer UI
```

## Authority boundary

```text
Constitution
    -> Deterministic Truth
    -> Replay
    -> Proof
```

The realtime anchor layer does not add authority. It only streams, indexes,
reconciles, and publishes evidence.

## Public surfaces

- `/public/architecture/anchors/stream/ws`
- `/public/architecture/anchors/stream/status`
- `/public/architecture/anchors/stream/replay`
- `/public/architecture/anchors/reconciliation`
- `/public/architecture/anchors/reconciliation/resolution`
- `/public/architecture/anchors/mainnet-promotion-gate`
- `/public/architecture/evidence/policy`
- `/public/architecture/evidence/semantics`
- `/public/architecture/evidence/protocol`
- `/public/architecture/anchors/explorer`
- `/public/architecture/adr/{adr_id}/hash`
- `/public/architecture/adr/{adr_id}/preview`
- `/public/architecture/adr/{adr_id}/contract-link`

## Stream replay

WebSocket is the primary real-time transport. Polling is retained only as an
operator-triggered backfill path for missed logs or deployment recovery.

Each broadcast event carries:

- `stream_sequence`
- `stream_event_id`
- `emitted_at_unix`

External explorers can reconnect and call
`/public/architecture/anchors/stream/replay?after_sequence=<n>` to recover
recent events without mutating the anchor index.

## Cross-network reconciliation

The anchor index preserves the same `anchor_id` across multiple networks by
keying observations with `anchor_id`, `network`, and transaction/publication
identity. Reconciliation groups by `proof_hash`, reports observed and missing
networks, and marks each group as `RECONCILED`, `PARTIAL`, `DIVERGENT`, or
`SINGLE_NETWORK`.

Formal invariants:

- observations with the same proof hash form one evidence set
- a reconciled evidence set must have one anchor identity
- a reconciled evidence set must not mix contract addresses
- mainnet promotion requires required pre-mainnet observations
- reconciliation never mutates chain state or claims truth authority

Conflict resolution:

- `RECONCILED`: no action required; promotion gates may evaluate
- `PARTIAL`: continue WebSocket observation and backfill missing networks
- `DIVERGENT`: freeze mainnet promotion, open governance review, and publish a
  resolution ADR before any superseding anchor
- `SINGLE_NETWORK`: insufficient distributed evidence for mainnet promotion

## Operational semantics

`/public/architecture/evidence/semantics` exposes the formal lifecycle states,
transition guards, terminal states, and authority boundaries as a stable
machine-readable packet. The packet is hashed as `semantics_hash` so an
operator or external verifier can detect changes to the evidence lifecycle.

Canonical flow:

```text
GOVERNED_DECISION
    -> PROOF_GENERATED
    -> PUBLISHED
    -> OBSERVED
    -> NORMALIZED
    -> RECONCILED
    -> POLICY_EVALUATED
    -> PROMOTION_GATED
    -> PUBLICLY_VERIFIABLE
```

The semantics packet preserves the platform rule that replay/proof remains
truth authority while blockchain, explorer, reconciliation, and promotion gates
remain evidence, visibility, analysis, or control surfaces.

## Governed evidence protocol

`/public/architecture/evidence/protocol` combines platform capabilities,
operational semantics, evidence policy, governance artifact hashes, public
surfaces, and required validators into one public protocol packet.

The packet includes:

- `protocol_hash`
- `semantics_hash`
- `policy_hash`
- `governance_artifacts`
- `required_validators`
- public surface map

This is the integration contract for external verifiers. It is still not truth
authority; it defines governed evidence behavior.

## Mainnet promotion gate

`/public/architecture/anchors/mainnet-promotion-gate` evaluates
reconciliation output before mainnet publication. The default required
pre-mainnet networks are `sepolia` and `base-sepolia`, configurable through
`AFRITECH_MAINNET_PROMOTION_REQUIRED_NETWORKS`.

Promotion is blocked when:

- no evidence has been observed
- any evidence set is `DIVERGENT`
- required pre-mainnet networks are missing
- WebSocket-first observation policy is not active

## ADR contract linking

ADR hash packets expose a contract-level link packet containing:

- ADR content hash as `bytes32`
- deterministic `anchor_id`
- `anchorProof(string,bytes32)` arguments
- `verifyAnchor(string,bytes32)` arguments
- target chain profile and contract metadata

## Governance

- `ADR-0046`
- `RULE-066`
- `BIND-044`

## Operator flow

1. Connect the explorer app to the websocket stream.
2. Inspect anchor status and cross-network reconciliation.
3. Preview an ADR hash and contract-link packet.
4. Anchor the ADR hash through the governed operator route if required.
5. Observe new publications as read-only stream events.
