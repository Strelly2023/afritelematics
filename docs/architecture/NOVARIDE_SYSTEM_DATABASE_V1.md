# NovaRide System Database V1

STATUS: BOUNDED OPERATIONAL DATABASE CONTRACT
CLASSIFICATION: ISOLATED PRODUCT DATA DESIGN SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Document Purpose

This document defines the NovaRide system database as it exists in the current
implementation layer. It maps the platform into authoritative tables,
projection tables, event streams, and trust/evidence artifacts.

The goal is not to invent a new data model. The goal is to freeze the current
NovaRide data contract so the backend, dispatch engine, dashboards, and mobile
apps all read the same canonical state.

## Architectural Rule

```text
Apps = Interface
Platform = Authority
Database = Deterministic Platform Memory
```

The database must preserve:

- tenant isolation
- deterministic dispatch and ride lifecycle state
- wallet and transaction integrity
- audit and replay evidence
- subscription and feature governance
- trust and compliance projections

The database must not:

- grant clients direct provider access
- allow UI state to override backend truth
- mutate already established proof chains silently
- mix tenants without an explicit organization key

## Canonical Persistence Layers

### 1. SaaS foundation tables

These tables power Phase 0 and every later NovaRide capability.

| Table | Role |
| --- | --- |
| `organizations` | Tenant registry |
| `organization_profiles` | Tenant type, status, owner, and default plan |
| `accounts` | User membership and organization-scoped role mapping |
| `subscriptions` | Plan, seats, status, and billing cycle |
| `catalog_features` | Global feature catalog |
| `feature_flags` | Organization-scoped feature toggles |
| `notifications` | Notification outbox and delivery state |
| `integrations` | External connector registry |
| `audit_events` | Immutable audit event log |
| `audit_chain_events` | Hash-chained audit ledger |
| `signed_audit_chain_events` | Signed audit ledger records |
| `usage_events` | Usage counter feed for billing and analytics |
| `billing_records` | Billing summary projections |

### 2. Mobility execution tables

These tables carry the operational ride and payment flow.

| Table | Role |
| --- | --- |
| `rides` | Authoritative ride state |
| `wallets` | User wallet balances |
| `transactions` | Wallet and settlement ledger entries |
| `driver_presence` | Live driver presence and availability |
| `dispatch_assignments` | Dispatch decisions and allocation history |
| `external_payment_authorizations` | External payment holds / authorizations |
| `external_payment_captures` | External payment captures |

### 3. Event and workflow tables

| Table | Role |
| --- | --- |
| `event_stream_topics` | Defined stream namespaces |
| `event_stream_events` | Append-only event stream |
| `workflow_instances` | Long-running business workflows |
| `workflow_steps` | Workflow step state |

### 4. Trust, policy, and governance tables

| Table | Role |
| --- | --- |
| `policy_definitions` | Declarative platform policies |
| `policy_decisions` | Policy evaluation results |
| `zero_trust_policies` | Zero-trust rules and bindings |
| `zero_trust_decisions` | Zero-trust decisions |
| `key_registry` | Key metadata and rotation state |
| `key_rotation_events` | Key rotation audit trail |
| `certificate_chains` | Certificate lineage |
| `trust_scores` | Trust score snapshots |
| `trust_stream_events` | Trust event stream |
| `trust_exchange_events` | Cross-organization trust exchange records |
| `trust_regions` | Trust region registry |
| `trust_region_links` | Region-to-region trust links |
| `trust_graph_nodes` | Trust graph vertices |
| `trust_graph_edges` | Trust graph edges |
| `identity_bindings` | Human/device binding evidence |
| `signed_http_requests` | Signed request evidence |
| `federation_nodes` | Federation peers |
| `federation_claims` | Federation claim records |
| `federation_events` | Federation event log |

### 5. Deployment, assurance, and evidence tables

| Table | Role |
| --- | --- |
| `verification_proofs` | Proof artifacts for controlled execution |
| `deployment_requests` | Deployment change requests |
| `deployments` | Deployment executions |
| `deployment_receipts` | Deployment evidence receipts |
| `replay_records` | Replay evidence records |
| `assurance_records` | Assurance summaries |
| `assurance_runs` | Assurance executions |
| `assurance_drift_events` | Drift observations |
| `assurance_alerts` | Assurance alert feed |
| `assurance_reports` | Assurance report snapshots |
| `certification_records` | Certification artifacts |
| `retention_policies` | Retention and legal-hold policy |

### 6. Analytics and AI tables

| Table | Role |
| --- | --- |
| `dashboard_analytics_snapshots` | Operator dashboard trend history |
| `ai_decision_snapshots` | AI decision summaries |
| `ai_action_snapshots` | AI action summaries |
| `outcome_snapshots` | Outcome and learning records |
| `risk_predictions` | Forward-looking risk signals |

## NovaRide Domain Model

### Organization and access

```text
Organization
  -> OrganizationProfile
  -> Account
  -> Subscription
  -> FeatureFlag
  -> Integration
  -> Notification
  -> AuditEvent
```

### Ride execution

```text
Ride
  -> DriverPresence
  -> DispatchAssignment
  -> ExternalPaymentAuthorization
  -> ExternalPaymentCapture
  -> Transaction
  -> Wallet
```

### Trust and governance

```text
PolicyDefinition -> PolicyDecision
KeyRegistry -> SignedAuditChainEvent
TrustScore -> DashboardAnalyticsSnapshot
TrustGraphNode -> TrustGraphEdge
```

## Authoritative Entities

The following tables are authoritative for NovaRide runtime truth:

- `organizations`
- `organization_profiles`
- `accounts`
- `subscriptions`
- `catalog_features`
- `feature_flags`
- `notifications`
- `integrations`
- `audit_events`
- `audit_chain_events`
- `signed_audit_chain_events`
- `rides`
- `wallets`
- `transactions`
- `driver_presence`
- `dispatch_assignments`
- `external_payment_authorizations`
- `external_payment_captures`
- `event_stream_topics`
- `event_stream_events`

Projection and evidence tables are allowed to exist, but they must remain
rebuildable from authoritative sources.

## Projection and Derived Tables

The following tables are read-heavy or evidence-oriented projections:

- `billing_records`
- `usage_events`
- `dashboard_analytics_snapshots`
- `ai_decision_snapshots`
- `ai_action_snapshots`
- `outcome_snapshots`
- `replay_records`
- `assurance_records`
- `assurance_runs`
- `assurance_drift_events`
- `assurance_alerts`
- `assurance_reports`
- `verification_proofs`
- `deployment_receipts`
- `certification_records`

These tables support dashboards, reports, exports, and governance evidence.
They are not the only source of truth for ride execution or tenant control.

## Core Table Design

### `organizations`

| Column | Purpose |
| --- | --- |
| `organization_id` | Stable tenant key |
| `organization_name` | Tenant display / legal name |
| `created_at` | Registration timestamp |

### `organization_profiles`

| Column | Purpose |
| --- | --- |
| `organization_id` | Tenant key |
| `organization_type` | business, fleet, partner, internal |
| `status` | active / suspended / onboarding |
| `default_plan` | Billing baseline |
| `owner_user_id` | Primary owner |
| `owner_role` | Owner role label |

### `accounts`

| Column | Purpose |
| --- | --- |
| `account_id` | Membership row key |
| `organization_id` | Tenant scope |
| `user_id` | Identity linkage |
| `role` | Role assignment |
| `status` | Active or inactive membership |
| `is_primary` | Primary member flag |

### `subscriptions`

| Column | Purpose |
| --- | --- |
| `subscription_id` | Subscription key |
| `organization_id` | Tenant scope |
| `plan` | free, basic, pro, enterprise |
| `status` | active / paused / cancelled |
| `billing_cycle` | monthly / annual |
| `seats` | Seat allocation |
| `start_date` | Billing start |
| `end_date` | Billing end |
| `auto_renew` | Renewal flag |

### `catalog_features`

| Column | Purpose |
| --- | --- |
| `feature_key` | Canonical feature id |
| `module` | Module family |
| `description` | Human-readable summary |
| `category` | Governance category |
| `default_enabled` | Default launch state |

### `feature_flags`

| Column | Purpose |
| --- | --- |
| `flag_id` | Toggle key |
| `organization_id` | Tenant scope |
| `feature_key` | Catalog link |
| `enabled` | Active/inactive |
| `reason` | Toggle justification |
| `updated_by` | Actor or system |

### `rides`

| Column | Purpose |
| --- | --- |
| `ride_id` | Ride key |
| `organization_id` | Tenant scope |
| `passenger_id` | Passenger identity |
| `driver_id` | Assigned driver |
| `pickup_location_json` | Pickup projection |
| `destination_location_json` | Destination projection |
| `status` | requested / matched / in_progress / completed / cancelled |
| `fare_estimate` | Pre-trip fare |
| `final_fare` | Completed fare |
| `currency` | Settlement currency |
| `created_at` | Creation timestamp |
| `updated_at` | Update timestamp |
| `completed_at` | Completion timestamp |

### `driver_presence`

| Column | Purpose |
| --- | --- |
| `presence_id` | Presence row key |
| `organization_id` | Tenant scope |
| `driver_id` | Driver identity |
| `status` | online / offline / busy |
| `location_json` | Latest known location |
| `last_seen` | Last heartbeat |
| `busy_ride_id` | Current ride if busy |
| `trust_score` | Operational trust score |
| `metadata_json` | Extra dispatch metadata |

### `dispatch_assignments`

| Column | Purpose |
| --- | --- |
| `assignment_id` | Assignment key |
| `organization_id` | Tenant scope |
| `ride_id` | Ride key |
| `driver_id` | Selected driver |
| `status` | assigned / released / failed |
| `decision_json` | Dispatch decision snapshot |
| `matched_at` | Assignment timestamp |
| `updated_at` | Update timestamp |

### `wallets`

| Column | Purpose |
| --- | --- |
| `wallet_id` | Wallet key |
| `organization_id` | Tenant scope |
| `user_id` | Wallet owner |
| `currency` | Currency code |
| `balance` | Current balance |

### `transactions`

| Column | Purpose |
| --- | --- |
| `transaction_id` | Ledger row key |
| `organization_id` | Tenant scope |
| `ride_id` | Linked ride |
| `user_id` | Affected user |
| `counterparty_user_id` | Counterparty user |
| `amount` | Transaction amount |
| `currency` | Settlement currency |
| `type` | debit / credit |
| `status` | completed / pending / failed |

### `external_payment_authorizations`

| Column | Purpose |
| --- | --- |
| `authorization_id` | Provider auth key |
| `organization_id` | Tenant scope |
| `ride_id` | Linked ride |
| `provider` | Payment provider |
| `provider_reference` | Provider side reference |
| `amount` | Authorized amount |
| `currency` | Settlement currency |
| `status` | authorization state |
| `settlement_status` | settlement state |
| `capture_status` | capture state |
| `raw_json` | Provider response |

### `external_payment_captures`

| Column | Purpose |
| --- | --- |
| `capture_id` | Capture key |
| `organization_id` | Tenant scope |
| `ride_id` | Linked ride |
| `authorization_id` | Linked auth |
| `provider` | Provider name |
| `provider_reference` | Provider reference |
| `amount` | Captured amount |
| `currency` | Settlement currency |
| `status` | capture status |
| `raw_json` | Provider response |

## Event Stream Design

`event_stream_topics` defines the stream namespace and retention policy.

`event_stream_events` is append-only and ordered by:

- `organization_id`
- `topic_name`
- `offset_number`

This stream is used for:

- dispatch lifecycle events
- payment orchestration events
- operator insight feeds
- replay and audit support

## Indexing and Uniqueness Strategy

The schema depends on the following uniqueness and access patterns:

- one organization profile per organization
- one subscription record per organization
- one feature flag per `(organization_id, feature_key)`
- one wallet per `(organization_id, user_id, currency)`
- one driver presence row per `(organization_id, driver_id)`
- one dispatch assignment per `(organization_id, ride_id)`
- one payment authorization per `(organization_id, ride_id)`
- one payment capture per `(organization_id, authorization_id)`
- one stream offset per `(organization_id, topic_name, offset_number)`

Recommended read indexes:

- `rides(organization_id, status, updated_at)`
- `rides(organization_id, passenger_id, updated_at)`
- `rides(organization_id, driver_id, updated_at)`
- `driver_presence(organization_id, status, updated_at)`
- `dispatch_assignments(organization_id, driver_id, updated_at)`
- `transactions(organization_id, ride_id, created_at)`
- `notifications(organization_id, status, created_at)`
- `audit_events(organization_id, created_at)`
- `event_stream_events(organization_id, topic_name, offset_number)`
- `external_payment_authorizations(organization_id, ride_id, status)`

## Tenant Isolation Rules

Every row that belongs to tenant-scoped data must include `organization_id`.

Every read path must either:

- explicitly filter by `organization_id`, or
- derive the tenant from a verified authenticated claim.

Every write path must:

- touch only the caller's tenant scope
- refuse cross-tenant spoofing
- record the actor and the tenant in audit or stream metadata

## Dispatch-Specific Contract

The dispatch engine uses:

- `driver_presence` as the live availability source
- `rides` as the requested trip source
- `dispatch_assignments` as the allocation ledger
- `event_stream_events` as the durable event trail

Dispatch must prefer:

- verified drivers
- fresh heartbeats
- low load
- proximity to pickup
- stable trust scores

Dispatch must reject:

- offline drivers
- busy drivers
- stale heartbeat records
- excluded drivers
- cross-tenant candidates

## Payment-Specific Contract

`external_payment_authorizations` and `external_payment_captures` are the
authoritative provider bridge.

Local wallets and transactions record the internal settlement ledger.

No app may talk directly to a payment provider. All provider calls pass through
the backend integration boundary.

## Readiness Contract

The database layer is considered contractually complete when:

- Phase 0 SaaS tables exist
- ride execution tables exist
- dispatch and payment tables exist
- event stream append order is stable
- trust and audit evidence can be reconstructed
- tenant isolation is enforced on every mutable surface

## Safe Final Classification

```text
NovaRide system database V1 is a bounded operational persistence contract
for tenant-controlled mobility execution, governed billing, trust evidence,
and deterministic dispatch.
```
