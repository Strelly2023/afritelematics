# Ledger Model

## ExecutionBlock

Each block contains:

- `index`
- `prev_hash`
- `proofs`
- `timestamp`
- `hash`

## Properties

- Immutable
- Verifiable
- Deterministic
- Append-only in normal operation

## Chain Integrity

`verify_chain()` checks:

- index continuity
- previous hash linkage
- block hash recomputation

## State Boundary

The ledger stores history. State is derived by replaying blocks through reducers.
