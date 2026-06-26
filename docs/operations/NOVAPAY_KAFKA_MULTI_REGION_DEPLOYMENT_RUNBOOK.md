# NovaPay Kafka and AWS Multi-Region Deployment Runbook

## Scope

This runbook describes the operator path for deploying the Phase 5 to Phase 6
NovaPay stack:

- Kafka event bus in AWS
- multi-region NovaPay application nodes
- AWS KMS-backed signing in production
- first cross-border settlement flow
- distributed validator node posture

This document is operational guidance. It does not claim the infrastructure is
already deployed.

## 0. Current implementation boundary

The codebase already supports:

- deterministic settlement routing
- FX-aware payment normalization
- event bus abstraction with Kafka support
- optional KMS signing
- optional CBDC provider rail
- public verification and audit surfaces

The following are deployment tasks, not current guarantees:

- AWS MSK or Redpanda cluster in production
- multi-region replication
- validator quorum enforcement
- live cross-region failover

## 1. Recommended topology

### Primary region

- `ap-southeast-2` for Australian control-plane execution
- PayID and operator control surfaces
- primary signing and audit publishing

### Secondary region

- `af-south-1` or `me-south-1` for Africa-facing mobile money execution
- regional settlement workers
- validator / observer nodes

### Optional tertiary region

- `eu-central-1` for expansion, DR, or external auditor ingress

### Event backbone

- recommended: AWS MSK
- alternative: Redpanda on EC2 or Kubernetes

## 2. Step 1 - Deploy Kafka cluster

### Option A - AWS MSK

1. Create a dedicated VPC in each region.
2. Create private subnets in at least two availability zones per region.
3. Create security groups for:
   - brokers
   - application nodes
   - admin access
4. Enable encryption at rest with AWS KMS.
5. Enable in-transit encryption.
6. Deploy the MSK cluster in the primary region.
7. Deploy the regional consumer cluster or mirror cluster in the secondary
   region.
8. Define the topics:
   - `novapay.payment.executed`
   - `novapay.payment.settled`
   - `novapay.trust.created`
   - `novapay.audit.generated`
9. Set retention and compaction policy by topic class.
10. Expose bootstrap brokers only to trusted application subnets.

### Option B - Redpanda

1. Provision a Redpanda cluster per region.
2. Run the cluster on EC2 or Kubernetes with private networking.
3. Enable TLS and authentication.
4. Mirror the same NovaPay topics.
5. Use cluster linking or MirrorMaker-style replication for regional sync.

### NovaPay configuration

Set the event bus backend:

```bash
NOVAPAY_EVENT_BUS_BACKEND=kafka
NOVAPAY_EVENT_BUS_KAFKA_BROKERS=broker1:9092,broker2:9092
```

If Kafka is unreachable, the codebase falls back to the in-memory bus. Do not
use the fallback for production traffic.

## 3. Step 2 - Deploy multi-region NovaPay nodes

### Node roles

- gateway node: receives external traffic
- execution node: processes payment authorization and settlement
- trust node: verifies, imports, and publishes evidence
- observer node: reads events and builds audit surfaces

### Node placement

1. Deploy the gateway and execution node in the Australian region.
2. Deploy at least one trust node and one observer node in the Africa region.
3. Deploy an optional DR or auditor node in the tertiary region.
4. Keep database and event-bus access private to the VPC.
5. Keep public traffic limited to the gateway and trust explorer surfaces.

### Runtime environment

Each node must receive:

```bash
DATABASE_URL=postgresql://...
NOVAPAY_EVENT_BUS_BACKEND=kafka
NOVAPAY_EVENT_BUS_KAFKA_BROKERS=...
NOVATRUST_SIGNING_PROVIDER=aws_kms
NOVATRUST_KMS_SIGNING_ENABLED=true
NOVATRUST_KMS_KEY_ID=...
NOVATRUST_KMS_SIGNING_ALGORITHM=ECDSA_SHA_256
```

For cross-border mobile money pilots, also configure:

```bash
NOVAPAY_CBDC_LIVE_ENABLED=false
NOVAPAY_CBDC_NETWORK=pilot-ledger
```

### Health checks

Verify:

```bash
GET /v1/core-platform/readiness
GET /v1/core-platform/payments/providers/status
GET /v1/core-platform/payments/settlement/status
GET /v1/core-platform/trust/node/network/status
GET /v1/core-platform/signing/status
```

## 4. Step 3 - Enable KMS signing in production

### Provision the key

1. Create an AWS KMS key per environment.
2. Grant the application role permission to sign and verify.
3. Record the key id in the deployment secrets store.

### Enable runtime signing

```bash
NOVATRUST_SIGNING_PROVIDER=aws_kms
NOVATRUST_KMS_SIGNING_ENABLED=true
NOVATRUST_KMS_KEY_ID=<aws_kms_key_id>
NOVATRUST_KMS_SIGNING_ALGORITHM=ECDSA_SHA_256
```

### Verify

Check:

```bash
GET /v1/core-platform/signing/status
```

The status must indicate that KMS signing is active or configured and ready
for production use.

## 5. Step 4 - Launch the first cross-border flow

### AU -> KE example

Submit a payment intent with:

```json
{
  "intent_id": "phase6-au-ke-001",
  "amount": "25.00",
  "currency": "AUD",
  "destination": "merchant-ke-001",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "KE"
  }
}
```

Expected settlement behavior:

- source country: AU
- settlement country: KE
- source currency: AUD
- settlement currency: KES
- FX rate locked before execution
- route hint resolves to the mobile money rail

### BI -> CD example

Submit a payment intent with:

```json
{
  "intent_id": "phase6-bi-cd-001",
  "amount": "50000.00",
  "currency": "BIF",
  "destination": "merchant-cd-001",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "CD"
  }
}
```

Expected settlement behavior:

- source country: BI
- settlement country: CD
- source currency: BIF
- settlement currency: CDF
- FX rate locked before execution

### Verification after execution

Inspect:

- `/trust/explorer/{trust_id}`
- `/trust/explorer/{trust_id}/signature`
- `/trust/explorer/{trust_id}/audit.pdf`
- `/trust/explorer/{trust_id}/compliance-report`
- `/trust/explorer/{trust_id}/anchor`
- `/trust/explorer/{trust_id}/bundle.zip`

## 6. Step 5 - Introduce distributed validator nodes

NovaPay already exposes trust-node import and federation readiness. The next
deployment layer is distributed validation.

### Recommended node behavior

- validators subscribe to Kafka topics
- validators verify signatures
- validators replay the trust packet
- validators import only after local verification succeeds

### Quorum policy

Define a simple threshold policy for the first deployment:

- N validators must observe the packet
- quorum is reached at `N/2 + 1`
- no validator can execute a payment
- no observer can override authority

### Initial state

For the first production rollout, keep consensus informational and do not allow
validator output to override execution authority unless the runtime flag for
consensus enforcement is explicitly enabled.

## 7. Recommended deployment order

1. Deploy Kafka or Redpanda.
2. Deploy the primary NovaPay region.
3. Deploy the regional trust / observer nodes.
4. Enable KMS signing.
5. Run a controlled cross-border pilot.
6. Verify explorer, signature, PDF, bundle, and audit surfaces.
7. Add secondary region and DR region.
8. Turn on multi-node observation and quorum monitoring.

## 8. Documentation set to keep aligned

Keep these files updated together:

- `docs/architecture/NOVAPAY_GLOBAL_ARCHITECTURE_PHASE_5.md`
- `docs/operations/NOVATECH_CORE_PLATFORM_PRODUCTION_OPERATION_VERIFICATION_GUIDE.md`
- `docs/operations/NOVAPAY_KAFKA_MULTI_REGION_DEPLOYMENT_RUNBOOK.md`

## 9. Honest boundary

This codebase is now ready for Kafka-backed, KMS-signed, cross-border pilot
deployment. Multi-region consensus is not yet an enforced runtime guarantee.
Treat validator quorum as an operational control layer until the consensus
engine is explicitly implemented and verified.

## 10. Failure Modes and Recovery

### Kafka unavailable

Symptoms:

- event publishing fails
- payment execution degrades

Recovery:

1. Verify broker connectivity.
2. Check security groups and TLS configuration.
3. Confirm the broker list env variable is populated.

### KMS not accessible

Symptoms:

- signing fails
- trust packets are not generated

Recovery:

1. Check the ECS task role.
2. Verify KMS permissions:
   - `kms:Sign`
   - `kms:GetPublicKey`
   - `kms:DescribeKey`
3. Confirm AWS region consistency.

### Incorrect FX routing

Symptoms:

- settlement currency mismatch
- incorrect route class

Recovery:

1. Inspect the settlement plan output.
2. Verify `metadata.country`.
3. Check the FX provider implementation.

### Cross-region latency

Symptoms:

- delayed settlement confirmation
- delayed event consumption

Recovery:

1. Verify Kafka replication.
2. Check region-to-region connectivity.

### Validator disagreement

Symptoms:

- inconsistent trust verification

Recovery:

1. Inspect packet signatures.
2. Verify replay logic.
3. Confirm canonical serialization.

### Consensus not reached

Symptoms:

- `consensus_reached = false`
- quorum-not-reached errors

Recovery:

1. Check the number of healthy validator nodes.
2. Verify network connectivity between validator nodes and Kafka.
3. Inspect rejected votes for signature or replay failure.
4. Confirm the canonical packet hash is identical across regions.

### Conflicting validator packets

Symptoms:

- `conflicting_validator_packet_hashes`

Recovery:

1. Inspect packet payload differences.
2. Verify canonical serialization.
3. Isolate the faulty validator node.
4. Quarantine or remove the node before re-joining quorum.

## 11. Validator Node Operations

### Startup

Each validator node must:

- connect to Kafka
- subscribe to:
  - `novapay.payment.executed`
  - `novapay.trust.created`

### Processing loop

For each event:

1. extract the trust packet
2. verify the signature
3. verify replay status
4. emit a validator vote

### Vote structure

```json
{
  "node_id": "...",
  "packet_hash": "...",
  "accepted": true
}
```

### Quorum monitoring

Operators must monitor:

- number of validators
- number of healthy nodes
- quorum threshold

### Readiness endpoint

```text
GET /v1/core-platform/trust/consensus/status
```

Expected:

- `consensus_enabled = true`
- `multi_node_consensus_ready = true`

### Safety rule

Validator nodes must not:

- interact with payment providers
- execute settlement
- modify packet content

### Operational metrics

Operators must monitor:

#### Event bus

- publish success rate
- consumer lag
- topic throughput

#### Settlement

- FX conversion success rate
- settlement latency
- cross-border success rate

#### Signing

- signature success rate
- KMS latency
- signing failures

#### Consensus

- validator participation rate
- accepted versus rejected votes
- quorum success rate
- packet conflict rate

#### Alert conditions

Trigger an alert if:

- consensus failure rate exceeds 5 percent over 5 minutes
- Kafka lag exceeds the defined threshold for more than 2 minutes
- signing failures occur consecutively
- quorum is not reached for 3 consecutive cycles

## 12. Pilot Safety Constraints

Before enabling live provider mode:

- run at least 10 successful dry-run transactions
- verify 100 percent trust packet integrity
- confirm zero consensus conflicts
- verify FX correctness across corridors

### Live limits

- maximum transaction amount must be capped
- live pilots must start at low volume
- all flows must be monitored in real time

### Rollback condition

Disable live mode if:

- any signature verification fails
- any consensus conflict occurs
- any incorrect settlement occurs

## 13. Manual Intervention Protocol

If a critical inconsistency occurs, the operator must:

1. stop affected region traffic
2. isolate the faulty node
3. verify trust packets manually
4. compare packet hashes across regions
5. reintroduce nodes only after verification

The system must never auto-resolve consensus conflicts.
