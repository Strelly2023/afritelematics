# NovaTech Production Trust Node Runbook

Status: PRODUCTION TRUST NODE OPERATIONS
Classification: LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE_DEPLOYMENT

Purpose: deploy a real public trust infrastructure node with Nginx, HTTPS,
external verification surfaces, live-anchor capability, and the operator trust
dashboard.

This runbook does not claim that production operation, government approval, or
mainnet publication has occurred. Those states require the execution logs,
chain receipts, and access records produced by the commands below.

## 1. Production Server

Prerequisites:

- Ubuntu host with Docker Engine and Docker Compose v2
- DNS `A` record for `AFRITECH_DOMAIN` pointing at the host
- ports `80/tcp` and `443/tcp` reachable
- funded chain wallet for live anchoring
- deployed anchor contract address

Create the trust-node environment:

```bash
cp deploy/production/.env.production.trust-node.example \
  deploy/production/.env.production.trust-node
```

Replace every placeholder in `deploy/production/.env.production.trust-node`.
Place private key material under `deploy/production/secrets/`:

```text
deploy/production/secrets/eth_private_key
deploy/production/secrets/afritech_private_key.pem
deploy/production/secrets/afritech_public_key.pem
```

Launch the production node:

```bash
./scripts/setup_production_trust_node.sh --issue-cert --apply-firewall
```

If Certbot reports `Certificate not yet due for renewal` but curl still shows
the temporary self-signed bootstrap certificate, repoint Nginx to the existing
valid Let's Encrypt lineage:

```bash
./scripts/setup_production_trust_node.sh --repair-cert
```

One-command go-live and anchor flow:

```bash
./scripts/go_live_anchor_now.sh --profile sepolia
```

This command verifies DNS, rejects placeholder secrets, deploys the HTTPS trust
node, opens ecosystem access, launches the dashboard, publishes a live anchor,
persists the live receipt, and re-runs public probes.

This starts:

- `afritech-api`
- `afritech-dashboard`
- `nginx`
- Let's Encrypt certificate issuance through `certbot` HTTP-01 challenge

The `nginx` service above is the Docker Compose service
`production-nginx-1`. Do not run `sudo systemctl restart nginx` after this
stack is healthy. A host-level `nginx.service` will try to bind the same
`80/tcp` and `443/tcp` ports and can fail even when the production trust node is
serving correctly.

If the host `nginx.service` was installed earlier, keep Docker Compose as the
edge and stop the host service:

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
docker compose --env-file deploy/production/.env.production.trust-node \
  -f deploy/production/docker-compose.trust-node.yml \
  exec -T nginx nginx -t
docker compose --env-file deploy/production/.env.production.trust-node \
  -f deploy/production/docker-compose.trust-node.yml \
  exec -T nginx nginx -s reload
```

## 2. Live Anchoring

Before publishing a real chain receipt:

```bash
COMPOSE_FILE=deploy/production/docker-compose.trust-node.yml \
ENV_FILE=deploy/production/.env.production.trust-node \
./scripts/check_chain_ready.sh
```

Publish a live Level 16 ecosystem anchor:

```bash
./scripts/enable_live_anchoring.sh sepolia
```

The script persists the live receipt to:

```text
AFRITECH_ECOSYSTEM_LIVE_RECEIPT_FILE
```

The public `/public/ecosystem-evolution/verify` route then reports
`LIVE_PUBLIC_LEDGER_ANCHORED` when the receipt is present and valid.

For Base Sepolia or Mainnet, change the profile only after the relevant RPC,
wallet, contract, and deployment-block settings are complete.

The live anchor proves public publication of the exported trust artifact. It
does not create runtime truth or production authorization.

## 3. ArchitectureAnchor V2 Rollout

Keep `ArchitectureAnchor.sol` deployed and readable during the full migration.
V2 is a separate contract used for bytes32 anchor IDs, context tagging, and
batch anchoring:

```text
afritech/contracts/ArchitectureAnchor.sol    # V1, live compatibility contract
afritech/contracts/ArchitectureAnchorV2.sol  # V2, opt-in scale contract
```

Configure both addresses during the parallel phase:

```bash
AFRITECH_CHAIN_CONTRACT_ADDRESS=0x...      # V1
AFRITECH_CHAIN_CONTRACT_ADDRESS_V2=0x...   # V2
AFRITECH_CHAIN_ANCHOR_VERSION=v1           # default until V2 acceptance
AFRITECH_CHAIN_V2_MAX_BATCH_SIZE=50
AFRITECH_CHAIN_V2_ENFORCE_UNIQUE_PROOF=true
```

Rollout phases:

```text
Phase 1: V1 only
Phase 2: V1 reads + V2 test writes in staging
Phase 3: V2 default writes with V1 still indexed
Phase 4: V1 read-only archival compatibility
```

The event subscriber indexes both events when both addresses are configured:

```text
ProofAnchored(string,bytes32,address,uint256)            # V1
ProofAnchored(bytes32,bytes32,address,uint256,bytes32)   # V2
```

For web-scale anchoring, enqueue proof items and flush bounded V2 batches. Keep
batch size conservative until gas telemetry proves headroom:

```python
from afritech.chain.anchor_batch_queue import DEFAULT_ANCHOR_BATCH_QUEUE

DEFAULT_ANCHOR_BATCH_QUEUE.enqueue("ride-001", proof_hash, "RIDE")
DEFAULT_ANCHOR_BATCH_QUEUE.flush(profile_name="sepolia")
```

If a batch fails, the in-process queue requeues the drained batch at the front.
Production workers should record failed anchor IDs, retry the batch, then fall
back to single-anchor publication only for the failing item set.

## 4. Open Ecosystem Access

After the node is reachable:

```bash
./scripts/open_ecosystem_access.sh https://trust.afritech.example
```

Share these read-only endpoints with partners and government observers:

```text
/public/feature-registry
/public/feature-registry/verify
/public/trust-infrastructure
/public/trust-infrastructure/verify
/public/global-verification
/public/global-verification/verify
/public/ecosystem-evolution
/public/ecosystem-evolution/verify
/public/ecosystem-evolution/standard
/public/ecosystem-evolution/portal
```

Partner onboarding starts from:

```text
docs/partners/AFRITECH_LIVE_ECOSYSTEM_ONBOARDING.md
docs/partners/AFRITECH_EXTERNAL_VERIFIER_CLI_PACKAGE.md
```

## 5. Launch Dashboard

Launch or refresh the operator trust dashboard:

```bash
./scripts/launch_trust_dashboard.sh
```

Dashboard entrypoints:

```text
/
/public/feature-registry/portal
/public/global-verification/portal
/public/ecosystem-evolution/portal
```

## 6. Healthcheck Optimization

If Docker marks `production-afritech-api-1` unhealthy while HTTPS routes are
still returning successful responses, inspect the container health log before
rebuilding:

```bash
docker compose -f deploy/production/docker-compose.trust-node.yml ps
docker compose -f deploy/production/docker-compose.trust-node.yml logs --tail=200 afritech-api
docker inspect --format='{{json .State.Health}}' production-afritech-api-1
```

The production trust-node compose file intentionally uses one Uvicorn worker on
small EC2 hosts:

```yaml
--workers
- "1"
```

This keeps startup overhead and worker churn aligned with the available CPU and
memory. Increase the worker count only after confirming the host has enough
headroom under production load.

The API healthcheck uses the same lightweight HTTP readiness path as external
monitoring, with a timeout that absorbs cold-start scheduling latency:

```yaml
healthcheck:
  test: ["CMD", "curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8000/health"]
  interval: 15s
  timeout: 12s
  retries: 5
  start_period: 30s
```

This avoids false-negative Docker health failures when the app is serving
requests but a probe lands during startup or temporary CPU contention. Verify
both the internal container readiness path and the public edge route:

```bash
docker compose -f deploy/production/docker-compose.trust-node.yml \
  exec -T afritech-api curl -fsS http://127.0.0.1:8000/health
curl -fsS https://api.trust.afritech.example/health
curl -fsS https://trust.afritech.example/public/ecosystem-evolution/verify
```

## Required Verification

Run after deployment:

```bash
./scripts/run_local_production_probe.sh https://trust.afritech.example
curl -I https://trust.afritech.example
curl -I https://app.trust.afritech.example
curl -I https://api.trust.afritech.example/health
curl -I https://verify.trust.afritech.example/public/architecture/proof
python3 -m afritech.cli.main verify --registry --json
python3 -m afritech.cli.main verify --global --json
python3 -m afritech.cli.main verify --ecosystem --json
```

End-to-end go-live verification:

```bash
./scripts/go_live_anchor_now.sh --profile sepolia
```

## Authority Boundary

- Nginx routes traffic only.
- HTTPS proves transport security only.
- public ledger anchors prove publication only.
- Dashboard observes trust surfaces only.
- Replay, evidence, signatures, quorum, and exported verification bundles remain
  the source of truth.
