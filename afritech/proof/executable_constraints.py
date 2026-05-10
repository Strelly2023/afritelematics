# afritech/proof/executable_constraints.py

"""
AfriTech Executable Constitutional Constraints
==============================================

THIS FILE IS LAW.

Rule:
If a constitutional invariant is not enforced here (or transitively),
it is NOT law — it is documentation.

Properties:
- No logging
- No warnings
- No soft checks
- No return values
- Violations raise ConstitutionalViolation immediately

NOTE:
Atomic constraints in this file MUST NOT be invoked directly
by runtime, replay, or reseal logic.
They are composed exclusively by constitutional profiles.
"""

from __future__ import annotations

from typing import Iterable

from afritech.guards.engine import ConstitutionalViolation
from afritech.state.state import State
from afritech.trace.trace_engine import TraceEngine
from afritech.trace.trace_hash import compute_trace_root


# =====================================================================
# I1 — SINGLE SOURCE OF TRUTH (REGISTRY)
# =====================================================================

def assert_registry_is_authoritative(
    registry_epoch: int,
    runtime_epoch: int,
) -> None:
    if registry_epoch != runtime_epoch:
        raise ConstitutionalViolation(
            "I1_REGISTRY_AUTHORITY_VIOLATION"
        )


def assert_registry_hash_match(
    expected_hash: str,
    actual_hash: str,
) -> None:
    if expected_hash != actual_hash:
        raise ConstitutionalViolation(
            "I1_REGISTRY_HASH_MISMATCH"
        )


# =====================================================================
# I2 — SEALED EXECUTION SURFACE
# =====================================================================

def assert_execution_surface_sealed(
    expected_surface_hash: str,
    actual_surface_hash: str,
) -> None:
    if expected_surface_hash != actual_surface_hash:
        raise ConstitutionalViolation(
            "I2_SEALED_SURFACE_VIOLATION"
        )


# =====================================================================
# I3 — NO SILENT MUTATION
# =====================================================================

def assert_mutation_is_constitutional(
    *,
    adr_present: bool,
    epoch_advanced: bool,
    registry_resealed: bool,
) -> None:
    if not (adr_present and epoch_advanced and registry_resealed):
        raise ConstitutionalViolation(
            "I3_SILENT_MUTATION_FORBIDDEN"
        )


# =====================================================================
# I4 — DETERMINISTIC EXECUTION
# =====================================================================

def assert_deterministic_execution(
    output_hash: str,
    replayed_output_hash: str,
) -> None:
    if output_hash != replayed_output_hash:
        raise ConstitutionalViolation(
            "I4_NON_DETERMINISTIC_EXECUTION"
        )


# =====================================================================
# I5 — REPLAY REQUIRED
# =====================================================================

def assert_replay_identity(
    original_hash: str,
    replay_hash: str,
) -> None:
    if original_hash != replay_hash:
        raise ConstitutionalViolation(
            "I5_REPLAY_IDENTITY_VIOLATION"
        )


# =====================================================================
# I6 + I7 — AUTHORITY FIRST / NO ESCALATION
# =====================================================================

def assert_authority_declared(authority_id: str | None) -> None:
    if not isinstance(authority_id, str) or not authority_id:
        raise ConstitutionalViolation(
            "I6_AUTHORITY_NOT_DECLARED"
        )


def assert_no_authority_escalation(
    declared_authority: str,
    effective_authority: str,
) -> None:
    if declared_authority != effective_authority:
        raise ConstitutionalViolation(
            "I7_AUTHORITY_ESCALATION_DETECTED"
        )


# =====================================================================
# I8 — CLOSED EXECUTION WORLD
# =====================================================================

def assert_closed_world_execution(
    accessed_surfaces: Iterable[str],
    allowed_surfaces: Iterable[str],
) -> None:
    illegal = set(accessed_surfaces) - set(allowed_surfaces)
    if illegal:
        raise ConstitutionalViolation(
            f"I8_UNDECLARED_SURFACE_ACCESS: {sorted(illegal)}"
        )


# =====================================================================
# I9 — PROOF REQUIRED
# =====================================================================

def assert_proof_present(
    proof_snapshot: object | None,
    runtime_certificate: object | None,
) -> None:
    if proof_snapshot is None or runtime_certificate is None:
        raise ConstitutionalViolation(
            "I9_PROOF_REQUIRED"
        )


# =====================================================================
# I10 — CONSENSUS DETERMINISM (DISTRIBUTED)
# =====================================================================

def assert_consensus_determinism(
    node_hashes: Iterable[str],
) -> None:
    hashes = list(node_hashes)
    if not hashes or len(set(hashes)) != 1:
        raise ConstitutionalViolation(
            "I10_CONSENSUS_HASH_DIVERGENCE"
        )


# =====================================================================
# I11 + I12 — NODE TRUST / IDENTITY
# =====================================================================

def assert_node_trusted(
    node_registered: bool,
) -> None:
    if not node_registered:
        raise ConstitutionalViolation(
            "I11_UNTRUSTED_NODE"
        )


def assert_identity_integrity(
    expected_identity_hash: str,
    actual_identity_hash: str,
) -> None:
    if expected_identity_hash != actual_identity_hash:
        raise ConstitutionalViolation(
            "I12_IDENTITY_INTEGRITY_VIOLATION"
        )


# =====================================================================
# I13 — EPOCH MONOTONICITY (REGISTRY / HISTORY DATA LAW)
# =====================================================================

def assert_epoch_monotonic(
    previous_epoch: dict,
    current_epoch: dict,
) -> None:
    if current_epoch["epoch"]["number"] <= previous_epoch["epoch"]["number"]:
        raise ConstitutionalViolation(
            "I13_EPOCH_MONOTONICITY_VIOLATION"
        )


def assert_epoch_parent(
    previous_epoch: dict,
    current_epoch: dict,
) -> None:
    if current_epoch["epoch"]["parent"] != previous_epoch["epoch"]["number"]:
        raise ConstitutionalViolation(
            "I13_EPOCH_PARENT_MISMATCH"
        )


# =====================================================================
# I14 — ADR REQUIRED
# =====================================================================

def assert_adr_required(adr_ids: Iterable[str]) -> None:
    if not list(adr_ids):
        raise ConstitutionalViolation(
            "I14_ADR_REQUIRED"
        )


# =====================================================================
# I15 — NON‑EXECUTABLE SURFACE ISOLATION
# =====================================================================

def assert_non_executable_isolation(
    executed_files: Iterable[str],
    non_executable_surfaces: Iterable[str],
) -> None:
    illegal = set(executed_files) & set(non_executable_surfaces)
    if illegal:
        raise ConstitutionalViolation(
            f"I15_NON_EXECUTABLE_SURFACE_EXECUTED: {sorted(illegal)}"
        )


# =====================================================================
# TRACE LAW (MANDATORY)
# =====================================================================

def assert_trace_present(trace: TraceEngine | None) -> None:
    if trace is None:
        raise ConstitutionalViolation(
            "TRACE_REQUIRED_BUT_MISSING"
        )


def assert_trace_root_binding(
    trace: TraceEngine,
    expected_root: str,
) -> None:
    actual_root = compute_trace_root(
        trace.to_dict()["events"]
    )
    if actual_root != expected_root:
        raise ConstitutionalViolation(
            "TRACE_ROOT_MISMATCH"
        )


# =====================================================================
# STATE LINEAGE LAW
# =====================================================================

def assert_state_lineage(
    parent: State,
    child: State,
) -> None:
    if child.provenance.parent_hash != parent.attestation.state_hash:
        raise ConstitutionalViolation(
            "STATE_LINEAGE_VIOLATION"
        )


def assert_state_epoch_consistency(
    parent: State,
    child: State,
) -> None:
    if child.epoch < parent.epoch:
        raise ConstitutionalViolation(
            "STATE_EPOCH_REGRESSION"
        )


# =====================================================================
# GUARD COVERAGE LAW
# =====================================================================

def assert_guards_exhaustive(
    evaluated_guards: Iterable[str],
    required_guards: Iterable[str],
) -> None:
    missing = set(required_guards) - set(evaluated_guards)
    if missing:
        raise ConstitutionalViolation(
            f"GUARD_COVERAGE_VIOLATION: {sorted(missing)}"
        )