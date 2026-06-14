# ADR-0031 Autonomous Fleet Governance

STATUS: GOVERNED IMPLEMENTATION SURFACE
CLASSIFICATION: ISOLATED ARCHITECTURE SPEC
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines the Gen-3 fleet governance surface for AfriRide and related mobility domains. It does not define truth authority, proof authority, or runtime admissibility. It describes a future governed implementation target that must remain evidence-backed, replayable, and bounded.

## Objective

Govern fleets as first-class, evidence-backed participants with replayable maintenance history, bounded trust derivation, and proof-ready eligibility summaries.

## Core Responsibilities

- fleet registration and operator binding
- vehicle maintenance traceability
- battery, safety, and route-compliance evidence
- deterministic fleet trust derivation
- dispatch eligibility projection
- proof-ready fleet governance reporting

## Authority Boundary

Fleet governance is reference-only. It may influence dispatch eligibility and fleet trust feedback, but it does not become truth authority, replay authority, or payment authority.

## Invariants

- IA-FLEET-001 maintenance history must be traceable
- IA-FLEET-002 fleet trust must be derived from operator and vehicle evidence
- IA-FLEET-003 vehicle state must be replayable
- IA-FLEET-004 custody and service evidence must be explicit
- IA-FLEET-005 fleet trust must remain bounded
- IA-FLEET-006 fleet governance must preserve the authority boundary

## Evidence Surface

- maintenance logs
- service custody links
- battery health records
- safety checks
- route compliance checks
- fleet governance proof artifacts

## Output Artifacts

- `fleet_governance_state.json`
- `fleet_governance_proof.json`

## Dependency Boundaries

- AfriID for operator identity
- Trust scoring for operator trust input
- Dispatch for fleet weighting input
- Proof / invariant layers for admissibility

