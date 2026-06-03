# AfriTech Wave 1 Epoch Compatibility Policy

## Document Classification

```text
STATUS: WAVE 1 STARTER ARTIFACT
CLASSIFICATION: EPOCH AND REPLAY COMPATIBILITY POLICY
ROLE: DEFINE SAFE SEMANTIC EVOLUTION RULES
BOUNDARY: POLICY ONLY; DOES NOT MIGRATE OR REDEFINE EXISTING TRUTH
```

This policy completes the first Wave 1 stabilization set:

```text
Sacred Kernel Inventory
Constitutional Interface Registry
Epoch Compatibility Policy
```

Its purpose is to let AfriTech evolve without invalidating prior legitimate execution.

## Core Rule

```text
New semantics may be introduced.
Old valid traces must remain replayable under their original semantics.
```

Replay compatibility is a constitutional survivability requirement.

## Epoch Definition

An epoch is a declared semantic boundary for constitutional interpretation.

An epoch may define:

1. invariant semantics
2. replay interpretation rules
3. admission interpretation rules
4. witness validation rules
5. identity interpretation rules
6. execution contract semantics

An epoch may not silently alter the meaning of existing traces.

## Required Trace Metadata

Every replayable trace must declare:

```yaml
semantic_epoch: epoch_id
interface_versions:
  replay: replay.vN
  witness: witness.vN
  admission: admission.vN
  invariant: invariant.vN
  execution_contract: execution_contract.vN
```

If a trace lacks epoch metadata, replay must either:

1. resolve it through an explicit legacy mapping, or
2. fail closed with a missing epoch error.

Implicit epoch inference is forbidden.

## Compatibility Classes

### Class A: Compatible Clarification

Meaning:

```text
Wording, documentation, diagnostics, or non-semantic report improvements.
```

Allowed without new epoch when:

1. replay result is unchanged
2. trace hash interpretation is unchanged
3. invariant meaning is unchanged
4. admission outcome is unchanged
5. witness outcome is unchanged

Example:

```text
Improve REPLAY_INVALID diagnostic wording.
```

### Class B: Compatible Extension

Meaning:

```text
New optional declared input, report field, or operational metadata.
```

Allowed within current epoch only if:

1. old traces replay unchanged
2. missing new fields have explicit defaults
3. defaults are declared in the interface schema
4. replay output remains backward compatible

Example:

```text
Add optional replay diagnostic context field.
```

### Class C: Semantic Extension

Meaning:

```text
New rule or interpretation that affects future traces.
```

Requires:

1. new epoch
2. compatibility fixtures
3. migration notes
4. explicit trace versioning
5. old trace replay under old epoch

Example:

```text
Add a new admissibility rule for distributed partition ownership.
```

### Class D: Breaking Semantic Change

Meaning:

```text
Change that would alter prior replay result, identity interpretation,
admission result, witness result, or invariant meaning.
```

Requires:

1. new epoch
2. replay translator or explicit non-translation decision
3. legacy replay preservation
4. formal approval
5. compatibility test suite

Example:

```text
Change canonical hash normalization rules.
```

## Replay Translator Policy

Replay translators exist only to preserve access to old truth.

They may:

1. map old trace envelopes into current replay entry points
2. select legacy semantic interpreters
3. report compatibility warnings
4. emit translated diagnostic reports

They may not:

1. rewrite old truth
2. silently upgrade semantic meaning
3. change old trace hashes
4. hide semantic incompatibility
5. make invalid traces valid

## Semantic Migration Policy

Migrations must distinguish between:

```text
artifact migration
semantic migration
```

Artifact migration may change storage format.

Semantic migration changes interpretation and therefore requires epoch handling.

Rule:

```text
Storage migration may be operational.
Semantic migration is constitutional.
```

## Interface Evolution Rules

Every stable constitutional interface must publish:

1. current version
2. supported legacy versions
3. deprecation status
4. compatibility fixtures
5. failure taxonomy
6. migration notes

Example:

```yaml
interface: replay
current: replay.v2
supported:
  - replay.v1
compatibility:
  old_traces_replay: true
  translator_required: true
```

## Required Compatibility Fixtures

Each epoch must include fixtures for:

1. valid minimal trace
2. valid full trace
3. admission failure
4. replay drift
5. witness mismatch
6. invariant violation
7. identity mismatch
8. execution contract violation

Fixtures must assert:

```text
same epoch + same inputs -> same replay report
```

## CI Enforcement Requirements

CI must fail when:

1. interface output changes without version update
2. old trace fixture no longer replays
3. epoch metadata is missing from new trace format
4. semantic rule changes without compatibility class declaration
5. translator changes old trace meaning
6. runtime code imports kernel internals instead of stable interfaces

## Forbidden Evolution Patterns

The following are prohibited:

1. silent semantic upgrade
2. wall-clock-based epoch selection
3. environment-based replay interpretation
4. storage-driven truth migration
5. AI-suggested semantic change without constitutional review
6. operational tooling mutating trace version metadata

## Wave 1 Work Items

1. Add epoch metadata requirement to trace schemas.
2. Create `epoch_compatibility.yaml` for interface support status.
3. Build compatibility fixtures for current AfriRide proof bundles.
4. Add CI validation for old trace replay.
5. Classify future semantic changes by compatibility class.
6. Document any legacy traces without epoch metadata and map them explicitly.

## Exit Criteria

Epoch compatibility is established when:

1. every replayable trace has an epoch or explicit legacy mapping
2. each constitutional interface declares supported versions
3. old valid traces replay under old semantics
4. semantic changes require compatibility class labels
5. CI prevents accidental replay breakage

## Final Boundary

This policy governs semantic evolution. It does not define truth by itself.

```text
Epochs select semantic context.
Interfaces expose stable semantics.
Replay validates truth.
Constitution defines legitimacy.
```
