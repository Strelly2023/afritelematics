# NCP-003 Workspace, Projects and Requests

Status: implemented and internally verified.

Date: 2026-07-18

Scope delivered

- Server-authoritative workspace selection and session rotation.
- Workspace, project and request APIs on `/v1/novacodepro`.
- Project creation, editing, archival, milestones, work items and risks.
- Request drafts, submission, transition, assignments, comments and attachments.
- Activity events, notifications and audit persistence.
- Portal routing for `/novacodepro/workspace`, `/novacodepro/projects`, and `/novacodepro/requests`.
- Dedicated NCP-003 API client and portal surface.

Implementation notes

- The new NCP-003 router is mounted ahead of the legacy platform project/request handlers so the NCP-003 flow is the active path.
- Session selection now rotates access, refresh and CSRF cookies and persists the selected workspace server-side.
- Tenant context is normalized server-side and cross-tenant project/request access is rejected.
- Attachment uploads are tenant/workspace scoped and reject disguised executables.

Verification completed

- Backend NCP-003 API flow tests.
- Portal package tests.
- Portal production build.
- Session login/logout regression tests.

Known limitations

- A true browser-driven Playwright-style E2E harness is not yet committed in this repository.
- Physical device verification and external deployment verification remain outside local repository evidence.
