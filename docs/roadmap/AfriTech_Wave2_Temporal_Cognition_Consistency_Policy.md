# AfriTech Wave 2 Temporal Cognition Consistency Policy

## Document Classification

```text
STATUS: WAVE 2 CONTROL ARTIFACT
CLASSIFICATION: TEMPORAL COGNITION CONSISTENCY POLICY
ROLE: PREVENT HUMAN-FACING COGNITION FROM PRODUCING DIFFERENT OPERATIONAL REALITIES FROM THE SAME EVIDENCE OVER TIME
BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT
```

Wave 2 has established cross-surface coherence. The next risk is temporal
cognition drift:

```text
same evidence -> future cognition surface -> different operational reality
```

This policy governs how explanations, salience, narratives, summaries, and AI
outputs may evolve over time without changing the operational reality produced
from replay-valid evidence.

## Core Rule

```text
Presentation may evolve.
Compression may evolve.
Interaction may evolve.

Operational reality must remain temporally coherent.
```

Time may improve cognition. Time must not rewrite operational meaning.

## Authority Boundary

```text
Constitution -> legitimacy
Replay -> truth validation
Validators -> governance enforcement
Explanation Schema -> safe explanation units
Composition Schema -> safe narrative aggregation
Cognitive Complexity Budget -> bounded cognition
Salience Policy -> bounded attention semantics
Cross-Surface Consistency Policy -> operational reality coherence across surfaces
Temporal Cognition Consistency Policy -> operational reality coherence across time
Views / AI / Dashboards / Replay Explorer -> governed projections of evidence
Operations -> consumption
```

Temporal cognition consistency governs longitudinal interpretation stability. It
does not validate truth.

## Temporal Drift Surfaces

### 1. Epoch Evolution

Risk:

```text
New epoch semantics cause old evidence to be cognitively explained differently.
```

Required containment:

1. epoch context must remain visible
2. old traces must retain original explanation context
3. epoch translators must not rewrite explanation meaning
4. semantic migrations must disclose cognition impact
5. old explanation records must remain replay-auditable

### 2. Translator Evolution

Risk:

```text
Replay translator changes alter the way old evidence is explained.
```

Required containment:

1. translator version must be visible
2. translated explanations must cite original source evidence
3. translator output must preserve original replay result
4. translator cognition changes must be declared
5. translator retirement must not erase historical cognition context

### 3. UI Redesign

Risk:

```text
New interface layout changes perceived meaning or importance of old evidence.
```

Required containment:

1. status semantics remain stable
2. hard failures remain visible
3. source evidence remains accessible
4. salience reasons remain inspectable
5. redesigned views preserve authority disclaimers

### 4. AI Model Upgrade

Risk:

```text
New AI model summarizes, prioritizes, or narrates old evidence differently.
```

Required containment:

1. model version must be visible
2. AI output remains advisory
3. source explanation IDs are preserved
4. salience and summary drift are detectable
5. AI upgrade cannot infer new legitimacy or replay truth

### 5. Summary Template Evolution

Risk:

```text
New summary wording changes operational interpretation of old evidence.
```

Required containment:

1. template version must be visible
2. summary must preserve source facts
3. wording changes must not soften hard failures
4. omitted detail indicators remain required
5. old summaries remain comparable to new summaries

### 6. Policy Evolution

Risk:

```text
New cognitive policies reinterpret old operational cognition.
```

Required containment:

1. policy version must be visible
2. old cognition artifacts retain applied policy version
3. policy migration must declare cognition impact
4. new policy cannot silently reinterpret old explanation meaning
5. cross-version cognition comparisons must preserve source references

## Temporal Explanation Equivalence

Explanation surfaces may change wording, layout, or density over time.

They must preserve:

1. explanation identifiers
2. source references
3. replay implications
4. validator semantics
5. status meaning
6. authority boundary

Forbidden:

1. changing `red` failure into `yellow` warning without source change
2. changing replay mismatch meaning through wording
3. removing source evidence from newer explanations
4. hiding old hard failures in modernized summaries
5. presenting translated explanation as original evidence

## Temporal Salience Stability

Salience may evolve only through declared policy change.

Required:

1. salience policy version visible
2. ordering rule version visible
3. urgency classification version visible
4. AI salience model version visible when AI is used
5. old and new salience classifications comparable

Forbidden:

1. silent priority downgrade
2. silent urgency inflation
3. hidden salience weighting change
4. AI-only reprioritization
5. visual redesign that hides critical historical failures

## Temporal Narrative Stability

Narratives may become clearer over time.

They must not:

1. infer new causality
2. add synthetic legitimacy
3. remove omitted detail indicators
4. change incident meaning without source change
5. convert advisory narrative into evidence

They must:

1. preserve composition source ids
2. preserve transformation steps
3. preserve authority disclaimers
4. expose narrative template version
5. expose summarization policy version

## AI Temporal Stability

AI-assisted cognition must remain version-transparent.

Every AI-generated cognitive artifact must expose:

1. model identifier
2. prompt or template version
3. source explanation ids
4. salience policy version
5. advisory status
6. omitted detail indicator
7. authority disclaimer

AI upgrades must not:

1. infer legitimacy from old evidence
2. synthesize replay truth
3. change hard failure severity
4. hide old evidence
5. create model-version-dependent operational reality

## Temporal Ordering Stability

Ordering over time must remain explainable.

Allowed ordering evolution:

1. new declared tie-breaker
2. clearer grouping with preserved source ids
3. role-scoped ordering with declared policy version
4. accessibility ordering with preserved semantics

Forbidden ordering evolution:

1. hidden priority rewrite
2. AI model preference ordering
3. dashboard redesign ordering without declaration
4. runtime-order-dependent historical replay display
5. removing hard failures from top-level historical view

## Evolution Transparency

Every temporal cognition artifact must declare:

1. evidence id
2. explanation schema version
3. composition schema version
4. cognitive complexity budget version
5. salience policy version
6. summary template version
7. AI model version when applicable
8. epoch context when applicable
9. translator context when applicable
10. authority disclaimer

Minimum authority disclaimer:

```text
This cognition artifact presents evidence under declared temporal context.
It does not validate truth or define legitimacy.
```

## Temporal Drift Detection

Future enforcement should detect:

1. summary drift
2. salience drift
3. explanation reinterpretation
4. narrative divergence
5. AI model cognition instability
6. hard failure softening
7. source reference loss
8. authority disclaimer loss
9. epoch context loss
10. translator context loss

## Future Policy Artifact

Future machine-readable policy:

```text
afritech/constitution/evolution/temporal_cognition_policy.yaml
```

Expected contents:

```yaml
schema: afritech.temporal_cognition_policy.v1
authority: TEMPORAL_CONSISTENCY_ONLY
required_context:
  - evidence_id
  - explanation_schema_version
  - composition_schema_version
  - cognitive_complexity_budget_version
  - salience_policy_version
  - summary_template_version
  - authority_disclaimer
conditional_context:
  - ai_model_version
  - epoch_context
  - translator_context
forbidden_temporal_drift:
  - ai_model_cognition_instability
  - authority_disclaimer_loss
  - explanation_reinterpretation
  - hard_failure_softening
  - narrative_divergence
  - salience_drift
  - source_reference_loss
  - summary_drift
```

This artifact constrains temporal cognition. It must not define truth.

## Future GA Guard

Future GA enforcement should include:

```bash
python3 -m afritech.ci.temporal_cognition_validator
```

The validator should check:

1. temporal context fields are declared
2. schema and policy versions are visible
3. AI model version is visible when AI is used
4. epoch and translator context are visible when applicable
5. source references remain stable
6. hard failures are not softened over time
7. salience changes are declared
8. narrative template changes preserve source ids
9. summaries remain operationally equivalent
10. no temporal cognition surface validates replay truth or defines legitimacy

This guard validates temporal cognition consistency. It must not validate replay
truth or define legitimacy.

## Success Criteria

Temporal cognition consistency is successful when:

1. old and new explanations preserve the same operational meaning
2. salience changes are visible and policy-linked
3. AI model upgrades do not produce hidden semantic drift
4. old incident narratives remain comparable to new narratives
5. source evidence remains inspectable across time
6. epoch and translator context remain visible where applicable
7. hard failures retain their severity unless source evidence changes
8. no cognition evolution creates a new operational reality from old evidence

## Final Boundary

```text
Evolution may improve cognition.
Evidence meaning must persist.
Operational reality must remain time-stable.
```

Temporal cognition consistency exists to keep human-facing AfriTech surfaces
coherent across versions, epochs, redesigns, and AI upgrades.
