"""
Shared Invariant Evaluation Logic
=================================

Pure invariant evaluation layer.

This module MUST remain completely isolated from:

- runtime engine
- execution orchestration
- guards
- replay verifier
- infrastructure layers

Constitutional guarantees:

- deterministic execution
- replay-safe evaluation
- pure functional semantics
- no side effects
- stable canonical serialization
"""

from __future__ import annotations

import json

from typing import Any, Mapping


# ============================================================
# EXCEPTIONS
# ============================================================

class InvariantEvaluationError(
    Exception
):
    """
    Raised when invariant evaluation
    cannot be performed safely.
    """
    pass


# ============================================================
# CANONICALIZATION
# ============================================================

def canonicalize(
    data: Any,
) -> str:
    """
    Deterministic replay-safe serialization.

    Guarantees:

    - stable ordering
    - deterministic hashing input
    - canonical structural comparison
    """

    try:

        return json.dumps(

            data,

            sort_keys=True,

            separators=(
                ",",
                ":",
            ),

            ensure_ascii=False,

        )

    except Exception as exc:

        raise InvariantEvaluationError(

            "non_serializable_input"

        ) from exc


# ============================================================
# STRUCTURE VALIDATION
# ============================================================

def validate_structure(
    data: Any,
) -> None:
    """
    Closed-world structural validation.
    """

    if data is None:

        raise InvariantEvaluationError(
            "null_input_forbidden"
        )

    if not isinstance(
        data,
        (
            dict,
            Mapping,
        ),
    ):

        raise InvariantEvaluationError(
            "mapping_required"
        )

    if not data:

        raise InvariantEvaluationError(
            "empty_mapping_forbidden"
        )


# ============================================================
# PURE EVALUATION
# ============================================================

def evaluate_invariant(
    data: Any,
) -> bool:
    """
    Pure replay-safe invariant evaluation.

    Constitutional guarantees:

    - deterministic
    - side-effect free
    - runtime isolated
    - replay stable
    - canonicalizable

    Returns:
        bool

    Raises:
        InvariantEvaluationError
    """

    # --------------------------------------------------------
    # structural validation
    # --------------------------------------------------------

    validate_structure(
        data
    )

    # --------------------------------------------------------
    # deterministic canonicalization
    # --------------------------------------------------------

    canonical = canonicalize(
        data
    )

    # --------------------------------------------------------
    # semantic evaluation
    # --------------------------------------------------------

    # Placeholder deterministic rule:
    # canonical representation must exist
    # and be non-empty.

    if not canonical:

        return False

    # --------------------------------------------------------
    # replay-safe acceptance
    # --------------------------------------------------------

    return True


# ============================================================
# EXPORTS
# ============================================================

__all__ = [

    "InvariantEvaluationError",

    "canonicalize",

    "validate_structure",

    "evaluate_invariant",
]