# NovaRide Decision Trace Event Binding

Status: CANONICAL GOVERNANCE BINDING
Classification: POLICY-TO-EVENT TRACEABILITY SURFACE

## Purpose

Bind control-plane decisions to emitted events so every governed execution can
be explained.

## Decision Trace Components

- `policy_id`
- `policy_version`
- `rule_ids`
- `approval_id`
- `flag_evaluations`
- `evaluation_result`
- `reviewer`
- `reason`

## Binding Rule

Events requiring governance must reference their decision trace.

## Required Event Types

- ride matching
- trip start
- trip completion
- payment authorization
- payment capture
- refunds
- admin overrides
- deployment actions
- feature activation

## Explanation Contract

The system must be able to answer:

- which policy allowed this action
- which approval allowed this action
- which flag state allowed this action
- which rules were evaluated

