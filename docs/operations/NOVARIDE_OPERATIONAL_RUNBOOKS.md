# NovaRide Operational Runbooks

Status: OPERATIONAL RUNBOOK INDEX
Classification: LIVE OPERATIONS SURFACE

Purpose: define the minimum operational playbooks required for institutional
maturity.

## Core Runbooks

### Incident response

- detect
- triage
- contain
- restore
- review

### Disaster recovery

- restore control plane first
- restore event store and authoritative data
- restore read projections
- verify tenant isolation
- reopen execution only after validation

### Failover

- switch traffic at the ingress layer
- preserve idempotency
- preserve replay chain

### On-call

- acknowledge
- assess blast radius
- assign owner
- execute recovery steps
- log actions and evidence

### Service restoration

- recover platform services in dependency order
- verify policy and approval services before execution services
- verify events and audit before dashboards

### Manual dispatch

- operator reviews live state
- policy and trust gates are checked
- dispatch decision is recorded
- event is emitted

### Refund dispute

- support opens case
- verify receipt and replay
- check policy and approval needs
- execute via NovaPay only

### Driver onboarding

- verify identity
- verify vehicle
- verify compliance
- activate presence only after approval

### Vehicle inspection

- inspect
- capture evidence
- submit report
- update compliance status

## Operational Rule

No live recovery step should depend on undocumented tribal knowledge.

