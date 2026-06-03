from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

import yaml


ALLOWED_STATES = {
    "PLANNED",
    "PARTIAL",
    "IMPLEMENTED",
    "FROZEN",
    "DOCUMENTARY",
    "FORBIDDEN_ALIAS",
}

ALLOWED_REPLAY_SIGNIFICANCE = {
    "NONE",
    "OPTIONAL",
    "REQUIRED",
    "CRITICAL",
    "FORBIDDEN",
}

REPLAY_REQUIRED_LEVELS = {
    "REQUIRED",
    "CRITICAL",
}

REQUIRED_FIELDS = {
    "implementation_state",
    "category",
    "ontology",
    "replay_significance",
    "semantic_properties",
    "forbidden_behaviors",
}

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE_DIR = ROOT / "afritech" / "architecture"

MAIN_REGISTRY = ARCHITECTURE_DIR / "implementation_registry.yaml"
SUB_MODULES = ARCHITECTURE_DIR / "sub_modules_registry.yaml"
SUB_ENFORCEMENT = ARCHITECTURE_DIR / "sub_enforcement_registry.yaml"


class ImplementationStateValidationError(Exception):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ImplementationStateValidationError(f"missing registry file: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ImplementationStateValidationError(
            f"registry file must contain a mapping: {path}"
        )

    return data


def _load_registry() -> dict[str, Any]:
    try:
        from afritech.architecture.registry_loader import (  # type: ignore
            load_implementation_registry,
        )

        registry = load_implementation_registry()
        if not isinstance(registry, dict):
            raise ImplementationStateValidationError(
                "registry_loader returned non-mapping registry"
            )
        return registry

    except ModuleNotFoundError:
        main = _load_yaml(MAIN_REGISTRY)

        if SUB_MODULES.exists():
            modules = _load_yaml(SUB_MODULES)
            main["implementations"] = modules.get(
                "implementations",
                main.get("implementations", {}),
            )

        if SUB_ENFORCEMENT.exists():
            enforcement = _load_yaml(SUB_ENFORCEMENT)
            for key, value in enforcement.items():
                if key not in {"metadata", "registry"}:
                    main[key] = value

        return main


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ImplementationStateValidationError(f"{label} must be a mapping")
    return value


def _require_sequence(value: Any, label: str) -> None:
    if not isinstance(value, list):
        raise ImplementationStateValidationError(f"{label} must be a list")


def _validate_metadata(registry: Mapping[str, Any]) -> None:
    metadata = _require_mapping(registry.get("metadata", {}), "metadata")
    authority = metadata.get("authority")

    if authority != "ARCHITECTURE":
        raise ImplementationStateValidationError(
            f"metadata.authority must be ARCHITECTURE, got {authority!r}"
        )


def _validate_implementations(registry: Mapping[str, Any]) -> int:
    implementations = _require_mapping(
        registry.get("implementations", {}),
        "implementations",
    )

    if not implementations:
        raise ImplementationStateValidationError("implementations must not be empty")

    for module_name in sorted(implementations):
        entry = implementations[module_name]

        if not isinstance(module_name, str) or not module_name.startswith("afritech."):
            raise ImplementationStateValidationError(
                f"invalid implementation module key: {module_name!r}"
            )

        entry_map = _require_mapping(entry, f"implementation entry {module_name}")

        missing = REQUIRED_FIELDS - set(entry_map.keys())
        if missing:
            raise ImplementationStateValidationError(
                f"{module_name} missing required fields: {sorted(missing)}"
            )

        state = entry_map.get("implementation_state")
        if state not in ALLOWED_STATES:
            raise ImplementationStateValidationError(
                f"{module_name} has invalid implementation_state: {state!r}"
            )

        replay_significance = entry_map.get("replay_significance")
        if replay_significance not in ALLOWED_REPLAY_SIGNIFICANCE:
            raise ImplementationStateValidationError(
                f"{module_name} has invalid replay_significance: "
                f"{replay_significance!r}"
            )

        semantic_properties = _require_mapping(
            entry_map.get("semantic_properties"),
            f"{module_name}.semantic_properties",
        )

        _require_sequence(
            entry_map.get("forbidden_behaviors"),
            f"{module_name}.forbidden_behaviors",
        )

        if state == "FORBIDDEN_ALIAS" and replay_significance != "FORBIDDEN":
            raise ImplementationStateValidationError(
                f"{module_name} is FORBIDDEN_ALIAS but replay_significance "
                f"is not FORBIDDEN"
            )

        if replay_significance in REPLAY_REQUIRED_LEVELS:
            if semantic_properties.get("replay_admissible") is not True:
                raise ImplementationStateValidationError(
                    f"{module_name} is replay {replay_significance} but "
                    f"semantic_properties.replay_admissible is not true"
                )

        if state in {"IMPLEMENTED", "FROZEN"}:
            if semantic_properties.get("deterministic_execution") is not True:
                raise ImplementationStateValidationError(
                    f"{module_name} is {state} but deterministic_execution is not true"
                )

        if replay_significance == "CRITICAL":
            if semantic_properties.get("proof_admissible") is not True:
                raise ImplementationStateValidationError(
                    f"{module_name} is replay CRITICAL but "
                    f"semantic_properties.proof_admissible is not true"
                )

    return len(implementations)


def validate() -> int:
    registry = _load_registry()

    _validate_metadata(registry)
    count = _validate_implementations(registry)

    print("✅ Implementation state validation PASSED")
    print(f"✅ Checked implementations: {count}")
    print("✅ Authority: ARCHITECTURE")
    print("✅ Replay significance levels validated")
    return 0


def main() -> int:
    try:
        return validate()
    except ImplementationStateValidationError as exc:
        print("❌ Implementation state validation FAILED")
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())