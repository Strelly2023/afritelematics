"""Shared validation helpers for AfriProgramming governed tooling surfaces."""

from __future__ import annotations

import ast
import inspect
from collections.abc import Callable
from types import ModuleType

from afritech.afriprogramming import tooling_manifest, tooling_surfaces
from afritech.afriprogramming.tooling_manifest import (
    FORBIDDEN_SURFACE_ACTIONS,
    SURFACES,
    assert_tooling_boundaries,
    get_surface,
)


VALIDATED_MODULES: tuple[ModuleType, ...] = (tooling_manifest, tooling_surfaces)

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.governance",
    "afritech.proof.constitutional_receipt",
    "afritech.ci.constitutional_validation",
    "openai",
    "requests",
    "subprocess",
)

FORBIDDEN_CALL_NAMES = (
    "open",
    "write",
    "writelines",
    "unlink",
    "remove",
    "rename",
    "replace",
    "rmdir",
    "mkdir",
    "makedirs",
    "exec",
    "eval",
    "run",
    "Popen",
    "system",
)


class AfriProgrammingToolingSurfaceError(RuntimeError):
    """Raised when AfriProgramming tooling surfaces violate authority rules."""


def fail(message: str) -> None:
    raise AfriProgrammingToolingSurfaceError(message)


def validate_common_tooling_boundaries() -> None:
    assert_tooling_boundaries()

    classification = tooling_manifest.build_upgrade_classification()
    expected = {
        "afriprogramming_upgrade": "VALID_AS_TOOLING",
        "ai_authority": "NON_AUTHORITATIVE",
        "replay_authority": "PRESERVED",
        "governance_authority": "PRESERVED",
        "runtime_mutation_authority": "DENIED",
        "operational_claim": "NOT_EXPANDED",
        "violation_status": "NO_VIOLATION_IF_VALIDATORS_PASS",
    }
    for key, value in expected.items():
        if classification.get(key) != value:
            fail(f"upgrade classification mismatch for {key}")

    if set(classification["forbidden_surface_actions"]) != set(
        FORBIDDEN_SURFACE_ACTIONS
    ):
        fail("forbidden surface actions mismatch")


def validate_surface(surface_id: str, validator_name: str) -> None:
    validate_common_tooling_boundaries()
    surface = get_surface(surface_id)
    payload = surface.canonical_dict()

    if payload["required_validator"] != validator_name:
        fail(f"{surface_id} required validator mismatch")
    if payload["authority"] != "non_authoritative":
        fail(f"{surface_id} must be non-authoritative")
    if payload["requires_validator_gate"] is not True:
        fail(f"{surface_id} must require validators")
    if payload["requires_replay_gate"] is not True:
        fail(f"{surface_id} must require replay")

    forbidden_true_flags = (
        "may_define_truth",
        "may_bypass_validators",
        "may_mutate_protected_runtime_state",
        "may_emit_proof",
        "may_emit_witness",
        "may_attest_constitutionally",
        "expands_operational_claims",
    )
    for key in forbidden_true_flags:
        if payload[key] is not False:
            fail(f"{surface_id} boundary flag must remain false: {key}")


def validate_surface_registry_complete() -> None:
    expected_ids = {
        "afriprogramming_cli",
        "ai_constraint_engine",
        "multi_agent_orchestrator",
        "llm_connector",
        "vscode_extension",
        "replay_graph_viewer",
        "timeline_playback_viewer",
    }
    discovered = {surface.surface_id for surface in SURFACES}
    if discovered != expected_ids:
        fail("AfriProgramming tooling surface registry mismatch")


def validate_no_forbidden_imports_or_calls() -> None:
    for module in VALIDATED_MODULES:
        tree = ast.parse(inspect.getsource(module))
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        fail(f"{module.__name__} has forbidden import {alias.name}")
            if isinstance(item, ast.ImportFrom):
                module_name = item.module or ""
                if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    fail(f"{module.__name__} has forbidden import {module_name}")
            if isinstance(item, ast.Call):
                call_name = ""
                if isinstance(item.func, ast.Name):
                    call_name = item.func.id
                elif isinstance(item.func, ast.Attribute):
                    call_name = item.func.attr
                if call_name in FORBIDDEN_CALL_NAMES:
                    fail(f"{module.__name__} has forbidden call {call_name}")


def validate_tooling_behavior(
    surface_id: str,
    validator_name: str,
    behavior_check: Callable[[], None],
) -> None:
    validate_surface_registry_complete()
    validate_surface(surface_id, validator_name)
    validate_no_forbidden_imports_or_calls()
    behavior_check()


__all__ = [
    "AfriProgrammingToolingSurfaceError",
    "fail",
    "validate_common_tooling_boundaries",
    "validate_no_forbidden_imports_or_calls",
    "validate_surface",
    "validate_surface_registry_complete",
    "validate_tooling_behavior",
]
