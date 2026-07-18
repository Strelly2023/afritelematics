# NCP-007 API Contracts

Base path: `/api/v1/development`

Implemented route families:

- Workspaces
- Repository browser
- Sessions
- Tasks
- Generation requests
- Change sets
- Validation runs
- Reviews
- Approvals
- Commit proposals
- Pull-request proposals
- Evidence
- Timeline
- Command execution

All routes are tenant-scoped, correlation-aware, and guarded by role and permission checks. Mutating operations record evidence and audit events.

External verification note:

- A real browser-driven E2E contract is not certified in this environment because no browser runtime is available.
