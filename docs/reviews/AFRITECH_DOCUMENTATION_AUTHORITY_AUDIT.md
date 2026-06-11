# AfriTech Documentation Authority Audit

Status: DOCUMENTATION AUTHORITY AUDIT
Classification: REPO_WIDE_DOCUMENTATION_GOVERNANCE_REVIEW

Purpose: assess documentation coherence, overlapping authority claims, and the
current canonical navigation problem across AfriTech and AfriRide markdown
surfaces.

This audit is a structural review surface.
It is not itself the constitutional authority root.

## Audit Snapshot

Repository observations at audit time:

- markdown files observed: `351`
- files under `docs/`: `230`
- files under `afritech/`: `74`
- uses of the word `canonical`: `133`
- uses of `authority boundary`: `62`
- files with `Status:` marker: `216`
- files with `Classification:` marker: `170`

These numbers are signals of strong documentation investment, but also strong
overlap risk.

## Primary Findings

### Finding 1. Canonical Surface Proliferation

Multiple documents use words such as:

- canonical
- final
- closure
- single source of truth

without a single enforced documentation root index.

Risk:

- readers cannot tell which document governs when surfaces overlap
- older “final” artifacts can appear equivalent to newer governed docs

### Finding 2. Split Documentation Centers

The repo has two major documentation centers:

- `docs/`
- `afritech/docs/` and markdown surfaces under `afritech/`

Risk:

- governance and constitutional material is partly outside `docs/`
- product, pilot, proof, and commercial layers mostly live under `docs/`
- authority can appear fragmented to new readers

### Finding 3. Duplicate And Parallel Narratives

There are many repeated narrative types:

- architecture
- pilot
- proof
- commercialization
- protocol
- mobile

Risk:

- duplicate authority declarations
- difficult onboarding
- harder doc maintenance

### Finding 4. Navigation Layer Was Too Thin

The previous `docs/README.md` described AfriTech at a high level but did not
act as a strong canonical navigation layer into:

- constitution
- unified architecture
- pilot gates
- mobile readiness
- commercial conversion surfaces

## Current Canonical Authority Proposal

Use this order:

1. `afritech/constitution/AFRITECH_CONSTITUTION_V1.md`
2. `afritech/governance/` and `afritech/guards/`
3. `docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md`
4. bounded pilot gate docs in `docs/pilot/`
5. bounded mobile, proof, and commercial packaging docs in `docs/mobile/`, `docs/proof/`, `docs/business/`, `docs/pitch/`, `docs/partners/`

This is the minimum viable doctrine order that matches the repo’s actual shape.

## Consolidation Rules

### Rule 1. One Navigation Root

`docs/README.md` should remain the human entry point for documentation
navigation.

### Rule 2. Constitution Beats Commentary

If a review, whitepaper, or final-sounding markdown file conflicts with the
constitution or governed architecture docs, the constitution and governed docs
win.

### Rule 3. Architecture Beats Parallel Product Storytelling

If multiple architecture-like docs overlap, the unified architecture should be
the first explanatory reference unless a narrower bounded surface is needed.

### Rule 4. Pilot Docs Must Stay Bounded

Pilot, activation, and readiness documents may describe execution states, but
must not silently become timeless canonical authority sources.

### Rule 5. Commercial Docs Package, Not Govern

Pricing, pitch, objection, negotiation, and contract docs may package runtime
truth surfaces. They may not redefine truth, replay, or governance authority.

## Immediate Repo-Backed Actions

- strengthen `docs/README.md` as the canonical documentation navigation surface
- declare active authority docs in `afritech/governance/document_registry.yaml`
- preserve `AFRITECH_UNIFIED_ARCHITECTURE.md` as the primary explanation root
- keep constitution and governance under `afritech/` as highest-order authority
- classify older final/canonical narrative docs through a conflict sweep review
- treat older “final canonical” narrative docs as historical or review surfaces unless explicitly re-ratified
- continue adding governance tests whenever a new top-level doctrine-like doc is introduced

## Non-Claims

This audit does not claim:

- that all duplicates have already been removed
- that every older canonical-seeming document is obsolete
- that the repo has finished documentation consolidation

## Practical Conclusion

The next bottleneck is not missing documentation volume.
It is documentation authority compression.

The repo needs:

- fewer competing roots
- stronger navigation
- explicit authority order
- continued governance tests around new doctrine surfaces
