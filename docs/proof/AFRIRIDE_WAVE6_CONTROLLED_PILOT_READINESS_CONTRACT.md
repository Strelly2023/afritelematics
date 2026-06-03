# AfriRide Wave 6 Controlled Pilot Readiness Contract

## Document Classification

```text
STATUS: WAVE 6 PLANNED
CLASSIFICATION: CONTROLLED PILOT READINESS CONTRACT
ROLE: DEFINE EXIT CRITERIA FOR CONTROLLED PILOT READINESS WITHOUT CLAIMING IT
BOUNDARY: WAVE 6 MAY PREPARE PILOT EVIDENCE; WAVE 6 MAY NOT DECLARE PILOT READINESS UNTIL ALL EXIT EVIDENCE PASSES
```

Wave 6 begins after Phase 5 closure.

It is not a continuation of Phase 5 and must not dilute the Phase 5 readiness
certificate. Wave 6 exists to prove operational realism in bounded field
conditions.

## Structured Readiness Contract

```yaml
wave6_controlled_pilot_readiness:
  schema: afriride.wave6_controlled_pilot_readiness.v1
  status: planned
  classification: controlled_pilot_readiness_contract
  predecessor: afriride.phase5_closure.v1
  controlled_pilot_ready: false
  authority: readiness_contract_only
  truth_authority: replay_only
  write_enabled: false
  mutation_authority: false

  required_exit_evidence:
    - pilot_readiness_contract
    - pilot_readiness_validator
    - pilot_readiness_certificate
    - field_run_evidence_receipts
    - pilot_incident_ledger
    - pilot_participant_onboarding_proof
    - pilot_device_registration_proof
    - pilot_completion_report

  operational_surfaces_to_prove:
    - real_pilot_participants
    - real_devices_in_the_field
    - network_instability_handling
    - operational_support_procedures
    - multi_day_pilot_execution
    - external_audit_visibility
    - pilot_incident_management
    - production_deployment_evidence

  non_claims:
    - controlled_pilot_ready
    - public_launch_ready
    - production_ready
    - regulatory_approval
    - external_audit_complete
    - production_key_custody_complete
```

## Exit Criteria

Wave 6 may be considered complete only after:

```text
pilot readiness contract passes
pilot readiness validator passes
pilot readiness certificate passes
field-run evidence receipts pass
pilot incident ledger passes
participant onboarding proof passes
device registration proof passes
pilot completion report passes
```

## Existing Related Protocol

Wave 6 may use the existing live pilot protocol gate:

```bash
python3 -m afritech.ci.afriride_live_pilot_protocol_validator
```

That protocol prepares real-world validation. It does not certify that a pilot
has occurred.
