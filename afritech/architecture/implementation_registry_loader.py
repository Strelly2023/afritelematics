from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import ast

import yaml


# ---------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REGISTRY_PATH = (
    PROJECT_ROOT
    / "afritech"
    / "architecture"
    / "implementation_registry.yaml"
)


# ---------------------------------------------------------------------
# CANONICAL EXECUTION SURFACES
# ---------------------------------------------------------------------

SURFACE_PREFIXES: Dict[str, str] = {
    "runtime": "afritech.runtime",
    "replay": "afritech.replay",
    "governance": "afritech.governance",
    "constitutional": "afritech.constitution",
    "speculative": "afritech.speculative",
}


# ---------------------------------------------------------------------
# HARD-BLOCK IMPLEMENTATION STATES
# ---------------------------------------------------------------------

HARD_BLOCK_STATES = (
    "PLANNED",
    "DOCUMENTARY",
    "FORBIDDEN_ALIAS",
)


# ---------------------------------------------------------------------
# REGISTRY LOADING
# ---------------------------------------------------------------------

def load_registry() -> Dict[str, str]:

    if not REGISTRY_PATH.exists():
        return {}

    try:
        raw = REGISTRY_PATH.read_text(
            encoding="utf-8"
        )

        data = yaml.safe_load(raw) or {}

    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    surfaces = data.get("surfaces", {})

    if not isinstance(surfaces, dict):
        return {}

    registry: Dict[str, str] = {}

    for surface, metadata in surfaces.items():

        if not isinstance(surface, str):
            continue

        if not isinstance(metadata, dict):
            continue

        state = metadata.get("state")

        if isinstance(state, str):
            registry[surface] = state

    return registry


# ---------------------------------------------------------------------
# BOUNDARY-SAFE PREFIX MATCHING
# ---------------------------------------------------------------------

def module_matches_prefix(
    module: str,
    prefix: str,
) -> bool:

    return (
        module == prefix
        or module.startswith(prefix + ".")
    )


# ---------------------------------------------------------------------
# EXECUTION SURFACE DETECTION
# ---------------------------------------------------------------------

def detect_surface(
    module: str,
) -> Optional[str]:

    for surface, prefix in SURFACE_PREFIXES.items():

        if module_matches_prefix(module, prefix):
            return surface

    return None


# ---------------------------------------------------------------------
# LONGEST-PREFIX IMPLEMENTATION RESOLUTION
# ---------------------------------------------------------------------

def resolve_state(
    module: str,
    registry: Dict[str, str],
) -> Optional[str]:

    matched_state: Optional[str] = None
    matched_prefix_length = -1

    for prefix, state in registry.items():

        if module_matches_prefix(module, prefix):

            prefix_length = len(prefix)

            if prefix_length > matched_prefix_length:

                matched_state = state
                matched_prefix_length = prefix_length

    return matched_state


# ---------------------------------------------------------------------
# IMPLEMENTATION LEGITIMACY ENFORCEMENT
# ---------------------------------------------------------------------

def violates_implementation_rules(
    importer: str,
    target: str,
    registry: Dict[str, str],
) -> Optional[str]:

    importer_surface = detect_surface(importer)

    if not importer_surface:
        return None

    state = resolve_state(target, registry)

    # Unknown → allowed (forward-compatible policy)
    if not state:
        return None

    # ---------------------------------------------------------
    # RUNTIME ENFORCEMENT
    # ---------------------------------------------------------

    if importer_surface == "runtime":

        if state in HARD_BLOCK_STATES:

            return (
                f"{importer} imports non-runtime-legitimate "
                f"surface {target} (state={state})"
            )

    # ---------------------------------------------------------
    # REPLAY ENFORCEMENT
    # ---------------------------------------------------------

    if importer_surface == "replay":

        if state in HARD_BLOCK_STATES:

            return (
                f"{importer} imports non-replay-legitimate "
                f"surface {target} (state={state})"
            )

    return None


# ---------------------------------------------------------------------
# IMPORT EXTRACTION
# ---------------------------------------------------------------------

def extract_import_targets(
    source: str,
) -> List[str]:

    tree = ast.parse(source)

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
# FILE VALIDATION
# ---------------------------------------------------------------------

def validate_file(
    path: Path,
    registry: Dict[str, str],
) -> List[str]:

    violations: List[str] = []

    try:
        source = path.read_text(
            encoding="utf-8"
        )

    except Exception as exc:
        return [f"Failed to read {path}: {exc}"]

    try:
        targets = extract_import_targets(source)

    except Exception as exc:
        return [f"Failed to parse {path}: {exc}"]

    importer = (
        path.relative_to(PROJECT_ROOT)
        .with_suffix("")
        .as_posix()
        .replace("/", ".")
    )

    for target in targets:

        violation = violates_implementation_rules(
            importer=importer,
            target=target,
            registry=registry,
        )

        if violation:
            violations.append(violation)

    return violations


# ---------------------------------------------------------------------
# REPOSITORY VALIDATION
# ---------------------------------------------------------------------

def validate_repository() -> List[str]:

    registry = load_registry()

    violations: List[str] = []

    for path in (
        PROJECT_ROOT / "afritech"
    ).rglob("*.py"):

        if "__pycache__" in path.parts:
            continue

        violations.extend(
            validate_file(
                path=path,
                registry=registry,
            )
        )

    return sorted(set(violations))


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:

    violations = validate_repository()

    if violations:

        print(
            "\n❌ IMPLEMENTATION LEGITIMACY "
            "VIOLATIONS DETECTED\n"
        )

        for violation in violations:
            print("  -", violation)

        raise SystemExit(1)

    print(
        "✅ Implementation legitimacy verified — "
        "constitutional execution topology preserved"
    )


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()