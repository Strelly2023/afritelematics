"""Fail-closed validation for governed NovaTech product bindings."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util
from typing import Any

import yaml

NOVAID_BINDING = ROOT / "afritech/governance/bindings/BIND-NOVAID-PRODUCT.yaml"


class ProductBindingViolation(RuntimeError):
    """Raised when a product binding is incomplete or cannot resolve."""


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProductBindingViolation(f"{path}: binding must be an object")
    return payload


def _module_resolves(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False


def validate_novaid_binding(path: Path = NOVAID_BINDING) -> bool:
    payload = _load(path)
    if payload.get("schema") != "novatech.product_binding.v1":
        raise ProductBindingViolation("NovaID binding schema mismatch")
    if payload.get("status") != "active" or payload.get("product") != "NovaID":
        raise ProductBindingViolation("NovaID binding is not active")

    authority = payload.get("authority", {})
    required = {
        "identity",
        "authentication",
        "verification",
        "authorization_claims",
        "device_trust",
        "session_risk",
    }
    if required - set(authority.get("capabilities", [])):
        raise ProductBindingViolation("NovaID authority capabilities are incomplete")
    forbidden = {"payment_execution", "ride_dispatch"}
    if forbidden - set(authority.get("forbidden_capabilities", [])):
        raise ProductBindingViolation("NovaID forbidden authority is incomplete")

    runtime = payload.get("runtime", {})
    modules = [
        runtime.get("canonical_package"),
        runtime.get("composition_root"),
        *runtime.get("api_surfaces", []),
        *runtime.get("persistence", []),
    ]
    unresolved = [name for name in modules if not isinstance(name, str) or not _module_resolves(name)]
    if unresolved:
        raise ProductBindingViolation(f"unresolved NovaID modules: {unresolved}")

    contracts = payload.get("contracts", {})
    missing = [
        relative
        for relative in contracts.values()
        if not isinstance(relative, str) or not (ROOT / relative).is_file()
    ]
    if missing:
        raise ProductBindingViolation(f"missing NovaID contracts: {missing}")

    tests = payload.get("enforcement", {}).get("tests", [])
    missing_tests = [relative for relative in tests if not (ROOT / relative).is_file()]
    if missing_tests:
        raise ProductBindingViolation(f"missing NovaID enforcement tests: {missing_tests}")
    if payload.get("failure_policy") != "HARD_FAILURE":
        raise ProductBindingViolation("NovaID binding must fail closed")
    return True


def main() -> int:
    try:
        validate_novaid_binding()
    except Exception as exc:
        print(f"NovaTech product binding validation FAILED: {exc}")
        return 1
    print("NovaTech product binding validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
