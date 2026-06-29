# NovaRide Platform Standards

Status: PLATFORM STANDARDS
Classification: INTERNAL CONSISTENCY RULES

## Naming

- event types use lower snake dot notation with version suffix
- aggregate identifiers are stable and tenant-scoped
- services use bounded context names
- documentation files use numbered prefixes for ordered surfaces

## Versioning

- breaking schema changes require a new semantic version
- breaking API changes require a new API version
- deprecations must be documented before removal

## Security

- secrets never in source control
- all privileged actions are authenticated and authorized
- all high-risk actions are approved when required

## Data

- every tenant-scoped record carries tenant identity
- authoritative data is not overridden by projection data
- ledger records are append-only

## Events

- every event is schema-bound
- every event is registry-resolved
- every event is idempotent or deduplicated
- every governed event contains a decision trace

## APIs

- API responses must identify version
- public APIs must not expose internal trust internals
- websocket payloads must have documented schemas

## Operational

- every service must have a runbook
- every release must have rollback guidance
- every incident must have a postmortem template

