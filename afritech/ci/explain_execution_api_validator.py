"""Validate the read-only Explain Execution API boundary."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from afritech.ci.traceability_bridge_validator import validate as validate_bridge
from afritech.ci.governance_projection_validator import validate as validate_projection


ROOT = Path(__file__).resolve().parents[2]
EXPLAINABILITY_DIR = ROOT / "afritech/explainability"
API_VIEW = ROOT / "afritech/api/explain_execution_views.py"
API_URLS = ROOT / "afritech/api/urls.py"

REQUIRED_FILES = {
    EXPLAINABILITY_DIR / "__init__.py",
    EXPLAINABILITY_DIR / "execution_explainer.py",
    API_VIEW,
}

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.core.runtime",
    "afritech.execution",
    "afritech.kernel",
    "afritech.guards",
)

FORBIDDEN_MUTATION_TOKENS = (
    ".save(",
    ".delete(",
    ".objects.",
    ".write_text(",
    ".write_bytes(",
    ".unlink(",
    ".mkdir(",
    "subprocess",
)

REQUIRED_BOUNDARY_TERMS = (
    'EXPLANATION_STATUS = "READ_ONLY_EXPLANATION"',
    "RUNTIME_AUTHORITY = False",
    "ENFORCEMENT_AUTHORITY = False",
    "VALIDATION_AUTHORITY = False",
    "PROJECTION_DISPLAY_ONLY = True",
)


class ExplainExecutionAPIValidationError(Exception):
    """Raised when the explain execution API boundary is invalid."""


def fail(message: str) -> None:
    raise ExplainExecutionAPIValidationError(message)


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
    missing = sorted(_repo_path(path) for path in REQUIRED_FILES if not path.is_file())
    if missing:
        fail(f"explain execution files missing: {missing}")


def validate_symbols_exist() -> None:
    tree = _parse(EXPLAINABILITY_DIR / "execution_explainer.py")
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if "ExecutionExplanation" not in classes:
        fail("ExecutionExplanation class missing")
    if "ExecutionExplanationStore" not in classes:
        fail("ExecutionExplanationStore class missing")
    if "explain_execution_payload" not in functions:
        fail("explain_execution_payload function missing")
    if "explain_execution_from_store" not in functions:
        fail("explain_execution_from_store function missing")


def validate_boundary_terms() -> None:
    for path in (
        EXPLAINABILITY_DIR / "__init__.py",
        EXPLAINABILITY_DIR / "execution_explainer.py",
    ):
        text = _read(path)
        missing = [term for term in REQUIRED_BOUNDARY_TERMS if term not in text]
        if missing:
            fail(f"{_repo_path(path)} missing explanation boundary terms: {missing}")


def validate_no_forbidden_imports() -> None:
    for path in sorted(tuple(EXPLAINABILITY_DIR.glob("*.py")) + (API_VIEW,)):
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import(path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                _check_import(path, node.module or "")


def _check_import(path: Path, module: str) -> None:
    if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
        fail(f"forbidden explain execution import in {_repo_path(path)}: {module}")


def validate_no_mutation_tokens() -> None:
    for path in sorted(tuple(EXPLAINABILITY_DIR.glob("*.py")) + (API_VIEW,)):
        text = _read(path)
        violations = [token for token in FORBIDDEN_MUTATION_TOKENS if token in text]
        if violations:
            fail(f"forbidden mutation token in {_repo_path(path)}: {violations}")


def validate_api_route() -> None:
    text = _read(API_URLS)
    if "explain_execution_view" not in text:
        fail("explain_execution_view must be imported in afritech/api/urls.py")
    if 'path("execution/<str:execution_id>/explain/", explain_execution_view)' not in text:
        fail("explain execution route missing")


def validate_projection_is_display_only() -> None:
    text = _read(EXPLAINABILITY_DIR / "execution_explainer.py")
    required_terms = (
        "from afritech.governance_projection.importer import project_governance",
        '"projection_display_only": PROJECTION_DISPLAY_ONLY',
        '"display_only": True',
        "authority remains in governance YAML, validators, replay, and CI",
    )
    missing = [term for term in required_terms if term not in text]
    if missing:
        fail(f"explainability projection display boundary missing: {missing}")


def validate() -> None:
    validate_bridge()
    validate_projection()
    validate_files_exist()
    validate_symbols_exist()
    validate_boundary_terms()
    validate_no_forbidden_imports()
    validate_no_mutation_tokens()
    validate_api_route()
    validate_projection_is_display_only()


def main() -> int:
    try:
        validate()
        print("Explain execution API validation PASSED")
        return 0
    except Exception as exc:
        print(f"Explain execution API validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
