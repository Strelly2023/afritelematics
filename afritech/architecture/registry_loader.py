"""Canonical loader for the split AfriTech implementation registry."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE_DIR = ROOT / "afritech" / "architecture"
MAIN_REGISTRY = ARCHITECTURE_DIR / "implementation_registry.yaml"
SUB_MODULES = ARCHITECTURE_DIR / "sub_modules_registry.yaml"
SUB_ENFORCEMENT = ARCHITECTURE_DIR / "sub_enforcement_registry.yaml"


class RegistryLoadError(Exception):
    """Raised when the canonical implementation registry cannot be composed."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RegistryLoadError(f"missing registry file: {path.relative_to(ROOT)}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RegistryLoadError(
            f"registry file must be a mapping: {path.relative_to(ROOT)}"
        )
    return payload


def load_implementation_registry() -> dict[str, Any]:
    """Return the deterministic aggregate registry used by validators."""

    registry = deepcopy(_load_yaml(MAIN_REGISTRY))
    modules = _load_yaml(SUB_MODULES)
    enforcement = _load_yaml(SUB_ENFORCEMENT)

    registry["implementation_states"] = deepcopy(
        modules.get("implementation_states", {})
    )
    registry["implementations"] = deepcopy(modules.get("implementations", {}))

    for key, value in enforcement.items():
        if key not in {"metadata", "schema", "version"}:
            registry[key] = deepcopy(value)

    return registry
