## Corrected final version

**File path**

```text
afritech/docs/adr/ADR_CRPS_TO_CIR_CONSTITUTIONAL_EXPANSION.md
```

This version incorporates the audit refinements, adds the missing **Observer-Free Invariant**, tightens constitutional language consistency, and aligns terminology with the mutation discipline already established in your repo.

---

# `afritech/docs/adr/ADR_CRPS_TO_CIR_CONSTITUTIONAL_EXPANSION.md`

# AfriTech ADR Set — CRPS → CIR Constitutional Expansion

**Document ID:** ADR-EXPANSION-CRPS-CIR
**Status:** PROPOSED
**Constitutional Scope:** Architectural Surface Expansion
**Mutation Class:** EXECUTION SURFACE ADDITION

---

## Required Constitutional Mutation Path

```text id="bbxq5v"
ADR Approval
→ Epoch Advance
→ Registry Reseal
→ Attestation Update
→ CI Enforcement Activation
```

No execution surface introduced by this document SHALL influence runtime execution until the full constitutional mutation sequence is successfully completed.

---

# Purpose

This document defines the lawful constitutional expansion required to introduce:

* Constitutional Intelligence Runtime (CIR)
* Constitutional Transition Layer
* Runtime Certification Artifacts
* Replay Feedback Governance

into the AfriTech constitutional system.

These additions extend AfriTech from a:

**Constitutional Research Proof System (CRPS)**

into a:

**Constitutionally Admitted Constitutional Intelligence Runtime (CIR)**

All changes defined herein are governed by constitutional mutation law.

---

# Constitutional Authority

This expansion is authorized under:

* Registry Sovereignty Rules
* Execution Surface Declaration Law
* Epoch Mutation Governance
* Replay Legitimacy Enforcement
* Constitutional Surface Admission Constraints

This document introduces constitutional surfaces only.

It does not activate them.

Activation requires successful completion of all post-approval mutation procedures.

---

# Foundational Constitutional Principle

AfriTech admits intelligence only through constitutional proof.

Runtime execution is a constitutional privilege, not an assumed capability.

---

# ADR-0006 — Runtime Admission Layer

## Status

**PROPOSED**

---

## Context

AfriTech currently supports constitutional proof certification through CRPS.

However, no explicit constitutional bridge exists between:

```text id="g5yn3d"
Certified Proof State
→ Runtime Admission
```

This creates a legitimacy discontinuity between certification and execution.

Without constitutional admission, runtime existence cannot be lawfully established.

---

## Decision

Introduce runtime admission surface:

```text id="4v9m5k"
afritech/runtime/activation/
```

---

## Declared Constitutional Components

```text id="j4wv7m"
afritech/runtime/activation/
    activation_proof.py
    runtime_admission.py
    constitutional_boot.py
```

---

## Responsibilities

The Runtime Admission Layer SHALL:

### 1. Validate RuntimeCertificate

Validation MUST prove:

* Registry continuity
* Epoch legitimacy
* Execution surface attestation integrity
* Replay verifier continuity
* Certificate signature authenticity

---

### 2. Enforce Runtime Admission

Runtime activation SHALL occur only if constitutional continuity is fully established.

---

### 3. Prevent Unauthorized Runtime Instantiation

The admission layer SHALL reject:

* Missing certificate
* Invalid certificate
* Partial certificate
* Hash mismatch
* Epoch divergence
* Surface admission mismatch

---

## Execution Surface Admission Clause

Newly declared surfaces MUST NOT influence runtime execution unless explicitly admitted into:

```text id="jlwm5n"
EXECUTION_SURFACES.yaml
```

Violation SHALL trigger immediate constitutional failure.

---

## Constitutional Invariant Introduced

# Runtime Admission Invariant

```text id="l2x5f8"
No valid constitutional proof
→ No runtime admission
```

---

## Runtime Refusal Law

Runtime MUST deterministically refuse execution if:

* Certificate invalid
* Epoch mismatch
* Surface not admitted
* Registry continuity broken
* Replay verifier mismatch

Refusal is:

```text id="9kyl98"
Deterministic
Non-discretionary
Immediate
```

---

## Failure Response

```text id="93mn90"
HARD FAILURE
RUNTIME REFUSAL
CONSTITUTIONAL INVALIDATION
```

---

## Impact

Enables:

* Deterministic runtime activation
* Proof-before-execution enforcement
* Constitutional continuity

---

# ADR-0007 — Constitutional Runtime Engine

## Status

**PROPOSED**

---

## Context

AfriTech inference capability exists.

However, execution is not yet formalized as a constitutionally governed runtime pipeline.

This prevents lawful orchestration of intelligence execution.

---

## Decision

Introduce constitutional runtime orchestration surface:

```text id="j80h2v"
afritech/runtime/engine/
```

---

## Declared Constitutional Components

```text id="qf2i31"
afritech/runtime/engine/
    dispatch.py
    router.py
    executor.py
    verifier.py

afritech/runtime/context/
    runtime_context.py
```

---

## Canonical Execution Flow

All runtime execution SHALL follow:

```text id="w1o8m7"
Request
→ Schema Validation
→ Authority Validation
→ Constitutional Context Resolution
→ Routing
→ Execution
→ TruthPacket Generation
→ Replay Binding
```

No alternate execution order is constitutionally admissible.

---

## Responsibilities

The Runtime Engine SHALL:

### Dispatch

Validate constitutional request schema.

---

### Authority Enforcement

Resolve authority prior to inference.

---

### Constitutional Context Resolution

Bind execution to:

* Active epoch
* RuntimeCertificate
* Admitted execution surfaces
* Authority domain

---

### Routing

Restrict execution to declared constitutional paths.

---

### Execution

Produce bounded lawful inference.

---

### Verification

Bind outputs to replay legitimacy.

---

## Constitutional Invariants Introduced

# Authority Ordering Invariant

```text id="v3w0v7"
Authority MUST precede inference
```

---

# Replay Legitimacy Invariant

```text id="f9q5lg"
All execution MUST be replay-valid
```

---

# Routing Constraint

```text id="1fh1rr"
No undeclared routing path may execute
```

---

## Runtime Refusal Law

Runtime MUST refuse execution if:

* Certificate invalid
* Epoch mismatch
* Surface not admitted
* Authority violation
* Replay violation

Refusal SHALL be deterministic.

No discretionary override is constitutionally permitted.

---

## Failure Response

```text id="ewcvfd"
EXECUTION TERMINATION
REPLAY INVALIDATION
CONSTITUTIONAL FAILURE
```

---

## Impact

Transforms inference into:

**Constitutionally governed execution**

---

# ADR-0008 — Runtime Certification Artifact

## Status

**PROPOSED**

---

## Context

CRPS currently establishes implicit constitutional validity.

No explicit machine-verifiable runtime credential exists.

Runtime admission requires a formal constitutional artifact.

---

## Decision

Introduce certification surface:

```text id="cvmxzn"
afritech/proof/
```

---

## Declared Constitutional Components

```text id="8a5ztm"
afritech/proof/
    runtime_certificate.py
    proof_snapshot.py
```

---

## Canonical Artifact

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeCertificate:
    registry_hash: str
    epoch: int
    execution_surfaces_hash: str
    authority_profiles_hash: str
    verifier_hash: str
    issued_at: str
    signature: str
    status: str
```

---

## Constitutional Requirements

RuntimeCertificate MUST:

### 1. Match Registry State

`registry_hash` MUST equal sealed registry

---

### 2. Bind to Active Epoch

`epoch` MUST equal current constitutional epoch

---

### 3. Match Execution Surfaces

`execution_surfaces_hash` MUST match:

```text id="4gmf4d"
EXECUTION_SURFACES.yaml
```

---

### 4. Match Authority Profiles

`authority_profiles_hash` MUST match:

```text id="z57htz"
authority_profiles.yaml
```

---

### 5. Match Replay Verifier Identity

`verifier_hash` MUST match active replay verifier

---

### 6. Be Cryptographically Valid

`signature` MUST validate against constitutional root

---

## Constitutional Role

RuntimeCertificate is the:

**sole admissible runtime credential**

No alternate admission artifact is constitutionally valid.

---

## Constitutional Invariant Introduced

# Runtime Credential Invariant

```text id="58e9ww"
Runtime existence requires valid RuntimeCertificate
```

---

## Failure Response

```text id="l6vt8e"
RUNTIME NON-EXISTENCE
```

---

## Impact

Formalizes:

```text id="df3tqf"
Proof
→ Runtime Admission
```

---

# ADR-0009 — Replay Feedback Governance

## Status

**PROPOSED**

---

## Context

Replay verification exists.

Structured constitutional evolution governance does not.

Replay divergence currently lacks lawful mutation escalation.

---

## Decision

Introduce evaluation surface:

```text id="v0p89v"
afritech/evaluation/
```

---

## Declared Constitutional Components

```text id="vwd2fx"
afritech/evaluation/
    telemetry/
    replay_analysis/
    drift_detection/
    adr_trigger/
```

---

## Responsibilities

The Evaluation Layer SHALL:

### Capture Runtime Outputs

Persist lawful execution transcripts

---

### Detect Replay Divergence

Identify constitutional deviation

---

### Classify Failure

Map divergence to constitutional taxonomy

---

### Trigger Mutation

Escalate divergence into ADR mutation proposals

---

## Canonical Feedback Loop

```text id="mqq3r8"
Execution
→ Transcript
→ Replay Verification
→ Drift Detection
→ ADR Trigger
→ Epoch Advance
→ Registry Reseal
→ Certificate Regeneration
```

No alternate adaptation path is constitutionally admissible.

---

## Constitutional Invariants Introduced

# Evolution Governance Invariant

```text id="bhb5q3"
All evolution MUST follow ADR mutation
```

---

# Drift Resolution Constraint

```text id="oc2mxz"
Replay divergence cannot be resolved outside constitutional mutation
```

---

## Failure Response

```text id="8k6u9l"
REPLAY INVALIDATION
EPOCH REJECTION
CONSTITUTIONAL FAILURE
```

---

## Impact

Enables:

* Lawful adaptation
* Controlled evolution
* Replay-governed intelligence improvement

---

# Global Constitutional Laws

# Runtime Existence Invariant

Runtime is constitutionally valid iff:

1. Derived from certified proof state
2. Operating under valid RuntimeCertificate
3. Remaining replay-valid throughout execution

---

## Violation Response

```text id="yc7mze"
HARD FAILURE
RUNTIME INVALID
EXECUTION LEGITIMACY REVOKED
```

---

# Non-Observability Invariant

Runtime validity MUST be objectively derivable from constitutional artifacts alone.

No external observer, discretionary interpretation, or undocumented system state may be required to determine execution legitimacy.

This guarantees:

* Objective auditability
* Independent reproducibility
* Constitutional closure

---

# Constitutional Visibility Rule

A capability exists constitutionally only if it is:

1. ADR declared
2. Registry sealed
3. Hash-attested
4. Replay-verifiable
5. RuntimeCertificate-admitted

Anything failing these conditions is:

```text id="j7j07t"
CONSTITUTIONALLY INVISIBLE
NON-EXECUTABLE
LEGALLY NON-EXISTENT
```

---

# Required Post-ADR Actions

Following approval of ADR-0006 through ADR-0009:

---

## 1. Epoch Advancement

Increment constitutional epoch

---

## 2. Registry Reseal

Update:

```text id="55c2c4"
afritech/registry/registry.yaml
```

---

## 3. Execution Surface Manifest Update

Add:

```text id="xqj5rr"
runtime.activation
runtime.engine
proof
evaluation
```

to:

```text id="0pss8m"
EXECUTION_SURFACES.yaml
```

---

## 4. Attestation Regeneration

Recompute constitutional hash chain

---

## 5. RuntimeCertificate Baseline Issuance

Generate initial certified runtime credential

---

## 6. CI Enforcement Update

CI SHALL reject:

* Runtime boot without certificate
* Missing activation layer
* Undeclared execution paths
* Replay-invalid execution

---

# Final Constitutional Assertion

AfriTech evolves exclusively through declared constitutional mutation.

No runtime capability may exist unless it is:

* Declared
* Sealed
* Hash-attested
* Replay-verifiable
* Certificate-admitted

---

# Final Assertion

AfriTech transitions from:

**Constitutional Research Proof System**

to

**Constitutional Intelligence Runtime**

only through lawful constitutional mutation.

No proof without governance.
No runtime without proof.
No execution without replay legitimacy.
No evolution without constitutional mutation.
