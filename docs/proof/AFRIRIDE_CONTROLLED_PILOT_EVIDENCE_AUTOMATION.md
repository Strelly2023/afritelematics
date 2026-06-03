# AfriRide Controlled Pilot Evidence Automation

Artifact Type: System Automation Layer

Purpose: Convert raw execution into a structured evidence bundle automatically.

STATUS: CONTROLLED PILOT EVIDENCE AUTOMATION CONTRACT

CLASSIFICATION: SYSTEM AUTOMATION LAYER

The evidence automation layer eliminates manual evidence assembly and ensures completeness, integrity, reproducibility, and validator-ready output.

## Pipeline Architecture

```text
Event Log
-> Execution Trace Extractor
-> Replay Engine
-> Proof Generator
-> Evidence Builder
-> Bundle Assembler
-> Bundle Validator
-> Evidence Bundle (Admissible)
```

## Core Components

```text
Trace Extractor:
- input: event_log
- output: structured execution traces per scenario

Scenario Mapper:
- maps event sequences to scenario IDs A1 through F3.
- enforces all 16 scenarios appear.

Replay Validator Engine:
- replay(trace) computes replay_hash.
- replay_hash must equal execution_hash.

Evidence Builder:
- generates scenario execution receipts.
- generates replay verification receipts.
- generates incident records.

Bundle Assembler:
- creates participant_registry.json.
- creates device_registry.json.
- creates scenario_execution_receipts.
- creates incident_records.
- creates replay_verification_receipts.
- creates pilot_completion_summary.json.
- creates bundle_manifest.json.

Bundle Validator Trigger:
- runs afriride_controlled_pilot_evidence_bundle_validator.py.
```

## Automation Law

```text
Evidence MUST be generated from system data.
Evidence MUST NOT be manually constructed.
```

## Forbidden

```text
- manual editing
- partial bundle creation
- skipping replay verification
```

## Canonical Evidence Automation Contract

```yaml
controlled_pilot_evidence_automation:
  schema: afriride.controlled_pilot_evidence_automation.v1
  status: controlled_pilot_evidence_automation_contract
  classification: system_automation_layer
  artifact_type: system_automation_layer
  purpose: convert_raw_execution_into_validator_ready_evidence_bundle
  manual_evidence_construction_allowed: false
  partial_bundle_creation_allowed: false
  replay_verification_required: true
  required_pipeline:
    - event_log
    - execution_trace_extractor
    - replay_engine
    - proof_generator
    - evidence_builder
    - bundle_assembler
    - bundle_validator
    - admissible_evidence_bundle
  required_components:
    - trace_extractor
    - scenario_mapper
    - replay_validator_engine
    - evidence_builder
    - bundle_assembler
    - bundle_validator_trigger
  generated_artifacts:
    - participant_registry.json
    - device_registry.json
    - scenario_execution_receipts
    - incident_records
    - replay_verification_receipts
    - pilot_completion_summary.json
    - bundle_manifest.json
  scenarios_required: 16
  output_authority: evidence_bundle_validator
```
