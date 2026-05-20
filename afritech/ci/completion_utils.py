"""Shared completion checks for AfriTech L1.5 validators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]

ARCHITECTURE_REGISTRIES = [
    ROOT / "afritech/architecture/implementation_registry.yaml",
    ROOT / "afritech/architecture/surface_implementation_binding.yaml",
    ROOT / "afritech/architecture/enforcement_matrix.yaml",
    ROOT / "afritech/architecture/surface_authority_registry.yaml",
]

STRUCTURAL_YAML = [
    *ARCHITECTURE_REGISTRIES,
    ROOT / "afritech/architecture/implementation_states.yaml",
    ROOT / "afritech/architecture/planned_surface_policy.yaml",
    ROOT / "afritech/epoch/epoch_registry.yaml",
    ROOT / "afritech/governance/binding_manifest.yaml",
    ROOT / "afritech/constitution/canonical/INDEX.yaml",
    ROOT / "afritech/proofs/audit/execution_trace.yaml",
    ROOT / "afritech/proofs/audit/proof_chain.yaml",
    ROOT / "afritech/proofs/audit/semantic_lineage.yaml",
    ROOT / "afritech/semantic_engine/satisfiability/pipeline.yaml",
    ROOT / "afritech/ci/completeness_policy.yaml",
    ROOT / "docs/roadmap/FUTURE_SURFACE_STATUS.yaml",
]

ACTIVE_SURFACE_SECTIONS = {
    "implementations",
    "bindings",
    "enforcement",
    "surfaces",
}

UNRESOLVED_STATES = {
    "PLANNED",
    "PARTIAL",
    "DOCUMENTARY",
}

RESOLVED_STATES = {
    "IMPLEMENTED",
    "FROZEN",
}

REQUIRED_WITNESSES = {
    "execution_chain_hash",
    "deterministic_execution_chain",
    "transcript_hash",
    "mutation_trace_hash",
    "replay_hash",
    "receipt_hash",
}


class CompletionError(Exception):
    """Raised when L1.5 completion validation fails."""


def fail(message: str) -> None:
    raise CompletionError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing artifact: {path.relative_to(ROOT)}")
    if path.stat().st_size == 0:
        fail(f"empty artifact: {path.relative_to(ROOT)}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"artifact must be a mapping: {path.relative_to(ROOT)}")
    return payload


def as_bool_true(value: Any) -> bool:
    return value is True


def active_entries() -> list[tuple[Path, str, dict[str, Any]]]:
    entries: list[tuple[Path, str, dict[str, Any]]] = []

    for path in ARCHITECTURE_REGISTRIES:
        payload = load_yaml(path)
        for section_name in ACTIVE_SURFACE_SECTIONS:
            section = payload.get(section_name)
            if isinstance(section, dict):
                for key, value in section.items():
                    if isinstance(value, dict):
                        entries.append((path, str(key), value))

    surface_status_path = ROOT / "docs/roadmap/FUTURE_SURFACE_STATUS.yaml"
    surface_status = load_yaml(surface_status_path)
    entries.append(
        (
            surface_status_path,
            str(surface_status.get("surface", "unknown_surface")),
            {
                "implementation_state": surface_status.get("status"),
                "runtime_admissible": surface_status.get("runtime_active"),
                "replay_participating": surface_status.get("replay_participating"),
                "proof_admissible": surface_status.get("proof_admissible"),
                "freeze_reason": surface_status.get("freeze_reason"),
            },
        )
    )

    return entries


def entry_state(entry: dict[str, Any]) -> str:
    state = entry.get("implementation_state", entry.get("status"))
    if isinstance(state, list) and len(state) == 1:
        state = state[0]
    if not isinstance(state, str):
        fail(f"surface entry missing implementation_state/status: {entry}")
    return state


def require_non_empty_list(entry: dict[str, Any], key: str, context: str) -> None:
    value = entry.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{context} must define non-empty list: {key}")


def require_no_empty_structural_artifacts() -> None:
    for path in STRUCTURAL_YAML:
        load_yaml(path)


def validate_entry_state_resolution() -> None:
    for path, name, entry in active_entries():
        state = entry_state(entry)
        context = f"{path.relative_to(ROOT)}::{name}"
        if state in UNRESOLVED_STATES:
            fail(f"{context} remains unresolved: {state}")
        if state not in RESOLVED_STATES:
            fail(f"{context} has unknown resolution state: {state}")
        if state == "FROZEN":
            if entry.get("runtime_admissible") is True:
                fail(f"{context} is frozen but runtime_admissible=true")
            if entry.get("replay_participating") is True:
                fail(f"{context} is frozen but replay_participating=true")
            if entry.get("proof_admissible") is True:
                fail(f"{context} is frozen but proof_admissible=true")
            if not entry.get("freeze_reason") and not entry.get("description"):
                fail(f"{context} is frozen without freeze_reason/description")


def validate_implemented_entry(entry: dict[str, Any], context: str) -> None:
    if entry_state(entry) != "IMPLEMENTED":
        return

    for key in (
        "canonical_identity",
        "ontology",
        "category",
        "replay_significance",
    ):
        if key in entry and not entry[key]:
            fail(f"{context} has empty {key}")

    if entry.get("missing_capabilities"):
        fail(f"{context} still declares missing_capabilities")
    if entry.get("missing_witnesses"):
        fail(f"{context} still declares missing_witnesses")

    if "deterministic_required" in entry and entry["deterministic_required"] is not True:
        fail(f"{context} is implemented without deterministic_required=true")
    if "replay_safe_required" in entry and entry["replay_safe_required"] is not True:
        fail(f"{context} is implemented without replay_safe_required=true")
    if "closed_world_required" in entry and entry["closed_world_required"] is not True:
        fail(f"{context} is implemented without closed_world_required=true")


def main_result(name: str, validator) -> int:
    try:
        validator()
        print(f"✅ {name} PASSED")
        return 0
    except CompletionError as exc:
        print(f"❌ {name} failed: {exc}")
        return 1
