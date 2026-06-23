# NovaTech Core Platform 2026 Implementation Plan

## Scope

This plan covers core NovaTech platform layers only:

- NovaTechSol main platform
- NovaID / AfriID
- NovaPower
- NovaPay / AfriPay
- NovaTrust
- NovaScript
- NovaProgramming

Product applications such as NovaRide, NovaEat, NovaHealth, NovaLearn, and
NovaLogistics are intentionally out of scope for this patch.

## Implemented Folder Structure

```text
afritech/
  core_platform/
    __init__.py
    models.py
    services.py
  api/
    core_platform_api.py
  tests/
    core_platform/
      test_core_platform_layers.py
    api/
      test_core_platform_api.py

dashboard/
  src/
    App.jsx
  tests/
    test_operator_dashboard_surface.py
```

## Core Flow

```text
Identity -> Authority -> Execution -> Payment -> Proof -> Intelligence -> Evolution
```

The runtime wiring is:

```text
NovaID -> NovaPower -> NovaPay -> NovaTrust -> NovaScript -> NovaProgramming
```

## API Patch Plan

All core platform API routes live under `/v1/core-platform` and use the
existing pilot JWT role dependency.

```text
GET  /v1/core-platform/console
GET  /v1/core-platform/identity/me
POST /v1/core-platform/authority/evaluate
POST /v1/core-platform/payments/execute
POST /v1/core-platform/trust/replay
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}/audit.pdf
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}/signature
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}/compliance-report
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}/anchor
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}/qr.png
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}/bundle.zip
GET  /v1/core-platform/persistence/status
GET  /v1/core-platform/payments/providers/status
GET  /v1/core-platform/signing/status
POST /v1/core-platform/auditor/dashboard
POST /v1/core-platform/ai/explain
POST /v1/core-platform/programming/proposals
POST /v1/core-platform/pilot/flow
GET  /trust/explorer/{receipt_or_trust_id}
GET  /trust/explorer/{receipt_or_trust_id}/audit.pdf
GET  /trust/explorer/{receipt_or_trust_id}/signature
GET  /trust/explorer/{receipt_or_trust_id}/compliance-report
GET  /trust/explorer/{receipt_or_trust_id}/anchor
GET  /trust/explorer/{receipt_or_trust_id}/qr.png
GET  /trust/explorer/{receipt_or_trust_id}/bundle.zip
GET  /trust/auditor/dashboard?ids={receipt_or_trust_ids}
```

These routes are included in `afritech.api.app`, the broader NovaTech FastAPI
entrypoint. They are not included in the NovaRide-specific API entrypoint.

## Console Wireframes

```text
/console/identity
  Session status | Organization switcher | Device registry | Role editor

/console/authority
  Policy table | Decision trace | Review queue | Control log

/console/payments
  Intent queue | Transactions | Receipts | Settlements

/console/trust
  Timeline | Actor | Action | Replay result

/console/intelligence
  Ask system | Risk assistant | Audit summary | Recommendations

/console/programming
  Project list | Proposal editor | Diff viewer | Validator results
```

## Provider and Persistence Patch

```text
afritech/core_platform/payments/providers.py
  PayIDProvider
  StripeProvider

afritech/core_platform/persistence.py
  InMemoryCorePlatformStore
  PostgresCorePlatformStore
```

PayID is deterministic for pilot execution. Stripe is available behind a
configuration boundary and can use the Stripe SDK when a live API key is
provided.

PostgreSQL persistence targets the `novatech_core_trust_packets` JSONB table.

## AWS Production Architecture

```text
infra/aws/novatech-core-platform/
  README.md
  main.tf
  variables.tf
  outputs.tf
```

The stack provisions:

- ECS Fargate service
- Application Load Balancer
- RDS PostgreSQL
- CloudWatch logs
- Secrets Manager reference for Stripe
- KMS key for NovaTrust signing

This is deploy-ready infrastructure code. It does not provision cloud resources
until `terraform apply` is run with real AWS account variables.

## External Pilot Runbook

```text
scripts/novatech_core_deploy_aws.sh
scripts/novatech_core_apply_migrations.py
scripts/novatech_core_live_pilot.py
```

Required runtime values:

```text
AWS credentials
Terraform variables
DATABASE_URL
STRIPE_API_KEY
STRIPE_LIVE_MODE=true
NOVATECH_API_BASE_URL
NOVATECH_BEARER_TOKEN
NOVATRUST_ED25519_PRIVATE_KEY_B64
NOVATRUST_KMS_KEY_ID
```

## Validation Plan

```text
pytest -q afritech/tests/core_platform/test_core_platform_layers.py afritech/tests/api/test_core_platform_api.py dashboard/tests/test_operator_dashboard_surface.py
npm run build --prefix dashboard
git diff --check
```

## Next Patch Phases

1. Add persistent stores for identity sessions, payment receipts, and trust
   packets.
2. Add provider adapters for Stripe, PayID, and mobile money behind the
   provider-neutral NovaPay service.
3. Add export surfaces for JSON proof packets and audit reports.
4. Add OpenTelemetry trace emission around each core platform layer.
5. Add production RBAC/ABAC policy storage for NovaPower.
