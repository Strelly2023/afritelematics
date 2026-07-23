# NovaRide market research and delivery plan

Status: research framework approved for execution; primary research results are **not yet available**.

## Research questions

| Workstream | Questions | Participants/data | Minimum target | Owner | Current state |
|---|---|---|---:|---|---|
| Rider demand | Journey frequency, reliability, price, payment, safety and accessibility needs | Adults who use ride-hail, taxi or community transport | 30 interviews and 200 survey responses per launch region | Product research | EXTERNAL_BLOCKED |
| Driver supply | Earnings, costs, working limits, acceptance, safety and app constraints | Active/prospective drivers | 25 interviews and 100 survey responses | Driver operations | EXTERNAL_BLOCKED |
| Fleet demand | Utilisation, maintenance, compliance, telematics and settlement needs | Fleet owners/managers | 12 interviews | Fleet product | EXTERNAL_BLOCKED |
| Corporate mobility | Policy, budget, duty-of-care, reporting and invoicing | Employers/institutions | 12 interviews | Corporate product | EXTERNAL_BLOCKED |
| Government/regulator | Licensing, reporting, privacy, safety and data-release rules | Transport and privacy authorities | All applicable authorities | Legal/compliance | EXTERNAL_BLOCKED |
| Airport/event | Holding areas, queue rules, permits, accessibility and incident response | Airport/venue operators and drivers | 6 operator workshops | Marketplace operations | EXTERNAL_BLOCKED |
| Competitors | Price, wait time, reliability, safety, support and driver proposition | Public terms plus lawful mystery shopping | 3 comparable services per region | Strategy | DESK_RESEARCH_PENDING |
| Partners | Identity, payments, maps, messaging, insurance and roadside availability | Qualified providers | 2 options per critical service | Partnerships | RFI_PENDING |

## Interview guide

1. Describe the participant's most recent relevant journey or operational shift.
2. Identify the outcome, failure points, workarounds and financial impact.
3. Rank reliability, price, safety, accessibility, support and payment concerns.
4. Test the trust/evidence proposition without promising unavailable features.
5. Explore poor-connectivity, device, language and accessibility constraints.
6. Ask what would prevent adoption and what evidence would create confidence.
7. Record region, participant role and relevant journey context—not unnecessary identity data.

## Survey instrument

The survey records journey frequency, mode alternatives, typical spend bands, wait-time tolerance, cancellation experience, preferred payment modes, accessibility needs, safety expectations, support expectations and likelihood to participate in a controlled pilot. Commercially sensitive assumptions must use ranges. Free-text responses must be optional.

## Recruitment, consent and privacy

- Recruit across geography, gender, age, disability, device capability and income bands relevant to the launch region.
- Do not recruit current employees as a substitute for customers without labelling the bias.
- Obtain informed consent, explain recording and retention, and allow withdrawal.
- Collect the minimum personal data; separate contact details from research responses.
- Restrict raw data by role and region; publish only aggregated findings.
- Legal/privacy owners must approve the protocol before participant contact.

## Evidence register

Each study records protocol version, owner, approver, dates, region, recruitment source, sample achieved, exclusions, consent evidence, anonymised dataset identifier, analysis method, limitations, findings, product decisions and requirement links. Empty templates do not count as completed research.

## Delivery roadmap

| Stage | Entry | Deliverables | Exit | Accountable owner |
|---|---|---|---|---|
| Foundation | Baseline accepted | Requirements, architecture, business assumptions, provider decisions | Critical scope traceable and approved | Product director |
| Engineering closure | Foundation exit | Core journeys, support/inspector, analytics foundation, production guards | Current-commit automated gates pass | Engineering director |
| Integration certification | Approved environments | PostgreSQL/Redis/Kafka, NovaID/NovaPay, browser and mobile builds | No unresolved blocker defect | Platform director |
| Controlled pilot | Staffed operations and allow-list | Real participants, limited geography/payments, daily evidence | Pilot criteria met | Pilot owner |
| Public pilot | Controlled-pilot approval | Larger bounded population, providers, support and telemetry | Public-pilot criteria met | Operations director |
| PRR/GA | Immutable RC and complete evidence | PRR, risk acceptance and approvals | Evidence-based decision | Release manager |

## RACI

| Decision/workstream | Accountable | Responsible | Consulted | Informed |
|---|---|---|---|---|
| Product scope | Product director | Product managers | Research, operations, engineering | Executive sponsor |
| Architecture | Architecture owner | Platform engineering | Security, data, mobile | Product and operations |
| Safety | Safety owner | Safety operations | Legal, trust, support | Release manager |
| Payments | Payments owner | Payments engineering | Finance, legal, NovaPay | Operations |
| Security/privacy | Security owner | Security/privacy teams | Architecture, legal | Executive sponsor |
| Pilot | Pilot owner | Regional operations | Support, safety, engineering | Participants and partners |
| Release | Release manager | Release engineering | All control owners | Executive approvers |

## Environment and dependency plan

Development may use explicit test adapters. Integration uses ephemeral PostgreSQL, Redis and Kafka. Pilot uses isolated regional tenants and provider sandbox/approved pilot modes. Production uses managed durable services, secret injection, observability, backup and recovery. Promotion is one-way through evidence gates; production data is never copied into lower environments without approved de-identification.

## Change control

Every material change records an owner, requirement, risk, compatibility impact, security/privacy impact, rollout, rollback, tests, evidence and approval. Emergency changes require incident linkage and retrospective approval. Scope expansion cannot silently inherit an earlier pilot or GA decision.
