# NovaRide Documentation Tree

Status: CANONICAL DOCUMENTATION INDEX
Classification: GOVERNED PRODUCT DOCUMENTATION SURFACE

Purpose: provide the full NovaRide documentation map from vision through
production, operations, maintenance, and governance.

This file is an index surface. It does not replace the underlying architecture,
control-plane, execution-plane, event, security, or runbook documents.

## Authority Order

```text
Constitution / Governance
-> Architecture / Control Plane
-> Execution Plane / Event Platform
-> Security / Compliance
-> Operations / Maintenance
-> Commercial / Product Surfaces
```

## Canonical NovaRide Runtime References

Use these existing repo docs as the current authoritative runtime surfaces:

- `docs/architecture/000_NOVARIDE_MASTER_INDEX.md`
- `docs/architecture/001_NOVARIDE_EXECUTIVE_OVERVIEW.md`
- `docs/architecture/002_NOVARIDE_FULL_SYSTEM_BLUEPRINT.md`
- `docs/architecture/003_NOVARIDE_PRODUCTION_CONTROL_PLANE.md`
- `docs/architecture/004_NOVARIDE_IMPLEMENTATION_PLAN.md`
- `docs/architecture/005_NOVARIDE_10_10_READINESS_CRITERIA.md`
- `docs/architecture/NOVARIDE_NEXT_GENERATION_ECOSYSTEM.md`
- `docs/architecture/NOVARIDE_PHASE0_DOMAIN_TABLES.md`
- `docs/architecture/NOVARIDE_SYSTEM_DATABASE_V1.md`

## Documentation Tree

### 1. Vision and product docs

- `01_NOVARIDE_VISION.md`
- `02_NOVARIDE_PRODUCT_STRATEGY.md`
- `03_NOVARIDE_MARKET_POSITIONING.md`
- `04_NOVARIDE_UBER_COMPARISON.md`
- `05_NOVARIDE_MVP_SCOPE.md`
- `06_NOVARIDE_ROADMAP.md`

Purpose:

- define the product thesis
- define the market category
- define the launch scope
- define the roadmap from pilot to scale

### 2. Use case and user journey docs

- `10_NOVARIDE_USE_CASES.md`
- `11_RIDER_USER_JOURNEY.md`
- `12_DRIVER_USER_JOURNEY.md`
- `13_OPERATOR_USER_JOURNEY.md`
- `14_ADMIN_USER_JOURNEY.md`
- `15_SUPPORT_USER_JOURNEY.md`
- `16_INSPECTOR_USER_JOURNEY.md`
- `17_FLEET_MANAGER_USER_JOURNEY.md`
- `18_BUSINESS_PORTAL_USER_JOURNEY.md`

Purpose:

- capture actor behavior
- define human workflows
- bind journeys to backend authority
- keep each app surface narrow and governed

### 3. App documentation

- `20_NOVARIDE_RIDER_APP_SPEC.md`
- `21_NOVARIDE_DRIVER_APP_SPEC.md`
- `22_NOVARIDE_OPERATOR_DASHBOARD_SPEC.md`
- `23_NOVARIDE_ADMIN_PANEL_SPEC.md`
- `24_NOVARIDE_SUPPORT_PORTAL_SPEC.md`
- `25_NOVARIDE_INSPECTOR_APP_SPEC.md`
- `26_NOVARIDE_FLEET_PORTAL_SPEC.md`
- `27_NOVARIDE_BUSINESS_PORTAL_SPEC.md`

Purpose:

- define screen contracts
- define app-level constraints
- define role-separated UX
- define what each app may request and display

### 4. Layer and architecture docs

- `30_NOVARIDE_SYSTEM_ARCHITECTURE.md`
- `31_NOVARIDE_LAYER_MODEL.md`
- `32_NOVARIDE_SHARED_PLATFORM.md`
- `33_NOVARIDE_CONTROL_PLANE_ARCHITECTURE.md`
- `34_NOVARIDE_EXECUTION_PLANE_ARCHITECTURE.md`
- `35_NOVARIDE_EVENT_PLATFORM_ARCHITECTURE.md`
- `36_NOVARIDE_TRUST_AUDIT_ARCHITECTURE.md`
- `37_NOVARIDE_DATA_ARCHITECTURE.md`
- `38_NOVARIDE_INTEGRATION_ARCHITECTURE.md`
- `39_NOVARIDE_OBSERVABILITY_ARCHITECTURE.md`

Purpose:

- define the bounded planes
- define shared services
- define event truth
- define trust, audit, and observability

### 5. Control plane docs

- `40_POLICY_ENGINE_SPEC.md`
- `41_FEATURE_FLAG_SERVICE_SPEC.md`
- `42_APPROVAL_SERVICE_SPEC.md`
- `43_WORKFLOW_ORCHESTRATOR_SPEC.md`
- `44_TRUST_ENGINE_SPEC.md`
- `45_COMPLIANCE_ENGINE_SPEC.md`
- `46_CONTROL_PLANE_ENFORCEMENT_RULES.md`
- `47_DECISION_TRACE_SPEC.md`

Purpose:

- gate execution through policy and approvals
- support controlled rollout
- preserve explainability and traceability

### 6. Execution plane docs

- `50_DISPATCH_SERVICE_SPEC.md`
- `51_TRIP_SERVICE_SPEC.md`
- `52_PRICING_SERVICE_SPEC.md`
- `53_PAYMENT_SERVICE_SPEC.md`
- `54_DRIVER_SERVICE_SPEC.md`
- `55_FLEET_SERVICE_SPEC.md`
- `56_SUPPORT_SERVICE_SPEC.md`
- `57_NOTIFICATION_SERVICE_SPEC.md`
- `58_MAPS_ROUTING_SERVICE_SPEC.md`

Purpose:

- define the business execution services
- ensure idempotent, auditable behavior
- keep decision logic outside app surfaces

### 7. Event schema and contract docs

- `60_EVENT_SCHEMA_SYSTEM.md`
- `61_EVENT_ENVELOPE_SCHEMA.md`
- `62_EVENT_REGISTRY.md`
- `63_EVENT_COMPATIBILITY_RULES.md`
- `64_EVENT_TOPIC_MODEL.md`
- `65_EVENT_PARTITIONING_RULES.md`
- `66_EVENT_REPLAY_MODEL.md`
- `67_EVENT_IDEMPOTENCY_RULES.md`
- `68_DECISION_TRACE_EVENT_BINDING.md`

Purpose:

- define the source-of-truth event system
- keep schema evolution controlled
- support replay and deterministic recovery

### 8. API docs

- `70_API_GATEWAY_SPEC.md`
- `71_AUTH_API_SPEC.md`
- `72_RIDER_API_SPEC.md`
- `73_DRIVER_API_SPEC.md`
- `74_OPERATOR_API_SPEC.md`
- `75_ADMIN_API_SPEC.md`
- `76_SUPPORT_API_SPEC.md`
- `77_INSPECTOR_API_SPEC.md`
- `78_PUBLIC_VERIFICATION_API_SPEC.md`
- `79_WEBSOCKET_API_SPEC.md`

Purpose:

- define ingress contracts
- keep app APIs narrow
- make websocket and public verification behavior explicit

### 9. Data and database docs

- `80_DATABASE_OWNERSHIP_MODEL.md`
- `81_POSTGRES_SCHEMA_GUIDE.md`
- `82_REDIS_USAGE_GUIDE.md`
- `83_OBJECT_STORAGE_GUIDE.md`
- `84_EVENT_STORE_GUIDE.md`
- `85_SEARCH_INDEX_GUIDE.md`
- `86_BACKUP_RESTORE_GUIDE.md`
- `87_DATA_RETENTION_POLICY.md`

Purpose:

- define data ownership
- prevent tenant leakage
- document persistence, recovery, and retention

### 10. Security and compliance docs

- `90_SECURITY_MODEL.md`
- `91_RBAC_ROLE_MODEL.md`
- `92_TENANT_ISOLATION_MODEL.md`
- `93_KYC_DRIVER_VERIFICATION.md`
- `94_VEHICLE_COMPLIANCE_MODEL.md`
- `95_AUDIT_LOG_POLICY.md`
- `96_PRIVACY_POLICY_TECHNICAL.md`
- `97_SECRETS_MANAGEMENT.md`
- `98_INCIDENT_RESPONSE_SECURITY.md`

Purpose:

- bind platform access to identity and role
- keep tenant isolation strict
- preserve compliance and incident response discipline

### 11. Trust, replay, and audit docs

- `100_TRUST_MODEL.md`
- `101_REPLAY_VERIFICATION_MODEL.md`
- `102_RECEIPT_VERIFICATION_MODEL.md`
- `103_PROOF_HASH_MODEL.md`
- `104_AUDIT_SIGNATURE_MODEL.md`
- `105_PUBLIC_TRUST_VERIFICATION.md`
- `106_DISPUTE_EVIDENCE_MODEL.md`

Purpose:

- define verifiable truth
- support public trust checks
- keep disputes evidence-backed

### 12. Testing docs

- `110_TEST_STRATEGY.md`
- `111_UNIT_TEST_PLAN.md`
- `112_API_CONTRACT_TEST_PLAN.md`
- `113_EVENT_CONTRACT_TEST_PLAN.md`
- `114_POLICY_TEST_MATRIX.md`
- `115_APPROVAL_GATE_TEST_MATRIX.md`
- `116_FEATURE_FLAG_TEST_MATRIX.md`
- `117_REPLAY_TEST_MATRIX.md`
- `118_MOBILE_APP_TEST_PLAN.md`
- `119_DASHBOARD_TEST_PLAN.md`
- `120_LOAD_TEST_PLAN.md`
- `121_CHAOS_TEST_PLAN.md`

Purpose:

- validate control-plane and execution-plane behavior
- prove schema compatibility
- keep release gates measurable

### 13. Deployment and infrastructure docs

- `130_AWS_DEPLOYMENT_TOPOLOGY.md`
- `131_DOCKER_COMPOSE_GUIDE.md`
- `132_CI_CD_PIPELINE.md`
- `133_ENVIRONMENT_VARIABLES.md`
- `134_SECRETS_AND_CONFIG.md`
- `135_DOMAIN_DNS_SSL_GUIDE.md`
- `136_OBSERVABILITY_DEPLOYMENT.md`
- `137_SCALING_STRATEGY.md`
- `138_DISASTER_RECOVERY_PLAN.md`

Purpose:

- define operational deployment
- keep environments reproducible
- support scaling and recovery

### 14. Operations docs

- `140_OPERATOR_RUNBOOK.md`
- `141_ADMIN_RUNBOOK.md`
- `142_SUPPORT_RUNBOOK.md`
- `143_INSPECTOR_RUNBOOK.md`
- `144_FLEET_MANAGER_RUNBOOK.md`
- `145_LIVE_INCIDENT_RUNBOOK.md`
- `146_MANUAL_DISPATCH_RUNBOOK.md`
- `147_REFUND_DISPUTE_RUNBOOK.md`
- `148_DRIVER_ONBOARDING_RUNBOOK.md`
- `149_VEHICLE_INSPECTION_RUNBOOK.md`

Purpose:

- give each role an operational playbook
- make live support and incident handling repeatable

### 15. Maintenance docs

- `150_SYSTEM_MAINTENANCE_PLAN.md`
- `151_RELEASE_MANAGEMENT.md`
- `152_SCHEMA_MIGRATION_GUIDE.md`
- `153_POLICY_MIGRATION_GUIDE.md`
- `154_DATABASE_MIGRATION_GUIDE.md`
- `155_DEPENDENCY_UPGRADE_GUIDE.md`
- `156_MONITORING_AND_ALERTING_RUNBOOK.md`
- `157_BACKUP_RESTORE_RUNBOOK.md`
- `158_POSTMORTEM_TEMPLATE.md`
- `159_PRODUCTION_READINESS_CHECKLIST.md`

Purpose:

- keep the platform maintainable after launch
- make release and migration behavior explicit
- standardize incident learning

### 16. Business and governance docs

- `160_BUSINESS_MODEL.md`
- `161_PRICING_AND_COMMISSION_MODEL.md`
- `162_DRIVER_TERMS.md`
- `163_RIDER_TERMS.md`
- `164_FLEET_PARTNER_TERMS.md`
- `165_PRIVACY_POLICY.md`
- `166_TERMS_OF_SERVICE.md`
- `167_REGULATORY_READINESS.md`
- `168_INSURANCE_AND_RISK_MODEL.md`
- `169_GOVERNANCE_MODEL.md`

Purpose:

- define commercial terms
- define legal and regulatory posture
- keep platform governance explicit

### 17. Final master docs

- `000_NOVARIDE_MASTER_INDEX.md`
- `001_NOVARIDE_EXECUTIVE_OVERVIEW.md`
- `002_NOVARIDE_FULL_SYSTEM_BLUEPRINT.md`
- `003_NOVARIDE_PRODUCTION_CONTROL_PLANE.md`
- `004_NOVARIDE_IMPLEMENTATION_PLAN.md`
- `005_NOVARIDE_10_10_READINESS_CRITERIA.md`

Purpose:

- provide the top-level navigation for leaders and builders
- define production readiness criteria
- tie the entire documentation tree together

## Current Canonical NovaRide Surfaces In Repo

The following existing documents already cover major parts of the tree:

- `docs/architecture/NOVARIDE_NEXT_GENERATION_ECOSYSTEM.md`
- `docs/architecture/NOVARIDE_PHASE0_DOMAIN_TABLES.md`
- `docs/architecture/NOVARIDE_SYSTEM_DATABASE_V1.md`

## Readiness Interpretation

If the NovaRide documentation tree is used as the canonical product map, then
implementation readiness requires:

- Phase 0 SaaS foundation docs
- control plane docs
- execution plane docs
- event schema docs
- API contracts
- security and tenant isolation docs
- testing and deployment docs
- runbooks and maintenance docs

## Recommended Next Documents To Generate

The next highest-value authored docs are:

1. `docs/architecture/NOVARIDE_REFERENCE_ARCHITECTURE.md`
2. `docs/architecture/NOVARIDE_NON_FUNCTIONAL_REQUIREMENTS.md`
3. `docs/architecture/NOVARIDE_SERVICE_CATALOG.md`
4. `docs/developer/NOVARIDE_DEVELOPER_HANDBOOK.md`
5. `docs/standards/NOVARIDE_PLATFORM_STANDARDS.md`
6. `docs/operations/NOVARIDE_OPERATIONAL_RUNBOOKS.md`
7. `docs/adr/NOVARIDE_ADR_INDEX.md`

## Institutional Maturity Pack

These documents close the remaining maturity gap:

- `docs/architecture/NOVARIDE_REFERENCE_ARCHITECTURE.md`
- `docs/architecture/NOVARIDE_NON_FUNCTIONAL_REQUIREMENTS.md`
- `docs/architecture/NOVARIDE_SERVICE_CATALOG.md`
- `docs/developer/NOVARIDE_DEVELOPER_HANDBOOK.md`
- `docs/standards/NOVARIDE_PLATFORM_STANDARDS.md`
- `docs/operations/NOVARIDE_OPERATIONAL_RUNBOOKS.md`
- `docs/adr/NOVARIDE_ADR_INDEX.md`

## Canonical Rule

```text
Index explains.
Architecture constrains.
Contracts bind.
Events prove.
Runbooks operate.
```
