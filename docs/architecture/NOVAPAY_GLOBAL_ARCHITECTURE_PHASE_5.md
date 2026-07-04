# NovaPay Global Architecture Phase 5+

## Classification

`distributed-financial-protocol | trust-governed | multi-rail | cross-border-ready`

This document describes the current NovaPay implementation state in this
repository and the next operational tier it is being extended toward.

## 1. System Identity

NovaPay is the financial execution layer of NovaTech. In this codebase it is
implemented as a trust-governed payment system that:

- authorizes payment intent through NovaPower
- routes settlement through a deterministic settlement planner
- executes via payment provider adapters
- records trust evidence in NovaTrust
- exposes public verification through the trust explorer

Execution is controlled. Settlement is verified. Trust is cryptographically
provable.

## 2. Current Implementation State

### Implemented

- settlement routing and currency normalization
- FX-aware cross-border execution
- provider abstraction for PayID, Stripe, mobile money, and CBDC
- event bus abstraction with in-memory default and Kafka-ready backend
- deterministic Ed25519 signing
- optional AWS KMS-backed signing
- trust node import and federation status surfaces
- public explorer, audit, compliance, QR, bundle, and anchor endpoints
- webhook verification and settlement event recording

### Present But Optional

- Kafka event bus backend, enabled by environment configuration
- CBDC live gateway mode, enabled by environment configuration
- blockchain anchor adapter, exposed as an optional verification layer

### Operational Readiness Dependencies

The following items are production activation requirements rather than source
control features:

- live provider credentials and webhook registration
- production signing material and secret provisioning
- store release activation and platform review approvals
- production monitoring, alerting, and backup services

### Future

- true multi-region infrastructure deployment
- distributed validator consensus
- external trust notarization

## 3. Architecture Overview

```text
Clients / Apps / Merchants
          |
          v
Global API Layer (NovaCore)
          |
          +--------------------+------------------+
          |                    |                  |
          v                    v                  v
   Settlement Router       Event Bus         Trust System
   (FX + rail choice)      (async topics)    (NovaTrust)
          |                    |                  |
          v                    v                  v
 Providers / Rails        Observers / Workers  Explorer / Audit
 (PayID / Mobile Money /  (Kafka-ready)        (public verification)
  Stripe / CBDC)
```

## 4. Settlement Routing Engine

The settlement planner is deterministic and implemented in
`afritech/core_platform/settlement.py`.

### Responsibilities

- infer source country and settlement country
- normalize currency codes
- lock FX rates when settlement currency differs from source currency
- choose the execution rail
- produce a normalized payment intent for downstream providers

### Routing examples

- AUD -> PayID for Australian domestic flows
- USD -> Stripe for USD domestic flows
- KE / BI / CD -> mobile money rails
- CBDC -> optional rail path, controlled by environment flags

### Output

The router returns a `SettlementResult` containing:

- `SettlementPlan`
- normalized `PaymentIntent`

The plan includes:

- route id
- corridor
- route class
- source and settlement currency
- source and settlement amount
- FX provider and locked reference, if applicable

## 5. FX Engine

The FX engine is deterministic and currently backed by the Afripay FX module.

### Behavior

- deterministic conversion
- locked rate reference
- replay-safe settlement amounts

### Supported corridors in the current code

- AUD -> KES
- USD -> KES
- KES -> BIF
- KES -> CDF

### Operational meaning

If the intent currency differs from the settlement currency, NovaPay locks an
FX conversion before execution and stores the normalized settlement amount in
the trust packet.

## 6. Event Bus

The event bus is abstracted in `afritech/core_platform/event_bus.py`.

### Current modes

| Mode | Behavior |
| ---- | -------- |
| in_memory | default local mode |
| kafka | optional production backend |

### Event topics

- `novapay.payment.executed`
- `novapay.payment.settled`
- `novapay.trust.created`

### Configuration

Kafka mode is enabled when:

```bash
NOVAPAY_EVENT_BUS_BACKEND=kafka
NOVAPAY_EVENT_BUS_KAFKA_BROKERS=broker1:9092,broker2:9092
```

If Kafka is not configured, the system remains functional with the in-memory
bus.

## 7. Signing and Production Security

Signing is implemented in `afritech/core_platform/signing.py`.

### Current signing modes

- local Ed25519, default
- AWS KMS-backed signing, optional

### KMS runtime flags

```bash
NOVATRUST_SIGNING_PROVIDER=aws_kms
NOVATRUST_KMS_SIGNING_ENABLED=true
NOVATRUST_KMS_KEY_ID=<aws_kms_key_id>
NOVATRUST_KMS_SIGNING_ALGORITHM=ECDSA_SHA_256
```

### Security properties

- deterministic signature verification
- backend-aware signature status
- key rotation planning
- compatible packet verification for local or KMS-produced signatures

## 8. Trust Node Network

The trust node network is exposed for observability and federation readiness.

### Current posture

- import layer: ready
- federation layer: conditional
- consensus layer: future

### Exposed status

- `/v1/core-platform/trust/node/network/status`
- `/trust/federation/status`

### Boundary

Trust nodes validate, import, observe, and publish trust evidence. They do
not execute payments.

## 9. CBDC Integration

CBDC support is modeled as an optional provider rail in
`afritech/core_platform/cbdc.py`.

### Behavior

- controlled pilot mode by default
- live gateway mode only when all required env vars are present

### Configuration

```bash
NOVAPAY_CBDC_LIVE_ENABLED=true
NOVAPAY_CBDC_API_URL=<provider_url>
NOVAPAY_CBDC_API_TOKEN=<token>
NOVAPAY_CBDC_MERCHANT_ID=<merchant_id>
NOVAPAY_CBDC_CALLBACK_URL=<callback_url>
NOVAPAY_CBDC_NETWORK=<network_name>
```

### Status surface

- `/v1/core-platform/payments/providers/status`
- `/v1/core-platform/readiness`

## 10. Current API Surface

### Core API

- `GET /v1/core-platform/payments/providers/status`
- `GET /v1/core-platform/payments/settlement/status`
- `GET /v1/core-platform/trust/node/network/status`
- `GET /v1/core-platform/signing/status`
- `GET /v1/core-platform/readiness`
- `POST /v1/core-platform/payments/execute`
- `POST /v1/core-platform/webhooks/payments`

### Public verification API

- `GET /trust/sandbox/demo`
- `GET /trust/explorer/{trust_id}`
- `GET /trust/explorer/{trust_id}/audit.pdf`
- `GET /trust/explorer/{trust_id}/signature`
- `GET /trust/explorer/{trust_id}/compliance-report`
- `GET /trust/explorer/{trust_id}/anchor`
- `GET /trust/explorer/{trust_id}/anchor/blockchain`
- `GET /trust/explorer/{trust_id}/qr.png`
- `GET /trust/explorer/{trust_id}/bundle.zip`
- `GET /trust/auditor/dashboard?ids=...`
- `GET /trust/audit/{trust_id}`

## 11. Readiness Matrix

| Capability | Status | Notes |
| ---------- | ------ | ----- |
| Settlement routing | ready | implemented in code |
| FX normalization | ready | deterministic locked rates |
| Event bus abstraction | ready | Kafka optional |
| KMS signing | ready | optional production backend |
| Public verification | ready | explorer and bundle available |
| CBDC provider | ready | controlled pilot by default |
| Multi-node trust import | ready | validation surface only |
| Distributed consensus | future | not authoritative yet |
| Multi-region deployment | future | infra workstream |

## 12. Honest Boundary

This repository now contains a functional trust-governed payment and
verification stack. It is not yet a globally distributed production network
with live Kafka-backed multi-region infrastructure and validator consensus.
Those are the next deployment steps, not claims about the current runtime.

## 13. Strategic Next Steps

1. Deploy Kafka and wire the event bus backend in production.
2. Deploy multi-region infrastructure and regional routing.
3. Add live FX rate providers and liquidity-aware routing.
4. Stand up distributed validator nodes.
5. Define consensus thresholds and rollback policy.

## 14. Executive Positioning

NovaPay is a trust-governed financial execution layer with settlement routing,
cryptographic verification, and public evidence surfaces. It is moving toward
a distributed financial protocol, but the current codebase must be described
as a production-capable trust system with protocol-ready extension points.

## 15. Phase 5 to Phase 6 Deployment Path

The step-by-step deployment plan for Kafka, multi-region nodes, KMS signing,
and the first cross-border pilot is documented in:

```text
docs/operations/NOVAPAY_KAFKA_MULTI_REGION_DEPLOYMENT_RUNBOOK.md
```

That runbook is the operator reference for the following sequence:

1. Deploy Kafka or MSK in AWS.
2. Deploy regional NovaPay nodes.
3. Enable KMS signing in production.
4. Launch the first cross-border settlement flow.
5. Introduce validator nodes and quorum-based verification.

This architecture document remains the authoritative description of the codebase
state. The deployment runbook describes how to move that state into a regional
and eventually multi-region production topology.

## 16. Runtime Guarantees (Enforced)

The following conditions are enforced at runtime and must hold for production:

### Event Bus

- Kafka must be configured when `AFRITECH_ENV=production`
- the in-memory event bus is prohibited in production

Failure condition:

```text
RuntimeError: event_bus_not_ready_for_production
```

### Error Taxonomy

All runtime failures must emit structured error identifiers.

#### Core errors

- `event_bus_not_ready_for_production`
- `signing_not_ready_for_production`
- `settlement_not_initialized`
- `consensus_not_ready`
- `quorum_not_reached`
- `conflicting_validator_packet_hashes`
- `invalid_signature_contract`

#### Requirements

- all errors must be deterministic
- all errors must be logged with context
- all errors must be observable via metrics

#### Example

```json
{
  "error": "quorum_not_reached",
  "details": {
    "votes": 2,
    "required": 3
  }
}
```

### Signing

- signing must be enabled in all production environments
- either:
  - Ed25519 private key is configured, or
  - AWS KMS is configured and reachable

Failure condition:

```text
RuntimeError: signing_not_ready_for_production
```

### Settlement

- FX must be resolved before execution when currencies differ
- a settlement plan must always exist
- settlement and execution must remain separate concerns

### Trust Integrity

- every payment must produce:
  - a signed packet
  - a deterministic payload hash
  - a verifiable trust receipt

## Execution Contract

Each payment must follow this invariant sequence:

1. authorization must succeed
2. settlement plan must be generated
3. FX must be locked if required
4. execution must occur
5. event must be emitted
6. trust packet must be created
7. packet must be signed
8. packet must be persisted
9. packet must be verifiable

### Invalid State

A payment is invalid if any step is missing.

### Enforcement

- incomplete payments must be rejected
- unsigned packets must be rejected
- unverifiable packets must be rejected

### Atomicity Guarantee

The execution sequence must behave atomically at the protocol level:

- failure in any step invalidates the entire payment
- partially executed payments must be rolled back or marked invalid
- no step may succeed independently of the full sequence

### Idempotency Requirement

- repeated execution of the same intent must produce identical results
- duplicate events must not create duplicate payments

### System Boot Guarantees

At startup, the system must validate:

- event bus readiness must pass
- signing readiness must pass
- settlement routing must initialize successfully

If consensus is enabled:

- validator consensus readiness must pass

Failure conditions:

- event bus not ready -> system must not start
- signing not ready -> system must not start
- settlement not initialized -> system must not start
- consensus enabled but not ready -> system must not start

## 17. Environment Modes

| Environment | Event Bus | Signing | FX | Consensus |
|------------|----------|--------|----|----------|
| development | in_memory | dev key | deterministic | disabled |
| staging | kafka | ed25519 | real or test | disabled |
| production | kafka | aws_kms | real + locked | controlled |

Production must not run with:

- in-memory event bus
- dev signing keys

## 18. Validator Consensus Certification (Active Layer)

The validator consensus engine provides cryptographic certification of trust
evidence.

### Purpose

- certify trust packets across multiple validator nodes
- ensure consistency of settlement and execution records
- prevent tampering or divergence across regions

### Input

Validator nodes submit:

- packet in canonical representation
- signature
- node identity

### Process

For each validator envelope:

1. verify signature
2. verify payload hash
3. verify replay integrity
4. compute packet hash

### Quorum Rule

```text
quorum = N/2 + 1
```

Consensus requires:

- all accepted votes to match the same packet hash
- conflicting packet hashes to be rejected
- duplicate votes to be ignored

### Output

```json
{
  "trust_id": "...",
  "consensus_reached": true,
  "accepted_votes": 3,
  "quorum": 2,
  "packet_hash": "...",
  "authority_boundary": "verification_only"
}
```

### Authority Boundary

Validator consensus can certify evidence and produce a verification
certificate. It cannot execute payments, alter settlement, or override policy.

### Consensus Scope

Consensus applies only to:

- trust packet verification
- payload integrity
- cross-node consistency

Consensus does not apply to:

- payment authorization
- settlement execution
- provider-level decision making

### Failure Conditions

- no valid signatures -> reject
- replay not verified -> reject
- conflicting hashes -> reject
- quorum not reached -> reject

### Consensus Enforcement Mode

Consensus operates in two modes:

| Mode | Behavior |
|-----|--------|
| informational | certifies evidence only |
| enforced | blocks inconsistent or invalid packets |

Activated by:

```text
NOVATRUST_CONSENSUS_ENABLED=true
NOVATRUST_CONSENSUS_ENFORCED=true
```

Enforcement rules when enabled:

- payments with failed consensus must be rejected
- packets with conflicting hashes must be rejected
- quorum must be reached before certification

Default state:

- consensus is disabled or informational
- execution remains authoritative

## 19. Multi-Region Consistency Model

NovaPay maintains consistency using event replication, deterministic replay,
and validator consensus.

### Rules

1. Packets must be identical across regions.
2. FX must be locked before broadcast.
3. Signatures must be verifiable globally.

### Conflict Handling

If regions diverge:

- consensus rejects inconsistent packets
- operator intervention is required
- the conflicting region is quarantined until the cause is resolved

## 20. Auditability Contract

Each payment must produce:

- signed trust packet
- settlement plan
- execution record
- validator certificate, when consensus is enabled

### Verification Surfaces

Operators and auditors must be able to retrieve:

- trust explorer record
- signature
- audit PDF
- compliance report
- bundle archive

### Integrity Guarantees

- payload hash is immutable
- signature is verifiable
- replay is deterministic

### Regulatory Position

This system supports transaction traceability, audit evidence generation, and
cross-border verification.

## Data Immutability

Once a trust packet is created:

- payload must not change
- hash must not change
- signature must remain valid

### Mutation Policy

- updates must create a new packet
- the previous packet must remain accessible

### Violation Handling

- hash mismatch must invalidate the packet
- signature mismatch must invalidate the packet

### Security Boundary Model

NovaPay enforces strict separation between layers.

#### External Boundary

NovaPay assumes:

- external payment providers are non-trusted systems
- all external data must be validated and normalized
- trust guarantees apply only after internal processing

#### Trust Boundary Entry Point

- settlement router
- provider adapters

#### Execution Layer

- authorized by NovaPower
- interacts with payment providers
- performs settlement execution

#### Trust Layer

- produces verification packets
- signs and validates data
- generates immutable evidence

#### Consensus Layer

- validates trust packets
- certifies multi-node agreement
- does not execute or mutate state

#### Hard Isolation Rules

- execution cannot bypass signing
- trust cannot execute payments
- consensus cannot override execution authority

#### Failure Behavior

If integrity is compromised:

- system must fail closed
- no partial execution is allowed

### Testability Contract

Each layer must be testable independently.

#### Settlement

- deterministic routing must match expected output
- FX conversions must be reproducible

#### Signing

- packet signature must verify correctly
- signature must match the payload hash

#### Event Bus

- events must be emitted on execution
- consumers must process events reliably

#### Consensus

- the same packets must produce identical hashes
- quorum must produce a valid certificate
- conflicting packets must be rejected

#### API

- readiness endpoint must reflect true system state
- trust endpoints must return verifiable data
