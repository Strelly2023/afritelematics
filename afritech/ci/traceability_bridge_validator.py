"""Validate the reference-only AfriTech traceability bridge boundary."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY_DIR = ROOT / "afritech/traceability"

REQUIRED_FILES = {
    "__init__.py",
    "references.py",
    "receipt_links.py",
    "serializers.py",
}

REQUIRED_CLASSES = {
    "GovernanceReference",
    "TraceabilityBundle",
    "GovernanceReferenceSerializer",
    "TraceabilitySerializer",
}

REQUIRED_FUNCTIONS = {
    "attach_traceability",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.core",
    "afritech.execution",
    "afritech.governance_projection",
    "afritech.governance",
    "afritech.ci",
)

FORBIDDEN_SOURCE_TOKENS = (
    "governance_projection",
    "yaml.safe_load",
    "yaml.",
    "open(",
    ".read_text(",
    ".write_text(",
    ".write_bytes(",
    ".save(",
    ".delete(",
    ".objects.",
    "subprocess",
)

REFERENCE_ONLY_TERMS = (
    'BRIDGE_STATUS = "REFERENCE_ONLY"',
    "REFERENCE_ONLY = True",
    "RUNTIME_AUTHORITY = False",
    "ENFORCEMENT_AUTHORITY = False",
    "PROJECTION_DEPENDENCY = False",
)


class TraceabilityBridgeValidationError(Exception):
    """Raised when traceability bridge boundaries are invalid."""


def fail(message: str) -> None:
    raise TraceabilityBridgeValidationError(message)


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


def validate_files_exist() -> None:
    missing = sorted(name for name in REQUIRED_FILES if not (TRACEABILITY_DIR / name).is_file())
    if missing:
        fail(f"traceability bridge files missing: {missing}")


def validate_symbols_exist() -> None:
    discovered_classes: set[str] = set()
    discovered_functions: set[str] = set()
    for path in sorted(TRACEABILITY_DIR.glob("*.py")):
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                discovered_classes.add(node.name)
            elif isinstance(node, ast.FunctionDef):
                discovered_functions.add(node.name)

    missing_classes = sorted(REQUIRED_CLASSES - discovered_classes)
    if missing_classes:
        fail(f"traceability bridge classes missing: {missing_classes}")

    missing_functions = sorted(REQUIRED_FUNCTIONS - discovered_functions)
    if missing_functions:
        fail(f"traceability bridge functions missing: {missing_functions}")


def validate_reference_only_terms() -> None:
    for name in ("__init__.py", "references.py", "receipt_links.py"):
        text = _read(TRACEABILITY_DIR / name)
        missing = [term for term in REFERENCE_ONLY_TERMS if term not in text]
        if missing:
            fail(f"{name} missing reference-only terms: {missing}")


def validate_no_forbidden_imports() -> None:
    for path in sorted(TRACEABILITY_DIR.glob("*.py")):
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import(path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                _check_import(path, node.module or "")


def _check_import(path: Path, module: str) -> None:
    if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
        fail(f"forbidden traceability import in {_repo_path(path)}: {module}")


def validate_no_forbidden_source_tokens() -> None:
    for path in sorted(TRACEABILITY_DIR.glob("*.py")):
        text = _read(path)
        violations = [token for token in FORBIDDEN_SOURCE_TOKENS if token in text]
        if violations:
            fail(f"forbidden traceability token in {_repo_path(path)}: {violations}")


def validate_receipt_link_shape() -> None:
    text = _read(TRACEABILITY_DIR / "receipt_links.py")
    required_terms = (
        "enriched = dict(receipt)",
        'TRACEABILITY_FIELD = "governance_traceability"',
        '"traceability_bridge"',
        '"reference_only": REFERENCE_ONLY',
        '"runtime_authority": RUNTIME_AUTHORITY',
        '"enforcement_authority": ENFORCEMENT_AUTHORITY',
        '"projection_dependency": PROJECTION_DEPENDENCY',
    )
    missing = [term for term in required_terms if term not in text]
    if missing:
        fail(f"receipt_links.py missing additive reference-only shape: {missing}")


def validate() -> None:
    validate_files_exist()
    validate_symbols_exist()
    validate_reference_only_terms()
    validate_no_forbidden_imports()
    validate_no_forbidden_source_tokens()
    validate_receipt_link_shape()


def main() -> int:
    try:
        validate()
        print("Traceability bridge validation PASSED")
        return 0
    except Exception as exc:
        print(f"Traceability bridge validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
