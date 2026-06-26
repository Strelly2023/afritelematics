# NovaReplay / NovaTrust RFC v1.0

Status: Draft

## Abstract

NovaReplay defines a deterministic replay model for mobility and operational event streams. NovaTrust defines the canonical receipt and projection envelope used to verify replay, render UI, and export portable proofs.

The core contract is simple:

`UI = render(canonical_state)`

`canonical_state = replay(canonical_events)`

If two clients receive the same canonical input, they must produce the same replay state, the same proof output, and the same UI hash.

## Goals

- deterministic replay across runtimes
- canonical serialization with no locale-dependent behavior
- portable proof receipts
- privacy-preserving ZK receipt bundles
- stateless mobile verification
- cross-chain light-client anchoring

## Non-goals

- market pricing logic
- dispatch authority
- mutable trust overrides
- non-deterministic UI projections

## Terminology

- Canonical state: the normalized, ordered, deep-canonicalized representation of a replay or receipt.
- Replay event: a signed or emitted event that can affect replay state.
- Proof receipt: a canonical receipt containing hashes, commitments, and verification metadata.
- ZK receipt: a privacy-preserving receipt bundle with hidden fields committed into a proof artifact.
- UI hash: the stable hash of the rendered projection state.

## Core invariants

1. Canonicalization is deterministic.
2. Replay is pure and side-effect free.
3. UI rendering is a pure function of canonical state.
4. Hashes are domain-separated.
5. Hidden fields are never required for proof verification unless explicitly provided as expected input.

## Canonicalization rules

- sort object keys recursively
- preserve list order unless the list is explicitly defined as a set at construction time
- normalize `undefined` to `null`
- reject ambiguous timestamps
- do not use locale-sensitive comparison
- do not use time-dependent logic inside render paths

## Replay envelope

The replay envelope contains:

- `events`: ordered event stream
- `replay_hash`: optional authoritative replay hash
- `event_count`: optional event count
- `failures`: optional failure count
- `confidence`: optional confidence value

The replay engine must accept alternate shapes only when they can be canonically mapped to the same ordered event stream.

## Deterministic UI projection

The renderer may compute:

- `checkpointLabel`
- `asOf`
- `status`
- `tone`
- `timeline`
- `snapshotHash`
- `uiHash`

These outputs must be stable under:

- event array reordering
- nested object key reordering
- equivalent timestamp formats after canonical normalization

## Proof receipts

Proof receipts are portable canonical artifacts with:

- `receipt_hash`
- `seal_hash`
- `consensus_root`
- `validator_root`
- `aggregate_signature`
- `signer_set_hash`
- `violations_hash`
- `signature_threshold`

When a threshold BLS scheme is used, verification requires:

1. signer set hash to match
2. proof-of-possession to be valid for each signer
3. aggregate signature to validate against the signer set and message root

## ZK receipt bundles

ZK bundles provide privacy-preserving transport of verification data.

Typical fields:

- `proof`
- `proof_hash`
- `commitment`
- `public_inputs`
- `redacted_receipt`
- `hidden_fields`

The public inputs should include, at minimum:

- receipt hash
- issued-at timestamp
- chain identifier when cross-chain anchoring is present

## QR envelopes

QR payloads are transport envelopes, not trust sources.

Rules:

- the QR hash must bind the full wrapper except `qr_hash`
- QR decode must fail closed on malformed base64, compression, UTF-8, JSON, or structure errors
- QR timestamps must be explicit UTC timestamps and must satisfy `0 <= age <= MAX_QR_AGE_SECONDS`

## Stateless verification

Stateless verification is the process of validating a QR payload, proof receipt, and optional ZK bundle without requiring network access.

Required checks:

- QR integrity
- receipt integrity
- proof receipt validity
- ZK proof validity when present
- TTL validity

## Cross-chain light-client anchoring

Cross-chain support is modeled as an optional bridge object containing:

- target chain identifier
- light-client state
- validator-set commitment
- bridge hash

The bridge does not grant execution authority; it only anchors verification data.

## Mobile UX contract

The mobile client must render:

- proof mode
- replay mode
- privacy mode
- trust score
- hashes
- hidden fields summary
- timeline

The UI must be deterministic for a given canonical state.

## Security considerations

- Do not rely on locale-dependent string comparison.
- Do not reconstruct canonical structures from partial field subsets when verifying future-compatible payloads.
- Do not silently accept malformed timestamps or payload structures.
- Do not treat missing proof material as verified state.

## Compatibility

This RFC is compatible with:

- the current deterministic renderer implementation
- portable proof receipt generation
- privacy-preserving QR bundles
- threshold BLS verification
- stateless mobile verification

