# NovaWorkflow Fabric

NovaWorkflow Fabric is the governed workflow layer for NovaCodePro. It adds a
durable workflow lifecycle, multiple workflow views, connector registry,
marketplace templates, replay, evidence, and role-aware APIs on top of the
existing NovaCodePro repository.

## Lifecycle

`DRAFT -> VALIDATED -> COMPILED -> REVIEWED -> APPROVED -> DEPLOYED -> RUNNING -> PAUSED -> RESUMED -> COMPLETED -> VERIFIED -> EVIDENCE_GENERATED -> ARCHIVED`

## Views

- Business View
- BPMN View
- Flowchart View
- State Machine
- Sequence Diagram
- Timeline
- Execution Graph
- Audit Timeline

## Core APIs

- `POST /v1/workflows`
- `GET /v1/workflows`
- `GET /v1/workflows/{id}`
- `POST /v1/workflows/{id}/validate`
- `POST /v1/workflows/{id}/compile`
- `POST /v1/workflows/{id}/review`
- `POST /v1/workflows/{id}/approve`
- `POST /v1/workflows/{id}/deploy`
- `POST /v1/workflows/{id}/execute`
- `POST /v1/workflows/{id}/pause`
- `POST /v1/workflows/{id}/resume`
- `POST /v1/workflows/{id}/complete`
- `POST /v1/workflows/{id}/verify`
- `POST /v1/workflows/{id}/evidence`
- `GET /v1/workflows/{id}/views`
- `GET /v1/workflows/{id}/timeline`
- `GET /v1/workflows/{id}/replay`
- `GET /v1/workflows/{id}/analytics`

## Fabric Surface

- `GET /v1/workflow-fabric`
- `GET /v1/workflow-fabric/connectors`
- `GET /v1/workflow-fabric/marketplace`

## Storage

Workflow fabric records are persisted through the existing NovaCodePro durable
repository. Workflow records, fabric records, execution records, review
records, approvals, evidence bundles, and replay events survive process
restart when the underlying database does.
