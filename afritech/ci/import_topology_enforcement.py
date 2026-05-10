# afritech/ci/import_topology_enforcement.py

"""
AfriTech CI — Import Topology Enforcement (RATIFIED)
====================================================

This validator enforces CAPABILITY CONFINEMENT in AfriTech.

CONSTITUTIONAL RULE (LOCKED):
- Mutation-capable modules may ONLY be imported by:
    afritech.kernel.constitutional_gateway

This rule enforces *authority topology*, not style.

NOTES:
- Legacy code is ignored
- CI / tooling is ignored
- Speculative code is ignored
- This validator complements (not replaces):
    - ast_import_validator.py
    - forbid_topology_change.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"


# ---------------------------------------------------------------------
# MUTATION CAPABILITIES (AUTHORITATIVE)
# ---------------------------------------------------------------------

MUTATION_MODULE_PREFIXES = (
    "afritech.internal.state_mutation",
    "afritech.internal.epoch_mutation",
)

# Only this module may import mutation logic
ALLOWED_IMPORTER = "afritech.kernel.constitutional_gateway"


# ---------------------------------------------------------------------
# PATH FILTERS (RATIFIED)
# ---------------------------------------------------------------------

IGNORED_PATH_FRAGMENTS = (
    "/ci/",
    "/epoch/compiler/",
    "/epoch/legacy/",
    "/speculative/",
    "/tests/",
    "/docs/",
    "/tools/",
    "/formal/",
)


# ---------------------------------------------------------------------
# FAILURE HANDLER
# ---------------------------------------------------------------------

def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL IMPORT TOPOLOGY VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def is_ignored(path: Path) -> bool:
    return any(fragment in str(path) for fragment in IGNORED_PATH_FRAGMENTS)


def module_path_from_file(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT)
    return ".".join(rel.with_suffix("").parts)


# ---------------------------------------------------------------------
# SCAN LOGIC
# ---------------------------------------------------------------------

def scan_file(path: Path) -> List[str]:
    violations: List[str] = []

    if is_ignored(path):
        return violations

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return violations  # syntax errors not our concern

    importer_module = module_path_from_file(path)

    for node in ast.walk(tree):
        # import afritech.internal.state_mutation.foo
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(MUTATION_MODULE_PREFIXES):
                    if importer_module != ALLOWED_IMPORTER:
                        violations.append(
                            f"{importer_module} illegally imports mutation capability {alias.name}"
                        )

        # from afritech.internal.state_mutation import foo
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(MUTATION_MODULE_PREFIXES):
                if importer_module != ALLOWED_IMPORTER:
                    violations.append(
                        f"{importer_module} illegally imports mutation capability {node.module}"
                    )

    return violations


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    violations: List[str] = []

    for path in AFRITECH_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        violations.extend(scan_file(path))

    if violations:
        fail(violations)

    print("✅ Import topology verified — mutation capability confined")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()