# AfriRide Controlled Pilot Execution Receipt

Artifact Type: Proof Anchor

Authority Level: Replay + Evidence Bundle + CI

Generated: ONLY after real pilot execution

STATUS: CONTROLLED PILOT EXECUTION RECEIPT CONTRACT

CLASSIFICATION: PROOF ANCHOR

The Execution Receipt is the single authoritative artifact that certifies a controlled pilot run occurred and that the evidence bundle is complete, consistent, and replay-validated.

Without this receipt:

```text
Pilot execution is NOT admissible
```

The receipt introduces no new truth. It binds existing truth from the evidence bundle, replay receipts, and validators into one cryptographically bound proof anchor.

## Wave 6 Position

```text
Layer
-> Scenario Matrix
-> Runbook
-> Evidence Bundle
-> Execution Receipt
-> Validation (CI + Replay)
```

## Mandatory Receipt Structure

```json
{
  "receipt_id": "UUID",
  "generated_at": "ISO_TIMESTAMP",
  "evidence_origin": "synthetic | runtime_generated | field_observed",
  "pilot_scope": {
    "locations": ["Melbourne", "Bujumbura_Uvira", "Kinshasa"],
    "total_scenarios": 16
  },
  "evidence_bundle": {
    "bundle_id": "...",
    "bundle_hash": "...",
    "manifest_hash": "...",
    "verified": true
  },
  "execution_summary": {
    "scenarios_executed": 16,
    "pass_count": 16,
    "fail_count": 0,
    "isolated_count": 0
  },
  "replay_verification": {
    "replay_success_rate": "100%",
    "all_hashes_match": true
  },
  "integrity_checks": {
    "identity_integrity": true,
    "event_integrity": true,
    "participant_registry_valid": true,
    "device_registry_valid": true
  },
  "incident_accountability": {
    "total_incidents": 0,
    "all_recorded": true
  },
  "final_status": "ADMISSIBLE",
  "constraints_acknowledged": {
    "not_production_ready": true,
    "not_scalable": true,
    "not_market_ready": true
  }
}
```

## Core Role

```text
Execution Receipt = Proof Compression Layer
```

The receipt binds:

```text
Evidence Bundle -> Hash
Replay -> Verified
Validators -> Passed
```

It MUST NOT:

```text
- modify data
- add new state
- correct failures
- reinterpret results
```

## Hash Binding Rule

```text
receipt.evidence_bundle.bundle_hash == evidence_bundle.manifest.hash
receipt.evidence_bundle.manifest_hash == evidence_bundle.manifest.hash
```

## Validator Requirements

The validator MUST check:

```text
Bundle Existence:
- evidence bundle is present.
- manifest exists.
- bundle hash valid.

Scenario Completeness:
- scenarios_executed == 16.
- locations == 3.

Replay Integrity:
- all_hashes_match == true.
- replay_success_rate == 100%.

Integrity Flags:
- identity_integrity == true.
- event_integrity == true.
- participant_registry_valid == true.
- device_registry_valid == true.

Incident Accountability:
- if incident_count > 0, all_recorded must be true.

Constraint Enforcement:
- not_production_ready == true.
- not_scalable == true.
- not_market_ready == true.
```

Final output:

```text
EXECUTION RECEIPT VALID
or
RECEIPT REJECTED
```

## Invalidation Conditions

Receipt is rejected if any:

```text
- Missing or mismatched bundle hash
- Replay success less than 100%
- Scenario count less than 16
- Location missing
- Integrity flag false
- Incident missing
- Constraint flags missing
```

## Receipt Law

```text
An Execution Receipt is admissible IF AND ONLY IF:

Evidence Bundle is complete
AND Replay verification passes
AND Integrity constraints hold
AND No prohibited claims are introduced
```

## Boundary

Even if valid, this receipt does not prove:

```text
production readiness
scale
reliability in uncontrolled environments
commercial viability
```

It proves only:

```text
A controlled pilot was executed
All required scenarios were run
All results are replay-verifiable
All evidence is complete and consistent
System behaves deterministically under constraints
```

## Canonical Execution Receipt Contract

```yaml
controlled_pilot_execution_receipt:
  schema: afriride.controlled_pilot_execution_receipt.v1
  status: controlled_pilot_execution_receipt_contract
  classification: proof_anchor
  artifact_type: proof_anchor
  authority_level: replay_evidence_bundle_ci
  purpose: bind_controlled_pilot_execution_into_single_authoritative_record
  generated_only_after_real_pilot_execution: true
  introduces_new_truth: false
  truth_authority: evidence_bundle_and_replay_receipts
  production_readiness_claimed: false
  scalability_claimed: false
  market_readiness_claimed: false
  required_locations:
    - Melbourne
    - Bujumbura_Uvira
    - Kinshasa
  total_scenarios: 16
  required_top_level_fields:
    - receipt_id
    - generated_at
    - evidence_origin
    - pilot_scope
    - evidence_bundle
    - execution_summary
    - replay_verification
    - integrity_checks
    - incident_accountability
    - final_status
    - constraints_acknowledged
  pilot_scope_fields:
    - locations
    - total_scenarios
  evidence_bundle_fields:
    - bundle_id
    - bundle_hash
    - manifest_hash
    - verified
  execution_summary_fields:
    - scenarios_executed
    - pass_count
    - fail_count
    - isolated_count
  replay_verification_fields:
    - replay_success_rate
    - all_hashes_match
  integrity_check_fields:
    - identity_integrity
    - event_integrity
    - participant_registry_valid
    - device_registry_valid
  incident_accountability_fields:
    - total_incidents
    - all_recorded
  constraint_fields:
    - not_production_ready
    - not_scalable
    - not_market_ready
  invalidation_conditions:
    - missing_or_mismatched_bundle_hash
    - replay_success_less_than_100
    - scenario_count_less_than_16
    - location_missing
    - integrity_flag_false
    - incident_missing
    - constraint_flags_missing
  receipt_law:
    - evidence_bundle_complete
    - replay_verification_passes
    - integrity_constraints_hold
    - no_prohibited_claims_introduced
```
