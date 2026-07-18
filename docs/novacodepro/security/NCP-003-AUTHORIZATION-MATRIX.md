# NCP-003 Authorization Matrix

Status: implemented with server-side enforcement.

Roles exercised in tests

- Platform Administrator
- Product Manager
- Developer
- Auditor
- External Regulator

Observed rules

- Product Manager can select a workspace, create projects, create requests, add milestones, add work items, submit requests, assign reviewers, add comments, upload attachments, and archive projects when route/service permissions allow it.
- Developer can create projects and requests in the supported internal preview flow.
- Auditor can read but cannot modify projects.
- External Regulator can be blocked from internal project access.
- Cross-tenant project access is rejected with `project_forbidden`.
- Cross-tenant request access is rejected with `request_forbidden`.
- Workspace membership is required for workspace-scoped access.

ABAC inputs

- tenant_id
- organization_id
- workspace_id
- role
- permissions
- session_id
- correlation_id

Security notes

- Tenant and workspace context are derived from authenticated server-side session state.
- Browser-supplied tenant and organization values are not trusted for authorization.
- Session selection rotates cookies and refresh tokens so the active workspace is server-authoritative.
