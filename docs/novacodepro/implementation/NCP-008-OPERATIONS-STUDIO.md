# NCP-008 Operations Studio

NCP-008 adds the governed runtime operations control plane for NovaCodePro.

Implemented capabilities:

- operations workspaces, environments, services, deployments, alerts, incidents, actions, SLOs, recovery plans, and post-incident reviews
- policy-gated operational actions with approval workflow
- deterministic in-memory observability and runtime adapters
- protected `/api/v1/operations/*` APIs
- Operations Studio portal route at `/novacodepro/operations`
- runtime configuration exposure for the portal
- test and live-verification tooling

Limitations:

- Docker Compose runtime operations remain disabled by default.
- External provider adapters are defined but not live-configured here.
- Browser E2E and accessibility certification are not claimed unless separately executed.
