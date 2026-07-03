        # NOVATECH OPERATOR MANUAL

        ## Version 1.0

        **Status:** Official role-specific manual

        **Audience:** Operations administrators and support operators

        **Owner:** NovaTech Operations

        **Purpose:** Operational runbook for live dashboard and incident work.

        **Authority boundary:** This manual explains governed operations and role-specific guidance. It does not replace constitutional truth, legal review, production incident authority, or the full reference manual.

        ## Document Control

        | Field | Value |
|---|---|
        | Document ID | NOVATECH-OPERATOR-MANUAL-V1 |
        | Version | 1.0 |
        | Classification | GENERATED_ROLE_MANUAL |
        | Owner | NovaTech Operations |
        | Minimum Words | 2800 |
        | Source Count | 4 |
        | Source Manifest | `docs/registry/lineage/NOVATECH-OPERATOR-MANUAL-V1.sources.json` |
        | Certificate | `docs/registry/certificates/NOVATECH-OPERATOR-MANUAL-V1.json` |

## 4. Dashboard Map and Navigation

The dashboard is the first operational map staff should learn.

| Navigation Item | What It Shows | Typical Use |
|---|---|---|
| Dashboard | Cross-platform overview, status, live signals | Start-of-day checks |
| Governance | Policy registry, bindings, rule validation | Governance review |
| Runtime | Service health, event throughput, queue health | Operations monitoring |
| Proof | Evidence, receipts, witness records, export packages | Verification work |
| Trust | Trust registry, public verification, certification | Trust administration |
| Intelligence | Analytics, AI insights, predictive surfaces | Decision support |
| Economy | Tenants, billing, invoices, subscriptions | Finance and SaaS |
| Organization OS | Intranet, extranet, knowledge, workflows, comms | Organizational control |
| Products | Product surfaces and operational views | Product operations |
| Marketplace | Trust services and cross-tenant exchange | Partner strategy |
| Settings | Access, preferences, environment configuration | Administration |

### Dashboard Reading Order

1. Check system health.
2. Check open incidents or alerts.
3. Check trust and proof status.
4. Check tenancy and billing readiness.
5. Check active decisions or controlled execution surfaces.
6. Check pending approvals or escalations.

### What Not to Do

- Do not treat dashboard color alone as authority.
- Do not ignore proof when the dashboard looks healthy.
- Do not use screenshots as evidence of truth.
- Do not reclassify a warning as healthy without review.

## 6. Runtime Operations

Runtime operations manage live services, orchestration, queues, throughput, and failure handling.

### Core Runtime Checks

- Active services
- Service dependencies
- Node health
- Queue backlog
- Event throughput
- Error rate
- Memory pressure
- CPU pressure
- Recovery status

### Operational Cadence

| Cadence | Checks |
|---|---|
| Start of day | Health dashboard, alerts, pending incidents |
| Midday | Queue health, throughput, backlog, retry storms |
| End of day | Incident log, resource trend, unresolved warnings |
| Weekly | Dependency review, scaling review, recovery rehearsal |

### What Runtime Staff Must Preserve

- Event ordering.
- Replay fidelity.
- Service traceability.
- Minimal blast radius for changes.
- Clear separation between observation and mutation.

### Common Failure Modes

- Backlog accumulation
- Timeouts
- Missing heartbeat
- Unexpected service restart
- Queue poisoning
- Dependency drift

### Runtime Response Pattern

1. Observe the symptom.
2. Confirm whether proof is affected.
3. Confirm whether replay is affected.
4. Isolate the failing component.
5. Preserve evidence.
6. Restore safely.
7. Record the resolution.

## 7. Proof and Verification

Proof is the record that a governed event occurred as declared.

### Proof Responsibilities

- Search evidence.
- Verify signatures.
- Review witness records.
- Validate registry entries.
- Export verification packages.
- Preserve receipt lineage.

### Verification Sequence

1. Select the evidence item.
2. Review metadata and source.
3. Validate the signature or deterministic hash.
4. Confirm registry match.
5. Confirm replay alignment.
6. Record the result.

### Evidence Types

- Receipts
- Replay traces
- Witness bundles
- Certificate chains
- Public verification packages
- Audit exports

### Proof Handling Rules

- Never edit proof records manually.
- Never publish unverified evidence as verified.
- Never delete evidence to simplify reporting.
- Preserve the chain from event to receipt to verification package.

### Operator Questions

- What happened?
- What source proves it?
- What replay or receipt anchors it?
- What remains unverified?
- What can be published publicly?

## 8. Trust Management

Trust management turns proof into a public-facing trust surface.

### Trust Responsibilities

- Maintain the trust registry.
- Review proposed trust features.
- Publish or withhold trust badges.
- Inspect evidence submissions.
- Monitor public verification status.
- Review certification eligibility.

### Trust Feature Requirements

- Every new trust feature must map to a proof source.
- Every trust badge must have a verification pathway.
- Every certification must identify its evidence basis.
- Every public trust claim must be reproducible.

### Trust States

- Verified
- Pending review
- Degraded
- Failed
- Revoked

### Public Trust Portal Expectations

- Clear receipt lookup.
- Clear verification result.
- Clear evidence package access.
- No hidden mutation path.

### Trust Administrator Review Questions

- Is the evidence complete?
- Does replay match the claim?
- Is the signature valid?
- Does the trust score align with observed evidence?
- Is the publication safe for external consumption?

## 12. Organization OS

The Organization OS is the internal operating layer that connects intranet, extranet, knowledge, workflows, and communication.

### Intranet

Internal dashboards, operations, staff surfaces, and private coordination live here.

### Extranet

External collaborators, clients, partners, suppliers, and investors use the controlled external view.

### Knowledge

Project files, documents, references, and structured knowledge live here.

### Workflows

Tasks, templates, approvals, and lifecycle states live here.

### Communications

Messages, alerts, and routed operational notifications live here.

### Operating Rule

The Organization OS must reduce cognitive load by putting the right surface in front of the right person at the right time.

## 14. Controlled Execution and Safety

Controlled execution is the most powerful operational surface and must remain bounded.

### Execution Tiers

- Advisory
- Assisted
- Controlled
- Supervised

### Safety Gates

- Tenant readiness
- Billing readiness
- Execution tier readiness
- Operator acknowledgment
- Safety gate pass

### Meaning of Safe Execution

Safe execution means the platform can recommend or prepare bounded action paths, but it does not bypass review or constitutional authority.

### Safety Rules

- Never treat readiness as automatic permission.
- Never confuse recommendation with execution.
- Never let a dashboard become the authority source.
- Never activate automation without evidence-backed gating.

### Controlled Execution Review Questions

- Is the action necessary?
- Is the evidence strong enough?
- Is the tier appropriate?
- Is the operator aware?
- Is rollback possible?

## 18. Security, Privacy, and Records

### Security Rules

- Use MFA.
- Use strong passwords.
- Protect credentials.
- Do not share secrets.
- Do not bypass governance controls.
- Do not alter evidence records.

### Records Rules

- Preserve audit logs.
- Preserve proof bundles.
- Preserve replay lineage.
- Preserve change history.
- Preserve record retention according to policy.

### Privacy Rules

- Collect only the data required for the role.
- Restrict export rights.
- Redact sensitive details when circulating evidence.
- Treat public verification as a controlled disclosure surface.

## 19. Incident Management and Escalation

### Incident Levels

| Level | Meaning | Response |
|---|---|---|
| 1 | Minor issue | Log and monitor |
| 2 | Operational disruption | Triage and fix with owner |
| 3 | Critical service impact | Escalate, preserve evidence, coordinate |
| 4 | Platform emergency | Command structure, rollback or isolation, executive awareness |

### Incident Procedure

1. Detect.
2. Verify.
3. Escalate.
4. Resolve.
5. Document.
6. Review.

### Incident Minimums

- Capture timestamps.
- Capture affected surface.
- Capture proof and logs.
- Capture owner and resolver.
- Capture the immediate containment action.

### Escalation Questions

- Is truth affected?
- Is proof affected?
- Is trust publication affected?
- Is tenant isolation affected?
- Is production safety affected?

## 21. Onboarding, Training, and Support

New staff should receive:

- Role-specific access walkthrough.
- Governance and proof orientation.
- Dashboard orientation.
- Incident reporting walkthrough.
- Security and records training.
- Product surface training.
- Escalation practice.

### Support Model

- First-line support handles known workflows and basic triage.
- Second-line support handles product or operational edge cases.
- Trust and proof support handles evidence and verification questions.
- Security support handles credential or access issues.
- Finance support handles billing and settlement questions.

### Training Rule

A staff member should not be handed a sensitive surface without understanding the proof and escalation rules that govern it.

## 22. Operational Cadence

### Daily

- Check health dashboards.
- Review alerts.
- Review incidents.
- Review trust and proof surfaces.
- Review tenant and billing readiness.

### Weekly

- Review trends.
- Review unresolved issues.
- Review access changes.
- Review backlog and release readiness.
- Review platform improvement notes.

### Monthly

- Review governance changes.
- Review policy drift.
- Review tenant growth.
- Review billing and revenue signals.
- Review incident patterns and automation quality.

### Quarterly

- Review manual updates.
- Review training effectiveness.
- Review role boundaries.
- Review trust marketplace readiness.
- Review long-term risk posture.

## 26. Documentation Certification and Compliance Product

The NovaTech documentation operating system is also a certification and compliance product.

### Product Purpose

It connects the manual system to:

- Policy Registry
- Certification Registry
- Trust Registry
- Organization OS
- Tenant Governance
- Operator Training Records
- Continuous Assurance Reports
- Certification Issuance
- Public Verification Portal

### Certification Model

NovaTech uses an ISO-style certification layer to classify documents and operating packs as:

- Verified
- Compliant
- Certified
- Revoked

Every certification must have:

- source lineage
- document hash
- validation result
- owner responsibility
- training evidence where relevant
- continuous assurance evidence where relevant

### Compliance Model

The compliance layer is designed for government and enterprise review. It provides:

- read-only proof surfaces
- registry-backed publication
- operator training acknowledgement
- assurance history
- certificate-ready exports

Documentation does not create legal authority. It creates governed evidence that can support internal compliance, procurement review, public sector pilots, and partner verification.

### Policy Registry Connection

The policy registry governs publication and change discipline for manuals and compliance packs.

Typical policy questions:

- Is the document source-backed?
- Is the document authority boundary explicit?
- Is the document hash aligned with the certificate?
- Is the publication role allowed to receive this manual?
- Is the document ready for compliance use?

### Organization OS and Public Verification Connection

Documentation compliance links the manual system to tenant governance and the public verification portal.

The connected surfaces include:

- organization directory
- tenant governance detail
- billing preview
- controlled execution readiness
- certification issuance
- public documentation portal
- public verification portal

This keeps documentation review tied to the organization, the tenant, and the public verification surface.

### Certification Registry Connection

The certification registry records which manuals and packs have been certified, when they were issued, and what evidence supported the result.

Certification records should include:

- document id
- title
- owner
- version
- source count
- hash
- validator version
- issued at

### Trust Registry Connection

The trust registry turns certification into a public trust surface. It is the bridge between internal proof and external verification.

It should answer:

- What is trusted?
- Who can verify it?
- What evidence supports the claim?
- What service or tenant can consume it?
- What changed since the last assurance cycle?

### Operator Training Records

Staff must acknowledge the manual set they use. Training records prove that the operator has been exposed to the correct role content.

Training records should capture:

- manual id
- manual version
- role
- trainee and trainer
- completion status
- assessment score
- evidence count
- acknowledgement hash

### Continuous Assurance Reports

Continuous assurance ties the documentation layer to live platform review. It tells operators and auditors whether the governing documents still match the platform state.

Assurance reports should show:

- document compliance status
- policy alignment
- trust posture
- training coverage
- open exceptions
- renewal or review dates

### Trust-as-a-Service Monetization

NovaTech can package documentation compliance as a service:

- free public verification
- team verification subscriptions
- enterprise compliance exports
- dedicated tenant certification
- partner onboarding packages
- annual assurance reporting

### AfriCPPT Expansion

AfriCPPT is the protocol surface for cross-tenant proof and compliance exchange. The documentation product should publish protocol mappings and certificate-ready exports that can be consumed by partners, regulators, and enterprise customers.

### Global Marketplace and Partner Onboarding

The marketplace exposes trust services across tenants, including verification, certification, replay, and assurance services. Partner onboarding should start with one narrow workflow, then expand to certification, training, and ongoing assurance.

### Operating Rule

The documentation operating system is projection-only. It informs policy, certification, trust, and training. It does not mutate runtime truth.

## Launch Sequence

### Step 1: Demo Freeze

- freeze rider and driver app demo build
- seed one clean demo ride fixture
- verify trust badge, receipt view, replay view, and evidence view
- record investor demo video from the frozen build

### Step 2: Operational Readiness

- assign one pilot operator
- assign backup operator
- register trusted drivers
- prepare rider invite list
- confirm support channel
- confirm hard-stop escalation owner

### Step 3: Evidence Readiness

- verify receipt generation
- verify replay hash generation
- verify evidence viewer
- verify public verification path
- verify audit package export
- prepare daily evidence folder

### Step 4: Field Execution

Run only bounded ride scenarios:

- normal ride completion
- driver reject cascade
- rider cancellation during matching
- network delay / timeout determinism
- payment failure observation without corrupting trip state

### Step 5: Daily Review

Each day must produce:

- ride count
- completed ride count
- failed ride count
- replay mismatch count
- evidence gap count
- driver feedback
- rider feedback
- operator decision log

## Required Readiness Sections

### 1. Governance And Cutover Evidence

- governed cutover gate result
- replay stability proof
- rollback decision path
- incident command ownership

### 2. Partner And External Proof Surface

- partner verification API evidence
- SDK integration evidence
- anchor publication pipeline evidence
- external reference retention policy

### 3. Operational Monitoring Surface

- replay-backed operator dashboard
- real-time anomaly alerting service
- evidence-complete operator alerts
- trace-linked replay verification snapshots

### 4. Enterprise Operations Controls

- on-call roster and escalation matrix
- SLO and error budget policy
- tenant isolation checklist
- multi-region failover drill evidence
- production key custody and rotation plan
- audit logging retention plan

### 5. Security And Compliance Boundary

- auth/token lifecycle evidence
- device revocation evidence
- receipt integrity evidence
- evidence export handling boundary
- declared non-claims and residual risks

## Phase 1: Persistence

### Goal

No ride state or driver state is lost on restart.

Execution setup for this phase is defined in:

- [`AFRIRIDE_PHASE1_SETUP_RUNBOOK.md`](../pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md)

### Current Problem

The authoritative backend stores operational state in memory in:

- [`afriride_system/backend/command_api/command_dispatcher_adapter.py`](../../afriride_system/backend/command_api/command_dispatcher_adapter.py)

Current structures:

- `drivers: dict[str, DriverSession]`
- `rides: dict[str, RideSession]`

This is not pilot-grade durability.

### Proposed Pilot Implementation

Use SQLite first.

Rationale:

- minimal operational complexity
- easy local and pilot deployment
- preserves an upgrade path to PostgreSQL

### Data To Persist

- driver status
- ride state
- ride lifecycle events
- idempotency records
- receipt metadata
- evidence metadata

### Files To Modify

- [`afriride_system/backend/command_api/command_dispatcher_adapter.py`](../../afriride_system/backend/command_api/command_dispatcher_adapter.py)
- [`afriride_system/backend/state.py`](../../afriride_system/backend/state.py)
- [`afriride_system/backend/api_gateway/gateway.py`](../../afriride_system/backend/api_gateway/gateway.py)
- [`afriride_system/api/dispatcher_adapter.py`](../../afriride_system/api/dispatcher_adapter.py)
- [`afriride_system/api/idempotency.py`](../../afriride_system/api/idempotency.py)

### New Files Likely Required

- `afriride_system/backend/storage.py`
- `afriride_system/backend/repositories/driver_repository.py`
- `afriride_system/backend/repositories/ride_repository.py`
- `afriride_system/backend/repositories/idempotency_repository.py`

Exact naming may vary, but the separation should be explicit.

### Acceptance Criteria

- restarting the API process does not erase rides
- restarting the API process does not erase driver online state unless intentionally designed
- ride status queries return previously stored rides after restart
- idempotency behavior survives restart for the configured window

### Tests Required

- persistence round-trip tests
- restart simulation tests
- idempotency durability tests
- lifecycle flow tests against persistent storage

### Pilot Gate

`Persistence = PASS`

## Phase 2: Authentication

### Goal

Enforce separate rider, driver, and operator authority boundaries in the authoritative FastAPI spine.

### Current Problem

The chosen production backend does not yet present a coherent production authentication boundary across:

- rider
- driver
- operator

### Proposed Pilot Implementation

Use JWT authentication with explicit role claims.

Minimum roles:

- `RIDER`
- `DRIVER`
- `OPERATOR`

### Scope

Protect mutating endpoints first:

- passenger ride request and cancel
- driver status, accept, start, complete
- ride contract endpoints
- any operator conversation or trust endpoint added to the spine

### Files To Modify

- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)
- [`afriride_system/api/passenger_routes.py`](../../afriride_system/api/passenger_routes.py)
- [`afriride_system/api/driver_routes.py`](../../afriride_system/api/driver_routes.py)
- [`afriride_system/api/ride_routes.py`](../../afriride_system/api/ride_routes.py)
- [`afriride_system/api/schemas.py`](../../afriride_system/api/schemas.py)

### New Files Likely Required

- `afriride_system/api/auth.py`
- `afriride_system/api/auth_models.py`
- `afriride_system/tests/test_authentication.py`

### Acceptance Criteria

- rider endpoints reject unauthenticated calls
- driver endpoints reject unauthenticated calls
- operator-only surfaces reject non-operator tokens
- role mismatch produces deterministic 401 or 403 behavior

### Tests Required

- token issuance tests
- role authorization tests
- protected-route tests
- negative tests for missing and invalid tokens

### Pilot Gate

`Authentication = PASS`

## Phase 3: Evidence Durability

### Goal

Replay records, trace lineage, and receipt lineage survive restart.

### Current Problem

The trace evidence path is memory-based in:

- [`afriride_system/backend/trace_enforcement.py`](../../afriride_system/backend/trace_enforcement.py)

Specifically:

- `TRACE_LOG = TraceEventLog()`

This weakens pilot evidence and replay authority after restart.

### Proposed Pilot Implementation

Persist:

- trace events
- ride-linked evidence events
- replay metadata
- receipt metadata

The API may still expose the same evidence summary endpoints, but they must read from durable records.

### Files To Modify

- [`afriride_system/backend/trace_enforcement.py`](../../afriride_system/backend/trace_enforcement.py)
- [`afriride_system/backend/event_ledger.py`](../../afriride_system/backend/event_ledger.py)
- [`afriride_system/backend/ledger_receipts.py`](../../afriride_system/backend/ledger_receipts.py)
- [`afriride_system/api/trace_middleware.py`](../../afriride_system/api/trace_middleware.py)
- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)

### New Files Likely Required

- `afriride_system/backend/repositories/trace_repository.py`
- `afriride_system/backend/repositories/evidence_repository.py`
- `afriride_system/backend/repositories/receipt_repository.py`

### Acceptance Criteria

- trace summaries remain available after restart
- ride trace validation remains available after restart
- receipts remain derivable from stored evidence after restart
- evidence endpoints no longer depend on process-local memory for authority

### Tests Required

- trace persistence tests
- evidence summary tests using persisted fixtures
- receipt regeneration tests from persisted records
- restart durability tests

### Pilot Gate

`Evidence = PASS`

`Replay = PASS`

`Receipt = PASS`

## Phase 4: Dashboard Contract Alignment

### Goal

The authoritative dashboard must depend only on endpoints provided by the authoritative backend spine.

### Current Problem

The dashboard currently expects:

- `/rides/active`
- `/system/replay/health`
- `/system/evidence`
- `/system/guards`
- `/trust/conversation`

The first four exist in the chosen FastAPI spine.
`/trust/conversation` currently does not.

### Decision Rule

Choose the smallest valid change.

### Option A

Implement `/trust/conversation` in the chosen FastAPI spine.

### Option B

Remove the dependency from the dashboard.

For a controlled pilot, prefer whichever option:

- reduces scope
- avoids pulling authority from non-spine code
- does not create a second backend dependency

### Files To Modify

If implementing:

- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)
- new route or router file under `afriride_system/api/`

If removing:

- [`dashboard/src/App.jsx`](../../dashboard/src/App.jsx)
- [`dashboard/tests/test_operator_dashboard_surface.py`](../../dashboard/tests/test_operator_dashboard_surface.py)

### Acceptance Criteria

- the dashboard uses only endpoints served by `afriride_system`
- no operator workflow depends on Django or alternate backend surfaces
- dashboard tests match the authoritative backend contract

### Tests Required

- dashboard contract tests
- end-to-end operator flow smoke test
- backend route test if `/trust/conversation` is added

### Pilot Gate

`Dashboard = PASS`

## Cross-Cutting Rules

### Rule 1

Do not add new product features outside:

- `afriride_system`
- `AfriRideMobile`
- `dashboard`

### Rule 2

Do not satisfy pilot blockers by wiring the dashboard or mobile app back into archived or experimental backends.

### Rule 3

If `afritech` is used, document the exact module dependency and classify it as production-supporting platform code.

### Rule 4

Any new persistence or auth code must land inside the authoritative spine, not in `ecosystems/afriride`, `afriride_backend`, or `afriride_system/django_app`.

## Suggested Delivery Order

1. persistence
2. evidence durability
3. authentication
4. dashboard contract alignment

Persistence is first by necessity.
Evidence durability follows immediately because it depends on persistence.
Authentication can proceed in parallel in implementation terms, but not as the first gate if evidence and state remain volatile.

## Current Blockers

The current pilot blockers are:

1. persistence
2. authentication
3. evidence durability
4. dashboard contract alignment

These are ordered deliberately.
Persistence comes first because replay, receipts, and evidence authority all depend on durable state.

## Operational notes

- control-plane routes remain authenticated even when the public verifier is live
- the public verification surface is intentionally bounded to `/public/*`
- TLS is intentionally disabled until the domain-based production cutover
- the zero-downtime deploy script is the normal pilot deploy path
- if Docker build context becomes too large, keep using the tightened
  `.dockerignore` already present in this repo
- if build state on the host becomes unhealthy, inspect:

```bash
docker compose -f deploy/production/docker-compose.production.yml logs --tail=200
docker system df
df -h
```

## Required Repo-Side Validators

```bash
python3 -m pytest afritech/tests/distributed/test_sovereign_ledger_protocol.py
python3 -m pytest afritech/tests/distributed/test_protocol_hardening_and_adversarial.py
python3 -m afritech.ci.app_surface_validator
python3 -m afritech.ci.driver_surface_validator
python3 -m afritech.ci.afriride_live_pilot_protocol_validator
python3 -m afritech.ci.afriride_field_validator
```

## Use This Checklist Before Merging

- Does the changed module sit on the `afritech.api.app` import path?
- Does the module import `django.*` or `rest_framework.*`?
- Does the module define or import `models.Model` subclasses?
- Does the module touch `settings`, `apps`, or ORM managers at import time?
- Does the module execute I/O, queue setup, or state reads during import?
- Does the module assume environment variables already exist?
- Does the module assume signing keys already exist?
- Does the module assume traces or receipts exist on disk?

## Safe Import Rules

- Keep FastAPI startup modules pure-Python where possible.
- Prefer function-level imports for Django-bound code.
- Prefer lazy service loaders over top-level ORM imports.
- Guard optional dependencies with fallback behavior where possible.
- Keep route registration import-safe.
- Keep `uvicorn afritech.api.app:app` startup side effects minimal.
- Make health endpoints lightweight and self-contained.
- Do not bind production truth to dashboard startup.

## Required Patterns

- `DJANGO_SETTINGS_MODULE` must be set before `django.setup()`
- `django.setup()` must run only when needed
- Django model import must happen after setup in mixed runtime paths
- startup-safe auth helpers must not require DRF to exist
- public verification endpoints must remain bounded and read-only

## Release Checklist

- Run targeted startup tests.
- Rebuild the API image with `--no-cache` when dependency metadata changes.
- Verify `/health` returns `{"status":"ok"}`.
- Verify startup logs do not show `ImproperlyConfigured`.
- Verify startup logs do not show `ModuleNotFoundError`.
- Verify public verifier routes still boot.
- Verify dashboard builds against the current API URL.

## Completion Definition

This execution plan is complete when all of the following are true:

- `Persistence = PASS`
- `Authentication = PASS`
- `Evidence = PASS`
- `Replay = PASS`
- `Receipt = PASS`
- `Dashboard = PASS`

and the controlled pilot no longer depends on process-local in-memory authority for core operational truth.

        ## Auditor Focus

        - Trace claims back to evidence and registry entries.
- Confirm that certification follows proof.
- Check for unauthorized mutation of evidence.
- Require lineage before publication or escalation closure.

        ## Auditor Focus

        - Trace claims back to evidence and registry entries.
- Confirm that certification follows proof.
- Check for unauthorized mutation of evidence.
- Require lineage before publication or escalation closure.

        ## Auditor Focus

        - Trace claims back to evidence and registry entries.
- Confirm that certification follows proof.
- Check for unauthorized mutation of evidence.
- Require lineage before publication or escalation closure.

        ## Operator Focus

        - Watch live signals before they become incidents.
- Preserve proof whenever the runtime deviates.
- Use the incident ladder and handover rules.
- Treat dashboard state as guidance, not authority.

## Document Lineage

| Source Document | SHA256 |
|---|---|
| `docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md` | `76d5fe0f05b01b1bbec087654e0b89dec7eb03364233649f2c557cb58e6a2888` |
| `docs/operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md` | `9c718eca5dd98b3b9118a1abc748ab0bd97cbfb616e151b44ba0235318b0bf7a` |
| `docs/operations/AfriRide_Operability_Playbook.md` | `6a762d1375944260b32d67d049102c28f4be321c9f2523f8eb4e6648eb01a5ad` |
| `docs/operations/AfriRide_First_10_Rides_Runbook.md` | `c476a623086a2048e52fb6fa1b8ad883c8bece30f0819cad515ca01ddf43230c` |

## Documentation Certification

This document is certified through the NovaTech documentation system.

- Source manifest: `docs/registry/lineage/NOVATECH-OPERATOR-MANUAL-V1.sources.json`
- Certificate: `docs/registry/certificates/NOVATECH-OPERATOR-MANUAL-V1.json`
- Validator version: `novatech-doc-system-v1`
