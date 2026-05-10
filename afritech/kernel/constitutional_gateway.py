# afritech/kernel/constitutional_gateway.py

"""
AfriTech Constitutional Gateway
===============================

SINGLE, UNAVOIDABLE constitutional entrypoint for all
legally admissible execution.

If any of the following occur outside this module:
- runtime admission
- state mutation
- epoch advancement
- registry reseal
- replay validation
- receipt emission

the system is constitutionally INVALID.

This module is:
- stateless
- functional
- explicit
- non-caching
- fail-closed

Law is enforced here by TOPOLOGY, not convention.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from afritech.kernel.constitutional_context import ConstitutionalContext

from afritech.constitution.compiled.invariants_index import (
    I1_REGISTRY_AUTHORITY,
    I2_SEALED_EXECUTION_SURFACE,
    I6_AUTHORITY_DECLARED,
    I7_NO_AUTHORITY_ESCALATION,
    I8_CLOSED_WORLD,
    I9_PROOF_REQUIRED,
    I5_REPLAY_REQUIRED,
)

from afritech.proof.constitutional_profiles import (
    assert_runtime_admission_legality,
    assert_execution_legality,
    assert_registry_reseal_legality,
    assert_replay_legitimacy,
)

from afritech.proof.constitutional_receipt import ConstitutionalReceipt

from afritech.internal.state_mutation.validate_state_mutation import (
    validate_state_mutation,
)
from afritech.internal.state_mutation.apply_state_transition import (
    apply_state_transition,
)

from afritech.internal.epoch_mutation.advance_epoch import advance_epoch
from afritech.internal.epoch_mutation.reseal_epoch import reseal_epoch

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import SemanticEpoch

from afritech.trace.canonicalization import (
    canonicalize_trace,
    hash_canonical_trace,
)

from afritech.state.state import State
from afritech.trace.trace_engine import TraceEngine


# =====================================================================
# CANONICAL EXECUTION ORDER ANCHOR (STATIC, NON-EXECUTED)
# =====================================================================

def _constitutional_execution_sequence_anchor() -> None:
    """
    STATIC ANCHOR — DO NOT EXECUTE.

    This function exists solely to make the constitutional
    execution order explicit and statically provable.

    It is never called at runtime.
    """

    if False:  # pragma: no cover
        ctx = None
        parent_state = None
        mutation_payload = None
        trace = None

        assert_runtime_admission_legality(ctx)
        validate_state_mutation(parent_state, mutation_payload)
        apply_state_transition(parent_state, mutation_payload)
        assert_execution_legality(ctx)
        canonicalize_trace(trace)
        hash_canonical_trace(trace)
        ConstitutionalReceipt.from_context(ctx, invariants_executed=())


# =====================================================================
# RUNTIME ADMISSION
# =====================================================================

def admit_runtime(
    ctx: ConstitutionalContext,
    *,
    registry_epoch: int,
    runtime_epoch: int,
    registry_hash: str,
    execution_surface_hash: str,
    authority_effective: str,
) -> ConstitutionalReceipt:
    """
    Admit a runtime under constitutional law.

    Runtime existence is not implicit.
    It is granted ONLY by this function.
    """

    assert_runtime_admission_legality(
        ctx,
        registry_epoch=registry_epoch,
        runtime_epoch=runtime_epoch,
        registry_hash=registry_hash,
        execution_surface_hash=execution_surface_hash,
        authority_effective=authority_effective,
    )

    return ConstitutionalReceipt.from_context(
        ctx,
        invariants_executed=(
            I1_REGISTRY_AUTHORITY,
            I2_SEALED_EXECUTION_SURFACE,
            I6_AUTHORITY_DECLARED,
            I7_NO_AUTHORITY_ESCALATION,
        ),
    )


# =====================================================================
# STATE TRANSITION (VALIDATE → MUTATE → PROVE → RECEIPT)
# =====================================================================

def transition_state(
    ctx: ConstitutionalContext,
    *,
    parent_state: State,
    mutation_payload: dict,
    trace: TraceEngine,
    accessed_surfaces: Iterable[str],
    allowed_surfaces: Iterable[str],
    evaluated_guards: Iterable[str],
    required_guards: Iterable[str],
    proof_snapshot: object,
    runtime_certificate: object,
) -> Tuple[State, ConstitutionalReceipt]:
    """
    Perform a constitutionally valid state transition.

    This is the ONLY lawful state mutation path.
    """

    validate_state_mutation(
        parent_state=parent_state,
        mutation_payload=mutation_payload,
    )

    child_state = apply_state_transition(
        parent_state,
        mutation_payload=mutation_payload,
    )

    assert_execution_legality(
        ctx,
        parent_state=parent_state,
        child_state=child_state,
        trace=trace,
        accessed_surfaces=accessed_surfaces,
        allowed_surfaces=allowed_surfaces,
        evaluated_guards=evaluated_guards,
        required_guards=required_guards,
        proof_snapshot=proof_snapshot,
        runtime_certificate=runtime_certificate,
    )

    canonical_events = canonicalize_trace(trace)
    trace_root = hash_canonical_trace(canonical_events)

    ctx_with_trace = ConstitutionalContext(
        authority_id=ctx.authority_id,
        epoch=ctx.epoch,
        registry_hash=ctx.registry_hash,
        execution_surface_hash=ctx.execution_surface_hash,
        trace_root=trace_root,
    )

    receipt = ConstitutionalReceipt.from_context(
        ctx_with_trace,
        invariants_executed=(
            I8_CLOSED_WORLD,
            I9_PROOF_REQUIRED,
        ),
    )

    return child_state, receipt


# =====================================================================
# EPOCH ADVANCEMENT + REGISTRY RESEAL
# =====================================================================

def advance_and_reseal_epoch(
    ctx: ConstitutionalContext,
    *,
    current_epoch: EpochSnapshot,
    next_semantic_epoch: SemanticEpoch,
    new_epoch_hash: str,
    reseal_hash: str,
    previous_epoch_snapshot: EpochSnapshot,
    adr_ids: Iterable[str],
    registry_resealed: bool,
) -> Tuple[EpochSnapshot, ConstitutionalReceipt]:
    """
    Perform a constitutionally valid epoch advance and registry reseal.
    """

    assert_registry_reseal_legality(
        ctx,
        previous_epoch_snapshot=previous_epoch_snapshot,
        current_epoch_snapshot=current_epoch,
        adr_ids=adr_ids,
        registry_resealed=registry_resealed,
    )

    advanced_epoch = advance_epoch(
        current_epoch.semantic_epoch,
        new_epoch_hash=new_epoch_hash,
    )

    resealed_semantic_epoch = reseal_epoch(
        advanced_epoch,
        reseal_hash=reseal_hash,
    )

    resealed_snapshot = EpochSnapshot(
        semantic_epoch=resealed_semantic_epoch,
        epoch_hash=reseal_hash,
    )

    receipt = ConstitutionalReceipt.from_context(
        ctx,
        invariants_executed=(
            I5_REPLAY_REQUIRED,
        ),
    )

    return resealed_snapshot, receipt


# =====================================================================
# REPLAY VALIDATION
# =====================================================================

def validate_replay(
    ctx: ConstitutionalContext,
    *,
    original_hash: str,
    replay_hash: str,
    trace: TraceEngine,
    consensus_node_hashes: Iterable[str] | None = None,
) -> ConstitutionalReceipt:
    """
    Validate replay under constitutional law.
    """

    canonical_events = canonicalize_trace(trace)
    expected_trace_root = hash_canonical_trace(canonical_events)

    assert_replay_legitimacy(
        ctx,
        original_hash=original_hash,
        replay_hash=replay_hash,
        trace=trace,
        expected_trace_root=expected_trace_root,
        consensus_node_hashes=consensus_node_hashes,
    )

    ctx_with_trace = ConstitutionalContext(
        authority_id=ctx.authority_id,
        epoch=ctx.epoch,
        registry_hash=ctx.registry_hash,
        execution_surface_hash=ctx.execution_surface_hash,
        trace_root=expected_trace_root,
    )

    return ConstitutionalReceipt.from_context(
        ctx_with_trace,
        invariants_executed=(
            I5_REPLAY_REQUIRED,
        ),
    )
