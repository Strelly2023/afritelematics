# NovaRide Next Generation Ecosystem

This document defines the high-level NovaRide application family and the shared
backend services used by every participant. It is a controlled-pilot product
contract; it does not replace the existing AfriRide execution spine.

For the full documentation map, see:

- `docs/architecture/NOVARIDE_DOCUMENTATION_TREE.md`

## Application Family

| App | Primary users | Platform | Backend role |
| --- | --- | --- | --- |
| NovaRide Rider App | Riders | Android, iOS, Web | `CUSTOMER` |
| NovaRide Driver App | Drivers | Android, iOS | `DRIVER` |
| NovaRide Operator App / Portal | Operations, safety, reliability | Web | `OPERATOR` |
| NovaRide Inspector App / Portal | Field inspectors, compliance | Android Tablet, Web | `VERIFIER` |
| NovaRide Fleet Portal | Fleet owners | Web | `FLEET_OWNER` |
| NovaRide Merchant Portal | Hotels, airports, venues, institutions | Web | `PARTNER` |
| NovaRide Corporate Portal | Corporate customers, government, NGOs | Web | `CLIENT` |
| NovaRide Trust & Safety Portal | Safety and compliance teams | Web | `OPERATOR` |
| NovaRide Customer Support Portal | Support agents | Web | `OPERATOR` |
| NovaRide Administrator Portal | Platform administrators | Web | `ADMIN` |
| NovaRide Developer Portal | Partners, integrators, developers | Web | `DEVELOPER` |

## API Contract

The ecosystem contract is exposed through:

- `GET /v1/novaride/ecosystem`
- `GET /v1/novaride/platform/architecture-contract`
- `GET /v1/novaride/{surface_key}/workspace`
- `GET /v1/novaride/operator/dashboard-contract`
- `GET /v1/novaride/fleet/manager-contract`
- `GET /v1/novaride/business/portal-contract`
- `GET /v1/novaride/admin/contract`
- `GET /v1/novaride/inspector/app-contract`
- `GET /v1/novaride/support/contract`
- `GET /v1/novaride/partner/portal-contract`

The workspace endpoint maps each app to existing governed AfriRide/NovaTech
routes instead of granting direct provider access.

## Shared Platform Architecture

The shared NovaRide architecture contract defines the boundary between app
interfaces, the NovaRide API gateway, and the backend execution platform.

High-level structure:

```text
              NovaRide Apps
                    |
   Passenger App   Driver App   Operator Dashboard
                    |
               NovaRide API
                    |
           Shared NovaRide Platform
```

Architecture principle:

```text
Apps = Interface
Platform = Authority
```

App layer responsibilities:

- Passenger App requests rides and displays trip state.
- Driver App receives assigned trips and displays execution state.
- Operator Dashboard monitors, escalates, and reviews evidence.
- Apps send requests and display data; they do not execute core authority.

NovaRide API gateway responsibilities:

- request validation
- NovaID authentication
- RBAC enforcement
- backend service routing

Shared platform services:

- NovaID for identity, authentication, roles, and access control.
- NovaPay for ride payments, driver earnings, refunds, wallets, corporate billing, and partner billing.
- Dispatch Engine for ride matching, assignment, and ride state transitions.
- Pricing Engine for fare calculation, surge rules, promotions, and pricing explanation.
- Maps & Routing for GPS tracking, ETA, navigation, and trip path recording.
- Trust Engine for safety, compliance, verification, fraud detection, and SOS handling.
- NovaNotify for push, SMS, email receipts, and operational alerts.
- Analytics Engine for ride data, revenue tracking, demand forecasting, and reporting.
- Audit & Replay for logs, trip replay, compliance evidence, and decision traceability.

Backend authority controls:

- dispatch decisions
- NovaPay payments
- pricing calculations
- fraud detection
- external integrations

App-forbidden authority:

- payment processing
- pricing mutation
- dispatch bypass
- direct provider access

Ride request flow:

```text
Passenger app requests ride
-> API validates request with NovaID
-> Pricing Engine estimates fare
-> Dispatch Engine matches driver
-> Driver app receives request
-> Driver accepts
-> Maps tracks trip
-> Trip completes
-> NovaPay processes payment
-> Audit Engine stores logs
-> Analytics updated
```

Cross-app service matrix:

| App | Services |
| --- | --- |
| Passenger | Pricing, Dispatch, NovaPay |
| Driver | Dispatch, Maps, Earnings |
| Operator | Analytics, Dispatch, Audit |
| Fleet | Analytics, NovaPay |
| Business | NovaPay, Analytics |
| Admin | RBAC, Pricing, Audit |
| Inspector | Trust, Audit |
| Support | Replay, NovaPay |
| Partner | Dispatch, Billing |

## Operator Dashboard

The NovaRide Operator Dashboard is the controlled-pilot command center for the
mobility platform. It is the human and system decision layer above backend
authority, not a bypass around backend authority.

Implemented contract modules:

- Operations
- Ride Management
- Driver Monitoring
- Safety & Emergency
- Analytics Dashboard
- NovaRide Ecosystem Panel
- Support & Escalation

The dashboard contract exposes:

- module purpose, features, actions, backend integrations, and status
- left navigation structure
- main and side-panel layout zones
- allowed operator controls
- forbidden bypass actions
- existing API alignment
- next-phase advanced capabilities

Allowed operator controls:

- manual dispatch
- ride reassignment
- monitoring
- emergency handling

Forbidden operator actions:

- direct payment execution
- direct provider integrations
- backend rule bypass

Authority ownership remains:

| Function | Owner |
| --- | --- |
| Dispatch | Backend |
| Payments | NovaPay |
| Fraud detection | Trust Engine |
| Replay | Audit Engine |

## Fleet Manager

The NovaRide Fleet Manager is the controlled-pilot business control surface for
fleet owners and taxi/logistics operators. It is bound to the `FLEET_OWNER` RBAC
role.

Implemented contract modules:

- Fleet Management
- Driver Management
- Vehicle Management
- Maintenance & Compliance
- Financial Management
- Fleet Analytics

The Fleet Manager contract exposes:

- module purpose, features, actions, backend integrations, and status
- navigation structure
- RBAC allowed and forbidden controls
- backend authority model
- workflow sequence
- implemented and next-phase API route alignment
- ecosystem integrations with Driver, Operator, Inspector, Business, and NovaPay

Allowed fleet-owner controls:

- manage vehicles
- assign drivers
- view earnings and reports
- receive payouts through NovaPay

Forbidden fleet-owner actions:

- override dispatch logic
- direct payment provider access
- bypass trust/compliance checks

Existing route alignment:

- `/v1/afriride/fleet/summary`
- `/v1/afriride/fleet/drivers`
- `/v1/novaride/fleet/workspace`

Next-phase route contracts:

- `/v1/fleet/vehicles`
- `/v1/fleet/maintenance`
- `/v1/fleet/earnings`
- `/v1/fleet/payouts`
- `/v1/fleet/analytics`

## Business Portal

The NovaRide Business Portal is the controlled-pilot corporate travel surface
for companies, organizations, and government agencies. It is bound to the
`CLIENT` RBAC role with `Admin`, `Manager`, and `Employee` sub-roles.

Implemented contract modules:

- Corporate Travel Management
- Employee Management
- Approval Workflow
- Business Wallet & Billing
- Department Budgets
- Reporting & Analytics

The Business Portal contract exposes:

- module purpose, features, actions, backend integrations, and status
- navigation structure for dashboard, employees, bookings, approvals, finance, budgets, and reports
- role and sub-role definitions
- RBAC allowed and forbidden controls
- backend authority ownership for dispatch, payments, identity, approvals, pricing, and audit
- workflow sequence from company onboarding through invoicing and reporting
- implemented and next-phase API route alignment
- ecosystem integrations with Passenger, Operator, Fleet, NovaPay, and NovaID

Allowed business controls:

- book rides
- approve or reject ride requests
- manage employees
- view billing and reports

Forbidden business actions:

- direct payment execution
- dispatch logic bypass
- pricing rule bypass

Existing route alignment:

- `/v1/novatech/organizations/{organization_id}/platform`
- `/v1/novatech/organizations/{organization_id}/billing`
- `/v1/novaride/business/workspace`

Next-phase route contracts:

- `/v1/business/employees`
- `/v1/business/approvals`
- `/v1/business/bookings`
- `/v1/business/budgets`
- `/v1/business/reports`

## Admin

The NovaRide Admin is the controlled-pilot governance, control, and
configuration surface for platform administrators, compliance officers, and
system operators. It defines how NovaRide behaves; it does not execute rides or
manually process payments.

Implemented contract modules:

- User & Role Management
- Driver & Vehicle Approval
- Pricing & Service Configuration
- Geography & Service Zones
- Promotions & Campaigns
- Compliance & Audit
- System Health & Monitoring

The Admin contract exposes:

- module purpose, features, actions, backend integrations, and status
- navigation structure for dashboard, users, approvals, pricing, zones, promotions, audit, and system health
- ADMIN RBAC plus managed role catalog
- allowed and forbidden governance controls
- backend authority ownership for payments, dispatch, trust, logs, pricing, and identity
- workflow sequence from driver approval through pricing, service zones, health monitoring, and rule adjustment
- implemented and next-phase API route alignment
- ecosystem integrations with Passenger, Driver, Operator, Fleet, Business, and NovaPay

Allowed admin controls:

- configure platform rules
- approve participants
- control pricing and zones
- monitor compliance

Forbidden admin actions:

- direct ride execution
- manual payment processing
- audit/replay bypass

Existing route alignment:

- `/v1/afriride/rbac/catalog`
- `/v1/afriride/rbac/assignments`
- `/v1/novatech/saas/status`
- `/v1/ops/audit/dashboard`
- `/v1/novaride/admin/workspace`

Next-phase route contracts:

- `/v1/admin/users`
- `/v1/admin/drivers/approvals`
- `/v1/admin/vehicles/approvals`
- `/v1/admin/pricing`
- `/v1/admin/zones`
- `/v1/admin/promotions`
- `/v1/admin/system-health`

## Inspector App

The NovaRide Inspector App is the controlled-pilot physical-world validation
surface for field inspectors and compliance officers. It is bound to the
`VERIFIER` RBAC role and feeds evidence to Trust and Audit; it does not make the
final compliance authority decision.

Implemented contract modules:

- Inspection Workflow
- Driver Verification
- Vehicle Inspection
- Document Validation
- Photo & Evidence Capture
- Inspection Reports
- Compliance Status

The Inspector contract exposes:

- structured inspection workflow and navigation
- driver, vehicle, document, photo, evidence, report, and compliance modules
- compliant, pending, and non-compliant status types
- VERIFIER RBAC allowed and forbidden controls
- Trust Engine final authority for compliance
- Audit Engine replay requirement for evidence
- implemented and next-phase API route alignment
- ecosystem integrations with Driver, Fleet, Admin, Operator, and Trust Engine

Allowed inspector controls:

- perform inspections
- submit reports
- capture evidence
- validate documents

Forbidden inspector actions:

- approve payments
- bypass admin decisions
- bypass Trust Engine

Existing route alignment:

- `/v1/operator/public-verification/status`
- `/v1/core-platform/trust/explorer/{receipt_id}`
- `/v1/novaride/inspector/workspace`

Next-phase route contracts:

- `/v1/inspector/inspections`
- `/v1/inspector/reports`
- `/v1/inspector/upload`
- `/v1/inspector/compliance-status`

## Support

The NovaRide Support system is the controlled-pilot problem-resolution layer for
customer support agents, operations teams, and escalation specialists. It is
mapped to the `OPERATOR` role and resolves ride, refund, dispute, driver, and
passenger issues through replay-backed evidence.

Implemented contract modules:

- Customer Ticket Management
- Ride Lookup & Investigation
- Refund & Dispute Handling
- Driver & Passenger Assistance
- Escalation Management
- Audit & Replay Integration

The Support contract exposes:

- ticket, ride lookup, refund, assistance, escalation, and replay modules
- open, in-progress, resolved, and closed ticket statuses
- level 1, level 2, and level 3 escalation levels
- OPERATOR RBAC allowed and forbidden controls
- NovaPay backend-only refund execution
- Pricing Engine fare validation
- Audit Engine replay requirement for evidence
- implemented and next-phase API route alignment
- ecosystem integrations with Passenger, Driver, Operator, NovaPay, Audit, and Trust

Allowed support controls:

- view ride data
- manage tickets
- request refunds
- contact users
- escalate cases

Forbidden support actions:

- bypass NovaPay
- mutate pricing rules
- bypass audit logs
- directly execute payments

Existing route alignment:

- `/v1/rider/rides/{ride_id}`
- `/v1/rider/rides/{ride_id}/receipt`
- `/v1/operator/replay-exceptions`
- `/v1/novaride/support/workspace`

Next-phase route contracts:

- `/v1/support/tickets`
- `/v1/support/refunds`
- `/v1/support/escalations`
- `/v1/support/ride-lookup`

## Partner Portal

The NovaRide Partner Portal is the controlled-pilot B2B and B2B2C integration
surface for hotels, airports, event organizers, corporations, and travel
agencies. It lets external organizations book rides for guests, manage bulk
transport, track usage, and review billing without direct control over dispatch,
pricing, payments, or drivers.

Implemented contract modules:

- Ride Booking & Widget Integration
- Guest Transport Management
- Bulk Ride Requests
- Partner Reporting
- Billing & Payments
- Partner Configuration

The Partner contract exposes:

- partner types for airports, hotels, events, corporations, and travel agencies
- booking widget, guest transport, bulk request, reporting, billing, and configuration modules
- PARTNER RBAC allowed and forbidden controls
- Dispatch Engine authority for ride execution
- NovaPay backend-only billing and payment execution
- Pricing Engine contract reference requirements
- implemented and next-phase API route alignment
- ecosystem integrations with Passenger, Driver, Operator, Fleet, NovaPay, and Analytics

Allowed partner controls:

- book guest rides
- manage bulk transport
- view reports and billing
- configure booking settings

Forbidden partner actions:

- dispatch logic bypass
- direct payment processing
- pricing rule bypass
- direct driver access

Existing route alignment:

- `/v1/partners/registry`
- `/v1/partner/verify`
- `/v1/novaride/partner/workspace`

Next-phase route contracts:

- `/v1/partner/bookings`
- `/v1/partner/bulk-requests`
- `/v1/partner/reports`
- `/v1/partner/billing`
- `/v1/partner/guests`

## Shared Platform

All NovaRide apps share:

- NovaID for identity and authentication.
- Policy Engine for jurisdiction, role, safety, and operational policy decisions.
- NovaPay for ride payments, wallets, refunds, driver earnings, and corporate billing.
- Dispatch Engine for driver matching and ride lifecycle coordination.
- Matching Engine for driver selection, queue balancing, and assignment explainability.
- Pricing Engine for fare estimates and deterministic price explanation.
- Maps & Routing for navigation, ETA, route display, and trip timeline.
- Trust Engine for driver and rider verification, safety, fraud monitoring, and SOS escalation.
- Inspection Registry for vehicle, driver, permit, insurance, roadworthiness, and evidence records.
- Incident Registry for SOS, safety escalation, incident lifecycle, and closure evidence.
- NovaNotify for push, SMS, email, receipts, and operational alerts.
- Analytics Engine for utilization, cancellations, demand, revenue, and fleet reporting.
- Audit & Replay for compliance logs, route replay, proof receipts, and verification.
- Event Platform for ride lifecycle event stream, replay, evidence binding, and proof emission.
- Control Plane for feature gates, RBAC, tenant controls, policies, and operational governance.

## 10/10 App/Web/Portal Stack

The next-generation stack is organized as one governed platform with
role-specific interfaces:

| Surface | Primary purpose |
| --- | --- |
| Rider App | Booking, live tracking, wallet, receipts, replay, and support |
| Driver App | Ride queue, navigation, trip lifecycle, earnings, trust score, and diagnostics |
| Operator App / Portal | Live control, dispatch, safety, reliability, provider health, and operational alerts |
| Inspector App / Portal | Vehicle, driver, document, permit, insurance, and regulatory compliance |
| Fleet Portal | Vehicle, driver, maintenance, fuel, performance, and fleet reporting |
| Merchant Portal | Guest ride booking, vouchers, invoices, settlement, and partner analytics |
| Corporate Portal | Employee travel, approvals, cost centres, budgets, invoices, and analytics |
| Trust & Safety Portal | SOS cases, incident timelines, replay, evidence viewer, and risk scoring |
| Customer Support Portal | Customer search, ride search, replay, disputes, refunds, and receipt verification |
| Administrator Portal | Organizations, RBAC, pricing rules, geofencing, feature flags, licensing, and providers |
| Developer Portal | API keys, SDKs, sandbox, webhooks, documentation, and usage analytics |

### Operator App / Portal

Purpose: live control, dispatch, safety, and reliability.

Core modules:

- Live Operations Dashboard
- Live Map: rides + drivers
- Manual Dispatch Override
- Driver Availability
- Demand Heatmap
- Incident Monitoring
- SOS Escalation
- Ride Replay
- Payment / Receipt Status
- Provider Health
- Operational Alerts

Core workflow:

```text
Monitor city
-> detect issue
-> inspect ride/driver
-> override dispatch if needed
-> escalate incident
-> verify replay/evidence
-> close operation log
```

### Inspector App / Portal

Purpose: vehicle, driver, and regulatory compliance.

Core modules:

- Vehicle Inspection
- Driver Verification
- License / Permit Check
- Insurance Check
- Roadworthiness Checklist
- Photo Evidence Capture
- Compliance Score
- Inspection History
- Regulatory Export
- Violation / Suspension Workflow

Core workflow:

```text
Select driver/vehicle
-> verify documents
-> inspect vehicle
-> capture evidence
-> approve / reject / suspend
-> generate compliance proof
```

## AI And Intelligence Layer

Every application connects to the shared intelligence service:

- Demand Forecasting
- Driver Position Prediction
- ETA Prediction
- Fraud Detection
- Safety Scoring
- Dynamic Pricing
- Traffic Intelligence
- Dispatch Optimization
- Operational Insights

## Evidence-Backed Trust Layer

Every ride is reconstructed from evidence:

```text
Ride Request
-> Dispatch Decision
-> Driver Assignment
-> Pickup
-> Trip
-> Payment
-> Receipt
-> Replay Timeline
-> Verification Package
```

## 10/10 Upgrade Principle

```text
Rider/Driver apps request and display.
Operator/Inspector portals control quality and compliance.
Control Plane decides.
Execution Plane performs.
Event Platform proves.
```

## Authority Boundary

Mobile apps request and observe. They do not directly call payment networks,
maps providers, settlement providers, or notification providers for
authority-sensitive actions.

The backend owns:

- dispatch authority
- payment and settlement authority through NovaPay
- trust and safety evaluation
- replay and audit evidence
- external provider integration

## Ride Lifecycle

```text
passenger_requests_ride
nearest_driver_matched
driver_accepts
driver_arrives
passenger_pickup
trip_in_progress
destination_reached
payment_via_novapay
driver_settlement
ratings_and_feedback
```

## Implementation Notes

The controlled-pilot router now exposes the NovaRide ecosystem contract from
`afritech.api.afriride_next_gen_mobile_api`. The operator dashboard consumes the
same contract so the product family is visible next to operational readiness,
NovaPay live-test status, replay health, and audit evidence.
