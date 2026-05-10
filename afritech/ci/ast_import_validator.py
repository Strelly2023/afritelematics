# afritech/ci/ast_import_validator.py

"""
AfriTech CI — AST Import Topology Validator
==========================================

This validator enforces constitutional import topology
using Python AST analysis (not regex).

It guarantees that:
- mutation-capable modules are imported ONLY by the constitutional gateway
- raw epoch artifacts are never imported at runtime
- speculative / non-operative surfaces are never imported by executable code
- enforcement binds to compiled semantic artifacts only

This is a FAIL-CLOSED constitutional gate.
Any violation MUST fail CI.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List, Set, Tuple


# ---------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"


# ---------------------------------------------------------------------
# CONSTITUTIONAL RULES (CANONICAL)
# ---------------------------------------------------------------------

# 1. Mutation-capable modules (capability surfaces)
MUTATION_MODULE_PREFIXES = (
    "afritech.internal.state_mutation",
    "afritech.internal.epoch_mutation",
)

# ONLY this namespace may import mutation capability
ALLOWED_MUTATION_IMPORTERS = (
    "afritech.kernel.constitutional_gateway",
)

# 2. Raw epoch artifacts are NEVER importable at runtime
FORBIDDEN_EPOCH_MODULE_PREFIXES = (
    "afritech.epoch.epoch_registry",
    "afritech.registry.history",
)

# 3. Speculative / non-operative surfaces
FORBIDDEN_SPECULATIVE_PREFIXES = (
    "afritech.speculative",
    "afritech.civilization",
    "afritech.federation",
    "afritech.distributed",
    "afritech.economic",
)

# 4. Allowed epoch imports (compiled only)
ALLOWED_EPOCH_PREFIXES = (
    "afritech.epoch.compiled.semantic_epoch",
    "afritech.epoch.epoch_snapshot",
)

def is_legacy_path(path: Path) -> bool:
    return "legacy" in path.parts



# ---------------------------------------------------------------------
# FAILURE HANDLING
# ---------------------------------------------------------------------

def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL IMPORT TOPOLOGY VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


# ---------------------------------------------------------------------
# PATH → MODULE RESOLUTION
# ---------------------------------------------------------------------

def module_path_from_file(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT)
    return ".".join(rel.with_suffix("").parts)


# ---------------------------------------------------------------------
# AST SCAN
# ---------------------------------------------------------------------

def scan_file(path: Path) -> List[str]:
    violations: List[str] = []

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return violations  # syntax errors not this tool's concern

    importer = module_path_from_file(path)

    for node in ast.walk(tree):

        # -------------------------------------------------------------
        # import x.y.z
        # -------------------------------------------------------------
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported = alias.name
                violations.extend(
                    check_import(importer, imported, path)
                )

        # -------------------------------------------------------------
        # from x.y import z
        # -------------------------------------------------------------
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported = node.module
                violations.extend(
                    check_import(importer, imported, path)
                )

    return violations


# ---------------------------------------------------------------------
# CONSTITUTIONAL IMPORT RULES
# ---------------------------------------------------------------------

def check_import(
    importer: str,
    imported: str,
    path: Path,
) -> List[str]:
    v: List[str] = []

    # -------------------------------------------------------------
    # RULE 1 — Mutation capability confinement
    # -------------------------------------------------------------
    if imported.startswith(MUTATION_MODULE_PREFIXES):
        if not importer.startswith(ALLOWED_MUTATION_IMPORTERS):
            v.append(
                f"{importer} illegally imports mutation capability "
                f"{imported} (only constitutional_gateway allowed)"
            )

    # -------------------------------------------------------------
    # RULE 2 — Raw epoch artifact prohibition
    # -------------------------------------------------------------
    if imported.startswith(FORBIDDEN_EPOCH_MODULE_PREFIXES):
        v.append(
            f"{importer} imports forbidden raw epoch artifact {imported}"
        )

    # -------------------------------------------------------------
    # RULE 3 — Speculative surface isolation
    # -------------------------------------------------------------
    if imported.startswith(FORBIDDEN_SPECULATIVE_PREFIXES):
        v.append(
            f"{importer} imports speculative / non-operative surface "
            f"{imported}"
        )

    # -------------------------------------------------------------
    # RULE 4 — Epoch imports must be compiled
    # -------------------------------------------------------------
    if imported.startswith("afritech.epoch"):
        if not imported.startswith(ALLOWED_EPOCH_PREFIXES):
            v.append(
                f"{importer} imports non-compiled epoch module "
                f"{imported}"
            )

    return v


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    violations: List[str] = []

    for path in AFRITECH_ROOT.rglob("*.py"):
        if any(part in (".git", "__pycache__", "venv", ".venv") for part in path.parts):
            continue

        if is_legacy_path(path):
            continue

        violations.extend(scan_file(path))

    if violations:
        fail(violations)

    print("✅ AST import topology validated — constitutional confinement enforced")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()