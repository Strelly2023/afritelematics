# NCP-004 AI Security Model

Controls implemented:

- tenant isolation on execution, agent, tool, approval, evidence, and replay records
- workspace validation before execution creation and state transitions
- RBAC checks at the route layer
- ABAC-style enforcement in the service layer for tenant, workspace, and approval scope
- fail-closed handling for missing provider configuration
- immutable execution timeline and evidence records
- deterministic test provider for local and automated verification

Denied operations:

- cross-tenant execution access
- cross-workspace mutation
- approval reuse after completion
- plan execution without approval
- execution completion without verification

Known limitation:

- real model-provider verification is blocked until external credentials are configured.
