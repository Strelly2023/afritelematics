"""Validate declared non-runtime bindings for AfriTech Constitution v1.0."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.ci.afritech_constitution_v1_validator import validate as validate_v1


ROOT = Path(__file__).resolve().parents[2]

ADR = ROOT / "afritech/governance/adr/ADR-0019-afritech-constitution-v1-binding.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-019-constitution-v1-binding.yaml"
BINDING = ROOT / "afritech/governance/bindings/BIND-019-constitution-v1.yaml"
CONSTITUTION_MD = ROOT / "afritech/constitution/AFRITECH_CONSTITUTION_V1.md"
CONSTITUTION_YAML = ROOT / "afritech/constitution/AFRITECH_CONSTITUTION_V1.yaml"
CHECKPOINT = ROOT / "docs/proof/AFRITECH_CONSTITUTION_V1_CHECKPOINT.md"

REQUIRED_BINDING_IDS = {
    "BIND-019-1",
    "BIND-019-2",
    "BIND-019-3",
    "BIND-019-4",
}

REQUIRED_RULE_IDS = {
    "RULE-019-1",
    "RULE-019-2",
    "RULE-019-3",
    "RULE-019-4",
    "RULE-019-5",
}

CHECKPOINT_TERMS = (
    "1378 passed",
    "98 passed, 0 failed",
    "Constitutional closure achieved",
    "not yet runtime-bound",
)


class ConstitutionV1BindingValidationError(Exception):
    """Raised when Constitution v1.0 declared binding validation fails."""


def fail(message: str) -> None:
    raise ConstitutionV1BindingValidationError(message)


def _repo_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing YAML artifact: {_repo_path(path)}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"YAML artifact must be a mapping: {_repo_path(path)}")
    return payload


def require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        fail(f"required file missing: {_repo_path(path)}")
    if not path.read_text(encoding="utf-8").strip():
        fail(f"required file empty: {_repo_path(path)}")


def validate_adr() -> None:
    payload = load_yaml(ADR)
    adr = payload.get("adr")
    if not isinstance(adr, dict):
        fail("ADR-0019 must define adr mapping")
    if adr.get("id") != "ADR-0019":
        fail("ADR-0019 id mismatch")
    if adr.get("status") != "ACCEPTED":
        fail("ADR-0019 must be ACCEPTED")

    boundary = adr.get("constitutional_boundary")
    if not isinstance(boundary, dict):
        fail("ADR-0019 must define constitutional_boundary")
    if boundary.get("runtime_authoritative") is not False:
        fail("ADR-0019 must declare runtime_authoritative=false")
    if boundary.get("silent_runtime_promotion_forbidden") is not True:
        fail("ADR-0019 must forbid silent runtime promotion")

    if "INVARIANT-019" not in set(adr.get("linked_invariants", [])):
        fail("ADR-0019 must link INVARIANT-019")
    if "RULE-019" not in set(adr.get("required_rule", [])):
        fail("ADR-0019 must require RULE-019")
    if "BIND-019" not in set(adr.get("required_binding", [])):
        fail("ADR-0019 must require BIND-019")


def validate_rule() -> None:
    payload = load_yaml(RULE)
    if payload.get("id") != "RULE-019":
        fail("RULE-019 id mismatch")

    rules = payload.get("rules")
    if not isinstance(rules, list):
        fail("RULE-019 must define rules list")

    discovered = {rule.get("id") for rule in rules if isinstance(rule, dict)}
    missing = REQUIRED_RULE_IDS - discovered
    if missing:
        fail(f"RULE-019 missing rule IDs: {sorted(missing)}")

    if "INVARIANT-019" not in set(payload.get("linked_invariants", [])):
        fail("RULE-019 must link INVARIANT-019")
    if "ADR-0019" not in set(payload.get("linked_adr", [])):
        fail("RULE-019 must link ADR-0019")


def validate_binding() -> None:
    payload = load_yaml(BINDING)
    if payload.get("id") != "BIND-019":
        fail("BIND-019 id mismatch")

    bindings = payload.get("bindings")
    if not isinstance(bindings, list):
        fail("BIND-019 must define bindings list")

    discovered = {binding.get("id") for binding in bindings if isinstance(binding, dict)}
    missing = REQUIRED_BINDING_IDS - discovered
    if missing:
        fail(f"BIND-019 missing binding IDs: {sorted(missing)}")

    for binding in bindings:
        if not isinstance(binding, dict):
            fail("BIND-019 binding entries must be mappings")
        if binding.get("runtime_authoritative") is not False:
            fail(f"{binding.get('id')} must remain runtime_authoritative=false")
        if not binding.get("target"):
            fail(f"{binding.get('id')} missing target")
        if not binding.get("linked_rules"):
            fail(f"{binding.get('id')} missing linked_rules")

    if "RULE-019" not in set(payload.get("linked_rules", [])):
        fail("BIND-019 must link RULE-019")
    if "INVARIANT-019" not in set(payload.get("linked_invariants", [])):
        fail("BIND-019 must link INVARIANT-019")
    if "ADR-0019" not in set(payload.get("linked_adr", [])):
        fail("BIND-019 must link ADR-0019")


def validate_targets() -> None:
    for path in (CONSTITUTION_MD, CONSTITUTION_YAML, CHECKPOINT):
        require_file(path)

    importlib.import_module("afritech.ci.afritech_constitution_v1_validator")
    validate_v1()


def validate_checkpoint() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    missing = [term for term in CHECKPOINT_TERMS if term not in text]
    if missing:
        fail(f"checkpoint missing terms: {missing}")


def validate() -> None:
    validate_adr()
    validate_rule()
    validate_binding()
    validate_targets()
    validate_checkpoint()


def main() -> int:
    try:
        validate()
        print("AfriTech Constitution v1.0 binding validation PASSED")
        return 0
    except Exception as exc:
        print(f"AfriTech Constitution v1.0 binding validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
