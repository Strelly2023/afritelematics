# Data Flow

## Execution Data Path

```text
fn_id + args
  -> P2P message
  -> deterministic execution
  -> signed proof
  -> consensus aggregation
  -> committed execution block
  -> ledger-derived state
```

## Proof Data

Proofs include:

- `node`
- `result`
- `hash`
- `signature`
- `metadata.contract_id`
- `metadata.epoch`

After block commit, proof copies also include `block_index`.

## State Data

State is not written directly. It is replayed from blocks using reducers keyed by `contract_id`.
