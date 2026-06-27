# NovaTech Core Platform AWS Deployment

This stack is a deploy-ready baseline for the core NovaTech platform API and
Trust Explorer.

## Components

- ECS Fargate service for `afritech.api.app`
- Application Load Balancer
- RDS PostgreSQL for `novatech_core_trust_packets`
- Secrets Manager reference for `STRIPE_API_KEY`
- KMS key for NovaTrust signing metadata and rotation readiness
- CloudWatch log group

## Required Variables

```text
aws_region
name
container_image
vpc_id
public_subnet_ids
private_subnet_ids
database_password
stripe_api_key_secret_arn
event_bus_backend
event_bus_kafka_brokers
novapay_region
novatrust_signing_provider
novatrust_kms_signing_enabled
novatrust_kms_signing_algorithm
novapay_cbdc_live_enabled
novapay_cbdc_network
novapay_rollout_mode
novapay_primary_corridor
novapay_corridors
novapay_settlement_mode
novapay_mobile_money_live_enabled
novapay_compliance_provider
novapay_compliance_live_enabled
novapay_env_vars
novapay_secret_arns
```

## Runtime Environment

```text
DATABASE_URL=postgresql://novatech:<password>@<rds-endpoint>:5432/novatech
STRIPE_LIVE_MODE=true
STRIPE_API_KEY=<from Secrets Manager>
NOVATRUST_KMS_KEY_ID=<from Terraform output>
NOVAPAY_EVENT_BUS_BACKEND=kafka
NOVAPAY_EVENT_BUS_KAFKA_BROKERS=broker1:9092,broker2:9092
NOVAPAY_REGION=AU
NOVATRUST_SIGNING_PROVIDER=aws_kms
NOVATRUST_KMS_SIGNING_ENABLED=true
NOVATRUST_KMS_SIGNING_ALGORITHM=ECDSA_SHA_256
NOVAPAY_CBDC_LIVE_ENABLED=false
NOVAPAY_CBDC_NETWORK=pilot-ledger
```

## Apply

```bash
terraform init
terraform plan
terraform apply
```

For a concrete starting point, copy `terraform.tfvars.example` to
`terraform.tfvars` and replace the placeholder values.

After deploy, initialize the database schema by applying:

```text
afritech/core_platform/migrations/001_core_trust_packets.sql
```

## Pilot

1. Confirm `/v1/core-platform/payments/providers/status`.
2. Run `POST /v1/core-platform/pilot/flow` with provider `stripe`.
3. Open the returned `/trust/explorer/{trust_id}` link.
4. Export `/trust/explorer/{trust_id}/audit.pdf`.
5. Share `/trust/explorer/{trust_id}/signature`.
6. Share `/trust/explorer/{trust_id}/compliance-report`.

## Multi-region and cross-border pilot path

Deploy the same Terraform stack per region, then treat the region label as the
deployment discriminator:

- AU control region
- KE settlement region
- Burundi settlement region
- DRC settlement region

### Manifest layout

Use one environment manifest per corridor region:

- `infra/aws/novatech-core-platform/environments/au/terraform.tfvars.example`
- `infra/aws/novatech-core-platform/environments/ke/terraform.tfvars.example`
- `infra/aws/novatech-core-platform/environments/bi/terraform.tfvars.example`
- `infra/aws/novatech-core-platform/environments/cd/terraform.tfvars.example`

Recommended pilot flows:

- AU -> Burundi
- AU -> DRC
- Burundi -> DRC
- DRC -> Burundi

For each run, confirm the settlement route, FX-locked amount, trust explorer,
signature payload, and audit PDF before enabling any live provider mode.
