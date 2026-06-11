# AfriRide Externalization And Scale Architecture

Status: EXTERNALIZATION AND SCALE DESIGN
Classification: REPLAY_BACKED_OPERATOR_AND_PARTNER_SURFACE

Purpose: define how AfriRide evolves from a governed single-spine pilot into
an externally consumable operator, regional, tenant, and partner system without
creating a second truth surface.

## Core Rule

```text
externalization may project replay-backed truth
externalization may not define truth
```

## 1. Replay-Backed Operator Dashboard

The authoritative operator UI remains:

```text
dashboard = projection(replay(trace_events))
```

It must not be:

```text
dashboard = direct database truth
```

Required dashboard surfaces:

- active rides
- replay health
- evidence status
- guard violations
- multi-region topology
- tenant isolation overview
- external anchor commitments
- partner proof packet readiness

## 2. Multi-Region Support

Regions must preserve one canonical replay outcome while allowing regional
placement, scheduling, and recovery.

Required region model:

- region-local ingestion
- region-local queue and worker placement
- region-scoped observability
- canonical cross-region replay equivalence
- bounded failover and merge policy

Required region identifiers:

```text
region_id
partition_id
authority_scope
replay_hash
```

## 3. Multi-Tenant Support

Tenant isolation must separate runtime authority from partner or operator
consumption surfaces.

Required tenant classes:

- authoritative runtime tenant
- city or fleet operator tenant
- audit or regulator tenant
- partner analytics tenant

Isolation requirements:

- tenant-scoped ride visibility
- tenant-scoped evidence exports
- tenant-scoped anchor receipts
- no cross-tenant truth mutation

## 4. External Proof Packets

External surfaces must consume proof packets rather than internal runtime state.

Required packet contents:

- trace hash
- replay hash
- receipt hash
- verification status
- region_id
- tenant_id
- anchor commitment hash

## 5. Cryptographic Anchoring

Every bounded proof packet may be committed to an external ledger or notarized
partner channel using:

```text
trace_hash + replay_hash + receipt_hash -> commitment_hash
```

Anchoring must remain:

- deterministic
- export-safe
- non-authoritative over replay
- suitable for partner evidence exchange

## 6. Bounded Non-Claims

This document does not claim:

- multi-region production active
- public multi-tenant launch complete
- external ledger anchoring proven in production
- partner integrations fully operational
