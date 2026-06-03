# AfriTech Wave 1 Epoch Translator Lifecycle Policy

## Document Classification

```text
STATUS: WAVE 1 CONTROL ARTIFACT
CLASSIFICATION: EPOCH AND TRANSLATOR LIFECYCLE POLICY
ROLE: PREVENT COMPATIBILITY MECHANISMS FROM BECOMING COMPLEXITY ACCUMULATORS
BOUNDARY: POLICY ONLY; DOES NOT RETIRE OR MIGRATE EXISTING EPOCHS
```

This policy extends the Wave 1 Epoch Compatibility Policy by controlling the long-term growth of epochs and replay translators.

Compatibility exists to preserve historical truth. It must not become an unbounded source of semantic complexity.

## Core Rule

```text
Translators preserve access to old truth.
They must not become new truth engines.
```

## Translator Lifecycle

Every replay translator must have a declared lifecycle.

```text
proposed -> active -> stable -> deprecated -> archived
```

### Proposed

Meaning:

```text
Translator design exists but is not trusted for replay.
```

Requirements:

1. source epoch declared
2. target interface declared
3. compatibility class declared
4. fixture requirements listed
5. failure taxonomy drafted

### Active

Meaning:

```text
Translator is used for supported legacy replay.
```

Requirements:

1. compatibility fixtures passing
2. trace hash preservation verified
3. mismatch reporting verified
4. CI coverage enabled
5. owner assigned

### Stable

Meaning:

```text
Translator has no active semantic changes and serves historical replay.
```

Requirements:

1. no open compatibility defects
2. fixture coverage frozen
3. documented supported trace population
4. diagnostics stable
5. no new semantic expansion allowed

### Deprecated

Meaning:

```text
Translator remains available but should not receive new trace volume.
```

Requirements:

1. replacement path documented
2. affected trace populations identified
3. operator warning available
4. archival plan drafted

### Archived

Meaning:

```text
Translator is retained for historical inspection but removed from active replay paths.
```

Requirements:

1. sealed fixture set retained
2. archival checksum recorded
3. historical access policy documented
4. no production trace depends on active use

## Translator Admission Rules

A new translator may be admitted only when:

1. an old valid trace cannot replay through the current interface directly
2. a legacy semantic context is explicitly declared
3. compatibility fixtures exist
4. the translator preserves old truth rather than changing it
5. the translator has an owner and retirement path

If these conditions are not met, the change must be modeled as a new epoch or rejected.

## Translator Budget

To prevent translator explosion:

```text
one translator per source epoch per interface is the default maximum.
```

Exceptions require:

1. written justification
2. affected trace set
3. risk assessment
4. expiration or consolidation plan

## Epoch Lifecycle

Every epoch must have a declared lifecycle.

```text
draft -> active -> legacy-supported -> sealed -> retired
```

### Draft

Epoch exists for review only. No production trace may depend on it.

### Active

Epoch may be used for new traces.

Requirements:

1. interface versions declared
2. compatibility fixtures published
3. failure taxonomy available
4. replay implementation available

### Legacy-Supported

Epoch no longer accepts new traces but remains replay-supported.

Requirements:

1. all active trace populations identified
2. compatibility fixtures frozen
3. translators stable
4. diagnostics available

### Sealed

Epoch is closed to semantic modification.

Requirements:

1. historical fixture set sealed
2. checksums recorded
3. no new translators added without exception
4. replay support retained

### Retired

Epoch is no longer on the active replay path.

Requirements:

1. no active operational dependency
2. historical access policy exists
3. archival artifacts retained
4. retirement decision recorded

## Epoch Admission Rules

A new epoch is required when:

1. invariant meaning changes
2. replay interpretation changes
3. admission outcome can change
4. witness validation outcome can change
5. identity interpretation changes
6. execution contract semantics change

A new epoch is not required for:

1. documentation improvements
2. UI or CLI improvements
3. non-semantic diagnostics
4. operational metadata that has declared defaults
5. infrastructure adapter changes that do not affect replay meaning

## Epoch Compression Rules

Epochs must be consolidated when possible.

Compression is allowed only when:

1. two epochs have equivalent replay semantics
2. fixture suites prove equivalence
3. diagnostics remain accurate
4. no trace meaning changes
5. operators can still inspect historical lineage

Compression may not:

1. rewrite trace metadata
2. hide semantic differences
3. collapse incompatible witness rules
4. change replay reports
5. remove historical explanation

## Retirement Safeguards

No epoch or translator may be retired if:

1. active evidence bundles still require it
2. legal or audit retention requires replay access
3. fixtures are not archived
4. replay reports would become unavailable
5. operators cannot explain the retirement effect

## Dashboard Requirements

Future operability tooling must show:

1. active epochs
2. legacy-supported epochs
3. translators by source and target
4. fixture health
5. trace populations by epoch
6. deprecated translators
7. retirement warnings

## CI Enforcement Requirements

CI must fail when:

1. a translator lacks lifecycle status
2. a translator lacks fixtures
3. an epoch lacks interface version mapping
4. an active epoch lacks compatibility fixtures
5. a retired epoch is referenced by active traces
6. multiple translators exist for the same source epoch and interface without exception

## Forbidden Patterns

The following are prohibited:

1. chain translators with hidden intermediate semantics
2. use translators to make invalid traces valid
3. introduce production traces on draft epochs
4. retire epochs without preserved fixture access
5. infer epoch from runtime environment
6. allow AI tools to generate translators without constitutional review

## Wave 1 Work Items

1. Create an epoch registry with lifecycle status.
2. Create a translator registry with lifecycle status.
3. Add fixture requirements to each translator entry.
4. Add CI checks for missing lifecycle metadata.
5. Add dashboard requirements to Replay Explorer planning.
6. Define exception workflow for translator budget overrides.

## Exit Criteria

Epoch and translator lifecycle control is established when:

1. every epoch has lifecycle status
2. every translator has lifecycle status
3. translator count is bounded by policy
4. old trace replay remains available
5. historical semantics remain inspectable
6. retirement cannot destroy auditability

## Final Boundary

This policy controls compatibility complexity. It does not define legitimacy.

```text
Epochs preserve semantic context.
Translators preserve access to old truth.
Replay validates truth.
Constitution defines legitimacy.
```
