# NovaCodePro Phase Roadmap

## Product Identity

AfriPro is kept as the product line and positioned as NovaCodePro for the
AI software engineering platform. Existing `afroprog` and `novaprogramming`
routes remain compatibility surfaces:

- AfriPro / NovaCodePro: user-facing software factory product line.
- AfriProg workspace: proposal-only productivity workspace.
- NovaProgramming: governed engineering control plane and authority path.

## Governance Chain

Every phase must preserve:

```text
ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI
```

Generated output remains proposal-only until replay, rule checks, guard checks,
and governance approval admit it into an execution path.

## Phase Summary

| Phase | Focus | Required Modules |
| --- | --- | --- |
| Phase 0 | SaaS foundation | core, organizations, accounts, subscriptions, catalog, audit, feature_flags, notifications, integrations |
| Phase 1 | AI core | prompt_engine, context_engine, thinker_engine, builder_engine, orchestrator, memory_engine |
| Phase 2 | Architecture engine | architecture_engine, pattern_library, diagram_engine, adr_engine, modeling_engine |
| Phase 3 | Code generation engine | code_engine, api_generator, service_generator, schema_generator, test_generator, refactor_engine |
| Phase 4 | Automation and DevOps | deployment_engine, ci_cd_engine, workflow_engine, infrastructure_engine, scheduler |
| Phase 5 | Testing and debugging | testing_engine, debug_engine, validation_engine, simulation_engine |
| Phase 6 | Monitoring and optimization | monitoring_engine, logging_engine, analytics_engine, optimization_engine, alerting_engine |
| Phase 7 | Knowledge and learning | knowledge_engine, documentation_engine, tutorial_engine, explanation_engine |
| Phase 8 | Apps layer | Studio, Dev, Architect, Automate, Learn, Operator, Admin |
| Phase 9 | Integration ecosystem | GitHub, GitLab, VS Code, cloud, Docker, Kubernetes, databases, third-party APIs |
| Phase 10 | Governance and enterprise | rbac_engine, policy_engine, compliance_engine, security_engine, audit_advanced, guard_engine |
| Phase 11 | Autonomous system builder | full-system generation, self-debugging, upgrade suggestions, adaptive architecture evolution |
| Phase 12 | NovaCodePro OS | multi-project orchestration, cross-system intelligence, company-level software generation, lifecycle automation |

## Current Implementation Boundary

The current implementation supports the AfriPro / NovaCodePro workspace as a
proposal-only surface and uses NovaProgramming for governed review, proof,
replay, and activation decisions. Phase 0 SaaS foundation is the next required
build step before NovaCodePro can be treated as a production SaaS product.

## Phase 0 Acceptance Criteria

- Multi-tenant organization and workspace model.
- Account and membership model with RBAC.
- Subscription plan and billing preview model.
- Catalog model for NovaCodePro apps and capabilities.
- Audit event model for all tenant-scoped operations.
- Feature flag model for phased rollout.
- Notification preference and delivery registry.
- Integration registry for GitHub, GitLab, cloud, container, database, and API providers.
- Tests proving tenant isolation, RBAC denial, audit capture, and backwards-compatible workspace behavior.
