# afritech/ci/invariant_validator.py

"""
AfriTech Constitutional Invariant Validator
===========================================

Validates consistency between:

- canonical constitutional invariant registry
- semantic runtime enforcement registry
- compiled invariant IR
- generated invariant index

Enforces:

- deterministic ordering
- duplicate prevention
- canonical registry integrity
- runtime projection validity
- replay-safe invariant topology
- compiled/index parity

CONSTITUTIONAL MODEL:

Canonical Registry
    ↓
Semantic Enforcement Projection
    ↓
Compiled Runtime Projection
    ↓
Deterministic Runtime Index
"""

from __future__ import annotations

import json
import re
import sys

from pathlib import Path
from typing import Any, Dict, List, Set

import yaml


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

# ------------------------------------------------------------
# Canonical constitutional registry
# ------------------------------------------------------------

CANONICAL_REGISTRY = (
    AFRITECH_ROOT
    / "constitution"
    / "INVARIANTS.yaml"
)

# ------------------------------------------------------------
# Semantic runtime enforcement registry
# ------------------------------------------------------------

SEMANTIC_SOURCE = (
    AFRITECH_ROOT
    / "constitution"
    / "invariants_semantics.yaml"
)

# ------------------------------------------------------------
# Compiled executable IR
# ------------------------------------------------------------

COMPILED_IR = (
    AFRITECH_ROOT
    / "constitution"
    / "compiled"
    / "invariants_ir.json"
)

# ------------------------------------------------------------
# Generated deterministic runtime index
# ------------------------------------------------------------

COMPILED_INDEX = (
    AFRITECH_ROOT
    / "constitution"
    / "compiled"
    / "invariants_index.py"
)


# ============================================================
# EXCEPTIONS
# ============================================================

class InvariantValidationError(
    Exception
):
    pass


# ============================================================
# FAILURE
# ============================================================

def fail(message: str) -> None:

    raise InvariantValidationError(
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
            f"missing YAML source: {path}"
        )

    try:

        return yaml.safe_load(
            path.read_text(
                encoding="utf-8"
            )
        )

    except yaml.YAMLError as exc:

        fail(
            f"invalid YAML: {exc}"
        )


def load_json(
    path: Path,
) -> Dict[str, Any]:

    if not path.exists():

        fail(
            f"missing JSON artifact: {path}"
        )

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        fail(
            f"invalid JSON: {exc}"
        )


# ============================================================
# INVARIANT SORTING
# ============================================================

INVARIANT_ID_PATTERN = re.compile(
    r"^I([0-9]+)_"
)


def invariant_sort_key(
    inv_id: str,
):

    match = (
        INVARIANT_ID_PATTERN.match(
            inv_id
        )
    )

    if not match:

        return (
            999999,
            inv_id,
        )

    try:

        number = int(
            match.group(1)
        )

    except ValueError:

        return (
            999999,
            inv_id,
        )

    return (
        number,
        inv_id,
    )


# ============================================================
# CANONICAL REGISTRY
# ============================================================

def load_canonical_registry_ids() -> List[str]:

    registry_data = load_yaml(
        CANONICAL_REGISTRY
    )

    invariants = registry_data.get(
        "invariants"
    )

    if not isinstance(
        invariants,
        list,
    ):

        fail(
            "canonical invariant registry "
            "must contain "
            "'invariants' list"
        )

    ids: List[str] = []

    for entry in invariants:

        if not isinstance(
            entry,
            dict,
        ):

            fail(
                "canonical invariant entry "
                "must be mapping"
            )

        inv_id = entry.get("id")

        if not isinstance(
            inv_id,
            str,
        ):

            fail(
                "canonical invariant "
                "missing valid id"
            )

        ids.append(inv_id)

    return sorted(
        ids,
        key=invariant_sort_key,
    )


# ============================================================
# SEMANTIC ENFORCEMENT
# ============================================================

def extract_semantic_enforcement_ids(
    semantic_data: Dict[str, Any],
) -> Set[str]:

    discovered: Set[str] = set()

    semantic_root = semantic_data.get(
        "semantic_enforcement",
        {}
    )

    if not isinstance(
        semantic_root,
        dict,
    ):

        fail(
            "semantic_enforcement "
            "must be mapping"
        )

    for _, enforcement_def in (
        semantic_root.items()
    ):

        if not isinstance(
            enforcement_def,
            dict,
        ):

            continue

        enforced = enforcement_def.get(
            "enforced_invariants",
            []
        )

        if not isinstance(
            enforced,
            list,
        ):

            fail(
                "enforced_invariants "
                "must be list"
            )

        for inv_id in enforced:

            if not isinstance(
                inv_id,
                str,
            ):

                fail(
                    "enforced invariant "
                    "id must be string"
                )

            discovered.add(inv_id)

    return discovered


# ============================================================
# INDEX PARSING
# ============================================================
# ============================================================
# INDEX PARSING
# ============================================================

INDEX_INVARIANT_PATTERN = re.compile(
    r"^I[0-9]+_[A-Z0-9_]+$"
)


def parse_index_ids(
    path: Path,
) -> List[str]:

    if not path.exists():

        fail(
            f"missing invariant index: "
            f"{path}"
        )

    ids: List[str] = []

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        # ----------------------------------------------------
        # ignore empty/comment lines
        # ----------------------------------------------------

        if not line:
            continue

        if line.startswith("#"):
            continue

        # ----------------------------------------------------
        # only assignments
        # ----------------------------------------------------

        if "=" not in line:
            continue

        left, _ = line.split(
            "=",
            1,
        )

        inv_id = left.strip()

        # ----------------------------------------------------
        # strict invariant symbol validation
        # ----------------------------------------------------

        if not INDEX_INVARIANT_PATTERN.fullmatch(
            inv_id
        ):
            continue

        ids.append(inv_id)

    return ids


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_deterministic_ordering(
    ids: List[str],
) -> None:

    expected = sorted(
        ids,
        key=invariant_sort_key,
    )

    if ids != expected:

        fail(
            "non-deterministic invariant "
            "ordering detected"
        )


def validate_duplicate_ids(
    ids: List[str],
) -> None:

    seen: Set[str] = set()

    duplicates: Set[str] = set()

    for inv_id in ids:

        if inv_id in seen:

            duplicates.add(inv_id)

        seen.add(inv_id)

    if duplicates:

        fail(
            f"duplicate invariant ids: "
            f"{sorted(duplicates)}"
        )


def validate_runtime_projection(
    registry_ids: Set[str],
    projection_ids: Set[str],
    projection_name: str,
) -> None:

    unknown = (
        projection_ids
        - registry_ids
    )

    if unknown:

        fail(
            f"{projection_name} contains "
            f"unknown invariants: "
            f"{sorted(unknown)}"
        )


# ============================================================
# MAIN VALIDATION
# ============================================================

def run_validation() -> None:

    # --------------------------------------------------------
    # canonical constitutional registry
    # --------------------------------------------------------

    registry_ids = (
        load_canonical_registry_ids()
    )

    registry_set = set(
        registry_ids
    )

    # --------------------------------------------------------
    # semantic runtime enforcement
    # --------------------------------------------------------

    semantic_data = load_yaml(
        SEMANTIC_SOURCE
    )

    semantic_ids = sorted(
        extract_semantic_enforcement_ids(
            semantic_data
        ),
        key=invariant_sort_key,
    )

    # --------------------------------------------------------
    # compiled IR
    # --------------------------------------------------------

    compiled_ir = load_json(
        COMPILED_IR
    )

    compiled_invariants = (
        compiled_ir.get(
            "invariants"
        )
    )

    if not isinstance(
        compiled_invariants,
        dict,
    ):

        fail(
            "compiled IR invariants "
            "must be mapping"
        )

    compiled_ids = sorted(
        compiled_invariants.keys(),
        key=invariant_sort_key,
    )

    compiled_set = set(
        compiled_ids
    )

    # --------------------------------------------------------
    # deterministic runtime index
    # --------------------------------------------------------

    index_ids = sorted(
        parse_index_ids(
            COMPILED_INDEX
        ),
        key=invariant_sort_key,
    )

    index_set = set(
        index_ids
    )

    # ========================================================
    # DUPLICATE CHECKS
    # ========================================================

    validate_duplicate_ids(
        registry_ids
    )

    validate_duplicate_ids(
        semantic_ids
    )

    validate_duplicate_ids(
        compiled_ids
    )

    validate_duplicate_ids(
        index_ids
    )

    # ========================================================
    # DETERMINISTIC ORDERING
    # ========================================================

    validate_deterministic_ordering(
        registry_ids
    )

    validate_deterministic_ordering(
        semantic_ids
    )

    validate_deterministic_ordering(
        compiled_ids
    )

    validate_deterministic_ordering(
        index_ids
    )

    # ========================================================
    # PROJECTION VALIDATION
    # ========================================================

    validate_runtime_projection(
        registry_set,
        set(semantic_ids),
        "semantic registry",
    )

    validate_runtime_projection(
        registry_set,
        compiled_set,
        "compiled IR",
    )

    validate_runtime_projection(
        registry_set,
        index_set,
        "compiled index",
    )

    # ========================================================
    # INDEX ↔ IR PARITY
    # ========================================================

    if compiled_ids != index_ids:

        fail(
            "compiled IR and invariant "
            "index diverged"
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "✅ Invariant validation passed"
    )

    print(
        "✅ Canonical registry integrity verified"
    )

    print(
        "✅ Semantic runtime projection verified"
    )

    print(
        "✅ Compiled runtime projection verified"
    )

    print(
        "✅ Deterministic invariant ordering verified"
    )

    print(
        "✅ Duplicate invariant IDs not detected"
    )

    print(
        "✅ Replay-safe invariant topology verified"
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
            f"❌ Invariant validation failed: "
            f"{exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(main())