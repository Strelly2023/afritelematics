# AfriRide Controlled Pilot Layer

STATUS: CONTROLLED PILOT LAYER DESIGN CONTRACT

CLASSIFICATION: GA ELITE CLOSED-WORLD CONTINUITY PROOF ENVIRONMENT

This artifact defines the AfriRide Controlled Pilot Layer as a deterministic, replay-verifiable, closed-world execution environment used to demonstrate continuity under controlled disruption.

It is not a production ride-hailing system. It does not certify production readiness, global scale, uncontrolled field operation, or external runtime guarantees.

## Purpose

The Controlled Pilot Layer exists to prove continuity invariants under bounded disruption:

```text
controlled input -> canonical event -> queued deterministic execution -> replay -> proof -> registry seal
```

It is scoped to proving continuity behavior, not optimizing dispatch, expanding business logic, or making production claims.

## Enforced Pipeline

```text
EDGE LAYER
  -> adapter
  -> normalization
  -> ingestion
  -> EDGE GUARD
  -> runtime_admission
  -> runtime_orchestration
  -> runtime_activation
  -> guard_engine
  -> core_engine (matching)
  -> worker_execution
  -> event_log + storage
  -> proof_generation
  -> evaluation_engine
  -> replay_verification
  -> constitutional_receipt
  -> registry_seal
```

External input MUST pass:

```text
adapter -> normalization -> ingestion -> guard
```

## Formal Validity Rule

An execution `e` is valid iff:

```text
valid(e) =
  admissible(e)
  and deterministic(e)
  and invariant_preserving(e)
  and replay_equivalent(e)
  and identity_stable(e)
  and trace_complete(e)
```

## Forbidden Violations

```text
FORBIDDEN:

- Direct API -> core execution
- Unnormalized input
- Runtime discovery
- Reflection-based execution
- Random driver selection
- Live map lookups as execution authority
- First-accept race conditions
- Undeclared failure execution
- Production readiness claims
- Global scale claims
- Optimization or probabilistic behavior claims
- External runtime guarantee claims
```

## Deterministic Failure Taxonomy

All failures must be explicit, declared, deterministic, and replay-verifiable.

Canonical failures:

```text
DRIVER_DROPOUT
DRIVER_REJECTION_CHAIN
TIMEOUT_EXCEEDED
```

Undeclared failure equals invalid execution.

## Required Continuity Scenarios

```text
1. Connectivity loss recovery
2. Replay reconstruction
3. Offline driver rejoin
4. Adversarial coordination
5. Multi-epoch recovery
```

Success requires:

```text
execution admissible
replay converges
identity preserved
coordination rebuilds
recovery deterministic
```

Hard fail if replay diverges, identity drifts, or recovery becomes nondeterministic.

## Observability Boundary

Allowed outputs:

```text
replay_hash
decision_hash
determinism_match
execution_trace
```

Observability cannot change execution, influence decisions, or redefine truth.

## Canonical Contract

```yaml
controlled_pilot_layer:
  schema: afriride.controlled_pilot_layer.v1
  status: controlled_pilot_design_contract
  classification: ga_elite_closed_world_continuity_proof_environment
  purpose: continuity_under_controlled_disruption
  production_readiness_claimed: false
  external_runtime_guarantees_claimed: false
  truth_authority: replay_only
  execution_environment: closed_world
  constitutional_pipeline_only: true
  required_pipeline:
    - adapter
    - normalization
    - ingestion
    - edge_guard
    - runtime_admission
    - runtime_orchestration
    - runtime_activation
    - guard_engine
    - core_engine_matching
    - worker_execution
    - event_log_storage
    - proof_generation
    - evaluation_engine
    - replay_verification
    - constitutional_receipt
    - registry_seal
  required_surfaces:
    afritech.edge.adapter.runtime_adapter: IMPLEMENTED
    afritech.edge.normalization.normalizer: IMPLEMENTED
    afritech.edge.ingestion.queue_ingestor: IMPLEMENTED
    afritech.guards.edge_input_guard: IMPLEMENTED
    afritech.api.app: IMPLEMENTED
    afritech.execution.partition.router: IMPLEMENTED
    afritech.execution.worker.worker_pool: IMPLEMENTED
    afritech.core.engine: IMPLEMENTED
    afritech.core.matching_engine: IMPLEMENTED
    afritech.storage.event_log: IMPLEMENTED
    afritech.storage.event_schema: IMPLEMENTED
    afritech.storage.replay_engine: IMPLEMENTED
    afritech.proof.constitutional_receipt: IMPLEMENTED
  deterministic_decisions:
    - ride_request_admission
    - driver_selection
    - retry_ordering
    - timeout_handling
    - state_transitions
  canonical_failures:
    - DRIVER_DROPOUT
    - DRIVER_REJECTION_CHAIN
    - TIMEOUT_EXCEEDED
  continuity_scenarios:
    - connectivity_loss_recovery
    - replay_reconstruction
    - offline_driver_rejoin
    - adversarial_coordination
    - multi_epoch_recovery
  validity_rule:
    - admissible
    - deterministic
    - invariant_preserving
    - replay_equivalent
    - identity_stable
    - trace_complete
  invariant_contracts:
    - proof_meaning
    - authority_boundaries
    - afriride_scope
    - claim_discipline
    - enforcement_integrity
  observability_outputs:
    - replay_hash
    - decision_hash
    - determinism_match
    - execution_trace
  forbidden:
    - direct_api_to_core_execution
    - unnormalized_input
    - runtime_discovery
    - reflection_based_execution
    - random_driver_selection
    - live_map_lookup_execution_authority
    - first_accept_race_condition
    - undeclared_failure_execution
    - production_readiness_claim
    - global_scale_claim
    - optimization_claim
    - external_runtime_guarantee_claim
```

## Final Definition

The AfriRide Controlled Pilot Layer is a closed-world, deterministic execution system where every ride decision, failure, recovery, and coordination event is replay-verifiable, proof-bound, and constitutionally governed, used exclusively to demonstrate continuity under controlled disruption.
