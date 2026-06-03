# AfriTech Wave 2 Cognitive Salience Governance Policy

## Document Classification

```text
STATUS: WAVE 2 CONTROL ARTIFACT
CLASSIFICATION: COGNITIVE SALIENCE GOVERNANCE POLICY
ROLE: PREVENT ATTENTION, PRIORITIZATION, HIGHLIGHTING, AND RECOMMENDATIONS FROM BECOMING HIDDEN SEMANTIC AUTHORITY
BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT
```

Wave 2 has bounded cognition. The next risk is attention:

```text
safe explanation -> bounded cognition -> unsafe salience
```

Salience determines what humans see first, what appears urgent, and what feels
operationally important. If unmanaged, salience becomes a hidden semantic force.

## Core Rule

```text
Prioritization allowed.
Attention-driven semantic drift forbidden.

Highlighting allowed.
Authority-by-emphasis forbidden.

Recommendations allowed.
Opaque urgency forbidden.
```

Salience may direct attention. It must not create truth, legitimacy, or hidden
semantic priority.

## Authority Boundary

```text
Constitution -> legitimacy
Replay -> truth validation
Validators -> governance enforcement
Explanation Schema -> safe explanation units
Composition Schema -> safe narrative aggregation
Cognitive Complexity Budget -> bounded cognition
Salience Governance Policy -> bounded attention semantics
Views / AI / Dashboards / Replay Explorer -> governed projections of evidence
Operations -> consumption
```

Salience governance constrains ordering, emphasis, urgency, and recommendation.
It does not validate truth.

## Salience Risk Surfaces

### 1. Ordering Salience

Risk:

```text
What appears first becomes perceived as most true or most important.
```

Required containment:

1. deterministic ordering source
2. declared tie-breaker
3. source evidence reference
4. visible ordering reason
5. no hidden priority ranking

### 2. Visual Emphasis

Risk:

```text
Color, size, animation, or pinning creates implied semantic authority.
```

Required containment:

1. bounded color escalation
2. no animation for non-critical state
3. highlight reason visible
4. source evidence drill-down
5. no emphasis without declared signal

### 3. Urgency Classification

Risk:

```text
Urgency labels reshape operator reality even when evidence is unchanged.
```

Required containment:

1. validator-linked urgency
2. replay-linked urgency when replay is involved
3. deterministic urgency thresholds
4. explicit unknown state
5. no AI-only urgency escalation

### 4. Recommendation Priority

Risk:

```text
Recommended next actions become hidden governance pathways.
```

Required containment:

1. recommendation source disclosed
2. advisory status visible
3. source evidence preserved
4. alternative checks accessible
5. no recommendation that overrides validator or replay result

### 5. AI Salience

Risk:

```text
AI decides what matters most without transparent source grounding.
```

Required containment:

1. AI salience must be advisory
2. AI salience must cite source explanation IDs
3. AI salience must not infer legitimacy
4. AI salience must not invent urgency
5. AI salience must expose omitted detail indicators

## Allowed Salience Sources

Salience may be derived from:

1. validator severity
2. replay mismatch status
3. declared lifecycle state
4. declared incident severity
5. canonical id ordering
6. declared timestamp ordering
7. role-specific operational need

Salience may not be derived from:

1. hidden heuristics
2. AI preference
3. dashboard-local urgency rules
4. user-specific semantic inference
5. runtime environment ordering
6. popularity or usage frequency without declaration

## Deterministic Prioritization Rules

Every prioritized list must declare:

1. primary ordering key
2. secondary tie-breaker
3. source authority
4. unknown-state handling
5. stable deterministic fallback

Allowed example:

```text
order by validator severity,
then declared timestamp,
then canonical id.
```

Forbidden example:

```text
order by AI-estimated importance.
```

## Highlighting Constraints

Highlighting must remain proportional to declared evidence.

Allowed highlight levels:

1. neutral
2. informational
3. warning
4. critical

Rules:

1. critical requires validator failure, replay mismatch, or declared incident severity
2. warning requires degraded, pending, or incomplete evidence
3. informational requires declared context
4. neutral is default
5. unknown must not be displayed as healthy

Forbidden:

1. flashing or animated emphasis for advisory-only content
2. critical styling without declared evidence
3. hiding hard failures behind low-emphasis styling
4. visually emphasizing AI speculation as fact
5. pinning recommendations without source explanation

## Recommendation Boundaries

Recommendations may guide investigation.

They must expose:

1. source explanation IDs
2. source replay or validator references
3. advisory status
4. reason for recommendation
5. alternative inspection paths

They must not:

1. approve exceptions
2. repair state
3. override validators
4. reinterpret replay
5. infer legitimacy
6. create hidden operational priority

## Salience Transparency

Every salient item must be explainable.

Required transparency fields:

1. salience id
2. salience type
3. salience level
4. source signal
5. ordering key
6. tie-breaker
7. source evidence reference
8. advisory flag
9. authority disclaimer

Minimum authority disclaimer:

```text
Salience directs attention. It does not validate truth or define legitimacy.
```

## Attention Budgets

Human attention must remain bounded.

### View Attention Budget

A single view may show at most:

1. one critical banner
2. three highlighted items
3. five recommended next actions
4. one pinned investigation path
5. one AI-generated summary

### Incident Attention Budget

A single incident view may show at most:

1. one primary failure
2. three secondary failures
3. five affected artifacts
4. seven replay or validator references
5. one recommended next check

### AI Attention Budget

An AI assistant may highlight at most:

1. one primary concern
2. three secondary concerns
3. five source explanation records
4. one recommended next check
5. one omitted detail warning

If a budget is exceeded, the surface must show an attention saturation warning.

## Role-Based Salience

Role-specific salience is allowed only when source evidence remains shared.

Allowed:

1. operators see operational urgency first
2. developers see failing artifact first
3. auditors see replay or evidence lineage first
4. executives see continuity posture first
5. AI assistants see investigation path first

Forbidden:

1. role-specific truth
2. role-specific replay result
3. role-specific validator severity
4. role-specific hidden evidence
5. role-specific legitimacy claims

## AI Salience Restrictions

AI may:

1. summarize declared salience
2. explain why an item is highlighted
3. suggest inspection order
4. identify omitted detail
5. group already-salient items

AI must not:

1. create urgency from speculation
2. infer causality
3. infer legitimacy
4. override deterministic ordering
5. hide lower-salience hard failures
6. prioritize without source evidence

AI salience must remain advisory, source-bound, and reversible.

## Future Salience Policy Artifact

Future machine-readable salience policy:

```text
afritech/constitution/evolution/cognitive_salience_policy.yaml
```

Expected contents:

```yaml
schema: afritech.cognitive_salience_policy.v1
authority: SALIENCE_ONLY
allowed_salience_sources:
  - validator_severity
  - replay_mismatch_status
  - declared_lifecycle_state
  - declared_incident_severity
  - canonical_id_ordering
  - declared_timestamp_ordering
  - role_specific_operational_need
forbidden_salience_sources:
  - ai_preference
  - dashboard_local_urgency_rules
  - hidden_heuristics
  - runtime_environment_ordering
  - user_specific_semantic_inference
highlight_levels:
  - neutral
  - informational
  - warning
  - critical
attention_budget:
  max_critical_banners: 1
  max_highlighted_items: 3
  max_recommended_next_actions: 5
  max_pinned_investigation_paths: 1
  max_ai_generated_summaries: 1
```

This artifact constrains attention. It must not define truth.

## Future GA Guard

Future GA enforcement should include:

```bash
python3 -m afritech.ci.cognitive_salience_validator
```

The validator should check:

1. salience sources are declared
2. forbidden salience sources are rejected
3. deterministic prioritization keys exist
4. highlight levels are bounded
5. urgency is tied to replay, validators, or declared incidents
6. recommendations expose source evidence
7. attention budgets are declared
8. role-specific salience preserves shared evidence
9. AI salience remains advisory
10. no salience surface validates replay truth or defines legitimacy

This guard validates salience containment. It must not validate replay truth or
define legitimacy.

## Success Criteria

Salience governance is successful when:

1. operators can see why an item is highlighted
2. prioritized lists have deterministic ordering
3. urgency labels cite validator, replay, or declared incident evidence
4. recommendations remain advisory and inspectable
5. AI salience cites source explanation IDs
6. hard failures are never hidden by low salience
7. attention budgets prevent everything from becoming urgent
8. salience never becomes legitimacy or replay truth

## Final Boundary

```text
Governed attention.
Transparent priority.
No salience-driven truth.
```

Cognitive salience governance exists to keep attention aligned with evidence as
AfriTech grows.
