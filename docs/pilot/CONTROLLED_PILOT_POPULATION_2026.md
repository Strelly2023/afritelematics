# Controlled Pilot Population 2026

## Purpose

This document defines the controlled-pilot roster for NovaTech v2026.1.

## Formal Controlled Pilot Definition

Goal is to validate core workflows, security controls, RBAC, device trust, identity verification, payment flows, audit logs, and support processes.

Typical users: internal staff, trusted partners, selected drivers, selected merchants, test consumers, operations team.

Characteristics: approved users only, approved drivers only, approved merchants only, approved devices only, restricted access lists, simulated or tightly controlled payments, internal operational oversight, limited test geography, high-touch support.

Typical questions:
- Does onboarding work?
- Do ride flows work?
- Do payment flows work?
- Does RBAC work?
- Do audit logs work?
- Are support procedures working?

Exit criteria: controlled-pilot tests passing, safety controls verified, no critical defects, governance approval granted.

## Population Summary

- 10 approved drivers
- 30 approved riders
- 2 approved merchants
- 3 approved agents
- 2 approved businesses
- 10 approved employees
- 40 approved devices
- Operator access uses a legacy alias and does not add a separate participant cohort.

## Rules

- Participant roles must not overlap.
- Every approved device must be bound and trusted.
- The approved user set is non-public and access controlled.
- NovaID owns identity and authentication.
- NovaPay owns simulated and sandbox payment execution.
- NovaRide owns mobility workflows only.
- NovaTrust records evidence and replay artifacts.
- NovaAI remains advisory only.

## Source Registries

- `docs/pilot/approved_pilot_registry.json`
- `pilot/controlled_pilot/approved_users.json`
- `pilot/controlled_pilot/approved_devices.json`
- `pilot/controlled_pilot/approved_drivers.json`
- `pilot/controlled_pilot/approved_riders.json`
- `pilot/controlled_pilot/approved_merchants.json`
- `pilot/controlled_pilot/approved_agents.json`
- `pilot/controlled_pilot/approved_businesses.json`
- `pilot/controlled_pilot/approved_employees.json`
