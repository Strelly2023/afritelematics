# NovaTech Platform Contract

Status: `ACTIVE`  
Contract version: `2.0.0`  
Constitutional authority: `docs/governance/PLATFORM_CONSTITUTION.md`  
Machine contract: `afritech/platform_contracts/platform.yaml`

## 1. Purpose and authority

NovaTech is a governed, multi-product execution platform. This contract defines
the mandatory architecture shared by every NovaTech product, service, API,
worker, automation, federation node, and AI-assisted subsystem.

The governing hierarchy is:

```text
Platform Constitution
  -> accepted ADR
  -> platform capability contract
  -> execution rule
  -> guard
  -> CI validator
  -> runtime enforcement
  -> evidence and audit
```

Lower authorities MUST cite and conform to their parent authority. A conflict is
resolved in favor of the highest authority. Runtime behavior may never silently
amend this contract.

## 2. Capability architecture

| Layer | Capability | Canonical systems | Authority |
|---|---|---|---|
| 0 | Infrastructure | compute, storage, network, event backbone | Resource availability only |
| 1 | Identity | NovaID | Authentication and tenant identity |
| 2 | Policy | NovaPower | Authorization and policy decisions |
| 3 | Execution | NovaScript, NovaPay, governed engines | Bounded state transition |
| 4 | Evidence | NovaTrust | Signed evidence production |
| 5 | Replay | NovaReplay | Deterministic verification |
| 6 | Federation | NovaFederation | Cross-node verification and exchange |
| 7 | Products | NovaRide, NovaHealth, NovaCommerce, others | Domain workflow only |

Dependencies MUST point downward or remain within a layer. Product code MUST
consume platform capabilities through declared contracts and MUST NOT replace
identity, policy, payment, signing, evidence, replay, or federation primitives.

## 3. Universal governed execution

Every state-changing operation MUST perform, in order:

```text
admission
  -> tenant-bound identity
  -> policy decision
  -> schema validation
  -> idempotency check
  -> deterministic execution
  -> domain event
  -> signed trust evidence
  -> replay record
  -> integration/analytics projection
```

Failure of a mandatory stage rejects or atomically rolls back the operation.
Partial success MUST NOT be represented as final success.

Commands express intent. Domain events record authoritative state transition.
Trust events record evidence production. Integration events notify external
consumers. Analytics events are non-authoritative projections.

## 4. Platform laws

1. Identity, policy, evidence, and replay are non-bypassable.
2. Execution is deterministic over declared inputs and controlled dependencies.
3. State mutation is atomic, idempotent, tenant-bound, observable, and replayable.
4. External systems and federation peers are untrusted until verified.
5. Evidence is immutable; corrections create linked successor records.
6. AI output is advisory unless admitted through the same policy and execution
   path as any other command.
7. Federation verifies and exchanges trust; it does not create local execution,
   payment, settlement, licensing, or policy authority.
8. Products own domain workflows. The platform owns shared infrastructure and
   constitutional controls.
9. Every public contract is schema-versioned and lifecycle-governed.
10. Production services publish measurable reliability and recovery objectives.

## 5. Trust levels

| Level | Name | Required proof |
|---|---|---|
| 0 | Unverified | No platform verification |
| 1 | Authenticated | Valid NovaID identity |
| 2 | Policy Verified | Bound NovaPower decision |
| 3 | Evidence Produced | Signed NovaTrust evidence |
| 4 | Replay Verified | Deterministic replay succeeds |
| 5 | Federated Verified | Trusted peer/quorum verification succeeds |
| 6 | Publicly Verifiable | Exportable verification bundle and public key path |

APIs returning governed outcomes MUST expose the achieved trust level and MUST
not claim a higher level than the attached evidence proves.

## 6. Sovereign multi-tenancy

Every authoritative record MUST carry a tenant or sovereign-domain identifier.
Identity, encryption context, policy, storage, keys, quotas, event partitions,
evidence, replay, retention, export, and deletion controls MUST preserve tenant
isolation. Cross-tenant access requires an explicit, auditable federation or
delegation contract. Global operators do not receive implicit domain authority.

## 7. Lifecycle contracts

Products progress through `CONCEPT`, `PROTOTYPE`, `PILOT`, `PRODUCTION`,
`CERTIFIED`, `FEDERATED`, and `RETIRED`.

APIs progress through `DRAFT`, `EXPERIMENTAL`, `STABLE`, `LTS`, `DEPRECATED`,
and `RETIRED`.

Promotion requires the gates declared in
`afritech/platform_contracts/platform.yaml`. Retirement requires notice,
migration, evidence retention, and a verified shutdown plan.

## 8. Version vector

Every governed envelope MUST independently identify:

- platform version
- contract version
- schema version
- API version
- replay version
- evidence version
- signature version

Compatibility is explicit. A major version may break compatibility. A minor
version may add backward-compatible behavior. A patch version may fix behavior
without changing the contract.

## 9. Reliability, security, and operations

Production services MUST declare an SLI, SLO, error budget, incident severity
model, RTO, RPO, backup policy, rollback path, key rotation policy, ownership,
and escalation route. Security is zero-trust: authenticate every workload,
authorize every operation, minimize privilege, encrypt in transit and at rest,
segment trust domains, and fail closed on integrity failure.

## 10. Developer platform

NovaTech MUST provide governed golden paths through versioned templates, SDKs,
CLI commands, local verification, developer portal documentation, contract
tests, and deployment scaffolding. Golden paths accelerate delivery but do not
bypass constitutional gates.

## 11. AI governance

NovaAI is a platform capability, not an independent authority. Model identity,
model version, prompt template, policy decision, data classification, tool use,
human approval, output hash, evidence, and replay metadata MUST be recorded for
governed AI operations. High-impact decisions require deterministic policy
gates and human approval where law or risk classification requires it.

## 12. Companion standards

- `docs/governance/PLATFORM_CONSTITUTION.md`
- `docs/standards/API_CONTRACT_STANDARD.md`
- `docs/standards/TRUST_PROTOCOL_SPECIFICATION.md`
- `docs/standards/PRODUCT_ARCHITECTURE_STANDARD.md`
- `docs/standards/SECURITY_OPERATIONS_STANDARD.md`
- `docs/standards/FEDERATION_PROTOCOL.md`
- `docs/standards/OBSERVABILITY_STANDARD.md`
- `docs/standards/PLATFORM_RELEASE_POLICY.md`
- `docs/standards/AI_GOVERNANCE_STANDARD.md`
- `docs/standards/DATA_EVENT_CONTRACT_STANDARD.md`

These documents specialize this contract. They may strengthen requirements but
may not weaken the Constitution or platform laws.

## 13. Enforcement

The canonical YAML contract and JSON Schemas are validated by
`python -m afritech.ci.novatech_platform_contract_validator`. Violations block
CI. Runtime services SHOULD consume `afritech.platform_contracts.runtime` so
trust levels, lifecycle states, version vectors, and capability-layer rules use
the same canonical vocabulary.

## 14. Contract distribution and negotiation

The platform contract is distributed through the core platform contract portal.
Canonical schemas are published with SHA-256 digests and NovaTrust signatures.
Governed request admission validates the request and response schemas, binds
tenant and actor context to authenticated claims, and negotiates contract,
replay, evidence, and signature versions before execution.

Capability dependencies are projected into an automatically verified acyclic
graph. Federation nodes publish a compatibility manifest containing their
version vector, supported signature algorithms, capabilities, and
verification-only authority boundary. CI verifies schema publication history,
SDK version alignment, developer portal completeness, and architectural
compliance metrics.

NovaTech is therefore not a collection of applications. It is a
constitutionally governed platform ecosystem in which products inherit one
identity, policy, execution, evidence, replay, federation, security, and
operational model.
