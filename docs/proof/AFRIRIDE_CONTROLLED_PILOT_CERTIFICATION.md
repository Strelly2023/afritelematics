# AfriRide Controlled Pilot Certification

Artifact Type: Certification Layer

Purpose: Formal closure of Wave 6 under strict controlled-pilot conditions.

STATUS: CONTROLLED PILOT CERTIFICATION CONTRACT

CLASSIFICATION: CERTIFICATION LAYER

The certification artifact provides a single authoritative statement that the controlled pilot executed and validated, without implying production readiness.

## Certification Artifact

```text
AFRIRIDE_CONTROLLED_PILOT_CERTIFICATE.json
```

## Required Structure

```json
{
  "certificate_id": "UUID",
  "generated_at": "ISO_TIMESTAMP",
  "evidence_origin": "field_observed",
  "execution_receipt": {
    "receipt_id": "...",
    "status": "VALID"
  },
  "evidence_bundle": {
    "bundle_id": "...",
    "validated": true
  },
  "verification": {
    "validators_passed": true,
    "replay_consistent": true,
    "identity_integrity": true
  },
  "scope": {
    "locations": 3,
    "scenarios": 16
  },
  "classification": "CONTROLLED_PILOT_CERTIFIED",
  "constraints": {
    "not_production_ready": true,
    "not_scalable": true,
    "not_market_ready": true
  }
}
```

## Certification Rules

```text
MUST HAVE:
- valid execution receipt
- valid evidence bundle
- all validators passed

MUST NOT CLAIM:
- production readiness
- scale readiness
- market readiness
```

## Certification Meaning

```text
System proved deterministic under controlled conditions.
System is NOT proven in uncontrolled environments.
```

## Canonical Certification Contract

```yaml
controlled_pilot_certification:
  schema: afriride.controlled_pilot_certification.v1
  status: controlled_pilot_certification_contract
  classification: certification_layer
  artifact_type: certification_layer
  certificate_filename: AFRIRIDE_CONTROLLED_PILOT_CERTIFICATE.json
  production_readiness_claimed: false
  scale_readiness_claimed: false
  market_readiness_claimed: false
  required_top_level_fields:
    - certificate_id
    - generated_at
    - evidence_origin
    - execution_receipt
    - evidence_bundle
    - verification
    - scope
    - classification
    - constraints
  execution_receipt_fields:
    - receipt_id
    - status
  evidence_bundle_fields:
    - bundle_id
    - validated
  verification_fields:
    - validators_passed
    - replay_consistent
    - identity_integrity
  scope_fields:
    - locations
    - scenarios
  constraint_fields:
    - not_production_ready
    - not_scalable
    - not_market_ready
  required_classification: CONTROLLED_PILOT_CERTIFIED
  required_locations: 3
  required_scenarios: 16
```
