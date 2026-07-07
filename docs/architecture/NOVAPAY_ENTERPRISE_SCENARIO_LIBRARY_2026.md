# NovaPay Enterprise Scenario Library 2026

The NovaPay Scenario Library is a structured registry of banking, payment, compliance, fraud, API, QA, UAT, and training journeys. It exists so product, QA, compliance, and partner teams can reuse the same scenario definitions instead of maintaining separate ad hoc lists.

## Why The Library Exists

- It standardizes how NovaPay scenarios are described.
- It keeps product boundaries explicit.
- It supports repeatable QA, UAT, compliance review, API testing, training, and demos.
- It scales beyond a flat catalog by separating domain, owner, evidence, policy, and test intent.

## Product Boundaries

- NovaID authenticates and verifies identity.
- NovaPay executes financial services.
- NovaRide handles mobility only.
- NovaTrust records evidence and audit trails.
- NovaAI remains advisory only.

## Scenario Schema

Every scenario includes:

- scenarioId
- domain
- title
- actors
- productsUsed
- sharedServicesUsed
- primaryProductOwner
- userStory
- preconditions
- workflowSteps
- expectedOutcome
- evidenceRequired
- policyChecks
- uiSurfaces
- apiSurfaces
- testType
- riskLevel
- complianceTags
- independenceRule

## Domain Matrix

| Domain | Minimum Coverage |
| --- | ---: |
| Consumer Remittance | 100 |
| Wallet Operations | 60 |
| Merchant Payments | 50 |
| Business Payments | 50 |
| Agent Banking | 40 |
| Cards | 40 |
| Savings & Investments | 30 |
| Lending | 30 |
| Insurance | 30 |
| Payroll | 30 |
| Government Services | 40 |
| Compliance / AML | 60 |
| Fraud & Risk | 60 |
| Customer Support | 40 |
| Recovery & Disaster | 30 |
| API / Integration Testing | 100 |

## QA Usage

- Run the library as a source of regression coverage.
- Filter by domain, risk level, or test type.
- Use the evidence and policy fields to select test fixtures and expected audit artifacts.

## UAT Usage

- Use the same scenarios to validate real product flows with business stakeholders.
- Keep acceptance criteria tied to `expectedOutcome` and `workflowSteps`.
- Use `independenceRule` to confirm that users can use NovaPay without NovaRide.

## Compliance Usage

- Use `policyChecks` and `evidenceRequired` to verify AML, KYC, sanctions, and audit requirements.
- Keep NovaAI advisory only.
- Keep financial activity tied to NovaTrust evidence.

## API Testing Usage

- Use `apiSurfaces` to choose the correct contracts.
- Use `sharedServicesUsed` for NovaID, NovaTrust, notification, and platform service dependencies.
- Keep API scenarios separate from UI-only walkthroughs.

## Training Usage

- Use the library to teach product ownership boundaries.
- Show how consumers, agents, merchants, and businesses follow different workflows.
- Teach that NovaPay is financial services only and does not own ride logic.

## Demo Usage

- Select one scenario per domain for product demonstrations.
- Present evidence artifacts alongside outcomes.
- Include NovaAI only when the scenario is explicitly advisory.

## How Not To Duplicate App Logic

- Do not encode payment execution logic inside screens.
- Do not place NovaRide workflows inside NovaPay.
- Do not place identity workflow logic inside NovaPay.
- Use shared SDK types for contracts, not duplicated business rules.
- Keep product-specific behavior inside each owning product.

## Current Coverage

- Total structured scenarios: 790
- NovaAI: advisory only
- NovaRide: only allowed in explicit cross-product scenarios, not in NovaPay core flows
