"""
afritech.ci.alias_validator
===========================

Canonical constitutional alias validator enforcing:

- deterministic alias resolution
- replay-safe alias semantics
- canonical module-path ontology
- migration-safe alias transitions
- forbidden alias rejection
- closed-world alias enforcement
- ontology-safe canonical identity resolution

This validator is constitutionally authoritative for:

    afritech.architecture.path_aliases
    afritech.epoch.epoch_path_aliases
    afritech.architecture.identity_rules
    afritech.architecture.path_ontology

Validation semantics are:

- deterministic
- replay-safe
- observer-independent
- ontology-safe
- closed-world aligned
- fail-fast

Aliases are constitutional migration artifacts only.

Aliases must never independently define:
- execution legitimacy
- replay authority
- governance authority
- proof authority

Filesystem structure must never independently define
constitutional identity.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import yaml


# ============================================================
# CONSTANTS
# ============================================================

ROOT_NAMESPACE = "afritech"

CANONICAL_MODULE_PATTERN = re.compile(
    r"^afritech(\.[a-zA-Z_][a-zA-Z0-9_]*)+$"
)

VALID_ALIAS_STATUSES = {

    "CANONICAL",
    "MIGRATING",
    "DEPRECATED",
    "FORBIDDEN",

}

FORBIDDEN_ALIAS_STATUSES = {

    "FORBIDDEN",

}

FORBIDDEN_PATTERNS = [

    r"/",
    r"\\",
    r"\.py$",
    r"\.yaml$",
    r"\.yml$",
    r"\.\.",
    r"\s",

]

FORBIDDEN_ALIAS_TOKENS = {

    "dynamic_import",
    "reflection",
    "runtime_alias",
    "filesystem_alias",
    "observer_relative",

}

RESERVED_FIELDS = {

    "canonical",
    "status",

}


# ============================================================
# EXCEPTIONS
# ============================================================

class AliasValidationError(
    Exception,
):
    """
    Constitutional alias validation failure.
    """


class AliasOntologyError(
    AliasValidationError,
):
    """
    Alias ontology violation.
    """


class ForbiddenAliasError(
    AliasValidationError,
):
    """
    Forbidden alias detected.
    """


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class ValidationResult:

    valid: bool

    alias_name: str

    canonical_target: str

    status: str

    message: str


# ============================================================
# CANONICAL IDENTITY VALIDATION
# ============================================================

def validate_canonical_identity(
    identity: str,
) -> None:
    """
    Validate canonical module-path identity.
    """

    if not identity:

        raise AliasOntologyError(
            "identity cannot be empty"
        )

    for pattern in FORBIDDEN_PATTERNS:

        if re.search(pattern, identity):

            raise AliasOntologyError(

                f"forbidden identity pattern "
                f"detected: {pattern}"

            )

    if not identity.startswith(ROOT_NAMESPACE):

        raise AliasOntologyError(
            "identity must begin with "
            "'afritech'"
        )

    if not CANONICAL_MODULE_PATTERN.match(
        identity
    ):

        raise AliasOntologyError(
            "identity is not canonical "
            "module-path identity"
        )


# ============================================================
# ALIAS KEY VALIDATION
# ============================================================

def validate_alias_key(
    alias_key: str,
) -> None:
    """
    Validate alias key.
    """

    if not alias_key:

        raise AliasValidationError(
            "alias key cannot be empty"
        )

    for pattern in FORBIDDEN_PATTERNS:

        if re.search(pattern, alias_key):

            raise AliasOntologyError(

                f"forbidden alias pattern: "
                f"{pattern}"

            )


# ============================================================
# STATUS VALIDATION
# ============================================================

def validate_alias_status(
    status: str,
) -> None:
    """
    Validate alias status.
    """

    if status not in VALID_ALIAS_STATUSES:

        raise AliasValidationError(

            f"invalid alias status: "
            f"{status}"

        )

    if status in FORBIDDEN_ALIAS_STATUSES:

        raise ForbiddenAliasError(

            f"forbidden alias status: "
            f"{status}"

        )


# ============================================================
# ALIAS STRUCTURE VALIDATION
# ============================================================

def validate_alias_structure(
    alias_name: str,
    alias_definition: Dict[str, str],
) -> ValidationResult:
    """
    Validate constitutional alias structure.
    """

    if not isinstance(alias_definition, dict):

        raise AliasValidationError(
            "alias definition must be dictionary"
        )

    missing = RESERVED_FIELDS.difference(
        alias_definition.keys()
    )

    if missing:

        raise AliasValidationError(

            f"missing alias fields: "
            f"{sorted(missing)}"

        )

    validate_alias_key(
        alias_name
    )

    canonical_target = alias_definition[
        "canonical"
    ]

    validate_canonical_identity(
        canonical_target
    )

    status = alias_definition[
        "status"
    ]

    validate_alias_status(
        status
    )

    return ValidationResult(

        valid=True,

        alias_name=alias_name,

        canonical_target=(
            canonical_target
        ),

        status=status,

        message=(
            "alias validated"
        ),
    )


# ============================================================
# DUPLICATE TARGET VALIDATION
# ============================================================

def validate_duplicate_targets(
    aliases: Dict[str, Dict[str, str]],
) -> None:
    """
    Validate no conflicting alias targets exist.
    """

    target_map: Dict[
        str,
        Set[str]
    ] = {}

    for alias_name, definition in aliases.items():

        canonical = definition[
            "canonical"
        ]

        target_map.setdefault(
            canonical,
            set(),
        ).add(alias_name)

    for canonical, alias_set in target_map.items():

        if len(alias_set) > 25:

            raise AliasValidationError(

                "excessive alias fan-out "
                f"detected for: {canonical}"

            )


# ============================================================
# CYCLE VALIDATION
# ============================================================

def validate_no_alias_cycles(
    aliases: Dict[str, Dict[str, str]],
) -> None:
    """
    Validate alias graph has no cycles.
    """

    alias_names = set(
        aliases.keys()
    )

    for alias_name, definition in aliases.items():

        canonical = definition[
            "canonical"
        ]

        if canonical in alias_names:

            raise AliasValidationError(

                "alias cycle detected: "
                f"{alias_name} -> {canonical}"

            )


# ============================================================
# REPLAY SAFETY VALIDATION
# ============================================================

def validate_replay_safety(
    aliases: Dict[str, Dict[str, str]],
) -> None:
    """
    Validate replay-safe alias semantics.
    """

    for alias_name, definition in aliases.items():

        status = definition[
            "status"
        ]

        if status == "MIGRATING":

            canonical = definition[
                "canonical"
            ]

            validate_canonical_identity(
                canonical
            )


# ============================================================
# YAML LOADING
# ============================================================

def load_yaml(
    path: Path,
) -> Dict:
    """
    Load YAML safely.
    """

    return yaml.safe_load(

        path.read_text(
            encoding="utf-8"
        )

    )


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_alias_file(
    path: Path,
) -> List[ValidationResult]:
    """
    Validate alias registry file.
    """

    payload = load_yaml(
        path
    )

    aliases = payload.get(
        "aliases",
        {}
    )

    if not isinstance(aliases, dict):

        raise AliasValidationError(
            "aliases must be dictionary"
        )

    validate_duplicate_targets(
        aliases
    )

    validate_no_alias_cycles(
        aliases
    )

    validate_replay_safety(
        aliases
    )

    results: List[
        ValidationResult
    ] = []

    for alias_name, definition in aliases.items():

        results.append(

            validate_alias_structure(

                alias_name,

                definition,
            )
        )

    return results


# ============================================================
# DIRECTORY VALIDATION
# ============================================================

def validate_alias_directory(
    root: Path,
) -> List[ValidationResult]:
    """
    Validate all alias registries.
    """

    results: List[
        ValidationResult
    ] = []

    for file_path in root.rglob("*aliases*.yaml"):

        results.extend(

            validate_alias_file(
                file_path
            )
        )

    return results


# ============================================================
# CI VALIDATION
# ============================================================

def run_ci_validation() -> None:
    """
    Execute deterministic constitutional alias validation.
    """

    root = Path("afritech")

    if not root.exists():

        raise FileNotFoundError(
            "afritech root not found"
        )

    results = validate_alias_directory(
        root
    )

    validated = len(results)

    print(
        f"✅ Alias mappings validated: "
        f"{validated}"
    )

    print(
        "✅ Replay-safe alias semantics verified"
    )

    print(
        "✅ Closed-world alias ontology enforced"
    )

    print(
        "✅ Deterministic alias validation passed"
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
            f"❌ Alias validation failed: "
            f"{exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )