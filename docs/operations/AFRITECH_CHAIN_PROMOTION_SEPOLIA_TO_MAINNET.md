# AfriTech Chain Promotion: Sepolia to Mainnet

Status: GA ELITE ROLLOUT RUNBOOK

Purpose: move public anchor publication from first live validation on Sepolia to
Mainnet without changing the authority boundary.

## Boundary Reminder

Blockchain publication proves public publication only.

Replay and governed execution remain truth authority.

## Profiles

- `sepolia`
  - first live partner verification sessions
  - low-risk RPC and explorer validation
  - expected next step after successful session: `promote_to_mainnet`
- `mainnet`
  - production immutable publication
  - requires confirmed Sepolia session evidence
  - requires operator sign-off and secret rotation review

## Environment Variables

- `AFRITECH_CHAIN_PROFILE`
- `AFRITECH_CHAIN_MODE=sepolia`
- `AFRITECH_CHAIN_ENABLE_PUBLISH=true`
- `AFRITECH_CHAIN_RPC_URL_SEPOLIA`
- `AFRITECH_CHAIN_RPC_URL_MAINNET`
- `AFRITECH_CHAIN_CONTRACT_ADDRESS`
- `AFRITECH_CHAIN_ADDRESS`
- `AFRITECH_CHAIN_PRIVATE_KEY`
- `AFRITECH_CHAIN_GAS_PRICE_GWEI`
- `AFRITECH_CHAIN_TX_TIMEOUT`

Do not commit private keys or RPC credentials. Provide them through the deployment
secret manager or host-level environment.

`AFRITECH_CHAIN_AUTO_PUBLISH_ON_PROOF=true` is available for controlled demos
that need `/public/architecture/proof` to attach a live receipt. Leave it unset
for normal production operation so public GET requests remain read-only.

## Promotion Sequence

1. deploy `afritech/contracts/ArchitectureAnchor.sol` to Sepolia
2. set `AFRITECH_CHAIN_CONTRACT_ADDRESS` to the deployed contract address
3. publish to Sepolia through `/v1/architecture/anchor/blockchain`
   with an authenticated operator or verifier token:

```json
{
  "profile": "sepolia",
  "mode": "contract"
}
```

The response must include:

- `publication.anchor_mode = smart_contract`
- `publication.method = anchorProof`
- `publication.network = sepolia`
- `publication.transaction_hash` beginning with `0x`

4. verify with `afritech-verify --base-url <url> --expect-network sepolia`
5. run `afritech-verify-session --base-url <url> --partner <name>`
6. archive the partner session report
7. confirm no dashboard drift and no verification mismatch
8. switch profile to Mainnet
9. publish Mainnet anchor
10. rerun verifier and session tools against Mainnet expectation

## Exit Criteria

- proof verification remains `VERIFIED`
- chain receipt network matches expected profile
- public trust dashboard remains `READY`
- partner session outcome is `PASSED`
