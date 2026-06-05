# Execution Model

Execution is deterministic and admission-controlled.

## Components

- `RuntimeEngine`
- `ExecutionKernel`
- `ExecutionContext`
- `ZeroTrustNode`

## Contract Model

Contracts are registered functions referenced by `fn_id`. The `fn_id` is carried into proof metadata as `contract_id`.

## Audit

Each execution records deterministic result hashes. Consensus-accepted proofs may be committed as ledger blocks.
