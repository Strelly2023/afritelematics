# NovaRide Production Control Plane

Status: CONTROL PLANE SPECIFICATION
Classification: GOVERNANCE AND DECISION SURFACE

## Purpose

The control plane evaluates requests before any execution service runs.

## Required Services

### Policy Engine

- deterministic evaluation
- versioned rules
- dry-run support
- explainable decisions

### Feature Flag Service

- tenant targeting
- city targeting
- percentage rollout
- kill switch

### Approval Service

- human-in-the-loop gating
- evidence binding
- exception review

### Workflow Orchestrator

- multi-step sequencing
- retry and compensation
- state tracking

### Trust and Compliance Engines

- risk scoring
- anomaly detection
- compliance gating
- evidence generation

## Decision Contract

```text
REQUEST
-> policy evaluation
-> flag evaluation
-> approval check
-> workflow admission
-> execution or reject
```

## Hard Rules

- apps cannot bypass control plane
- execution services cannot self-authorize
- overrides must be recorded
- decisions must be explainable

