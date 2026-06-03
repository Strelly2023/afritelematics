# AfriTech Wave 2 Cognitive Scale Governance Policy

## Document Classification

```text
STATUS: WAVE 2 CONTROL ARTIFACT
CLASSIFICATION: COGNITIVE SCALE GOVERNANCE POLICY
ROLE: KEEP GOVERNED COGNITION HUMAN-USABLE AS EXPLANATIONS, NARRATIVES, AND LINEAGE SURFACES GROW
BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT
```

Wave 2 has established governed cognition:

```text
observability -> governed visibility
interpretation -> governed simplification
explanation schema -> governed explanation units
composition schema -> governed narrative aggregation
```

The next risk is scale:

```text
governed cognition -> too much governed cognition -> human overload
```

This policy keeps cognitive surfaces bounded as AfriTech grows.

## Core Rule

```text
Compression allowed.
Mutation forbidden.

Organization allowed.
Synthetic truth forbidden.

Scale must reduce human load.
Scale must not hide source evidence.
```

Governed cognition exists to make replay-valid evidence usable. It must not
become a cognitive burden that forces operators into shortcuts.

## Authority Boundary

```text
Constitution -> legitimacy
Replay -> truth validation
Validators -> governance enforcement
Explanation Schema -> safe explanation units
Composition Schema -> safe narrative aggregation
Cognitive Scale Policy -> bounded human comprehension
Views / AI / Dashboards / Replay Explorer -> governed projections of evidence
Operations -> consumption
```

Cognitive scale governance constrains presentation and navigation. It does not
validate truth.

## Cognitive Scale Risk Surfaces

### 1. Lineage Explosion

Risk:

```text
Replay, epoch, translator, witness, and artifact lineage becomes graph-heavy.
```

Required containment:

1. lineage compression
2. progressive expansion
3. source artifact drill-down
4. visible omitted detail counts
5. stable ordering

### 2. Narrative Density

Risk:

```text
Incident narratives accumulate too many explanation records and cross-links.
```

Required containment:

1. narrative summaries
2. bounded composition depth
3. role-specific incident views
4. explicit complexity warnings
5. raw source access

### 3. Diagnostic Branching

Risk:

```text
Guided diagnostics branch into too many possible next checks.
```

Required containment:

1. one primary recommended next check
2. secondary checks hidden behind expansion
3. validator-derived cause labels
4. no speculative root cause
5. replay or artifact links for each branch

### 4. Role Overload

Risk:

```text
Every user sees the full constitutional complexity of every surface.
```

Required containment:

1. role-scoped cognition
2. operator, developer, auditor, and executive views
3. explicit role boundaries
4. consistent underlying evidence
5. no role-specific truth model

### 5. AI Explanation Sprawl

Risk:

```text
AI assistants generate long summaries, inferred relationships, or hidden priorities.
```

Required containment:

1. short evidence-bound summaries
2. source explanation IDs
3. advisory status
4. omitted detail indicators
5. no semantic conclusions

## Cognitive Budgets

Every cognitive surface should declare a budget.

### View Budget

A single view should expose at most:

1. one primary health signal
2. five top-level facts
3. three primary actions
4. two visible lineage groups
5. one evidence drill-down entry point

### Narrative Budget

A single narrative should expose at most:

1. one primary summary
2. twenty source explanation records
3. three nesting levels
4. five cross-reference groups
5. one recommended investigation path

### Diagnostic Budget

A single diagnostic guide should expose at most:

1. one primary cause
2. one primary affected artifact
3. one primary source evidence reference
4. one primary next check
5. three secondary checks behind expansion

### Role Budget

A role-scoped view should expose only what the role can act on.

Examples:

| Role | Primary Cognitive Need |
| --- | --- |
| Operator | current health and next action |
| Developer | failing artifact and source evidence |
| Auditor | replay result and evidence lineage |
| Executive | continuity posture and risk summary |
| AI assistant | source-bounded explanation and safe next checks |

No role may receive a different truth model.

## Progressive Disclosure Requirements

Every cognitive surface must support layered access:

```text
Layer 1: health or state
Layer 2: cause
Layer 3: affected artifact
Layer 4: source evidence
Layer 5: raw record or replay reference
```

Rules:

1. Layer 1 must fit on one screen or one CLI summary.
2. Layer 2 must cite a validator, replay, registry, or artifact source.
3. Layer 3 must identify the affected object.
4. Layer 4 must link to source evidence.
5. Layer 5 must remain available for expert inspection.

Progressive disclosure may hide detail temporarily. It must not remove access
to detail.

## Deterministic Ordering

Human-facing ordering must be stable.

Allowed ordering sources:

1. declared sequence
2. declared timestamp
3. canonical id
4. severity derived from validator or replay result
5. explicit role priority

Forbidden ordering sources:

1. AI preference
2. dashboard-local ranking without declaration
3. hidden heuristic priority
4. runtime environment ordering
5. user-specific semantic inference

Stable ordering prevents different surfaces from telling different operational
stories.

## Lineage Compression Rules

Lineage may be compressed only if the compression remains reversible.

Allowed:

1. collapse repeated healthy branches
2. group records by declared source
3. summarize identical validator outcomes
4. hide low-risk branches behind expansion
5. show omitted detail counts

Forbidden:

1. remove failing branches
2. merge distinct semantic contexts
3. hide unknown lineage
4. collapse replay mismatches into generic warnings
5. omit source identifiers

Compression must preserve source traceability.

## Role-Scoped Cognition Rules

Role-specific views may simplify the same evidence differently.

They may not:

1. change health classification
2. change replay result
3. change validator severity
4. hide hard failures
5. create role-specific legitimacy

They must:

1. cite the shared source evidence
2. preserve drill-down access
3. expose authority disclaimers
4. use the canonical explanation schema
5. use the canonical composition schema for narratives

## AI Copilot Boundaries

Operational copilots may assist cognitive scale management.

AI may:

1. summarize within budget
2. suggest inspection order
3. group explanation records
4. highlight missing evidence
5. explain declared relationships

AI must not:

1. infer legitimacy
2. synthesize replay truth
3. override validator severity
4. hide missing evidence
5. invent source relationships
6. exceed cognitive budgets without warning

AI output must always remain advisory and source-bound.

## Complexity Warning Rules

A cognitive surface must display a complexity warning when it exceeds any
declared budget.

Warning must include:

1. exceeded budget name
2. actual count
3. allowed count
4. omitted detail count
5. drill-down path

Example:

```text
Complexity warning:
lineage groups exceed MVP budget (8 shown / 5 allowed).
3 groups collapsed. Expand to inspect source evidence.
```

Warnings explain overload. They do not change validity.

## Future Budget Artifact

Future machine-readable budget:

```text
afritech/constitution/evolution/cognitive_complexity_budget.yaml
```

Expected contents:

```yaml
schema: afritech.cognitive_complexity_budget.v1
authority: BUDGET_ONLY
view_budget:
  max_primary_health_signals: 1
  max_top_level_facts: 5
  max_primary_actions: 3
  max_visible_lineage_groups: 2
  max_evidence_drill_down_entry_points: 1
narrative_budget:
  max_primary_summaries: 1
  max_source_explanation_records: 20
  max_nesting_levels: 3
  max_cross_reference_groups: 5
  max_recommended_investigation_paths: 1
diagnostic_budget:
  max_primary_causes: 1
  max_primary_affected_artifacts: 1
  max_primary_source_refs: 1
  max_primary_next_checks: 1
  max_secondary_checks_collapsed: 3
```

This artifact constrains cognitive load. It must not define truth.

## Future GA Guard

Future GA enforcement should include:

```bash
python3 -m afritech.ci.cognitive_complexity_validator
```

The validator should check:

1. cognitive budgets are declared
2. views cite canonical explanation schema
3. narratives cite canonical composition schema
4. role-scoped views preserve shared source evidence
5. hard failures are never hidden
6. complexity warnings appear when budgets are exceeded
7. AI surfaces remain advisory
8. ordering sources are deterministic
9. compression is reversible
10. no cognitive surface validates replay truth or defines legitimacy

This guard validates cognitive scale containment. It must not validate replay
truth or define legitimacy.

## Success Criteria

Cognitive scale governance is successful when:

1. operators can identify health and next action quickly
2. developers can drill down to source evidence
3. auditors can inspect replay and lineage references
4. executives can see continuity posture without semantic detail overload
5. AI assistants remain advisory and source-bound
6. complex narratives expose omitted detail counts
7. all compressed views remain reversible
8. no role receives a different truth model

## Final Boundary

```text
Bounded cognition.
Preserved evidence.
No hidden meaning.
```

Cognitive scale governance exists to make governed explanation survivable as
AfriTech grows.
