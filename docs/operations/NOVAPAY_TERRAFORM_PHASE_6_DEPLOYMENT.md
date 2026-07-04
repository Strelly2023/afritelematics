# NovaPay Terraform Phase 6 Deployment Guide

## Purpose

This guide describes the step-by-step Terraform deployment path for moving the
current NovaPay stack toward Kafka-backed, multi-region operation with KMS
signing and cross-border settlement pilots.

Operational prerequisites that remain outside source control, including live
provider credentials, store release activation, and production secret
provisioning, are documented in:

`docs/operations/PRODUCTION_READINESS_REQUIREMENTS.md`

## 1. What is already in code

The repository already implements:

- deterministic settlement routing
- FX-aware payment normalization
- provider abstraction for PayID, Stripe, mobile money, and CBDC
- event bus abstraction with Kafka support
- public trust explorer and audit surfaces
- optional KMS-backed signing

This guide assumes those code paths remain the source of truth.

## 2. Terraform stack location

```text
infra/aws/novatech-core-platform
```

## 3. Stack inputs

Required inputs:

- `aws_region`
- `name`
- `container_image`
- `vpc_id`
- `public_subnet_ids`
- `private_subnet_ids`
- `database_password`
- `stripe_api_key_secret_arn`

Phase 6 inputs:

- `event_bus_backend`
- `event_bus_kafka_brokers`
- `novapay_region`
- `novatrust_signing_provider`
- `novatrust_kms_signing_enabled`
- `novatrust_kms_signing_algorithm`
- `novapay_cbdc_live_enabled`
- `novapay_cbdc_network`

## 4. Step 1 - Prepare AWS networking

For each region:

1. Create or select a VPC.
2. Create at least two public subnets.
3. Create at least two private subnets.
4. Ensure outbound access for ECS tasks to reach:
   - secrets manager
   - KMS
   - Kafka brokers
   - payment providers
5. Keep databases and brokers private.

## 5. Step 2 - Deploy Kafka

Preferred path:

- AWS MSK for managed operation

Alternative:

- Redpanda on EC2 or Kubernetes

Deployment order:

1. create private Kafka network
2. deploy brokers
3. enable encryption at rest
4. enable TLS in transit
5. define NovaPay topics
6. expose brokers only to application subnets

NovaPay topics:

- `novapay.payment.executed`
- `novapay.payment.settled`
- `novapay.trust.created`
- `novapay.audit.generated`

## 6. Step 3 - Apply Terraform for the primary region

From `infra/aws/novatech-core-platform`:

```bash
terraform init
terraform plan \
  -var 'aws_region=ap-southeast-2' \
  -var 'name=novatech-core-au' \
  -var 'container_image=<image>' \
  -var 'vpc_id=<vpc-id>' \
  -var 'public_subnet_ids=["subnet-a","subnet-b"]' \
  -var 'private_subnet_ids=["subnet-c","subnet-d"]' \
  -var 'database_password=<password>' \
  -var 'stripe_api_key_secret_arn=<secret-arn>' \
  -var 'event_bus_backend=kafka' \
  -var 'event_bus_kafka_brokers=broker1:9092,broker2:9092' \
  -var 'novapay_region=AU' \
  -var 'novatrust_signing_provider=aws_kms' \
  -var 'novatrust_kms_signing_enabled=true' \
  -var 'novatrust_kms_signing_algorithm=ECDSA_SHA_256' \
  -var 'novapay_cbdc_live_enabled=false' \
  -var 'novapay_cbdc_network=pilot-ledger'
terraform apply
```

Record the outputs:

- API URL
- PostgreSQL endpoint
- KMS key id

## 7. Step 4 - Apply Terraform for the Burundi or DRC region

Repeat the same module in the target Africa region with:

- a different `aws_region`
- a region-specific `name`
- the same or mirrored Kafka endpoint strategy
- the same KMS policy model
- the region label set to `BI` or `CD`

This region must host settlement workers and trust observers.

## 8. Step 5 - Enable KMS signing

Set:

```bash
NOVATRUST_SIGNING_PROVIDER=aws_kms
NOVATRUST_KMS_SIGNING_ENABLED=true
NOVATRUST_KMS_KEY_ID=<terraform-output>
```

Verify:

```bash
GET /v1/core-platform/signing/status
```

## 9. Step 6 - Launch cross-border pilot flows

### AU -> Burundi

Use:

```json
{
  "intent_id": "phase6-au-bi-001",
  "amount": "25.00",
  "currency": "AUD",
  "destination": "merchant-bi-001",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "BI"
  }
}
```

Expected result:

- settlement currency: BIF
- FX rate locked
- mobile money rail selected

### AU -> DRC

Use:

```json
{
  "intent_id": "phase6-au-cd-001",
  "amount": "25.00",
  "currency": "AUD",
  "destination": "merchant-cd-001",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "CD"
  }
}
```

Expected result:

- settlement currency: CDF
- FX rate locked

### Burundi -> DRC

Use:

```json
{
  "intent_id": "phase6-bi-cd-001",
  "amount": "50000.00",
  "currency": "BIF",
  "destination": "merchant-cd-002",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "CD"
  }
}
```

### DRC -> Burundi

Use:

```json
{
  "intent_id": "phase6-cd-bi-001",
  "amount": "50000.00",
  "currency": "CDF",
  "destination": "merchant-bi-002",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "BI"
  }
}
```

## 10. Step 7 - Verify the evidence surface

For each trust id, inspect:

- `/trust/explorer/{trust_id}`
- `/trust/explorer/{trust_id}/signature`
- `/trust/explorer/{trust_id}/audit.pdf`
- `/trust/explorer/{trust_id}/compliance-report`
- `/trust/explorer/{trust_id}/anchor`
- `/trust/explorer/{trust_id}/bundle.zip`

## 11. Step 8 - Promote to live provider mode

Only after the dry-run pilots are stable:

1. enable real provider credentials
2. confirm payment provider status
3. confirm KMS signing status
4. rerun a low-value live pilot
5. validate the trust explorer and PDF artifacts

## 12. Operational boundary

This guide intentionally stops short of claiming a live multi-region AWS
deployment in the repository itself. It is the step-by-step operator path to
reach that state.

## 13. Pre-Deployment Gate (Mandatory)

Before applying Terraform, verify:

- Kafka brokers are reachable from the VPC
- the KMS key exists and policy allows `ecs-tasks.amazonaws.com`
- the container image is available in ECR
- Secrets Manager contains:
  - database password
  - payment provider credentials
- security groups allow:
  - ECS -> Kafka
  - ECS -> KMS
  - ECS -> Database

Production deployment must be blocked unless:

- `event_bus_backend = kafka`
- signing provider is `aws_kms` or a valid production key
- `NOVAPAY_REGION` is defined
- the database is persistent and not SQLite

Failure to satisfy these conditions will result in:

- task startup failure
- signing failure
- event bus failure

### Failure Result

Deployment must fail if:

- Kafka brokers are missing
- the KMS key is missing
- the region configuration is invalid

## 14. Post-Deployment Validation

After deployment, verify:

### System readiness

```text
GET /v1/core-platform/readiness
```

Expected:

- `settlement_routing_ready = true`
- `event_bus_ready = true`
- `signing_ready = true`

### Payment execution test

```text
POST /v1/core-platform/payments/execute
```

Expected:

- settlement plan exists
- FX applied if cross-border
- event emitted

### Trust validation

```text
GET /trust/explorer/{trust_id}
```

Expected:

- signature present
- payload hash matches
- audit PDF downloadable

## 15. Environment Separation Rule

Each environment must use:

- separate Kafka clusters
- separate KMS keys
- separate databases

Resource sharing between environments is prohibited.
