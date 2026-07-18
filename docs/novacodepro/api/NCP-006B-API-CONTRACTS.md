# NCP-006B API Contracts

Date: 2026-07-18

## Base path

`/v1/novacodepro/design`

## Primary route families

- `/workspaces`
- `/briefs`
- `/research`
- `/personas`
- `/journeys`
- `/service-blueprints`
- `/information-architecture`
- `/user-flows`
- `/wireframes`
- `/screens`
- `/systems`
- `/tokens`
- `/themes`
- `/components`
- `/interaction-patterns`
- `/responsive-specifications`
- `/content`
- `/localization`
- `/accessibility`
- `/prototypes`
- `/validation`
- `/fitness`
- `/reviews`
- `/approvals`
- `/baselines`
- `/traceability`
- `/coverage`
- `/gaps`
- `/impact`
- `/drift`
- `/handoffs`
- `/imports`
- `/exports`

## Governance

All mutations are tenant- and workspace-authoritative, versioned, audited, and evidence-backed. Design approval and baseline creation are fail-closed and require the configured role and policy checks.

## External blockers

Real browser certification, live Figma/provider integration, and external visual regression evidence remain blocked in this environment.
