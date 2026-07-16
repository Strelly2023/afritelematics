# NovaCodePro Solution Engineering Portal

The portal exposes the governed customer solution lifecycle through the existing
`/novacodepro` experience. It uses the live Solution Engineering and Workflow
Fabric APIs and preserves tenant, role, and project context in the browser.

## Routes

- `/novacodepro/solutions`
- `/novacodepro/solutions/customers`
- `/novacodepro/solutions/projects`
- `/novacodepro/solutions/projects/:projectId`
- `/novacodepro/solutions/projects/:projectId/:section`

## Windows

- Overview
- Customers
- Projects
- Discovery
- Requirements
- Business Analysis
- UX/UI
- Architecture
- Engineering
- Quality
- Security
- Compliance & Risk
- Releases
- Deployments
- Acceptance
- Operations
- Support & Evolution
- Workflow Fabric
- Approvals
- Knowledge
- Evidence

## Notes

- Sign-in and sign-out remain handled by the existing NovaID session flow.
- Direct access to unauthorized sections renders a 403 state.
- Offline or degraded backend responses fall back to cached read-only data when available.
- Approval, deployment, and acceptance actions always round-trip to the backend.
