# AfriTech Wave 1 Sacred Kernel Inventory

## Document Classification

```text
STATUS: WAVE 1 STARTER ARTIFACT
CLASSIFICATION: SACRED KERNEL INVENTORY
ROLE: IDENTIFY LEGITIMACY-CRITICAL CORE SURFACES
BOUNDARY: INVENTORY ONLY; DOES NOT REDEFINE CONSTITUTION
```

This inventory begins Wave 1 of the AfriTech Operational Evolution Execution Matrix.

Its purpose is to separate the minimal constitutional truth kernel from the operational shell so AfriTech can grow without increasing constitutional density.

## Kernel Rule

```text
If a component is not required for legitimacy, it must not live in the sacred kernel.
```

## Sacred Kernel Categories

Only these categories are eligible for the sacred kernel:

1. admissibility law
2. replay law
3. ontology law
4. identity law
5. witness law
6. deterministic execution law
7. invariant semantics

Everything else must be classified as constitutional runtime, operational runtime, tooling, product, or documentation.

## Initial Candidate Inventory

| Category | Candidate surfaces | Kernel reason | Status |
| --- | --- | --- | --- |
| Admissibility law | `afritech/constitution/core/admissibility.yaml`, `afritech/constitution/canonical/concepts/admissibility.yaml`, `afritech/replay/ci/ADMISSION_REQUIRED.yaml` | Defines what may enter legitimate execution | Candidate |
| Replay law | `afritech/constitution/core/replay.yaml`, `afritech/constitution/canonical/concepts/replay_admissibility.yaml`, `afritech/replay/VERIFY_INTERFACE_SPEC.md`, `afritech/replay/verify.py` | Defines reconstruction and truth validation authority | Candidate |
| Ontology law | `afritech/constitution/path_ontology.yaml`, `afritech/architecture/PATH_ONTOLOGY.yaml`, `afritech/constitution/canonical/INDEX.yaml` | Defines allowed semantic structure and path meaning | Candidate |
| Identity law | `afritech/constitution/core/identity.yaml`, `afritech/architecture/identity_rules.yaml`, `afritech/ci/identity_validator.py` | Defines stable identity semantics | Candidate |
| Witness law | `afritech/proof/witness/`, `afritech/ci/witness_validator.py`, `afritech/ci/witness_proof_validator.py`, `afritech/ci/full_witness_coverage_validator.py` | Defines evidence artifacts required for proof | Candidate |
| Deterministic execution law | `afritech/constitution/core/determinism.yaml`, `afritech/constitution/canonical/concepts/deterministic_execution.yaml`, `afritech/ci/execution_integrity_validator.py` | Defines execution reproducibility constraints | Candidate |
| Invariant semantics | `afritech/constitution/INVARIANTS.yaml`, `afritech/constitution/invariants_semantics.yaml`, `afritech/constitution/compiled/invariants_ir.json`, `afritech/ci/invariant_validator.py` | Defines invariant meaning and enforcement expectations | Candidate |

## Likely Non-Kernel Surfaces

The following surfaces may remain constitutionally important, but they should not live inside the sacred kernel unless a legitimacy-critical dependency is proven.

| Surface | Likely classification | Reason |
| --- | --- | --- |
| Runtime locality scheduler | Constitutional runtime | Enforces locality but does not define truth |
| Execution graph optimizer | Operational optimization | Improves topology while remaining replay-bounded |
| Distributed fabric | Operational runtime | Places execution but does not define legitimacy |
| Distributed OS | Operational environment | Frames execution environment but does not define truth |
| Admin UI | Human experience | Observes and explains proof surfaces |
| Proof CLI | Operability tooling | Calls existing proof core |
| Evidence store adapters | Infrastructure evidence layer | Stores artifacts that must replay before trust |
| AI operations | Operational intelligence | Suggests actions but cannot define legitimacy |

## Compression Questions

Every candidate kernel surface must answer yes to all questions:

1. Is this required to decide legitimacy?
2. Would removing it make replay truth invalid or ambiguous?
3. Does it define meaning rather than operational behavior?
4. Does it need slow semantic evolution?
5. Can operational layers depend on it through a stable interface?

If any answer is no, the surface should be moved out of the sacred kernel.

## Proposed Kernel Boundary

```text
Sacred kernel:
  law and meaning required for legitimacy

Constitutional runtime:
  execution mechanisms that enforce law

Operational runtime:
  scalability, recovery, orchestration, locality, adaptation

Human experience:
  UI, CLI, explainability, onboarding, diagnostics

Infrastructure:
  storage, queues, cloud, network, deployment
```

## Wave 1 Work Items

1. Review each candidate surface and classify as kernel, constitutional runtime, operational runtime, tooling, or documentation.
2. Remove duplicate authority declarations where one canonical source exists.
3. Bind each retained kernel surface to a stable interface.
4. Mark all non-kernel surfaces as operationally evolvable.
5. Add a kernel compression audit to CI once classifications are stable.

## Exit Criteria

Wave 1 kernel inventory is complete when:

1. every sacred kernel surface maps to a legitimacy requirement
2. no operational component is classified as kernel without justification
3. stable interfaces exist for replay, witness, admission, invariant, and execution contracts
4. future growth can happen outside the kernel by default

## Final Boundary

This inventory does not define truth.

```text
It identifies candidate truth-critical surfaces.
The constitution defines legitimacy.
Replay validates truth.
```
