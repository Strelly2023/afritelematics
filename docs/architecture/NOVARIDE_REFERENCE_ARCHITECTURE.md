# NovaRide Reference Architecture

Status: REFERENCE ARCHITECTURE
Classification: END-TO-END SYSTEM VIEW

Purpose: describe the canonical end-to-end structure of NovaRide for
engineering, operations, and review.

## Sequence Overview

```text
Rider/Driver/Operator App
-> API Gateway
-> Auth + Tenant Resolution
-> Policy Engine
-> Feature Flags
-> Approval Service (if required)
-> Workflow Orchestrator
-> Execution Service
-> Event Platform
-> Audit / Replay / Projections
-> Dashboard / Public Verification / Reporting
```

## Component Layers

### 1. Presentation layer

- rider app
- driver app
- operator dashboard
- admin panel
- support portal
- inspector app
- fleet portal
- business portal
- partner portal

### 2. Ingress layer

- API gateway
- websocket gateway
- public verification gateway

### 3. Control plane

- policy engine
- feature flag service
- approval service
- workflow orchestrator
- trust engine
- compliance engine

### 4. Execution plane

- trip service
- dispatch service
- pricing service
- payment service
- driver service
- fleet service
- support service
- notification service
- maps and routing service

### 5. Event platform

- event registry
- event store
- replay engine
- consumer projections

### 6. Storage and infrastructure

- PostgreSQL
- Redis
- object storage
- search index
- analytics warehouse
- queue or log transport

## Trust Boundaries

- apps cannot write authoritative truth
- control plane cannot silently execute business side effects
- execution plane cannot bypass policy
- public verification cannot mutate state

## Core Guarantees

- tenant isolation
- deterministic replay
- idempotent command handling
- schema-versioned events
- bounded execution
- auditable decisions

