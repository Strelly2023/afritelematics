# Protocol Definition

AfriTech is a Sovereign Distributed Execution Ledger Protocol.

## Protocol Object Model

- Node: network participant capable of receiving messages and producing proofs
- Contract: registered function referenced by `fn_id`
- Proof: signed execution result
- Vote: proof-derived consensus decision
- Block: committed batch of accepted proofs
- State: deterministic projection over ledger blocks

## Core Invariant

Only consensus-accepted proof batches may be committed to the execution ledger.
