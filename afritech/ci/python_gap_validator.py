"""Validate non-marker Python implementation gaps."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (
    ROOT / "afritech",
    ROOT / "ecosystems",
)

REQUIRED_FROZEN_NAMES = {
    "IMPLEMENTATION_STATE",
    "RUNTIME_ADMISSIBLE",
    "REPLAY_PARTICIPATING",
    "PROOF_ADMISSIBLE",
    "MUTATION_AUTHORITY",
    "FREEZE_REASON",
    "FrozenSurfaceError",
    "assert_admissible",
    "is_runtime_admissible",
}


class PythonGapValidationError(Exception):
    """Raised when a non-marker Python gap remains."""


def fail(message: str) -> None:
    raise PythonGapValidationError(message)


def python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        files.extend(sorted(root.rglob("*.py")))
    return files


def exported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
    return names


def is_frozen_surface(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id != "IMPLEMENTATION_STATE":
                continue
            if isinstance(node.value, ast.Constant) and node.value.value == "FROZEN":
                return True
    return False


def validate() -> None:
    empty_non_markers: list[str] = []
    invalid_frozen: list[str] = []

    for path in python_files():
        if path.name == "__init__.py":
            continue
        relative = str(path.relative_to(ROOT))
        source = path.read_text(encoding="utf-8")
        if not source.strip():
            empty_non_markers.append(relative)
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            fail(f"{relative} is not parseable Python: {exc}")

        if is_frozen_surface(tree):
            missing = REQUIRED_FROZEN_NAMES - exported_names(tree)
            if missing:
                invalid_frozen.append(f"{relative}: missing {sorted(missing)}")

    if empty_non_markers:
        fail(f"empty non-marker Python files remain: {empty_non_markers}")
    if invalid_frozen:
        fail(f"invalid frozen Python surfaces: {invalid_frozen}")

    print("✅ Python implementation gap validation PASSED")
    print("✅ Empty non-marker Python files: 0")


def main() -> int:
    try:
        validate()
        return 0
    except PythonGapValidationError as exc:
        print(f"❌ Python implementation gap validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
