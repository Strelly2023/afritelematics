# NovaTech Platform Constitution

Status: `RATIFIED`  
Version: `1.0.0`  
Governing ADR: `ADR-0049`

## Article I — Supremacy

This Constitution is the highest NovaTech platform authority beneath the
canonical AfriTech Constitution and applicable law. ADRs, contracts, schemas,
rules, code, deployment configuration, and operations MUST conform to it.
Conflicting lower-level behavior is invalid.

## Article II — Bounded authority

Every component has explicitly declared authority. No product, operator,
federation peer, AI model, worker, or administrative interface may escalate its
own authority. External observations and consensus are evidence, not local
execution authority.

## Article III — Governed execution

Authoritative mutation requires tenant-bound identity, policy authorization,
schema-valid input, deterministic execution, immutable evidence, replay data,
and an auditable event. Mandatory stages are non-bypassable and fail closed.

## Article IV — Truth and evidence

Authoritative claims MUST be supported by verifiable evidence. Replay confirms
execution equivalence. Evidence is append-only and cryptographically bound to
its payload, policy, schema, versions, actor, tenant, and execution result.

## Article V — Sovereignty and privacy

Tenants retain bounded control of identity, policy, keys, data location,
retention, export, and federation. Cross-domain processing requires explicit
purpose, policy, minimization, and an auditable trust agreement.

## Article VI — Product/platform boundary

Products own domain workflows and user experience. Platform capabilities own
identity, policy, payment rails, execution controls, signing, evidence, replay,
federation, security primitives, and shared operational infrastructure.

## Article VII — Security and reliability

Zero-trust controls apply to people, workloads, nodes, and integrations.
Production capability requires measurable SLOs, bounded error budgets, recovery
objectives, incident response, key rotation, backups, rollback, and ownership.

## Article VIII — AI

AI has no inherent authority. AI proposals, predictions, and generated actions
are untrusted inputs until admitted by policy. Governed AI use MUST be
attributable, versioned, evidence-producing, reviewable, and replayable to the
extent technically possible; irreducible nondeterminism MUST be isolated from
authoritative state transition.

## Article IX — Evolution

Constitutional amendments require an accepted ADR, impact analysis, migration
plan, compatibility declaration, security review, evidence of validation, and
recorded approval. Emergency controls may suspend capability but may not
silently rewrite constitutional meaning.

## Article X — Enforcement

Contracts MUST be represented in machine-readable form where feasible. CI
validators reject drift before deployment. Runtime guards reject invalid
execution. Audits verify that deployed behavior matches the ratified contract.
