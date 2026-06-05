# Trust Model

Trust is maintained per node.

## Components

- `TrustEngine`
- `TrustScoreRules`
- `SlashingEngine`
- `ReputationStore`
- `TrustFirewall`

## Events

- `valid_proof`
- `invalid_proof`
- `timeout`
- `consensus_match`
- `consensus_mismatch`

## Slashing

Scores are reduced for invalid proofs, timeout behavior, and consensus mismatch. Low-scoring peers may be blocked at the network firewall.
