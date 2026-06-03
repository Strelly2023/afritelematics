"""Validator for projection-enriched explanation boundary."""

from __future__ import annotations

import ast
import inspect
import sys
from types import ModuleType

from afritech.explainability import projection_enrichment


class ProjectionEnrichedExplanationValidationError(RuntimeError):
    pass


FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.proof",
    "afritech.verify",
    "afritech.registry",
)

FORBIDDEN_CALLS = (
    "open",
    "safe_load",
    "load",
    "save",
    "delete",
    "execute",
    "enforce",
    "validate",
    "authorize",
    "admit",
    "decide",
)

REQUIRED_FLAGS = {
    "ENRICHMENT_STATUS": "READ_ONLY_PROJECTION_ENRICHMENT",
    "RUNTIME_AUTHORITY": False,
    "ENFORCEMENT_AUTHORITY": False,
    "VALIDATION_AUTHORITY": False,
    "RECEIPT_MUTATION": False,
    "PROJECTION_DISPLAY_ONLY": True,
}


def _fail(message: str) -> None:
    raise ProjectionEnrichedExplanationValidationError(message)


def _source(module: ModuleType) -> str:
    return inspect.getsource(module)


def _tree(module: ModuleType) -> ast.Module:
    return ast.parse(_source(module))


def _validate_flags() -> None:
    for name, expected in REQUIRED_FLAGS.items():
        actual = getattr(projection_enrichment, name, None)
        if actual != expected:
            _fail(f"{name} must equal {expected!r}, got {actual!r}")


def _validate_imports(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"forbidden import: {alias.name}")

        if isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"forbidden import: {module_name}")


def _validate_calls(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            call_name = ""

            if isinstance(func, ast.Name):
                call_name = func.id
            elif isinstance(func, ast.Attribute):
                call_name = func.attr

            if call_name in FORBIDDEN_CALLS:
                _fail(f"forbidden call: {call_name}")


def _validate_copy_semantics() -> None:
    payload = {
        "execution_id": "exec-1",
        "governance_traceability": [{"type": "ADR", "id": "ADR-0016"}],
    }

    projection_index = {
        "ADR-0016": {
            "title": "Multi-Source Consensus",
            "description": "Read-only governance doctrine.",
        }
    }

    enriched = projection_enrichment.enrich_explanation_payload(
        payload,
        projection_index,
    )

    if enriched is payload:
        _fail("enrichment must return a copied payload")

    if "projection_enrichment" in payload:
        _fail("original payload must not be mutated")

    if enriched.get("runtime_authority") is not False:
        _fail("runtime authority must remain false")

    if enriched.get("validation_authority") is not False:
        _fail("validation authority must remain false")


def validate_projection_enriched_explanation() -> None:
    _validate_flags()
    _validate_imports(projection_enrichment)
    _validate_calls(projection_enrichment)
    _validate_copy_semantics()


def main() -> None:
    try:
        validate_projection_enriched_explanation()
    except ProjectionEnrichedExplanationValidationError as exc:
        print(f"Projection-enriched explanation validation FAILED: {exc}")
        sys.exit(1)

    print("Projection-enriched explanation validation PASSED")


if __name__ == "__main__":
    main()