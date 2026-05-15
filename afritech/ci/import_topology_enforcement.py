from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"


# ---------------------------------------------------------------------
# CANONICAL SURFACE DEFINITIONS
# ---------------------------------------------------------------------
# Surface identity must remain deterministic and boundary-safe.
# ---------------------------------------------------------------------

SURFACE_MAP: Dict[str, str] = {
    "runtime": "afritech.runtime",
    "replay": "afritech.replay",
    "governance": "afritech.governance",
    "constitutional": "afritech.constitution",
    "speculative": "afritech.speculative",
}


# ---------------------------------------------------------------------
# EXECUTION SURFACES (CLOSED-WORLD DOMAIN)
# ---------------------------------------------------------------------
# Only these surfaces participate in constitutional execution law.
# ---------------------------------------------------------------------

EXECUTION_SURFACE_PREFIXES = (
    "afritech.runtime",
    "afritech.replay",
    "afritech.governance",
    "afritech.constitution",
    "afritech.speculative",
)


# ---------------------------------------------------------------------
# DECLARATIVE GOVERNANCE (READ-ONLY FOR RUNTIME)
# ---------------------------------------------------------------------
# Runtime may consume declarative governance artifacts only.
# Runtime may not consume operational governance machinery.
# ---------------------------------------------------------------------

DECLARATIVE_GOVERNANCE_PREFIXES = (
    "afritech.governance.rules",
    "afritech.governance.execution_surfaces",
    "afritech.constitution",
)


# ---------------------------------------------------------------------
# DECLARATIVE RUNTIME (READ-ONLY FOR GOVERNANCE)
# ---------------------------------------------------------------------
# Governance may observe runtime metadata and receipts,
# but may not control operational runtime execution.
# ---------------------------------------------------------------------

DECLARATIVE_RUNTIME_PREFIXES = (
    "afritech.runtime.schemas",
    "afritech.runtime.receipts",
    "afritech.runtime.metadata",
)


# ---------------------------------------------------------------------
# REPLAY-SAFE RUNTIME SURFACES
# ---------------------------------------------------------------------
# Replay authority is verification authority only.
# Replay may consume replay-safe runtime artifacts,
# but may not execute operational runtime logic.
# ---------------------------------------------------------------------

REPLAY_SAFE_RUNTIME_PREFIXES = (
    "afritech.runtime.replay_safe",
)


# ---------------------------------------------------------------------
# MUTATION CONTROL
# ---------------------------------------------------------------------
# Mutation authority is constitutionally confined to a
# single authorized gateway surface.
# ---------------------------------------------------------------------

MUTATION_MODULE_PREFIXES = (
    "afritech.internal.state_mutation",
    "afritech.internal.epoch_mutation",
)

ALLOWED_MUTATION_IMPORTER = (
    "afritech.kernel.constitutional_gateway"
)


# ---------------------------------------------------------------------
# IGNORED PATHS
# ---------------------------------------------------------------------

IGNORED_PATH_FRAGMENTS = (
    "/ci/",
    "/tests/",
    "/docs/",
    "/tools/",
    "/formal/",
    "/legacy/",
)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def is_ignored(path: Path) -> bool:
    return any(
        fragment in str(path)
        for fragment in IGNORED_PATH_FRAGMENTS
    )


def module_path_from_file(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT)
    return ".".join(rel.with_suffix("").parts)


def module_matches_prefix(module: str, prefix: str) -> bool:
    """
    Boundary-safe namespace matching.

    Prevents:
        afritech.runtimex
    from matching:
        afritech.runtime
    """

    return module == prefix or module.startswith(prefix + ".")


def detect_surface(module: str) -> Optional[str]:

    for surface, prefix in SURFACE_MAP.items():

        if module_matches_prefix(module, prefix):
            return surface

    return None


# ---------------------------------------------------------------------
# UNKNOWN EXECUTION SURFACE DETECTION
# ---------------------------------------------------------------------
# Closed-world enforcement applies ONLY to execution surfaces.
# ---------------------------------------------------------------------

def is_unknown_execution_surface(module: str) -> bool:

    # Only enforce inside afritech namespace
    if not module.startswith("afritech."):
        return False

    if not any(
        module == prefix or module.startswith(prefix + ".")
        for prefix in EXECUTION_SURFACE_PREFIXES
    ):
        return False

    return detect_surface(module) is None


def is_declarative_governance_surface(module: str) -> bool:
    return any(
        module_matches_prefix(module, prefix)
        for prefix in DECLARATIVE_GOVERNANCE_PREFIXES
    )


def is_declarative_runtime_surface(module: str) -> bool:
    return any(
        module_matches_prefix(module, prefix)
        for prefix in DECLARATIVE_RUNTIME_PREFIXES
    )


def is_replay_safe_runtime_surface(module: str) -> bool:
    return any(
        module_matches_prefix(module, prefix)
        for prefix in REPLAY_SAFE_RUNTIME_PREFIXES
    )


# ---------------------------------------------------------------------
# SURFACE RULES
# ---------------------------------------------------------------------
# Constitutional directional authority enforcement.
# ---------------------------------------------------------------------

def violates_surface_rules(
    importer: str,
    target: str,
) -> Optional[str]:

    # ---------------------------------------------------------
    # Closed-world execution enforcement
    # ---------------------------------------------------------

    if is_unknown_execution_surface(target):
        return (
            f"{importer} imports unknown execution "
            f"surface {target}"
        )

    importer_surface = detect_surface(importer)
    target_surface = detect_surface(target)

    # Ignore non-execution surfaces
    if not importer_surface or not target_surface:
        return None

    # =========================================================
    # RUNTIME RULES
    # =========================================================
    # Runtime execution may consume declarative governance,
    # but not operational governance or speculation.
    # =========================================================

    if importer_surface == "runtime":

        if target_surface == "speculative":
            return (
                f"{importer} violates runtime closed-world "
                f"isolation by importing speculative surface "
                f"{target}"
            )

        if target_surface == "governance":

            if not is_declarative_governance_surface(target):
                return (
                    f"{importer} illegally imports operational "
                    f"governance surface {target}"
                )

    # =========================================================
    # REPLAY RULES
    # =========================================================
    # Replay authority is verification authority only.
    # =========================================================

    if importer_surface == "replay":

        if target_surface == "runtime":

            if not is_replay_safe_runtime_surface(target):
                return (
                    f"{importer} illegally imports runtime "
                    f"execution logic {target}"
                )

        if target_surface == "governance":
            return (
                f"{importer} violates replay authority by "
                f"importing governance surface {target}"
            )

        if target_surface == "speculative":
            return (
                f"{importer} violates replay purity by "
                f"importing speculative surface {target}"
            )

    # =========================================================
    # GOVERNANCE RULES
    # =========================================================
    # Governance may observe declarative runtime artifacts,
    # but may not control operational runtime execution.
    # =========================================================

    if importer_surface == "governance":

        if target_surface == "runtime":

            if not is_declarative_runtime_surface(target):
                return (
                    f"{importer} illegally imports operational "
                    f"runtime surface {target}"
                )

        if target_surface == "speculative":
            return (
                f"{importer} cannot import speculative "
                f"execution surfaces {target}"
            )

    # =========================================================
    # CONSTITUTIONAL RULES
    # =========================================================
    # Constitutional admissibility surfaces may not depend
    # on speculative execution doctrine.
    # =========================================================

    if importer_surface == "constitutional":

        if target_surface == "speculative":
            return (
                f"{importer} violates constitutional closure "
                f"by importing speculative surface {target}"
            )

    return None


# ---------------------------------------------------------------------
# MUTATION RULES
# ---------------------------------------------------------------------
# Mutation authority is restricted to a single constitutional
# mutation gateway.
# ---------------------------------------------------------------------

def violates_mutation_rules(
    importer: str,
    target: str,
) -> Optional[str]:

    for prefix in MUTATION_MODULE_PREFIXES:

        if module_matches_prefix(target, prefix):

            if importer != ALLOWED_MUTATION_IMPORTER:
                return (
                    f"{importer} illegally imports mutation "
                    f"surface {target}"
                )

    return None


# ---------------------------------------------------------------------
# IMPORT EXTRACTION
# ---------------------------------------------------------------------

def extract_import_targets(
    tree: ast.AST,
) -> List[str]:

    targets: List[str] = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                targets.append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                targets.append(node.module)

    return targets


# ---------------------------------------------------------------------
# SCAN FILE
# ---------------------------------------------------------------------

def scan_file(path: Path) -> List[str]:

    violations: List[str] = []

    if is_ignored(path):
        return violations

    try:
        tree = ast.parse(
            path.read_text(encoding="utf-8")
        )

    except Exception as exc:
        violations.append(
            f"Failed to parse {path}: {exc}"
        )
        return violations

    importer = module_path_from_file(path)

    for target in extract_import_targets(tree):

        mutation_violation = violates_mutation_rules(
            importer,
            target,
        )

        if mutation_violation:
            violations.append(mutation_violation)

        surface_violation = violates_surface_rules(
            importer,
            target,
        )

        if surface_violation:
            violations.append(surface_violation)

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

    unique_violations = sorted(set(violations))

    if unique_violations:

        print(
            "\n❌ EXECUTION SURFACE VIOLATIONS DETECTED\n"
        )

        for violation in unique_violations:
            print("  -", violation)

        sys.exit(1)

    print(
        "✅ Execution surfaces verified — "
        "constitutional isolation enforced"
    )


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()