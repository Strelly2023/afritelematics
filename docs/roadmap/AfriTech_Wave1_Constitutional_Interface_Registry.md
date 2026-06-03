# AfriTech Wave 1 Constitutional Interface Registry

## Document Classification

```text
STATUS: WAVE 1 STARTER ARTIFACT
CLASSIFICATION: CONSTITUTIONAL INTERFACE REGISTRY
ROLE: DEFINE STABLE BOUNDARIES BETWEEN KERNEL AND OPERATIONS
BOUNDARY: INTERFACE PLANNING ONLY; DOES NOT CHANGE IMPLEMENTATION
```

This registry begins the slow-moving interface layer required by the AfriTech Operational Evolution Execution Matrix.

The registry exists so operational systems can evolve quickly while constitutional semantics evolve slowly.

## Interface Rule

```text
Operational layers may call constitutional interfaces.
Operational layers may not bypass or redefine constitutional semantics.
```

## Required Stable Interfaces

### Replay Interface

Purpose:

```text
Validate truth through deterministic reconstruction.
```

Candidate sources:

1. `afritech/replay/VERIFY_INTERFACE_SPEC.md`
2. `afritech/replay/verify.py`
3. `afritech/replay/replay_equivalence_engine.py`
4. `afritech/storage/replay_engine.py`
5. `afritech/runtime/replay/`

Interface contract:

```text
replay(trace, declared_inputs, semantic_version) -> replay_report
```

Required properties:

1. deterministic
2. fail-closed
3. version-aware
4. infrastructure-independent
5. explicit about mismatch causes

### Witness Interface

Purpose:

```text
Bind proof artifacts to execution and replay evidence.
```

Candidate sources:

1. `afritech/proof/witness/`
2. `afritech/ci/witness_validator.py`
3. `afritech/ci/witness_proof_validator.py`
4. `afritech/ci/full_witness_coverage_validator.py`
5. `afritech/ci/ast_witness_validator.py`

Interface contract:

```text
validate_witness(witness_bundle, execution_context) -> witness_report
```

Required properties:

1. deterministic
2. tamper-detecting
3. replay-bindable
4. explicit about missing evidence
5. independent of storage trust

### Admission Interface

Purpose:

```text
Decide whether declared inputs may enter legitimate execution.
```

Candidate sources:

1. `afritech/constitution/core/admissibility.yaml`
2. `afritech/constitution/canonical/concepts/admissibility.yaml`
3. `afritech/replay/ci/ADMISSION_REQUIRED.yaml`
4. `afritech/guards/edge_input_guard.py`
5. `afritech/ci/adversarial_runner_validator.py`

Interface contract:

```text
admit(input_bundle, execution_contract, semantic_version) -> admission_report
```

Required properties:

1. closed-world
2. deterministic
3. explicit about rejection reason
4. version-aware
5. separate from optimization

### Invariant Interface

Purpose:

```text
Validate invariant semantics and runtime conformance.
```

Candidate sources:

1. `afritech/constitution/INVARIANTS.yaml`
2. `afritech/constitution/invariants_semantics.yaml`
3. `afritech/constitution/compiled/invariants_ir.json`
4. `afritech/ci/invariant_validator.py`
5. `afritech/ci/invariant_runtime_guard.py`

Interface contract:

```text
validate_invariants(subject, invariant_set, semantic_version) -> invariant_report
```

Required properties:

1. canonical invariant lookup
2. deterministic result
3. explicit invariant identifiers
4. version-aware interpretation
5. no hidden runtime context

### Execution Contract Interface

Purpose:

```text
Declare the execution environment and constraints without making environment truth.
```

Candidate sources:

1. `afritech/distributed/contracts/`
2. `afritech/runtime/dsl/workflow_model.py`
3. `afritech/runtime/orchestration/execution_graph_optimizer.py`
4. `afritech/runtime/locality/scheduler.py`
5. `afritech/ci/execution_integrity_validator.py`

Interface contract:

```text
validate_execution_contract(contract, declared_inputs, semantic_version) -> contract_report
```

Required properties:

1. deterministic
2. declares resources and boundaries
3. trace-integrated
4. replay-inspectable
5. unable to override replay truth

## Interface Versioning

Every stable interface must include:

1. semantic version
2. accepted input schema
3. canonical output schema
4. failure taxonomy
5. backward replay compatibility policy

Example:

```text
replay.v1
witness.v1
admission.v1
invariant.v1
execution_contract.v1
```

## Forbidden Interface Behavior

No constitutional interface may:

1. read hidden environment state
2. depend on wall-clock timing unless declared
3. use randomness
4. trust storage without replay
5. allow operational tooling to define legitimacy
6. silently upgrade semantic versions

## Operational Consumption Rules

Operational layers may:

1. call stable interfaces
2. cache interface outputs as evidence
3. visualize reports
4. route failures to diagnostics
5. propose recovery actions

Operational layers may not:

1. rewrite interface results
2. bypass interface checks
3. treat cached reports as truth without replay
4. mutate semantic versions
5. collapse interface responsibilities

## Wave 1 Work Items

1. Confirm one canonical implementation owner per interface.
2. Write schema files for each interface request and report.
3. Add version labels to all interface outputs.
4. Create compatibility fixtures for `v1` replay, witness, admission, invariant, and execution contract reports.
5. Add CI checks preventing direct operational imports of sacred kernel internals where stable interfaces exist.

## Exit Criteria

The constitutional interface registry is complete when:

1. operational layers have stable call points
2. kernel internals are not directly imported by fast-evolving layers
3. interface outputs are versioned and replay-compatible
4. failures are structured enough for human diagnostics
5. no interface grants authority to operations, storage, UI, AI, or infrastructure

## Final Boundary

This registry guides interface stabilization. It does not itself define legitimacy.

```text
Interfaces expose constitutional semantics.
Constitution defines legitimacy.
Replay validates truth.
Operations consume reports.
```
