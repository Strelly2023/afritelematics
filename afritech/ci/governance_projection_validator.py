"""Validate the read-only AfriTech governance projection boundary."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
PROJECTION_DIR = ROOT / "afritech/governance_projection"

REQUIRED_FILES = {
    "__init__.py",
    "models.py",
    "importer.py",
    "serializers.py",
    "admin.py",
    "apps.py",
}

REQUIRED_MODELS = {
    "GovernanceADR",
    "GovernanceInvariant",
    "GovernanceRule",
    "GovernanceBinding",
    "GovernanceCICheck",
    "GovernanceNonClaim",
    "GovernanceNextStep",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.core.runtime",
    "afritech.execution",
    "afritech.kernel",
    "afritech.guards",
    "afritech.ci",
)

FORBIDDEN_MUTATION_TOKENS = (
    ".save(",
    ".delete(",
    ".objects.create(",
    ".objects.update(",
    ".bulk_create(",
    ".bulk_update(",
    ".update_or_create(",
    ".get_or_create(",
    ".write_text(",
    ".write_bytes(",
    ".unlink(",
    ".mkdir(",
    "open(",
    "subprocess",
)

BOUNDARY_ADRS = (
    ROOT / "afritech/governance/adr/ADR-0016-multisource-consensus.yaml",
    ROOT / "afritech/governance/adr/ADR-0018-cross-system-continuity.yaml",
)


class GovernanceProjectionValidationError(Exception):
    """Raised when the documentary projection boundary is invalid."""


def fail(message: str) -> None:
    raise GovernanceProjectionValidationError(message)


def _repo_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _read(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {_repo_path(path)}")
    return path.read_text(encoding="utf-8")


def _parse(path: Path) -> ast.Module:
    try:
        return ast.parse(_read(path), filename=str(path))
    except SyntaxError as exc:
        fail(f"syntax error in {_repo_path(path)}: {exc}")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing governance YAML: {_repo_path(path)}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"governance YAML must be a mapping: {_repo_path(path)}")
    return payload


def validate_files_exist() -> None:
    missing = sorted(name for name in REQUIRED_FILES if not (PROJECTION_DIR / name).is_file())
    if missing:
        fail(f"governance projection files missing: {missing}")


def validate_models_exist() -> None:
    tree = _parse(PROJECTION_DIR / "models.py")
    discovered = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    missing = sorted(REQUIRED_MODELS - discovered)
    if missing:
        fail(f"governance projection models missing: {missing}")

    text = _read(PROJECTION_DIR / "models.py")
    required_terms = (
        'PROJECTION_STATUS = "DOCUMENTARY"',
        "PROJECTION_IS_DOCUMENTARY_ONLY = True",
        "RUNTIME_AUTHORITY = False",
        "ENFORCEMENT_AUTHORITY = False",
        "managed = False",
        'app_label = "governance_projection"',
    )
    missing_terms = [term for term in required_terms if term not in text]
    if missing_terms:
        fail(f"models.py missing documentary boundary terms: {missing_terms}")


def validate_importer_is_read_only() -> None:
    text = _read(PROJECTION_DIR / "importer.py")
    required_terms = (
        "READ_ONLY = True",
        'PROJECTION_DIRECTION = "YAML_TO_DJANGO_PROJECTION"',
        'FORBIDDEN_REVERSE_DIRECTION = "DJANGO_PROJECTION_TO_AUTHORITY"',
        "read_text(",
    )
    missing_terms = [term for term in required_terms if term not in text]
    if missing_terms:
        fail(f"importer.py missing read-only terms: {missing_terms}")

    violations = [token for token in FORBIDDEN_MUTATION_TOKENS if token in text]
    if violations:
        fail(f"importer.py contains mutation-capable tokens: {violations}")


def validate_no_runtime_or_enforcement_imports() -> None:
    for path in sorted(PROJECTION_DIR.glob("*.py")):
        tree = _parse(path)
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    _check_forbidden_import(path, module)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                _check_forbidden_import(path, module)


def _check_forbidden_import(path: Path, module: str) -> None:
    if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
        fail(f"forbidden runtime/enforcement import in {_repo_path(path)}: {module}")


def validate_projection_status() -> None:
    for name in ("__init__.py", "models.py", "apps.py"):
        text = _read(PROJECTION_DIR / name)
        if "DOCUMENTARY" not in text:
            fail(f"{name} must declare DOCUMENTARY projection status")
        if "runtime_authority = False" not in text and "RUNTIME_AUTHORITY = False" not in text:
            fail(f"{name} must declare runtime authority false")
        if (
            "enforcement_authority = False" not in text
            and "ENFORCEMENT_AUTHORITY = False" not in text
        ):
            fail(f"{name} must declare enforcement authority false")


def validate_boundary_adrs_remain_non_runtime_authoritative() -> None:
    for path in BOUNDARY_ADRS:
        payload = _load_yaml(path)
        adr = payload.get("adr")
        if not isinstance(adr, dict):
            fail(f"{_repo_path(path)} must define adr mapping")

        boundary = adr.get("constitutional_boundary")
        if not isinstance(boundary, dict):
            fail(f"{adr.get('id')} must define constitutional_boundary")
        if boundary.get("runtime_authoritative") is not False:
            fail(f"{adr.get('id')} must remain runtime_authoritative=false")
        if boundary.get("replay_authoritative") is not False:
            fail(f"{adr.get('id')} must remain replay_authoritative=false")

        if adr.get("id") == "ADR-0016":
            if boundary.get("may_override_replay") is not False:
                fail("ADR-0016 must not override replay")
            if boundary.get("may_override_invariants") is not False:
                fail("ADR-0016 must not override invariants")
        if adr.get("id") == "ADR-0018":
            if boundary.get("external_system_may_define_afritech_truth") is not False:
                fail("ADR-0018 must reject external AfriTech truth authority")


def validate() -> None:
    validate_files_exist()
    validate_models_exist()
    validate_importer_is_read_only()
    validate_no_runtime_or_enforcement_imports()
    validate_projection_status()
    validate_boundary_adrs_remain_non_runtime_authoritative()


def main() -> int:
    try:
        validate()
        print("Governance projection validation PASSED")
        return 0
    except Exception as exc:
        print(f"Governance projection validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
