# AfriRide Controlled Pilot Evidence Bundle

Artifact Type: Proof-Bound Evidence Package

Authority Level: Replay + CI + Constitutional Pipeline

Purpose: Convert pilot execution into admissible system truth

STATUS: CONTROLLED PILOT EVIDENCE BUNDLE CONTRACT

CLASSIFICATION: PROOF-BOUND EVIDENCE PACKAGE

The Evidence Bundle defines the minimum required artifacts that prove controlled pilot execution occurred and that all results are replay-verifiable.

Without this bundle:

```text
Pilot is NOT admissible
Execution is NOT provable
```

This bundle does not prove production readiness, real-world scalability, adversarial resilience, or market readiness.

## Mandatory Bundle Structure

```text
/afriride/pilot_evidence_bundle/

├── participant_registry.json
├── bundle_metadata.json
├── device_registry.json
├── scenario_execution_receipts/
│   ├── Melbourne/
│   ├── Bujumbura_Uvira/
│   └── Kinshasa/
├── incident_records/
├── replay_verification_receipts/
├── pilot_completion_summary.json
└── bundle_manifest.json
```

## Participant Registry

File:

```text
participant_registry.json
```

Rules:

```text
- All participants MUST be whitelisted.
- IDs MUST match execution events.
- No runtime identity creation allowed.
```

## Device Registry

File:

```text
device_registry.json
```

Purpose:

```text
Bind physical execution context to events.
```

## Scenario Execution Receipts

Structure:

```text
scenario_execution_receipts/{location}/{scenario_id}/receipt.json
```

Rules:

```text
- One receipt per scenario execution.
- MUST match runbook ordering.
- MUST align with event log.
```

## Incident Records

Structure:

```text
incident_records/{scenario_id}_{timestamp}.json
```

Rules:

```text
- ALL failures MUST be recorded.
- Missing incident = invalid bundle.
```

## Replay Verification Receipts

Structure:

```text
replay_verification_receipts/{scenario_id}.json
```

Core rule:

```text
execution_hash == replay_hash
```

Violation:

```text
Mismatch -> bundle invalid
```

## Pilot Completion Summary

File:

```text
pilot_completion_summary.json
```

Rule:

```text
This is a SUMMARY.
NOT a source of truth.
```

Truth remains:

```text
Replay receipts
```

## Bundle Manifest

File:

```text
bundle_manifest.json
```

Purpose:

```text
Bind entire bundle into single verifiable identity.
```

## Validator Requirements

The validator MUST enforce:

```text
Completeness:
- All required files exist.
- All 3 locations present.
- All 16 scenarios executed.

Structural Integrity:
- JSON schemas valid.
- No missing fields.

Replay Consistency:
- ALL execution_hash values equal replay_hash values.

Identity Integrity:
- participant_registry matches receipts.
- no new IDs introduced.

Incident Accountability:
- Every failure has a record.

Manifest Consistency:
- Bundle hash matches content.
```

Final output:

```text
EVIDENCE BUNDLE VALID
or
EVIDENCE BUNDLE REJECTED
```

## Invalidation Conditions

Bundle is rejected if any:

```text
- Missing scenario receipt
- Replay mismatch
- Identity inconsistency
- Missing incident record
- Manifest hash invalid
- Unregistered participant used
```

## Evidence Law

```text
Pilot execution is admissible IF AND ONLY IF:

Scenario Execution
-> Event Log
-> Replay Verification
-> Evidence Bundle

forms a complete, consistent, and hash-bound system.
```

## Boundary

This bundle proves:

```text
Controlled pilot execution occurred
Deterministic behavior preserved
Replay truth maintained
```

It does not prove:

```text
production readiness
real-world scalability
adversarial resilience
market readiness
```

## Canonical Evidence Bundle Contract

```yaml
controlled_pilot_evidence_bundle:
  schema: afriride.controlled_pilot_evidence_bundle.v1
  status: controlled_pilot_evidence_bundle_contract
  classification: proof_bound_evidence_package
  artifact_type: proof_bound_evidence_package
  authority_level: replay_ci_constitutional_pipeline
  purpose: convert_pilot_execution_into_admissible_system_truth
  production_readiness_claimed: false
  scalability_claimed: false
  adversarial_resilience_claimed: false
  market_readiness_claimed: false
  truth_authority: replay_receipts
  bundle_root: /afriride/pilot_evidence_bundle/
  required_files:
    - bundle_metadata.json
    - participant_registry.json
    - device_registry.json
    - pilot_completion_summary.json
    - bundle_manifest.json
  required_directories:
    - scenario_execution_receipts
    - incident_records
    - replay_verification_receipts
  required_locations:
    - Melbourne
    - Bujumbura_Uvira
    - Kinshasa
  scenarios_total: 16
  scenario_receipt_path: scenario_execution_receipts/{location}/{scenario_id}/receipt.json
  incident_record_path: incident_records/{scenario_id}_{timestamp}.json
  replay_receipt_path: replay_verification_receipts/{scenario_id}.json
  participant_registry_fields:
    riders:
      - rider_id
      - location
    drivers:
      - driver_id
      - vehicle
      - location
  device_registry_fields:
    devices:
      - device_id
      - user_id
      - type
      - gps_enabled
      - network_type
  scenario_receipt_fields:
    - scenario_id
    - location
    - trip_id
    - participants
    - execution_hash
    - timestamp
    - status
  incident_record_fields:
    - scenario_id
    - location
    - incident_type
    - event_id
    - execution_hash
    - replay_hash
    - resolution
    - status
  replay_receipt_fields:
    - scenario_id
    - execution_hash
    - replay_hash
    - match
    - validator_status
  completion_summary_fields:
    - locations
    - scenarios_total
    - scenarios_executed
    - pass_count
    - fail_count
    - isolated_count
    - replay_success_rate
    - identity_integrity
    - event_integrity
    - final_status
  manifest_fields:
    - bundle_id
    - generated_at
    - evidence_origin
    - locations_covered
    - total_scenarios
    - receipts_count
    - incident_count
    - replay_verified
    - hash
  invalidation_conditions:
    - missing_scenario_receipt
    - replay_mismatch
    - identity_inconsistency
    - missing_incident_record
    - manifest_hash_invalid
    - unregistered_participant_used
  evidence_law:
    - scenario_execution
    - event_log
    - replay_verification
    - evidence_bundle
```
