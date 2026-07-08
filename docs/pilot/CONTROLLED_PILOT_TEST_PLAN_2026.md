# Controlled Pilot Test Plan 2026

Controlled Pilot is the stage after Private Development and Internal QA, before general availability.

## Purpose

- Validate invited pilot users, approved devices, and approved operators in limited geography.
- Exercise NovaRide mobility, NovaPay financial services, NovaID identity verification, and NovaTrust evidence capture under monitored conditions.
- Keep real payments blocked unless an explicit pilot payment approval file exists.

## Boundary rules

- NovaID authenticates and verifies identity.
- NovaRide handles mobility only.
- NovaPay executes financial services only.
- NovaTrust records evidence and audit trails.
- NovaAI remains advisory only.

## Required checks

- Environment is `CONTROLLED_PILOT`.
- Approved users and devices are enforced.
- Payments are simulated by default.
- Support and incident response are enabled.
- Rollback is documented.

## Exit condition

- All controlled-pilot tests pass.
- No critical security or payment-safety violations remain.
- General availability stays false unless explicitly approved.
