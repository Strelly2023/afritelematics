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
```

## Runtime Environment

```text
DATABASE_URL=postgresql://novatech:<password>@<rds-endpoint>:5432/novatech
STRIPE_LIVE_MODE=true
STRIPE_API_KEY=<from Secrets Manager>
NOVATRUST_KMS_KEY_ID=<from Terraform output>
```

## Apply

```bash
terraform init
terraform plan
terraform apply
```

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
