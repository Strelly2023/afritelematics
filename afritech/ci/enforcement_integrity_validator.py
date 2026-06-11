"""Validate that invariant enforcement remains non-bypassable."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "afritech/constitution/FIVE_INVARIANT_CONTRACT.yaml"
FOUR_GATE = ROOT / "afritech/ci/four_gate_validator.py"
FOUR_GATE_TEST = ROOT / "afritech/tests/governance/test_four_gate_validator.py"
CONSTITUTIONAL_VALIDATION = ROOT / "afritech/ci/constitutional_validation.py"
CONSTITUTIONAL_PIPELINE = ROOT / "afritech/ci/constitutional_pipeline.py"
EXTERNAL_ROOTS = (
    ROOT / "afriride_system",
)
PROTECTED_IMPORT_PREFIXES = (
    "afritech.demo",
    "afritech.ci",
    "afritech.constitution",
)
PROTECTED_PATH_TOKENS = (
    "afritech/demo/proof.py",
    "afritech/constitution/FIVE_INVARIANT_CONTRACT.yaml",
    "afritech/constitution/CLAIM_DISCIPLINE.yaml",
    "afritech/ci/four_gate_validator.py",
    "afritech/ci/enforcement_integrity_validator.py",
    "afritech/ci/constitutional_validation.py",
    "afritech/ci/constitutional_pipeline.py",
)
INTERNAL_ROOTS = (
    ROOT / "afritech",
    ROOT / "ecosystems" / "afriride",
)
ALLOWED_INTERNAL_PRODUCT_BRIDGES = (
    "afritech/verify/verify_proof.py",
    "afritech/tests/sdk/test_verify_proof.py",
)

EXPECTED_INVARIANTS = (
    "preserve_proof_meaning",
    "preserve_authority_boundaries",
    "preserve_afriride_scope",
    "preserve_claim_discipline",
    "preserve_enforcement_integrity",
)

FORBIDDEN_BYPASS_TOKENS = (
    "SKIP_FOUR_GATE",
    "DISABLE_FOUR_GATE",
    "BYPASS_FOUR_GATE",
    "FOUR_GATE_OPTIONAL",
    "ALLOW_DRIFT",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_contract() -> dict[str, Any]:
    payload = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("five-invariant contract must be a mapping")
    return payload


def validate_contract_serialization() -> None:
    payload = load_contract()
    if payload.get("schema") != "afritech.constitution.five_invariant_contract.v1":
        fail("five-invariant contract schema mismatch")
    if payload.get("status") != "PROVEN_GOVERNANCE":
        fail("five-invariant contract status mismatch")
    if payload.get("authority") != "afritech.demo.proof":
        fail("five-invariant contract authority mismatch")
    operating_law = payload.get("operating_law")
    if not isinstance(operating_law, dict):
        fail("five-invariant contract must define operating law")
    if operating_law.get("name") != "preserve_or_isolate":
        fail("operating law must be preserve_or_isolate")
    if operating_law.get("internal_domain") != "preserve_exactly":
        fail("operating law must preserve internal domain exactly")
    if operating_law.get("external_domain") != "remain_fully_decoupled":
        fail("operating law must keep external domain fully decoupled")
    if operating_law.get("mixed_or_ambiguous") != "drift":
        fail("operating law must classify mixed or ambiguous changes as drift")

    invariants = payload.get("invariants")
    if not isinstance(invariants, list):
        fail("five-invariant contract must list invariants")

    names = tuple(
        invariant.get("name")
        for invariant in invariants
        if isinstance(invariant, dict)
    )
    if names != EXPECTED_INVARIANTS:
        fail(f"five-invariant contract names mismatch: {names}")


def validate_four_gate_mandatory() -> None:
    validation_text = CONSTITUTIONAL_VALIDATION.read_text(encoding="utf-8")
    if (
        'name="four_gate_validator"' not in validation_text
        or 'module="afritech.ci.four_gate_validator"' not in validation_text
    ):
        fail("four_gate_validator missing from constitutional validation")

    pipeline_text = CONSTITUTIONAL_PIPELINE.read_text(encoding="utf-8")
    if (
        'name="four_gate_validator"' not in pipeline_text
        or '"afritech.ci.four_gate_validator"' not in pipeline_text
    ):
        fail("four_gate_validator missing from constitutional pipeline")

    if (
        'name="enforcement_integrity_validator"' not in validation_text
        or 'module="afritech.ci.enforcement_integrity_validator"' not in validation_text
    ):
        fail("enforcement_integrity_validator missing from constitutional validation")

    if (
        'name="enforcement_integrity_validator"' not in pipeline_text
        or '"afritech.ci.enforcement_integrity_validator"' not in pipeline_text
    ):
        fail("enforcement_integrity_validator missing from constitutional pipeline")

    if not FOUR_GATE.exists():
        fail("four_gate_validator file missing")
    if not FOUR_GATE_TEST.exists():
        fail("four_gate_validator test missing")


def validate_no_bypass_tokens(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for token in FORBIDDEN_BYPASS_TOKENS:
        if token in text:
            fail(f"forbidden enforcement bypass token in {path}: {token}")


def validate_no_conditional_bypass(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in {"getenv", "environ"}:
                fail(f"environment-controlled enforcement found in {path}")
        if isinstance(node, ast.Name):
            if node.id in {"getenv", "environ"}:
                fail(f"environment-controlled enforcement found in {path}")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def python_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(
        path
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def validate_external_isolation() -> None:
    for root in EXTERNAL_ROOTS:
        for path in python_files(root):
            modules = imported_modules(path)
            for module in modules:
                if module.startswith(PROTECTED_IMPORT_PREFIXES):
                    fail(
                        "external product code imports protected surface: "
                        f"{path.relative_to(ROOT)} -> {module}"
                    )

            text = path.read_text(encoding="utf-8")
            for token in PROTECTED_PATH_TOKENS:
                if token in text:
                    fail(
                        "external product code references protected path: "
                        f"{path.relative_to(ROOT)} -> {token}"
                    )


def validate_internal_no_product_dependency() -> None:
    for root in INTERNAL_ROOTS:
        for path in python_files(root):
            if path == Path(__file__).resolve():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in ALLOWED_INTERNAL_PRODUCT_BRIDGES:
                continue
            modules = imported_modules(path)
            for module in modules:
                if module.startswith("afriride_system"):
                    fail(
                        "protected/internal code imports external product layer: "
                        f"{rel} -> {module}"
                    )


def validate_no_bypass_controls() -> None:
    validate_no_bypass_tokens(FOUR_GATE)
    validate_no_bypass_tokens(CONSTITUTIONAL_VALIDATION)
    validate_no_bypass_tokens(CONSTITUTIONAL_PIPELINE)
    validate_no_conditional_bypass(FOUR_GATE)


def validate() -> None:
    validate_contract_serialization()
    validate_four_gate_mandatory()
    validate_no_bypass_controls()
    validate_external_isolation()
    validate_internal_no_product_dependency()


def main() -> int:
    try:
        validate()
        print("✅ Enforcement integrity validation PASSED")
        print("✅ Five-invariant contract serialized")
        print("✅ Four-gate validator remains mandatory")
        print("✅ No enforcement bypass controls detected")
        print("✅ Preserve-or-isolate boundary enforced")
        return 0
    except Exception as exc:
        print(f"❌ Enforcement integrity validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
