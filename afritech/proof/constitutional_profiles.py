# afritech/proof/constitutional_profiles.py

"""
AfriTech Constitutional Profiles
================================

Composite constitutional law profiles.

This module defines COMPLETE, NON-PARTIAL constitutional
legality checks for each admissible system operation.

RULES:
- No subsystem may call atomic constraints directly
- All constitutional enforcement MUST route through a profile
- Profiles are fail-closed
- Profiles return no values
- Any violation raises ConstitutionalViolation immediately

This module is consumed exclusively by:
- afritech/kernel/constitutional_gateway.py
"""

from __future__ import annotations

from typing import Iterable

from afritech.guards.engine import ConstitutionalViolation
from afritech.kernel.constitutional_context import ConstitutionalContext
from afritech.state.state import State
from afritech.trace.trace_engine import TraceEngine

from afritech.proof.executable_constraints import (
    assert_registry_is_authoritative,
    assert_registry_hash_match,
    assert_execution_surface_sealed,
    assert_mutation_is_constitutional,
    assert_deterministic_execution,
    assert_replay_identity,
    assert_authority_declared,
    assert_no_authority_escalation,
    assert_closed_world_execution,
    assert_proof_present,
    assert_consensus_determinism,
    assert_node_trusted,
    assert_identity_integrity,
    assert_epoch_monotonic,
    assert_epoch_parent,
    assert_adr_required,
    assert_non_executable_isolation,
    assert_trace_present,
    assert_trace_root_binding,
    assert_state_lineage,
    assert_state_epoch_consistency,
    assert_guards_exhaustive,
)


# =====================================================================
# RUNTIME ADMISSION PROFILE
# =====================================================================

def assert_runtime_admission_legality(
    ctx: ConstitutionalContext,
    *,
    registry_epoch: int,
    runtime_epoch: int,
    registry_hash: str,
    execution_surface_hash: str,
    authority_effective: str,
) -> None:
    """
    Constitutional law for runtime admission.

    Enforces:
    - registry supremacy
    - authority declaration
    - authority non-escalation
    - epoch alignment
    - execution surface sealing
    """

    assert_authority_declared(ctx.authority_id)
    assert_no_authority_escalation(
        ctx.authority_id,
        authority_effective,
    )

    assert_registry_is_authoritative(
        registry_epoch,
        runtime_epoch,
    )

    assert_registry_hash_match(
        ctx.registry_hash,
        registry_hash,
    )

    assert_execution_surface_sealed(
        ctx.execution_surface_hash,
        execution_surface_hash,
    )


# =====================================================================
# EXECUTION / STATE TRANSITION PROFILE
# =====================================================================

def assert_execution_legality(
    ctx: ConstitutionalContext,
    *,
    parent_state: State,
    child_state: State,
    trace: TraceEngine,
    accessed_surfaces: Iterable[str],
    allowed_surfaces: Iterable[str],
    evaluated_guards: Iterable[str],
    required_guards: Iterable[str],
    proof_snapshot: object | None,
    runtime_certificate: object | None,
) -> None:
    """
    Constitutional law for execution and state transition.

    Enforces:
    - closed-world execution
    - guard completeness
    - proof requirement
    - state lineage
    - epoch consistency
    - trace presence
    """

    assert_closed_world_execution(
        accessed_surfaces,
        allowed_surfaces,
    )

    assert_guards_exhaustive(
        evaluated_guards,
        required_guards,
    )

    assert_proof_present(
        proof_snapshot,
        runtime_certificate,
    )

    assert_state_lineage(
        parent_state,
        child_state,
    )

    assert_state_epoch_consistency(
        parent_state,
        child_state,
    )

    assert_trace_present(trace)


# =====================================================================
# REGISTRY RESEAL PROFILE
# =====================================================================

def assert_registry_reseal_legality(
    ctx: ConstitutionalContext,
    *,
    previous_epoch_snapshot: dict,
    current_epoch_snapshot: dict,
    adr_ids: Iterable[str],
    registry_resealed: bool,
) -> None:
    """
    Constitutional law for registry reseal.

    Enforces:
    - ADR requirement
    - epoch monotonicity
    - epoch parent linkage
    - reseal completion
    """

    assert_adr_required(adr_ids)

    assert_epoch_monotonic(
        previous_epoch_snapshot,
        current_epoch_snapshot,
    )

    assert_epoch_parent(
        previous_epoch_snapshot,
        current_epoch_snapshot,
    )

    if not registry_resealed:
        raise ConstitutionalViolation(
            "REGISTRY_RESEAL_REQUIRED"
        )


# =====================================================================
# REPLAY VERIFICATION PROFILE
# =====================================================================

def assert_replay_legitimacy(
    ctx: ConstitutionalContext,
    *,
    original_hash: str,
    replay_hash: str,
    trace: TraceEngine,
    expected_trace_root: str,
    consensus_node_hashes: Iterable[str] | None = None,
) -> None:
    """
    Constitutional law for replay verification.

    Enforces:
    - replay identity
    - trace root binding
    - consensus determinism (if distributed)
    """

    assert_replay_identity(
        original_hash,
        replay_hash,
    )

    assert_trace_root_binding(
        trace,
        expected_trace_root,
    )

    if consensus_node_hashes is not None:
        assert_consensus_determinism(
            consensus_node_hashes,
        )