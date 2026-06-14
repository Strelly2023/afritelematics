# AfriRide Public Evidence Network

ADR-0034 defines the external trust surface for Gen-3 mobility.

## Purpose

Expose replayable, proof-backed mobility evidence to auditors, regulators,
partners, and public verification surfaces without creating new authority.

## Governance Rules

- Public evidence is read-only.
- Public evidence must be deterministic and hash-stable.
- Public evidence must preserve replay and proof integrity.
- Public evidence must not mutate dispatch, custody, settlement, or trust.
- Public evidence must not become an authority source.

## Proof Boundary

The public evidence network emits reference-only proof artifacts.

