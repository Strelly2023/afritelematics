# AfriRide Evidence Origin Control

Artifact Type: Provenance Enforcement Layer

Purpose: Prevent synthetic or test-generated evidence from being used for certification or Wave 7 authorization.

STATUS: EVIDENCE ORIGIN CONTROL CONTRACT

CLASSIFICATION: PROVENANCE ENFORCEMENT LAYER

Evidence origin is mandatory across:

```text
- evidence bundle metadata
- bundle manifest
- execution receipt
- certification artifact
```

## Evidence Origins

```text
synthetic:
- CLI-generated test data
- used for validation only
- never admissible for certification

runtime_generated:
- system-generated events from staging or controlled runtime
- may be partially admissible
- not sufficient alone for Wave 7

field_observed:
- real-world pilot execution
- real participants
- real devices
- required for certification and Wave 7
```

## Enforcement Scope

```text
Bundle Validator:
- allows synthetic
- allows runtime_generated
- allows field_observed

Receipt Validator:
- allows synthetic
- allows runtime_generated
- allows field_observed

Certification Validator:
- rejects synthetic
- rejects runtime_generated
- requires field_observed

GO / NO-GO Gate:
- rejects synthetic
- rejects runtime_generated
- requires field_observed
```

## Origin Law

```text
Correct structure + valid replay does not equal admissible truth.
Only field_observed evidence is admissible for certification and Wave 7 authorization.
```

## Canonical Evidence Origin Control Contract

```yaml
evidence_origin_control:
  schema: afriride.evidence_origin_control.v1
  status: evidence_origin_control_contract
  classification: provenance_enforcement_layer
  artifact_type: evidence_origin_control
  allowed_origins:
    - synthetic
    - runtime_generated
    - field_observed
  certification_required_origin: field_observed
  wave7_required_origin: field_observed
  bundle_validator_allows_all_origins: true
  receipt_validator_allows_all_origins: true
  certification_rejects_non_field_observed: true
  go_no_go_rejects_non_field_observed: true
  synthetic_certification_allowed: false
  runtime_generated_wave7_allowed: false
  origin_law:
    - structure_and_replay_are_not_enough
    - origin_authenticates_admissibility
    - field_observed_required_for_progression
```
