# AfriTech Wave 2 Canonical Explanation Composition Policy

## Document Classification

```text
STATUS: WAVE 2 CONTROL ARTIFACT
CLASSIFICATION: CANONICAL EXPLANATION COMPOSITION POLICY
ROLE: PREVENT SAFE EXPLANATION RECORDS FROM COMBINING INTO UNSAFE SYNTHETIC MEANING
BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT
```

Wave 2 now has a canonical explanation schema for safe explanation units.
The next risk is composition:

```text
safe explanation records -> unsafe synthetic narrative
```

This policy governs how explanation records may be grouped, sequenced,
summarized, and cross-referenced without becoming a new truth engine.

## Core Rule

```text
Compositions may organize explanations.
Compositions may correlate evidence.
Compositions may guide investigation.

Compositions may not synthesize legitimacy,
infer truth beyond replay,
or create emergent semantic authority.
```

Narratives explain replay-valid evidence. Narratives do not create truth.

## Authority Boundary

```text
Constitution -> legitimacy
Replay -> truth validation
Validators -> governance enforcement
Canonical Explanation Schema -> safe explanation units
Composition Policy -> safe explanation aggregation
Views / AI / Replay Explorer -> governed narrative projections
Operations -> consumption
```

Composition is an organization layer. It is not a validation layer.

## Allowed Composition Types

### 1. Timelines

Purpose:

```text
Order explanation records by declared sequence or declared timestamp.
```

Allowed examples:

1. replay event timeline
2. incident sequence
3. lifecycle transition timeline
4. validation failure timeline

Rules:

1. ordering must come from declared metadata
2. inferred ordering must be labeled as inferred
3. timeline gaps must be visible
4. ordering must not imply causality unless causality is declared

### 2. Lineage Grouping

Purpose:

```text
Group explanation records by declared ancestry or dependency.
```

Allowed examples:

1. epoch lineage group
2. translator dependency group
3. witness dependency group
4. trace artifact lineage group

Rules:

1. lineage must cite source records
2. derived lineage must remain marked as derived
3. missing lineage must be shown as unknown
4. grouping must not invent parent-child semantics

### 3. Replay Trace Aggregation

Purpose:

```text
Make replay evidence navigable across many explanation records.
```

Allowed examples:

1. replay branch summary
2. replay mismatch cluster
3. trace segment grouping
4. replay context bundle

Rules:

1. aggregation must preserve source explanation IDs
2. aggregation must expose replay source references
3. aggregation must not reinterpret replay result
4. aggregation must not convert explanation into evidence

### 4. Validator Clustering

Purpose:

```text
Group validation outcomes for operational diagnosis.
```

Allowed examples:

1. fixture failures by translator
2. budget violations by source epoch
3. invariant failures by subsystem
4. lifecycle failures by registry

Rules:

1. clusters must identify the validator source
2. clusters must not change validator severity
3. clusters must not downgrade hard failures
4. clusters must preserve each original validation result

### 5. Diagnostic Sequencing

Purpose:

```text
Guide investigation through a safe sequence of checks.
```

Allowed examples:

1. inspect validator failure
2. inspect affected artifact
3. inspect source registry field
4. run replay check
5. review remediation workflow

Rules:

1. sequencing is advisory
2. sequencing must not auto-repair
3. sequencing must not assert root cause unless declared by source evidence
4. sequencing must show when evidence is incomplete

## Forbidden Composition Behaviors

### 1. Synthetic Legitimacy

Forbidden:

```text
Multiple explanation records agree -> legitimacy is established.
```

Required:

```text
Legitimacy remains constitutional.
```

### 2. Synthetic Replay Truth

Forbidden:

```text
Narrative says replay is valid -> replay is valid.
```

Required:

```text
Replay result says replay is valid.
Narrative reports that result.
```

### 3. Inferred Causality

Forbidden:

```text
Event A appears before Event B -> Event A caused Event B.
```

Required:

```text
Causality must be declared by trace, replay, validator, or artifact evidence.
```

### 4. Semantic Interpolation

Forbidden:

```text
Missing evidence is filled in to make the story coherent.
```

Required:

```text
Missing evidence remains explicit.
```

### 5. Narrative Truth Generation

Forbidden:

```text
Incident report becomes the authoritative truth.
```

Required:

```text
Incident report remains an organized projection of source evidence.
```

### 6. Speculative Operational Conclusions

Forbidden:

```text
Dashboard or AI concludes a system state that no source evidence declares.
```

Required:

```text
Speculation must be labeled advisory and excluded from truth claims.
```

### 7. AI Semantic Synthesis

Forbidden:

```text
AI combines explanation records into new semantic conclusions.
```

Required:

```text
AI may summarize, group, highlight, and suggest inspection paths only.
```

## Composition Source Integrity

Every composed explanation must preserve:

1. source explanation IDs
2. source authority references
3. transformation steps
4. omitted detail indicators
5. replay authority references when replay is involved
6. validator references when validation is involved

No composition may hide its source chain.

## Evidence Boundary Preservation

```text
Composition cannot strengthen evidence authority.
```

Ten explanation records combined together do not become new proof.
They remain organized projections of existing proof.

Required language:

```text
This composition summarizes source explanations.
It is not itself replay evidence.
```

## AI Composition Restrictions

AI-assisted composition is allowed only when it remains evidence-bounded.

AI may:

1. summarize
2. group
3. highlight
4. suggest inspection paths
5. explain source relationships

AI must not:

1. infer legitimacy
2. synthesize operational truth
3. override replay outcomes
4. create semantic conclusions
5. hide missing evidence
6. transform advisory output into validation output

AI output must always expose:

1. source explanation IDs
2. confidence boundary
3. omitted detail indicator
4. advisory status
5. replay or validator source references

## Composition Transparency

Every composition must expose:

1. composition id
2. composition type
3. source explanation ids
4. source evidence references
5. transformation steps
6. omitted detail count
7. advisory status
8. authority disclaimer

Minimum authority disclaimer:

```text
This composition organizes explanations.
It does not validate truth or define legitimacy.
```

## Composition Complexity Budget

Compositions must remain cognitively bounded.

### MVP Budget

A composition may contain at most:

1. twenty source explanation records
2. three nesting levels
3. five cross-reference groups
4. one primary narrative summary
5. one recommended investigation path

### Expansion Rule

A larger composition requires a declared reason:

1. incident severity
2. replay branch complexity
3. distributed lineage requirement
4. audit request scope
5. regulatory reporting requirement

### Compression Rule

If a composition exceeds the MVP budget, it must provide:

1. a summary
2. omitted detail indicators
3. drill-down links
4. raw source explanation access
5. explicit complexity warning

## Composition Schema Requirements

Future schema enforcement should require:

```yaml
composition_record:
  id: string
  type: timeline | lineage_group | replay_trace | validator_cluster | diagnostic_sequence
  status: green | yellow | red | unknown
  summary: string
  source_explanation_ids: [string]
  source_refs: [...]
  transformation_steps: [string]
  omitted_detail_count: integer
  advisory: boolean
  authority_disclaimer: string
```

Required properties:

1. `source_explanation_ids` must not be empty
2. `advisory` must be true
3. `authority_disclaimer` must deny truth validation and legitimacy definition
4. `status` must derive from source explanation statuses
5. `summary` must not introduce new source facts

## Future GA Guard

Future GA enforcement should include:

```bash
python3 -m afritech.ci.canonical_explanation_composition_validator
```

The validator should check:

1. composition types are allowed
2. source explanation ids are present
3. transformation steps are declared
4. authority disclaimer is present
5. advisory status is true
6. complexity budget is respected
7. AI-assisted summaries remain advisory
8. hard failures are not softened
9. composition does not validate replay truth
10. composition does not define legitimacy

This guard validates composition containment. It must not validate replay truth
or define legitimacy.

## Success Criteria

Composition governance is successful when:

1. incident narratives preserve source explanation IDs
2. timelines do not imply undeclared causality
3. lineage summaries expose source evidence
4. AI-assisted diagnostics remain advisory
5. summaries preserve omitted detail indicators
6. composed explanations remain drill-down capable
7. no composition becomes evidence, replay validation, or legitimacy

## Final Boundary

```text
Safe units.
Safe aggregation.
No synthetic truth.
```

Explanation composition exists to make evidence navigable at scale.
It must never become evidence itself.
