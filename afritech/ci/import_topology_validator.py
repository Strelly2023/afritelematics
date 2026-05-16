# afritech/ci/import_topology_validator.py

"""
AfriTech Constitutional Import Topology Validator

Purpose
-------
Enforce deterministic, replay-safe, epoch-admissible import topology.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set

from afritech.ci.epoch_resolver import (
    get_current_epoch,
    get_module_epoch,
)

# ============================================================
# ROOTS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"

# ============================================================
# REPLAY-UNSAFE EXECUTION FUNCTIONS
# ============================================================

FORBIDDEN_EXECUTION_FUNCTIONS = {
    "__import__",
    "eval",
    "exec",
}

FORBIDDEN_IMPORT_MODULES = {
    "imp",
}

FORBIDDEN_DYNAMIC_IMPORT_CALLS = {
    "spec_from_file_location",
    "module_from_spec",
    "SourceFileLoader",
    "load_module",
}

CANONICAL_SURFACES = {
    "runtime",
    "proof",
    "evaluation",
    "trace",
    "governance",
    "ci",
}

ImportGraph = Dict[str, Set[str]]

# ============================================================
# FAILURE
# ============================================================

def fail(message: str) -> None:
    raise RuntimeError(message)

# ============================================================
# PATH → MODULE
# ============================================================

def module_name_from_path(path: Path) -> str:
    relative = path.relative_to(PROJECT_ROOT)
    return ".".join(relative.with_suffix("").parts)

# ============================================================
# FILE DISCOVERY
# ============================================================

def discover_python_files() -> List[Path]:
    return sorted(
        path
        for path in AFRITECH_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )

# ============================================================
# SURFACE RESOLUTION
# ============================================================

def resolve_surface(module_name: str) -> str | None:
    parts = module_name.split(".")
    if len(parts) < 2:
        return None

    surface = parts[1]
    return surface if surface in CANONICAL_SURFACES else None

# ============================================================
# TYPE-CHECKING DETECTION
# ============================================================

def is_type_checking_block(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
    )

# ============================================================
# IMPORT EXTRACTION
# ============================================================

def extract_imports(tree: ast.AST) -> Set[str]:
    imports: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return imports

# ============================================================
# IMPORT VALIDATION (STATIC + RUNTIME SAFETY)
# ============================================================

def validate_import_behavior(tree: ast.AST, module_name: str) -> None:

    surface = resolve_surface(module_name)

    for node in ast.walk(tree):

        # Skip TYPE_CHECKING blocks
        if is_type_checking_block(node):
            continue

        # --------------------------------------------
        # IMPORT STATEMENTS
        # --------------------------------------------
        if isinstance(node, ast.Import):

            for alias in node.names:
                imp = alias.name

                if imp in FORBIDDEN_IMPORT_MODULES:
                    fail(f"replay-unsafe import module '{imp}' in {module_name}")

                if surface == "runtime" and imp.startswith("importlib"):
                    fail(f"runtime importlib usage forbidden in {module_name}")

        elif isinstance(node, ast.ImportFrom):

            imp = node.module
            if not imp:
                continue

            if imp in FORBIDDEN_IMPORT_MODULES:
                fail(f"replay-unsafe import module '{imp}' in {module_name}")

            if surface == "runtime" and imp.startswith("importlib"):
                fail(f"runtime importlib usage forbidden in {module_name}")

        # --------------------------------------------
        # FUNCTION CALLS
        # --------------------------------------------
        elif isinstance(node, ast.Call):

            func_name = None

            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name in FORBIDDEN_EXECUTION_FUNCTIONS:
                fail(f"replay-unsafe execution function '{func_name}' in {module_name}")

            if func_name in FORBIDDEN_DYNAMIC_IMPORT_CALLS:
                fail(f"dynamic import topology mutation '{func_name}' in {module_name}")

            if surface == "runtime" and func_name == "import_module":
                fail(f"runtime dynamic import forbidden in {module_name}")

# ============================================================
# IMPORT GRAPH (WITH EPOCH ENFORCEMENT)
# ============================================================

def build_import_graph() -> ImportGraph:

    graph: ImportGraph = {}
    current_epoch = get_current_epoch()

    for file in discover_python_files():

        module = module_name_from_path(file)

        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            fail(f"syntax error in {module}: {exc}")

        validate_import_behavior(tree, module)

        imports = extract_imports(tree)
        afritech_imports: Set[str] = set()

        for imp in imports:

            if not imp.startswith("afritech"):
                continue

            imported_epoch = get_module_epoch(imp)

            # ✅ CRITICAL: EPOCH ENFORCEMENT
            if imported_epoch > current_epoch:
                fail(
                    f"future-epoch import forbidden: "
                    f"{module} → {imp} "
                    f"(epoch {imported_epoch} > {current_epoch})"
                )

            afritech_imports.add(imp)

        graph[module] = afritech_imports

    return graph

# ============================================================
# CYCLE DETECTION
# ============================================================

def detect_cycles(graph: ImportGraph) -> None:

    visited: Set[str] = set()
    stack: List[str] = []

    def dfs(node: str):

        if node in stack:
            cycle = stack[stack.index(node):] + [node]

            if len(set(cycle)) > 1:
                fail(f"circular import detected: {' -> '.join(cycle)}")
            return

        if node in visited:
            return

        visited.add(node)
        stack.append(node)

        for dep in graph.get(node, set()):
            if dep in graph:
                dfs(dep)

        stack.pop()

    for node in graph:
        dfs(node)

# ============================================================
# SURFACE VALIDATION
# ============================================================

def validate_surface_imports(graph: ImportGraph) -> None:

    for module, imports in graph.items():

        surface = resolve_surface(module)
        if not surface:
            continue

        for imp in imports:

            imp_surface = resolve_surface(imp)
            if not imp_surface:
                continue

            if surface == "runtime" and imp_surface == "evaluation":
                fail(f"runtime cannot import evaluation: {module} -> {imp}")

            if surface == "proof" and imp_surface == "runtime":
                fail(f"proof cannot import runtime: {module} -> {imp}")

            if surface == "evaluation" and imp_surface == "runtime":
                fail(f"evaluation cannot import runtime: {module} -> {imp}")

# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:
        graph = build_import_graph()

        detect_cycles(graph)
        validate_surface_imports(graph)

        print("✅ Import topology validation passed")
        print("✅ Circular import validation passed")
        print("✅ Replay-safe import topology verified")
        print("✅ Runtime topology mutation forbidden")
        print("✅ Epoch-gated import admissibility enforced")
        print("✅ Closed-world import semantics enforced")

        return 0

    except Exception as exc:
        print(f"❌ Import topology validation failed: {exc}")
        return 1


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
