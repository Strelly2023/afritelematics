# NovaTech Enterprise Scenario Registry 2026

## Purpose

The NovaTech Scenario Registry is the structured source for product design, QA, UAT, API testing, compliance validation, training, partner onboarding, and demonstrations.

It extends the existing scenario catalogs into a metadata-driven registry. Scenarios are no longer only examples; they are typed testable records with personas, corridors, classifications, test suites, and evidence requirements.

## Registry Tree

```text
NovaTech Scenario Registry
|
+-- Consumer
|   +-- Remittance
|   +-- Wallet
|   +-- QR Payments
|   +-- Cards
|   +-- Savings
|   +-- Investments
|   +-- Lending
|   +-- Insurance
|   +-- Bill Payments
|
+-- Business
|   +-- Merchant
|   +-- SME
|   +-- Corporate
|   +-- Payroll
|   +-- Treasury
|   +-- Supplier Payments
|
+-- Agent Banking
+-- Government
+-- Compliance
+-- Fraud
+-- Customer Support
+-- Disaster Recovery
+-- API Integration
+-- Mobile UI
+-- Performance
+-- Accessibility
```

## Standard Metadata

Every enterprise scenario uses the same metadata pattern:

| Field | Example |
| --- | --- |
| `scenarioId` | `NP-CONS-001` |
| `version` | `2026.1` |
| `domain` | `Consumer` |
| `category` | `International Transfer` |
| `personaId` | `PER-MIGRANT-WORKER` |
| `corridorId` | `COR-AU-CD` |
| `currencies` | `AUD -> CDF` |
| `amount` | `AUD 500` |
| `receiveMethod` | `Mobile Money` |
| `riskLevel` | `Low` |
| `kycLevel` | `Enhanced` |
| `amlRequired` | `true` |
| `sanctionsCheck` | `true` |
| `fraudChecks` | `Device`, `Velocity` |
| `expectedStatus` | `Completed` |
| `services` | `NovaID`, `NovaPay`, `NovaTrust` |
| `evidence` | `Receipt`, `Audit`, `Ledger` |
| `testSuites` | `API`, `UI`, `Regression` |
| `automation` | `true` |
| `uiTest` | `true` |
| `apiTest` | `true` |
| `regression` | `true` |

## Classifications

Scenarios can be tagged as:

- Happy Path
- Alternative Path
- Exception
- Compliance
- Fraud
- Recovery
- Performance
- Security
- Accessibility
- Offline
- Integration
- Disaster Recovery
- Negative Testing
- Boundary Testing

## Personas

Reusable personas live in the SDK as `scenarioPersonas`:

- First-time customer
- Returning customer
- Refugee
- International student
- Tourist
- Migrant worker
- Freelancer
- Small business owner
- Merchant
- Corporate finance officer
- NGO administrator
- Government officer
- Elderly customer
- Visually impaired customer
- Agent operator
- Compliance analyst

Scenarios reference personas by `personaId` instead of duplicating user descriptions.

## Corridor Library

Supported corridors live in the SDK as `scenarioCorridors`. Each corridor defines:

- Origin country
- Destination country
- Supported currencies
- Supported receive methods
- Settlement time
- Compliance requirements

Initial corridors include Australia, United States, Canada, United Kingdom, Europe, Middle East, and Africa origin markets.

| Region | Corridor Count |
| --- | ---: |
| Australia | 17 |
| United States | 17 |
| Canada | 17 |
| United Kingdom | 17 |
| Europe | 10 |
| Middle East | 9 |
| Africa | 10 |

Total global corridors: `97`.

The initial global set includes:

- Australia to DR Congo, Burundi, Rwanda, Uganda, Kenya, Tanzania, Zambia, Zimbabwe, Malawi, Nigeria, Ghana, South Africa, India, Philippines, Indonesia, Vietnam, and Nepal
- United States to DR Congo, Burundi, Rwanda, Uganda, Kenya, Tanzania, Zambia, Zimbabwe, Malawi, Nigeria, Ghana, South Africa, Mexico, India, Pakistan, Philippines, and Vietnam
- Canada to DR Congo, Burundi, Rwanda, Uganda, Kenya, Tanzania, Zambia, Zimbabwe, Malawi, Nigeria, Ghana, South Africa, India, Pakistan, Philippines, Nepal, and Bangladesh
- United Kingdom to DR Congo, Burundi, Rwanda, Uganda, Kenya, Tanzania, Zambia, Zimbabwe, Malawi, Nigeria, Ghana, South Africa, India, Pakistan, Bangladesh, Sri Lanka, and Nepal
- France, Belgium, Germany, Netherlands, Italy, Spain, and Portugal routes into selected African destinations
- United Arab Emirates, Qatar, Saudi Arabia, Kuwait, and Oman routes into selected Asian and African destinations
- South Africa, Kenya, Uganda, Burundi, Rwanda, Nigeria, and Ghana regional African corridors

## Test Coverage Matrix

Scenarios declare applicable suites:

- Unit
- Integration
- API
- UI
- Mobile
- Performance
- Security
- Compliance
- Accessibility
- End-to-End
- Regression
- Pilot
- Production Certification

This lets QA teams run targeted scenario subsets without running every scenario every time.

## Evidence Requirements

Governed scenarios specify expected evidence artifacts:

- Identity Verified
- KYC Complete
- AML Check
- Sanctions Check
- Device Trust
- Risk Score
- Ledger Entry
- Settlement Record
- Digital Signature
- Replay Evidence
- Audit Package
- PDF Receipt
- Customer Notification
- Operator Log

## Target Scale

| Domain | Target |
| --- | ---: |
| Consumer | 150 |
| Business | 120 |
| Merchant | 80 |
| Wallet | 70 |
| Agent Banking | 60 |
| Government | 60 |
| Compliance | 80 |
| Fraud | 80 |
| Customer Support | 60 |
| Recovery | 40 |
| API Integration | 120 |
| Mobile UI | 100 |
| Performance | 60 |
| Accessibility | 40 |

Total long-term target: `1120` structured scenarios.

## Current SDK Anchors

The registry is implemented in `packages/novatech-platform-sdk/src/index.ts`:

- `scenarioPersonas`
- `scenarioCorridors`
- `scenarioDomainTargets`
- `enterpriseScenarioRegistrySeed`
- `scenarioRegistrySummary`
- `novaTechScenarioCatalog`
- `novapayConsumerScenarioCatalog`
- `novapayConsumerFeatureScenarios`

The current documented journey count remains available through `scenarioRegistrySummary.currentDocumentedJourneys`.

## Consumer Scenario Expansion

The NovaPay Consumer catalog now includes scenarios `20-99`. Scenarios `70-99` add United States, Canada, and United Kingdom remittance and payment use cases:

- United States scenarios: salary to family, school fees, emergency medical support, mortgage support, business supplier payment, church donation, university tuition, freelancer payment, vacation support, and cash pickup
- Canada scenarios: family monthly support, parent medical bills, student allowance, import goods payment, mobile money transfer, business invoice, passport fee payment, charity donation, emergency cash pickup, and hotel deposit
- United Kingdom scenarios: salary remittance, house construction payment, family support, university fees, medical treatment, merchant payment, business supplier settlement, church donation, freelancer payment, and cash pickup

## Product Boundary Rule

The registry must preserve NovaTech boundaries:

```text
NovaID authenticates and manages identity.
NovaPay executes financial services.
NovaRide executes mobility services.
NovaPower enforces authorization and policy.
NovaTrust records evidence.
NovaAI is advisory only.
```

No registry entry may imply that NovaAI approves identity, approves payments, or dispatches rides.
