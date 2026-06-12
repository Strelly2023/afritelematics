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

1. In Remix, switch `Environment` from `Remix VM` to `Injected Provider - MetaMask`.
2. In MetaMask, select `Sepolia` and confirm the publishing wallet. For the
   current EC2 configuration this is expected to be:

```text
0x544CbDC41ce28b5758ee64217c4D4836Ef9b2825
```

3. Fund the wallet with enough Sepolia ETH for deployment and one anchor
   transaction.
4. Deploy `afritech/contracts/ArchitectureAnchor.sol` to Sepolia.

Deployment to Remix VM is local and temporary. Do not copy a Remix VM contract
address into production; the backend can only use a contract deployed to the
configured public network.

5. Copy the deployed Sepolia `ArchitectureAnchor` contract address.
6. On EC2, edit `deploy/production/.env.production`:

```env
AFRITECH_CHAIN_MODE=sepolia
AFRITECH_CHAIN_NETWORK=sepolia
AFRITECH_CHAIN_RPC_URL_SEPOLIA=<provider Sepolia RPC URL>
AFRITECH_CHAIN_ADDRESS_CHECKSUM=0x544CbDC41ce28b5758ee64217c4D4836Ef9b2825
AFRITECH_CHAIN_PRIVATE_KEY_PATH=/run/secrets/eth_private_key
AFRITECH_CHAIN_CONTRACT_ADDRESS=<deployed Sepolia ArchitectureAnchor address>
AFRITECH_CHAIN_ENABLE_PUBLISH=true
```

`AFRITECH_CHAIN_CONTRACT_ADDRESS` must not be
`0x1234567890ABCDEF1234567890ABCDEF12345678` or the zero address. Contract mode
rejects placeholders before submitting a transaction.

7. Recreate the API container:

```bash
docker compose -f deploy/production/docker-compose.production.yml up -d --force-recreate afritech-api
```

8. Verify the live container configuration:

```bash
docker exec -it production-afritech-api-1 printenv | grep AFRITECH_CHAIN
```

9. Publish to Sepolia through `/v1/architecture/anchor/blockchain`
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
- `publication.status = live`

10. verify with `afritech-verify --base-url <url> --expect-network sepolia`
11. run `afritech-verify-session --base-url <url> --partner <name>`
12. archive the partner session report
13. confirm no dashboard drift and no verification mismatch
14. switch profile to Mainnet
15. publish Mainnet anchor
16. rerun verifier and session tools against Mainnet expectation

## Exit Criteria

- proof verification remains `VERIFIED`
- chain receipt network matches expected profile
- public trust dashboard remains `READY`
- partner session outcome is `PASSED`
