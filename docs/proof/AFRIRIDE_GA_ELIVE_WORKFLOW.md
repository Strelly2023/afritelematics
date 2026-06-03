# AfriRide GA eLive Workflow Upgrade

## Document Classification

```text
STATUS: PHASE 5 ACTIVE WORKFLOW CONTRACT
CLASSIFICATION: GA ELIVE DETERMINISTIC MOBILITY WORKFLOW
ROLE: DEFINE UBER-LIKE RIDER AND DRIVER UX THROUGH AFRITECH REPLAY-GOVERNED EXECUTION
BOUNDARY: WORKFLOW CAPABILITY MAY INCREASE; CLIENT AND PRODUCT SURFACES MAY NOT DEFINE TRUTH
```

This document defines the GA eLive workflow target for AfriRide.

It upgrades the user-facing ride lifecycle toward an Uber-like experience while
keeping the execution model deterministic, replayable, event-ledger-backed, and
constitutionally bounded.

This document does not claim completed public launch readiness, completed field
pilot readiness, global dispatch fairness, Byzantine network resilience,
external audit anchoring, PKI completeness, hardware-backed key custody, or
jurisdiction-grade non-repudiation.

## Structured Workflow Contract

```yaml
ga_elive_workflow:
  schema: afriride.ga_elive_workflow.v1
  status: phase_5_active
  classification: ga_elive_deterministic_mobility_workflow
  authority: workflow_contract_only
  write_enabled: false
  mutation_authority: false
  truth_authority: replay_only

  required_pipeline:
    - rider_request
    - edge_adapter
    - normalization
    - queue_ingestion
    - partition_routing
    - worker_execution
    - core_matching_engine
    - immutable_event_log
    - replay_proof
    - portable_receipt
    - rider_driver_notification
    - trip_lifecycle
    - payment_event
    - rating_event
    - constitutional_receipt

  execution_rules:
    no_direct_api_to_core_execution: true
    deterministic_matching_required: true
    race_based_matching_forbidden: true
    event_log_is_append_only: true
    replay_defines_truth: true
    receipts_are_derived_evidence: true
    client_truth_authority: false
    ui_mutation_authority: false

  core_modules:
    api_entry: afritech.api.app
    adapter: edge.adapter.runtime_adapter
    normalization: edge.normalization.normalizer
    edge_guard: guards.edge_input_guard
    queue_ingestion: edge.ingestion.queue_ingestor
    partition_router: execution.partition.router
    worker_pool: execution.worker.worker_pool
    core_engine: core.engine
    matching_engine: core.matching_engine
    event_log: storage.event_log
    event_schema: storage.event_schema
    replay_engine: storage.replay_engine
    constitutional_receipt: proof.constitutional_receipt
    witness_system: proof.witness
    ci_enforcement: afritech.ci

  rider_steps:
    - request_ride
    - confirm_location_destination
    - observe_driver_assignment
    - track_driver
    - observe_trip_start
    - observe_trip_completion
    - observe_payment_receipt
    - submit_rating_event

  driver_steps:
    - go_online
    - receive_deterministic_assignment
    - accept_ride
    - navigate_pickup
    - start_trip
    - complete_trip
    - observe_earnings
    - submit_feedback_event

  proven_phase5_evidence:
    - driver_app_isolated_validation
    - driver_backend_contract
    - rider_backend_contract
    - sha256_ledger_validation
    - identity_bound_signatures
    - portable_ledger_receipts
    - rider_proof_visibility
    - driver_proof_visibility
    - adversarial_fail_closed_integration
    - live_local_rider_driver_e2e
    - running_backend_rider_driver_e2e

  not_yet_proven:
    - real_flutter_driver_app_to_running_backend_to_real_rider_app
    - multi_driver_contention
    - concurrent_ride_execution
    - network_interruption_recovery
    - cross_device_signed_event_emission
    - pilot_field_operation
    - external_audit_anchoring
    - production_key_custody
```

## Required Flow

```text
Rider Request
-> Edge Adapter
-> Normalization
-> Queue Ingestion
-> Partition Routing
-> Worker Execution
-> Core Matching Engine
-> Immutable Event Log
-> Replay Proof and Portable Receipt
-> Rider and Driver Notification
-> Trip Lifecycle
-> Payment Event and Rating Event
-> Constitutional Receipt
```

## Rider Workflow

```text
App request
-> adapter structure
-> canonical normalization
-> queue event
-> worker execution
-> deterministic matching
-> event log
-> notification
-> read-only proof surfaces
```

No direct API-to-core execution allowed.

The rider may request, observe, pay, rate, and inspect proof.

The rider may not define driver assignment, fare truth, replay hash, receipt
hash, trip legitimacy, event ordering, or final system truth.

## Driver Workflow

```text
Driver online
-> deterministic assignment observed
-> acceptance event
-> trip start event
-> trip completion event
-> derived earnings
-> feedback event
-> read-only proof surfaces
```

The driver may submit lifecycle actions and inspect evidence.

The driver may not win a race condition, override assignment, mutate the event
log, define fare truth, define replay truth, or self-authorize completion.

## Deterministic Matching Rule

Uber-like first-accept race semantics are forbidden for GA eLive.

AfriRide matching must use:

```text
pre-recorded candidates
deterministic scoring
stable tie-breaking
partition-bound inputs
replay-visible selection parameters
```

The required invariant is:

```text
same declared matching input -> same driver assignment
```

## Proof Surfaces

The GA eLive workflow must emit or preserve:

```text
canonical event log
SHA-256 ledger chain
registered-key signature validation
replay proof
portable ledger receipt
constitutional receipt
execution witness
replay witness
transcript witness
```

Receipts and UI summaries are derived evidence only.

They must not participate in or mutate the canonical event hash chain.

## Enforcement Surface

```text
docs/proof/AFRIRIDE_GA_ELIVE_WORKFLOW.md
afritech/ci/afriride_ga_elive_workflow_validator.py
afritech/tests/ci/test_afriride_ga_elive_workflow_validator.py
afriride_system/tests/e2e/test_live_local_mobile_clients_e2e.py
afriride_system/tests/test_phase5_adversarial_integration.py
```

## Current Gate

```bash
python3 -m afritech.ci.afriride_ga_elive_workflow_validator
```

Passing this gate means the GA eLive workflow contract preserves the AfriTech
execution boundary: all ride actions flow through declared deterministic
stages, all proof surfaces remain derived from canonical ledger truth, and all
remaining operational realism gaps stay explicit.
