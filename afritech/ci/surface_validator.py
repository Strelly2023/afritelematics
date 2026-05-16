# afritech/ci/surface_validator.py

"""
AfriTech Execution Surface Validator
====================================

Validates constitutional execution surface topology.

Enforces:

- no overlapping canonical surfaces
- no undeclared runtime surfaces
- replay-safe execution topology
- closed-world execution legality
- canonical namespace normalization
- deprecated aggregate isolation

CONSTITUTIONAL RULE:
All runtime execution must occur exclusively through
declared canonical execution surfaces.

Undeclared or overlapping surfaces are constitutionally
invalid and replay-inadmissible.
"""

from __future__ import annotations

import sys
import yaml

from pathlib import Path
from typing import Any, Dict, List, Set


# ============================================================
# PATHS
# ============================================================

REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

AFRITECH_ROOT = (
    REPO_ROOT
    / "afritech"
)

SURFACE_FILE = (
    AFRITECH_ROOT
    / "governance"
    / "EXECUTION_SURFACES.yaml"
)


# ============================================================
# CONSTANTS
# ============================================================

CANONICAL_SURFACES = {
    "runtime_activation",
    "runtime_engine",
    "proof",
    "evaluation",
}

DEPRECATED_AGGREGATES = {
    "runtime",
}

REQUIRED_GLOBAL_EXECUTION_LAW = {
    "closed_world_execution",
    "undeclared_surface_effect",
    "runtime_admission_required",
    "replay_validity_required",
    "authority_precedes_inference",
}

REQUIRED_CANONICAL_STATUS = "CANONICAL"

REQUIRED_DEPRECATED_STATUS = (
    "DEPRECATED_AGGREGATE"
)


# ============================================================
# FAILURE
# ============================================================

class SurfaceValidationError(
    Exception
):
    pass


def fail(message: str) -> None:

    raise SurfaceValidationError(
        message
    )


# ============================================================
# LOADERS
# ============================================================

def load_yaml(
    path: Path,
) -> Dict[str, Any]:

    if not path.exists():

        fail(
            f"missing execution surface "
            f"definition: {path}"
        )

    try:

        data = yaml.safe_load(
            path.read_text(
                encoding="utf-8"
            )
        )

    except yaml.YAMLError as exc:

        fail(
            f"invalid execution surface "
            f"YAML: {exc}"
        )

    if not isinstance(
        data,
        dict,
    ):

        fail(
            "execution surface definition "
            "must be mapping"
        )

    return data


# ============================================================
# GLOBAL EXECUTION LAW
# ============================================================

def validate_global_execution_law(
    data: Dict[str, Any],
) -> None:

    law = data.get(
        "global_execution_law"
    )

    if not isinstance(
        law,
        dict,
    ):

        fail(
            "global_execution_law "
            "missing or invalid"
        )

    missing = (
        REQUIRED_GLOBAL_EXECUTION_LAW
        - set(law.keys())
    )

    if missing:

        fail(
            f"missing execution law "
            f"fields: {sorted(missing)}"
        )

    if (
        law.get(
            "closed_world_execution"
        )
        is not True
    ):

        fail(
            "closed_world_execution "
            "must be true"
        )

    if (
        law.get(
            "replay_validity_required"
        )
        is not True
    ):

        fail(
            "replay_validity_required "
            "must be true"
        )


# ============================================================
# SURFACE EXTRACTION
# ============================================================

def extract_surfaces(
    data: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:

    surfaces = data.get(
        "allowed_execution_surfaces"
    )

    if not isinstance(
        surfaces,
        dict,
    ):

        fail(
            "allowed_execution_surfaces "
            "missing or invalid"
        )

    return surfaces


# ============================================================
# STATUS VALIDATION
# ============================================================

def validate_deprecated_aggregate(
    surfaces: Dict[str, Dict[str, Any]],
) -> None:

    if "runtime" not in surfaces:

        fail(
            "deprecated aggregate "
            "'runtime' missing"
        )

    runtime_surface = (
        surfaces["runtime"]
    )

    if (
        runtime_surface.get("status")
        != REQUIRED_DEPRECATED_STATUS
    ):

        fail(
            "runtime surface must have "
            "status DEPRECATED_AGGREGATE"
        )

    replacements = runtime_surface.get(
        "canonical_replacements"
    )

    if not isinstance(
        replacements,
        list,
    ):

        fail(
            "runtime canonical_replacements "
            "must be list"
        )

    replacement_set = set(
        replacements
    )

    if replacement_set != CANONICAL_SURFACES:

        fail(
            "runtime canonical_replacements "
            "do not match canonical "
            "surface set"
        )


def validate_canonical_surfaces(
    surfaces: Dict[str, Dict[str, Any]],
) -> None:

    discovered: Set[str] = set()

    for surface_name in (
        CANONICAL_SURFACES
    ):

        if surface_name not in surfaces:

            fail(
                f"missing canonical "
                f"surface: {surface_name}"
            )

        surface = surfaces[
            surface_name
        ]

        if not isinstance(
            surface,
            dict,
        ):

            fail(
                f"surface {surface_name} "
                f"must be mapping"
            )

        status = surface.get(
            "status"
        )

        if (
            status
            != REQUIRED_CANONICAL_STATUS
        ):

            fail(
                f"surface {surface_name} "
                f"must be CANONICAL"
            )

        if surface_name in discovered:

            fail(
                f"duplicate canonical "
                f"surface: {surface_name}"
            )

        discovered.add(
            surface_name
        )


# ============================================================
# OVERLAP VALIDATION
# ============================================================

def normalize_paths(
    paths: List[str],
) -> Set[str]:

    normalized: Set[str] = set()

    for path in paths:

        cleaned = (
            str(path)
            .strip()
            .rstrip("/")
        )

        normalized.add(
            cleaned
        )

    return normalized


def validate_no_overlapping_surfaces(
    surfaces: Dict[str, Dict[str, Any]],
) -> None:

    canonical_paths: Dict[
        str,
        Set[str]
    ] = {}

    for surface_name in (
        CANONICAL_SURFACES
    ):

        surface = surfaces[
            surface_name
        ]

        paths = surface.get(
            "paths",
            [],
        )

        if not isinstance(
            paths,
            list,
        ):

            fail(
                f"surface {surface_name} "
                f"paths must be list"
            )

        canonical_paths[
            surface_name
        ] = normalize_paths(
            paths
        )

    # --------------------------------------------------------
    # overlap detection
    # --------------------------------------------------------

    names = sorted(
        canonical_paths.keys()
    )

    for i, left in enumerate(names):

        for right in names[i + 1:]:

            overlap = (
                canonical_paths[left]
                .intersection(
                    canonical_paths[right]
                )
            )

            if overlap:

                fail(
                    f"overlapping canonical "
                    f"surfaces detected "
                    f"between {left} and "
                    f"{right}: "
                    f"{sorted(overlap)}"
                )


# ============================================================
# REPLAY TOPOLOGY VALIDATION
# ============================================================

def validate_replay_safe_topology(
    surfaces: Dict[str, Dict[str, Any]],
) -> None:

    runtime_engine = surfaces.get(
        "runtime_engine",
        {},
    )

    proof = surfaces.get(
        "proof",
        {},
    )

    evaluation = surfaces.get(
        "evaluation",
        {},
    )

    # --------------------------------------------------------
    # runtime_engine
    # --------------------------------------------------------

    engine_ops = set(
        runtime_engine.get(
            "allowed_operations",
            [],
        )
    )

    if (
        "replay_binding"
        not in engine_ops
    ):

        fail(
            "runtime_engine missing "
            "replay_binding operation"
        )

    # --------------------------------------------------------
    # proof isolation
    # --------------------------------------------------------

    proof_forbidden = set(
        proof.get(
            "forbidden_operations",
            [],
        )
    )

    if (
        "runtime_execution"
        not in proof_forbidden
    ):

        fail(
            "proof surface must forbid "
            "runtime_execution"
        )

    # --------------------------------------------------------
    # evaluation isolation
    # --------------------------------------------------------

    evaluation_forbidden = set(
        evaluation.get(
            "forbidden_operations",
            [],
        )
    )

    if (
        "autonomous_mutation"
        not in evaluation_forbidden
    ):

        fail(
            "evaluation surface must "
            "forbid autonomous_mutation"
        )


# ============================================================
# UNDECLARED SURFACE VALIDATION
# ============================================================

def validate_undeclared_surfaces(
    surfaces: Dict[str, Dict[str, Any]],
) -> None:

    allowed = (
        CANONICAL_SURFACES
        .union(
            DEPRECATED_AGGREGATES
        )
        .union(
            {
                "registry",
                "epoch_state",
                "authority_profiles",
                "invariants",
                "rules",
                "execution_specs",
                "inference_request_schema",
                "truth_packet_schema",
            }
        )
    )

    discovered = set(
        surfaces.keys()
    )

    undeclared = (
        discovered - allowed
    )

    if undeclared:

        fail(
            f"undeclared execution "
            f"surfaces detected: "
            f"{sorted(undeclared)}"
        )


# ============================================================
# MAIN VALIDATION
# ============================================================

def run_validation() -> None:

    data = load_yaml(
        SURFACE_FILE
    )

    validate_global_execution_law(
        data
    )

    surfaces = extract_surfaces(
        data
    )

    validate_deprecated_aggregate(
        surfaces
    )

    validate_canonical_surfaces(
        surfaces
    )

    validate_no_overlapping_surfaces(
        surfaces
    )

    validate_replay_safe_topology(
        surfaces
    )

    validate_undeclared_surfaces(
        surfaces
    )

    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "✅ Execution surface "
        "validation passed"
    )

    print(
        "✅ Canonical surface "
        "topology verified"
    )

    print(
        "✅ No overlapping canonical "
        "surfaces detected"
    )

    print(
        "✅ No undeclared runtime "
        "surfaces detected"
    )

    print(
        "✅ Replay-safe topology "
        "verified"
    )

    print(
        "✅ Deprecated aggregate "
        "isolation verified"
    )

    print(
        "✅ Closed-world execution "
        "enforcement verified"
    )


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:

    try:

        run_validation()

        return 0

    except Exception as exc:

        print(
            f"❌ Execution surface "
            f"validation failed: {exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(main())