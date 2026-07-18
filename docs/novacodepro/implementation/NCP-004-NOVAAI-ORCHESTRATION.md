# NCP-004 — Governed NovaAI Orchestration

Status: implemented internally

Scope:

- governed request classification
- clarification workflow
- requirements generation
- plan generation
- risk classification
- policy evaluation
- human approval
- deterministic execution and verification
- evidence and replay timelines
- cancellation and rollback controls
- agent and tool registries

Implementation notes:

- The AI surface is exposed at `/v1/novacodepro/ai`.
- Execution state is persisted server-side in the NovaCodePro repository.
- Tenant and workspace access are derived from authenticated claims and normalized to the repository tenant key.
- The implementation uses a deterministic model provider by default and fails closed when a real provider is not configured.

Known limitation:

- Browser-based E2E automation could not be added because the local repository does not currently include a browser automation framework.
