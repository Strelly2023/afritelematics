# State Machine

State is derived from the ledger using reducers.

## Components

- reducer registry
- `contract_id` mapping
- `replay()`
- `replay_ledger()`

## Canonical Transition Rule

A block may contain many validator proofs for the same result. State applies one canonical transition per `(contract_id, result_hash)` while preserving all proofs in the ledger.

## Guarantee

State is deterministic and reproducible from the ledger.
