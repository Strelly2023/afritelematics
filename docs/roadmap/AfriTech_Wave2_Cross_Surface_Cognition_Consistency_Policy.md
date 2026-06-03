# AfriTech Wave 2 Cross-Surface Cognition Consistency Policy

## Document Classification

```text
STATUS: WAVE 2 CONTROL ARTIFACT
CLASSIFICATION: CROSS-SURFACE COGNITION CONSISTENCY POLICY
ROLE: PREVENT CLI, DASHBOARDS, AI COPILOTS, REPORTS, INCIDENT SYSTEMS, AND REPLAY EXPLORERS FROM PRODUCING DIVERGENT OPERATIONAL REALITIES
BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT
```

Wave 2 has governed individual human-facing surfaces. The next risk is
cross-surface divergence:

```text
each surface is safe -> surfaces disagree -> operators receive different realities
```

This policy governs parity across human-facing cognition surfaces.

## Core Rule

```text
Same evidence.
Same status.
Same salience logic.
Same explanation semantics.

Different presentation allowed.
Different operational realities forbidden.
```

Surface variation may improve usability. It must not fragment operational
truth perception.

## Authority Boundary

```text
Constitution -> legitimacy
Replay -> truth validation
Validators -> governance enforcement
Explanation Schema -> safe explanation units
Composition Schema -> safe narrative aggregation
Cognitive Complexity Budget -> bounded cognition
Salience Policy -> bounded attention semantics
Cross-Surface Consistency Policy -> operational reality coherence
Views / AI / Dashboards / Replay Explorer -> governed projections of evidence
Operations -> consumption
```

Cross-surface consistency governs parity between presentations. It does not
validate truth.

## Governed Surfaces

The policy applies to:

1. CLI summaries
2. dashboards
3. replay explorers
4. lineage maps
5. incident reports
6. AI copilots
7. operational consoles
8. audit reports

Every surface may present differently, but all must remain evidence-equivalent.

## Consistency Risk Surfaces

### 1. Explanation Parity

Risk:

```text
Two surfaces reference the same event but expose different explanation meaning.
```

Required containment:

1. same explanation identifiers
2. same source references
3. same validator outcomes
4. same replay references
5. same status semantics

### 2. Salience Parity

Risk:

```text
Dashboard highlights one issue while CLI prioritizes another without declaration.
```

Required containment:

1. same salience source
2. same urgency rules
3. same deterministic ordering rules
4. same hard-failure visibility
5. declared role-scoped variance when applicable

### 3. Narrative Equivalence

Risk:

```text
Incident report tells a different story than replay explorer or AI summary.
```

Required containment:

1. same composition source ids
2. same causality boundaries
3. same omitted detail indicators
4. same authority disclaimer
5. no contradictory operational conclusion

### 4. AI Copilot Consistency

Risk:

```text
AI copilot becomes a parallel cognition universe.
```

Required containment:

1. same explanation schema
2. same composition schema
3. same salience policy
4. same cognitive complexity budget
5. advisory status always visible

### 5. Deterministic Ordering

Risk:

```text
CLI, dashboard, and report order the same items differently without declaration.
```

Required containment:

1. shared ordering keys
2. shared tie-breakers
3. shared unknown-state handling
4. role-scoped ordering declared
5. stable deterministic fallback

## Allowed Surface Differences

Surfaces may differ in:

1. visual layout
2. density
3. role-specific depth
4. progressive disclosure level
5. export format
6. accessibility mode
7. interaction affordances

These differences must not change evidence, status, salience, or meaning.

## Forbidden Surface Differences

Surfaces must not differ in:

1. replay result
2. validator outcome
3. hard failure visibility
4. source evidence reference
5. explanation identifier
6. composition source ids
7. salience source
8. legitimacy implication
9. authority disclaimer

## Role-Scoped Equivalence

Role-specific views may show different depth or emphasis.

Allowed:

1. operator sees current health and next action first
2. developer sees failing artifact first
3. auditor sees replay and evidence lineage first
4. executive sees continuity posture first
5. AI assistant sees investigation path first

Required:

1. same underlying evidence
2. same status semantics
3. same replay result
4. same validator severity
5. same authority boundary

Forbidden:

1. role-specific truth
2. role-specific replay outcome
3. role-specific validator result
4. role-specific legitimacy claim
5. hidden evidence by role

## Surface Transparency

Every surface must declare:

1. surface id
2. surface type
3. source schemas used
4. source evidence references
5. salience policy reference
6. cognitive budget reference
7. role scope
8. presentation differences
9. authority disclaimer

Minimum authority disclaimer:

```text
This surface presents governed evidence. It does not validate truth or define legitimacy.
```

## Cross-Surface Drift Patterns

The following are forbidden:

1. inconsistent health labels
2. conflicting urgency labels
3. mismatched explanation ids
4. incompatible source references
5. divergent AI recommendations
6. hidden role-specific evidence
7. dashboard-only truth
8. CLI-only truth
9. replay explorer-only narrative
10. incident report-only causality

## Cross-Surface Consistency Checks

Future enforcement should compare surface outputs for:

1. same explanation ids
2. same composition ids
3. same status values
4. same salience levels
5. same source references
6. same hard failure visibility
7. same authority disclaimer
8. same replay and validator references
9. declared presentation differences only
10. declared role-scoped variance only

## Future Policy Artifact

Future machine-readable policy:

```text
afritech/constitution/evolution/cross_surface_cognition_policy.yaml
```

Expected contents:

```yaml
schema: afritech.cross_surface_cognition_policy.v1
authority: CONSISTENCY_ONLY
required_parity:
  - explanation_ids
  - source_refs
  - status_values
  - salience_levels
  - authority_disclaimers
allowed_variance:
  - accessibility_mode
  - density
  - export_format
  - progressive_disclosure_level
  - role_specific_depth
  - visual_layout
forbidden_variance:
  - cli_only_truth
  - conflicting_urgency_labels
  - dashboard_only_truth
  - hidden_role_specific_evidence
  - inconsistent_health_labels
  - replay_explorer_only_narrative
```

This artifact constrains cross-surface cognition. It must not define truth.

## Future GA Guard

Future GA enforcement should include:

```bash
python3 -m afritech.ci.cross_surface_cognition_validator
```

The validator should check:

1. required parity fields are declared
2. allowed variance is explicit
3. forbidden variance is rejected
4. CLI and dashboard health labels match
5. AI recommendations cite the same source ids
6. replay explorer narratives match composition source ids
7. incident reports preserve source evidence
8. role-scoped variance is declared
9. hard failures remain visible across surfaces
10. no surface validates replay truth or defines legitimacy

This guard validates cross-surface cognition consistency. It must not validate
replay truth or define legitimacy.

## Success Criteria

Cross-surface cognition consistency is successful when:

1. CLI, dashboard, and AI surfaces report the same health state
2. replay explorer and incident report use compatible narrative sources
3. salience levels remain consistent unless role-scoped variance is declared
4. hard failures remain visible everywhere
5. source evidence references match across surfaces
6. presentation differences are explicit
7. role-specific views preserve shared truth semantics
8. no surface creates an independent operational reality

## Final Boundary

```text
Presentation may vary.
Evidence must match.
Operational reality must not fork.
```

Cross-surface cognition consistency exists to keep human-facing AfriTech
surfaces aligned as the platform grows.
