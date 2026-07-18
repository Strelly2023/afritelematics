# NCP-007 — Development Studio & Governed Code Generation

Status: IMPLEMENTED_INTERNAL

This phase adds the governed Development Studio surface, backend API router, repository-aware code generation service, safe patch application, validation and review workflows, commit and pull-request proposal handling, evidence capture, and portal integration.

Implemented capabilities:

- Development workspaces, sessions, tasks, generation requests, change sets, validations, reviews, approvals, commit proposals, pull-request proposals, command execution, evidence, and timeline records.
- Tenant-scoped authorization and correlation-aware audit events.
- Repository browser endpoints for tree, file, search, status, and diff.
- Deterministic code generation path for automated verification.
- Frontend Development Studio shell wired into the NovaCodePro app registry.

External blockers:

- Real browser E2E automation is blocked because this environment does not provide a configured browser runtime or Playwright installation.
- Live provider verification is blocked until external model-provider credentials are configured.

Related verification:

- Backend tests exercise workspace, session, generation, approval, evidence, and isolation flows.
- Portal tests cover route wiring and Development Studio source surfaces.
- Build and repository validation must be rerun in the active worktree before certification claims.
