"""
afritech.ci.witness_validator
=============================

Canonical deterministic witness validation subsystem.

Enforces:

- replay-safe witness admissibility
- canonical identity ontology
- deterministic witness topology
- closed-world witness semantics
- bundle integrity
- constitutional receipt validation
- deterministic mutation trace validation
- deterministic transcript trace validation

This validator is:

- deterministic
- replay-safe
- observer-independent
- ontology-safe
- closed-world aligned
- fail-fast
"""

from __future__ import annotations

import json
import sys

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_HASH_ALGORITHM = "sha256"

CANONICAL_WITNESS_TYPES = {
    "REPLAY",
    "EXECUTION",
    "TRANSCRIPT",
    "MUTATION",
    "BUNDLE",
}

REQUIRED_WITNESS_FLAGS = {
    "deterministic",
    "replay_safe",
    "closed_world_aligned",
    "observer_independent",
}

REQUIRED_HASH_FIELDS = {
    "witness_hash",
}

REQUIRED_RECEIPT_FIELDS = {
    "receipt_hash",
    "execution_surface_hash",
    "surface_validation_hash",
}

FORBIDDEN_METADATA_FIELDS = {
    "observer",
    "local_path",
    "filesystem_path",
    "runtime_alias",
    "dynamic_reference",
}

ADMISSIBLE_IMPLEMENTATION_STATES = {
    "PARTIAL",
    "IMPLEMENTED",
}

FORBIDDEN_IMPLEMENTATION_STATES = {
    "PLANNED",
    "DOCUMENTARY",
    "FORBIDDEN_ALIAS",
}

VALID_JSON_ARTIFACTS = {
    "replay_witness.json",
    "execution_witness.json",
    "mutation_witness.json",
    "transcript_witness.json",
    "witness_bundle.json",
    "constitutional_receipt.json",
}

WITNESS_MAPPING = {
    "afritech.proof.witness.replay_witness":
        "REPLAY",

    "afritech.proof.witness.execution_witness":
        "EXECUTION",

    "afritech.proof.witness.transcript_witness":
        "TRANSCRIPT",

    "afritech.proof.witness.mutation_witness":
        "MUTATION",

    "afritech.proof.witness.witness_bundle":
        "BUNDLE",
}


# ============================================================
# EXCEPTIONS
# ============================================================

class WitnessValidationError(Exception):
    pass


class WitnessOntologyError(
    WitnessValidationError
):
    pass


class ReplayViolationError(
    WitnessValidationError
):
    pass


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class ValidationResult:

    valid: bool
    witness_identity: str
    witness_type: str
    implementation_state: str
    message: str


# ============================================================
# HASHING
# ============================================================

def stable_hash(payload: Any) -> str:
    """
    Deterministic hashing.
    """

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


def compute_witness_hash(
    payload: Dict[str, Any],
) -> str:
    """
    Compute witness hash while excluding
    self-referential witness_hash field.
    """

    payload_copy = dict(payload)

    payload_copy.pop(
        "witness_hash",
        None,
    )

    return stable_hash(payload_copy)


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_required_fields(
    payload: Dict[str, Any],
    required_fields: Set[str],
) -> None:

    missing = required_fields.difference(
        payload.keys()
    )

    if missing:

        raise WitnessValidationError(
            f"missing required fields: "
            f"{sorted(missing)}"
        )


def validate_canonical_identity(
    identity: Any,
    file_path: Path,
) -> str:

    if identity is None:

        raise WitnessValidationError(
            f"missing canonical_identity "
            f"in {file_path}"
        )

    if (
        not isinstance(identity, str)
        or not identity.strip()
    ):

        raise WitnessOntologyError(
            "invalid canonical identity"
        )

    identity = identity.strip()

    if not identity.startswith("afritech."):

        raise WitnessOntologyError(
            f"non-canonical identity: "
            f"{identity}"
        )

    if "/" in identity:

        raise WitnessOntologyError(
            "filesystem identity forbidden"
        )

    if identity.endswith(".py"):

        raise WitnessOntologyError(
            "extension identity forbidden"
        )

    return identity


def validate_implementation_state(
    state: Any,
    file_path: Path,
) -> None:

    if not isinstance(state, str):

        raise WitnessValidationError(
            f"invalid implementation state "
            f"in {file_path}"
        )

    if state in FORBIDDEN_IMPLEMENTATION_STATES:

        raise WitnessValidationError(
            f"forbidden implementation state: "
            f"{state}"
        )

    if state not in (
        ADMISSIBLE_IMPLEMENTATION_STATES
    ):

        raise WitnessValidationError(
            f"non-admissible implementation "
            f"state: {state}"
        )


def validate_replay_flags(
    payload: Dict[str, Any],
) -> None:

    for field in REQUIRED_WITNESS_FLAGS:

        if payload.get(field) is not True:

            raise ReplayViolationError(
                f"invalid replay flag: "
                f"{field}"
            )


def validate_metadata(
    payload: Dict[str, Any],
) -> None:

    forbidden = (
        FORBIDDEN_METADATA_FIELDS
        .intersection(payload.keys())
    )

    if forbidden:

        raise WitnessOntologyError(
            f"forbidden metadata fields: "
            f"{sorted(forbidden)}"
        )


def validate_hash_fields(
    payload: Dict[str, Any],
) -> None:

    validate_required_fields(
        payload,
        REQUIRED_HASH_FIELDS,
    )

    if (
        payload.get("hash_algorithm")
        != SUPPORTED_HASH_ALGORITHM
    ):

        raise WitnessValidationError(
            "unsupported hash algorithm"
        )

    expected_hash = compute_witness_hash(
        payload
    )

    if payload["witness_hash"] != expected_hash:

        raise WitnessValidationError(
            "witness hash mismatch"
        )


def validate_witness_type(
    witness_type: str,
) -> None:

    if witness_type not in (
        CANONICAL_WITNESS_TYPES
    ):

        raise WitnessOntologyError(
            f"invalid witness type: "
            f"{witness_type}"
        )


# ============================================================
# VALIDATION ROUTES
# ============================================================

def validate_constitutional_receipt(
    payload: Dict[str, Any],
) -> ValidationResult:

    validate_required_fields(
        payload,
        REQUIRED_RECEIPT_FIELDS,
    )

    validate_replay_flags(payload)
    validate_metadata(payload)

    return ValidationResult(
        True,
        "afritech.proof.constitutional_receipt",
        "RECEIPT",
        payload["implementation_state"],
        "constitutional receipt validated",
    )


def validate_witness(
    payload: Dict[str, Any],
    witness_type: str,
) -> ValidationResult:

    validate_witness_type(
        witness_type
    )

    validate_replay_flags(payload)
    validate_metadata(payload)
    validate_hash_fields(payload)

    return ValidationResult(
        True,
        payload["canonical_identity"],
        witness_type,
        payload["implementation_state"],
        "witness validated",
    )


def validate_bundle(
    payload: Dict[str, Any],
) -> ValidationResult:

    validate_required_fields(
        payload,
        {
            "bundle_hash",
            "references",
            "replay_hash",
            "execution_trace_hash",
        },
    )

    validate_replay_flags(payload)
    validate_metadata(payload)

    references = payload["references"]

    if (
        not isinstance(references, list)
        or not references
    ):

        raise WitnessValidationError(
            "invalid bundle references"
        )

    for ref in references:

        validate_required_fields(
            ref,
            {
                "canonical_identity",
                "witness_hash",
                "witness_type",
            },
        )

        validate_canonical_identity(
            ref["canonical_identity"],
            Path("bundle"),
        )

        validate_witness_type(
            ref["witness_type"]
        )

    return ValidationResult(
        True,
        "afritech.proof.witness.witness_bundle",
        "BUNDLE",
        payload["implementation_state"],
        "bundle validated",
    )


# ============================================================
# MUTATION TRACE VALIDATION
# ============================================================

def validate_mutation_trace(
    payload: Any,
) -> ValidationResult:
    """
    Validate deterministic replay mutation trace.
    """

    if not isinstance(payload, list):

        raise WitnessValidationError(
            "mutation witness must be a list"
        )

    if not payload:

        raise WitnessValidationError(
            "empty mutation trace"
        )

    previous_order = -1

    for index, step in enumerate(payload):

        if not isinstance(step, dict):

            raise WitnessValidationError(
                f"invalid mutation step "
                f"at {index}"
            )

        order = step.get("order")

        if not isinstance(order, int):

            raise WitnessValidationError(
                f"invalid mutation order "
                f"at {index}"
            )

        if order <= previous_order:

            raise ReplayViolationError(
                "non-deterministic mutation "
                "ordering"
            )

        required_fields = {
            "mutation_type",
            "target",
            "action",
            "deterministic",
        }

        missing = (
            required_fields
            .difference(step.keys())
        )

        if missing:

            raise WitnessValidationError(
                f"missing mutation fields: "
                f"{sorted(missing)}"
            )

        if step["deterministic"] is not True:

            raise ReplayViolationError(
                "non-deterministic mutation step"
            )

        previous_order = order

    return ValidationResult(
        True,
        "afritech.proof.witness.mutation_witness",
        "MUTATION",
        "IMPLEMENTED",
        "mutation trace validated",
    )


# ============================================================
# TRANSCRIPT TRACE VALIDATION
# ============================================================

def validate_transcript_trace(
    payload: Any,
) -> ValidationResult:
    """
    Validate deterministic replay transcript trace.
    """

    if not isinstance(payload, list):

        raise WitnessValidationError(
            "transcript witness must be a list"
        )

    if not payload:

        raise WitnessValidationError(
            "empty transcript trace"
        )

    previous_order = -1

    for index, step in enumerate(payload):

        if not isinstance(step, dict):

            raise WitnessValidationError(
                f"invalid transcript step "
                f"at {index}"
            )

        order = step.get("order")

        if not isinstance(order, int):

            raise WitnessValidationError(
                f"invalid transcript order "
                f"at {index}"
            )

        if order <= previous_order:

            raise ReplayViolationError(
                "non-deterministic transcript "
                "ordering"
            )

        if "event" not in step:

            raise WitnessValidationError(
                "missing transcript event"
            )

        if step.get("deterministic") is not True:

            raise ReplayViolationError(
                "non-deterministic transcript step"
            )

        previous_order = order

    return ValidationResult(
        True,
        "afritech.proof.witness.transcript_witness",
        "TRANSCRIPT",
        "IMPLEMENTED",
        "transcript trace validated",
    )


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_json_file(
    file_path: Path,
) -> Optional[ValidationResult]:

    # ========================================================
    # FILTER BEFORE LOAD
    # ========================================================

    if file_path.name not in (
        VALID_JSON_ARTIFACTS
    ):

        return None

    try:

        payload = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        raise WitnessValidationError(
            f"invalid json artifact: "
            f"{file_path}"
        ) from exc

    # ========================================================
    # TRACE-BASED WITNESSES
    # ========================================================

    if file_path.name == "mutation_witness.json":

        return validate_mutation_trace(
            payload
        )

    if file_path.name == "transcript_witness.json":

        return validate_transcript_trace(
            payload
        )

    # ========================================================
    # ALL OTHER ARTIFACTS MUST BE DICTS
    # ========================================================

    if not isinstance(payload, dict):

        raise WitnessValidationError(
            f"invalid payload structure "
            f"in {file_path}"
        )

    # ========================================================
    # SCHEMA VALIDATION
    # ========================================================

    if payload.get("schema_version") != 1:

        raise WitnessValidationError(
            f"invalid schema version in "
            f"{file_path}: "
            f"{payload.get('schema_version')}"
        )

    # ========================================================
    # CANONICAL IDENTITY
    # ========================================================

    canonical_identity = (
        validate_canonical_identity(
            payload.get(
                "canonical_identity"
            ),
            file_path,
        )
    )

    # ========================================================
    # IMPLEMENTATION STATE
    # ========================================================

    validate_implementation_state(
        payload.get(
            "implementation_state"
        ),
        file_path,
    )

    # ========================================================
    # CONSTITUTIONAL RECEIPT
    # ========================================================

    if (
        canonical_identity
        == "afritech.proof.constitutional_receipt"
    ):

        return validate_constitutional_receipt(
            payload
        )

    # ========================================================
    # UNKNOWN IDENTITY
    # ========================================================

    if canonical_identity not in (
        WITNESS_MAPPING
    ):

        raise WitnessOntologyError(
            f"unknown canonical identity: "
            f"{canonical_identity}"
        )

    witness_type = WITNESS_MAPPING[
        canonical_identity
    ]

    # ========================================================
    # BUNDLE VALIDATION
    # ========================================================

    if witness_type == "BUNDLE":

        return validate_bundle(
            payload
        )

    # ========================================================
    # STANDARD WITNESS VALIDATION
    # ========================================================

    return validate_witness(
        payload,
        witness_type,
    )


# ============================================================
# DIRECTORY VALIDATION
# ============================================================

def validate_witness_directory(
    root: Path,
) -> List[ValidationResult]:

    results: List[
        ValidationResult
    ] = []

    identities: Set[str] = set()

    for file_path in sorted(
        root.rglob("*.json")
    ):

        if "__pycache__" in file_path.parts:
            continue

        if file_path.name.startswith("."):
            continue

        if file_path.name not in (
            VALID_JSON_ARTIFACTS
        ):
            continue

        result = validate_json_file(
            file_path
        )

        if result is None:
            continue

        if (
            result.witness_identity
            in identities
        ):

            raise WitnessOntologyError(
                f"duplicate witness identity: "
                f"{result.witness_identity}"
            )

        identities.add(
            result.witness_identity
        )

        results.append(result)

    return results


# ============================================================
# CI VALIDATION
# ============================================================

def run_ci_validation() -> None:

    root = Path("afritech/proof")

    if not root.exists():

        raise FileNotFoundError(
            "proof directory not found"
        )

    results = validate_witness_directory(
        root
    )

    validated = len(results)

    expected = len(
        VALID_JSON_ARTIFACTS
    )

    if validated != expected:

        raise WitnessValidationError(
            f"artifact count mismatch: "
            f"{validated} != {expected}"
        )

    print(
        f"✅ Witness artifacts validated: "
        f"{validated}"
    )

    print(
        "✅ Replay admissibility verified"
    )

    print(
        "✅ Closed-world witness semantics "
        "enforced"
    )

    print(
        "✅ Deterministic witness validation "
        "passed"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:

        run_ci_validation()

        return 0

    except Exception as exc:

        print(
            f"❌ Witness validation failed: "
            f"{exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(main())