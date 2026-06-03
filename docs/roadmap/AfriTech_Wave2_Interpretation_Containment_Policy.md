# AfriTech Wave 2 Interpretation Containment Policy

## Document Classification

```text
STATUS: WAVE 2 CONTROL ARTIFACT
CLASSIFICATION: INTERPRETATION CONTAINMENT POLICY
ROLE: PREVENT EXPLANATION SURFACES FROM ACCUMULATING AUTHORITY OR COMPLEXITY
BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY OR REPLAY TRUTH
```

Wave 2 makes AfriTech understandable to humans. That creates a new risk:

```text
many views -> many interpretations -> hidden authority drift
```

This policy contains that risk.

## Core Rule

```text
Views may simplify.
Views may summarize.
Views may guide.
Views must not reinterpret, override, or create legitimacy.
```

Interpretation exists to reduce human cognitive load. It must not become a
parallel truth system.

## Authority Boundary

```text
Constitution -> legitimacy
Replay -> truth validation
Validators -> governance enforcement
Status / observability -> explanation
Operations -> consumption
```

All interpretation surfaces are subordinate to validator-derived state and
replay-validated truth.

## Allowed View Types

Interpretation surfaces may provide the following views.

### 1. Status Views

Purpose:

```text
Show current validator-derived state.
```

Examples:

1. compatibility health
2. epoch lifecycle status
3. fixture status
4. translator budget status
5. replay failure status

Rules:

1. status must identify its data source
2. status must not mutate state
3. status must not replace validator output
4. status must expose uncertainty or incomplete inputs

### 2. Lineage Views

Purpose:

```text
Show historical or causal relationships.
```

Examples:

1. epoch lineage
2. translator paths
3. replay trace lineage
4. witness dependency chains

Rules:

1. lineage edges must come from declared metadata
2. inferred lineage must be labeled as derived
3. hidden lineage inference is forbidden
4. lineage views must link back to source artifacts

### 3. Diagnostic Views

Purpose:

```text
Explain why validation or replay failed.
```

Examples:

1. missing compatibility fixture
2. translator budget violation
3. replay hash mismatch
4. epoch context mismatch
5. witness inconsistency

Rules:

1. diagnostics must cite the failing validator or replay check
2. diagnostics may suggest next actions
3. diagnostics must not auto-repair
4. diagnostics must not downgrade failures

### 4. Summary Views

Purpose:

```text
Compress complex state for rapid human scanning.
```

Examples:

1. green / amber / red health
2. active epoch count
3. translator pressure score
4. retirement readiness summary
5. compatibility debt summary

Rules:

1. summary logic must be documented
2. summaries must be traceable to raw fields
3. summaries must not hide hard failures
4. summaries must provide drill-down paths

### 5. Guided Views

Purpose:

```text
Help humans follow the correct operational path.
```

Examples:

1. replay walkthroughs
2. compatibility failure guides
3. retirement readiness checklists
4. CLI command hints
5. onboarding flows

Rules:

1. guidance must preserve replay authority
2. guidance must not create shortcut truth
3. guidance must distinguish advice from validation
4. guidance must remain reversible and inspectable

## Forbidden Interpretation Patterns

The following are not allowed.

### 1. Dashboard-As-Truth

Forbidden:

```text
Dashboard says valid -> therefore valid.
```

Required:

```text
Replay or validator says valid.
Dashboard reports that result.
```

### 2. Hidden Semantic Inference

Forbidden:

```text
View infers epoch state from environment, runtime shape, or naming convention.
```

Required:

```text
View reads declared metadata or validator output.
```

### 3. Failure Softening

Forbidden:

```text
Hard validator failure displayed as warning for convenience.
```

Required:

```text
Hard validator failure remains hard in interpretation.
```

### 4. Summary Without Drill-Down

Forbidden:

```text
Health: green
```

without source evidence.

Required:

```text
Health: green -> derived from fixture status, budget status, lifecycle status.
```

### 5. View-Specific Truth

Forbidden:

```text
CLI says valid but dashboard says valid under different rules.
```

Required:

```text
CLI and dashboard consume the same governed explanation model.
```

### 6. Auto-Repair From Interpretation

Forbidden:

```text
Dashboard fixes registry, translator, epoch, trace, or witness state.
```

Required:

```text
Dashboard may guide remediation.
Only governed workflows may mutate state.
```

## Diagnostic Layering Rules

Interpretation must use progressive disclosure.

```text
Layer 1: state
Layer 2: cause
Layer 3: affected artifact
Layer 4: source evidence
Layer 5: recommended next action
```

### Layer 1: State

Examples:

```text
green
amber
red
pending
unknown
```

### Layer 2: Cause

Examples:

```text
fixture_missing
translator_budget_exceeded
epoch_retirement_blocked
trace_context_mismatch
```

### Layer 3: Affected Artifact

Examples:

```text
EPOCH-1
translator:EPOCH-1->replay.v2
trace:abc123
witness:def456
```

### Layer 4: Source Evidence

Examples:

```text
validator result
registry field
replay mismatch
fixture output
```

### Layer 5: Recommended Next Action

Examples:

```text
add fixture
remove duplicate translator
request budget exception
run replay
inspect trace
```

Recommended actions are advisory. They are not validation.

## Progressive Disclosure Rules

Every human-facing interpretation surface must support at least two levels:

1. summary view
2. evidence view

Complex surfaces should support:

1. summary
2. cause
3. artifact
4. evidence
5. action

Rules:

1. novice users must see a simple health signal
2. expert users must be able to inspect the raw evidence
3. no summary may block access to source artifacts
4. no view may require understanding the full constitution to operate safely

## Dashboard Complexity Budget

Dashboards must remain cognitively bounded.

### MVP Budget

An MVP dashboard may expose at most:

1. one primary health signal
2. five top-level metric cards
3. two lineage views
4. one failure table
5. one evidence drill-down panel

### Expansion Rule

A new dashboard component may be added only if it answers a distinct operator
question that cannot be answered by an existing component.

### Removal Rule

A dashboard component must be removed or merged if:

1. it duplicates another view
2. it is not used in operational diagnosis
3. it hides source evidence
4. it creates confusion about authority

## Explanation Source-Of-Truth Rules

All explanation surfaces must declare their source.

Allowed sources:

1. validator output
2. replay output
3. declared registry metadata
4. fixture output
5. canonical trace or witness artifact

Forbidden sources:

1. hidden runtime environment
2. dashboard-local rules
3. undocumented heuristics
4. AI-only interpretation
5. cached state without validation context

AI may assist explanation, but AI output must be labeled advisory and must link
back to deterministic evidence.

## CLI / Dashboard Parity Requirements

For every dashboard interpretation surface, there should be an equivalent CLI
or JSON output path.

Required parity:

1. same source data
2. same health classification
3. same failure identifiers
4. same affected artifact identifiers
5. same authority disclaimer

Allowed differences:

1. visual layout
2. grouping
3. progressive disclosure depth
4. copy/export affordances

Forbidden differences:

1. different validation rules
2. different legitimacy criteria
3. dashboard-only truth
4. CLI-only truth

## GA Guard For Interpretive Drift

Future GA enforcement should include:

```bash
python3 -m afritech.ci.interpretation_containment_validator
```

The validator should check:

1. interpretation surfaces declare `OBSERVATION_ONLY`
2. dashboards and CLI surfaces cite governed sources
3. summaries provide drill-down evidence paths
4. hard failures are not softened
5. AI-assisted explanations are advisory only
6. CLI and dashboard health labels remain compatible
7. no interpretation surface mutates constitutional or compatibility registries

This guard validates interpretation containment.
It must not validate replay truth or define legitimacy.

## Success Criteria

Interpretation containment is successful when:

1. every view declares its source of explanation
2. every summary has a drill-down path
3. every failure shows cause, artifact, and evidence
4. CLI and dashboard outputs use compatible health language
5. no view can approve exceptions or mutate registries
6. operators can distinguish explanation from validation
7. contributors can add new views without adding new authority

## Final Boundary

```text
Many views.
One governed explanation model.
Zero new authority.
```

Interpretation containment exists to keep AfriTech human-usable as its
observability surfaces grow.
