# ADR-0032 Institutional Mobility Networks

STATUS: GOVERNED IMPLEMENTATION SURFACE
CLASSIFICATION: ISOLATED ARCHITECTURE SPEC
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines the institutional mobility layer for AfriRide Gen-3. It describes how institutions may impose explicit, deterministic, replayable constraints on mobility operations without becoming truth authority, replay authority, settlement authority, or proof authority.

## Objective

Allow institutions to operate bounded mobility domains with specialized dispatch, custody, access, and market rules inside the federation while preserving global invariants.

## Core Responsibilities

- institution registration and participant binding
- institution-owned fleet and participant scoping
- explicit policy registration
- deterministic policy projection
- institution-specific dispatch, access, market, and custody constraints
- proof-ready institutional governance reporting

## Authority Boundary

Institutional rules are contextual constraints only. They may influence dispatch, access, custody, or market projections, but they may not override replay truth, proof truth, settlement truth, or runtime admissibility.

## Invariants

- IA-INSTITUTION-001 policies must be explicit and hashable
- IA-INSTITUTION-002 policies must be replayable
- IA-INSTITUTION-003 institutions must not override proof authority
- IA-INSTITUTION-004 institutional dispatch constraints must be deterministic
- IA-INSTITUTION-005 institutional boundaries must be enforceable
- IA-INSTITUTION-006 institutional networks must not duplicate identities

## Evidence Surface

- policy registrations
- participant bindings
- fleet bindings
- dispatch projections
- custody constraints
- access constraints
- market constraints
- institutional proof artifacts

## Output Artifacts

- `institution_governance_state.json`
- `institution_governance_proof.json`

## Dependency Boundaries

- AfriID for participant identity
- Fleet governance for institution-owned fleets
- Dispatch / custody / market for policy projection inputs
- Proof and invariant layers for admissibility

