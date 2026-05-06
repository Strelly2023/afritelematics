# Phase‑2B Admissibility Specification

## Status

SPECIFICATION ONLY

No Phase‑2B execution claims are made in this document.


## Purpose

This document defines the admissibility requirements for Phase‑2B of the AfriTech constitutional execution system.

It establishes:

- required runtime artifacts
- validation boundaries
- proof surfaces
- ratification criteria

No implementation or execution is asserted until admissible runtime evidence is produced.


## Scope

Phase‑2B extends the constitutional system to include:

- inference-bound execution
- deterministic replay over model outputs
- verification of inference identity

The focus is not model correctness, but **deterministic replay compatibility**.


## Core Principle

All Phase‑2B ratification MUST follow the established constitutional rule:

runtime artifact  
→ bounded interpretation  
→ narrowly scoped claim  
→ ratification

No claim SHALL exceed the evidentiary artifact.


## Required Runtime Artifacts

A Phase‑2B admissible execution MUST produce:

### 1. Replay Transcript

A complete transcript containing:

- authority_profile
- request_hash
- replay_environment
- execution_trace
- truth_packet_hash
- replay_hash


### 2. Inference Binding

A persisted, immutable inference_binding structure:

This binding MUST:

- be included in the TruthPacket payload
- be persisted in replay_environment as `_inference_binding`
- be used for validator reconstruction (never regenerated)


### 3. Deterministic Execution Trace

The execution trace MUST include:

- scope_evaluation
- routing_selection
- real_inference_invocation
- truth_emission

Trace MUST match byte‑for‑byte during replay verification.


### 4. TruthPacket Hash

A canonical hash computed over:

- claims
- authority_profile
- inference_binding
- provenance_chain
- epoch_id
- epistemic_confidence
- causal_trace


### 5. Replay Hash

A terminal replay hash computed from:

This MUST match under verification.


## Replay Environment Requirements

The replay_environment MUST contain:

- runtime_version
- model_id
- model_version
- constitution_version
- deterministic_mode = true
- `_inference_binding`

No field may be inferred or reconstructed at verification time.


## Proof Surfaces

Phase‑2B ratification requires evidence across ALL of the following surfaces:

### 1. Deterministic Replay Identity

- TruthPacket reconstruction matches
- Replay hash matches
- No hash divergence

---

### 2. Inference Binding Consistency

- input_hash == request hash
- model_id / model_version match replay_environment
- output_hash remains stable across replay

---

### 3. Execution Trace Identity

- Trace reconstructed exactly
- Includes inference step
- No divergence at any step

---

### 4. Authority Isolation Preservation

- Authority_profile enforced
- No cross-authority acceptance

---

### 5. Environment Identity

- All required fields present
- deterministic_mode == true
- binding included


## Ratification Criteria

Phase‑2B may be ratified ONLY if:

- ReplayVerifier returns:


VERDICT: REPLAY_VALID
FAILURE_MODE: None
VIOLATED_INVARIANT: None
DIVERGENCE_LOCATION: None

- The run is performed under a defined repository state
- The replay hash is recorded as an evidentiary anchor
- The interpretation remains bounded to that artifact


## Explicit Non-Claims

Phase‑2B DOES NOT establish:

- semantic correctness of model outputs
- truthfulness of generated content
- model reliability or performance
- cross-environment invariance
- stochastic equivalence across runs
- production readiness

It only establishes:

→ deterministic replay compatibility under binding


## Failure Conditions

Any of the following invalidates Phase‑2B admissibility:

- missing inference_binding
- mismatch in input_hash
- mismatch in model identity
- trace divergence
- environment mismatch
- truthpacket hash mismatch
- replay hash mismatch

All failures MUST map to canonical ReplayFailure definitions.


## Epistemic Boundary

Inference is treated as:

- externally opaque
- probabilistically unconstrained

Determinism is enforced ONLY at:

- binding level (input_hash, output_hash)
- replay verification surface

This preserves replay law independence from model behavior.


## Admissibility Sequence

Phase‑2B MUST follow:

1. Specification (this document)
2. Implementation (no claims)
3. Runtime execution
4. Artifact capture
5. Verifier replay
6. Evidence interpretation
7. Bounded ratification


## Notes

- No inference is re-executed during replay
- Binding is the sole authoritative inference record
- Replay validity is independent of model internals
- This document introduces no executable behavior


## End of Specification