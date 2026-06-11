# AfriTech Live Deployment Architecture (AWS / GCP / Azure)

This document maps the current AfriTech execution and verification surfaces to a
deployable cloud topology. It is an architecture plan, not a claim that all
cloud resources are already deployed.

## Common deployment shape

- API tier: FastAPI runtime for authenticated control surfaces
- dashboard tier: React operator dashboard
- secret tier: managed secret store
- audit / log tier: centralized observability sink
- public edge tier: controlled public verification endpoint only

## AWS mapping

- API: ECS Fargate or Lambda + API Gateway
- secrets: AWS Secrets Manager
- logs / metrics: CloudWatch + OpenSearch
- public edge: CloudFront + WAF

## GCP mapping

- API: Cloud Run
- secrets: Secret Manager
- logs / metrics: Cloud Logging + Monitoring
- public edge: Cloud Load Balancer + Cloud Armor

## Azure mapping

- API: Azure Container Apps or App Service
- secrets: Key Vault
- logs / metrics: Azure Monitor + Log Analytics
- public edge: Front Door + WAF

## Public endpoint boundary

- public:
  - `/public/verify/health`
  - `/public/registry`
  - `/public/verify/{anchor_id}`
  - `/public/partners/registry`
- authenticated:
  - `/v1/ops/observability/dashboard`
  - `/v1/ops/audit/dashboard`
  - `/v1/partners/registry*`
  - `/v1/trust/*`

## Observability and audit

- operator observability dashboard resolves alerts back to trace and replay
- audit dashboard resolves readiness back to receipt, registry, and export state
- logs feed SIEM, but SIEM never becomes authority

## Multi-region posture

- region-local ingestion
- replay-safe publication packets
- tenant isolation at API, secret, and registry layers
- public verification remains read-only across regions
