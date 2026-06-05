# Consensus

The consensus layer accepts proof batches and selects the result hash with quorum.

## Components

- `ProofConsensusEngine`
- `QuorumPolicy`
- `ProofValidator`
- `ProofAggregator`
- `Vote`

## Default Quorum

Default mode is majority:

```text
required_votes = floor(total_nodes / 2) + 1
```

## Finalization

`finalize(proofs)` returns:

```text
(accepted_value, accepted_proofs)
```

If consensus fails, it returns:

```text
(None, [])
```
