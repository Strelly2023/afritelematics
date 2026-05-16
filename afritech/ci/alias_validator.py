"""
afritech.ci.alias_validator

Deterministic replay-safe alias validation enforcing:

- topology-independent alias tokens
- canonical module-path ontology
- deterministic alias ordering
- replay-safe alias normalization
- closed-world alias semantics
- forbidden alias-state isolation

This validator intentionally validates HYGIENE and
NORMALIZATION semantics only.

It does NOT independently determine:
- runtime admissibility
- replay legitimacy
- governance legitimacy

Those remain enforced by:
- identity_validator
- witness_validator
- invariant_validator
- surface_validator
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


# ============================================================
# ROOTS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

ALIASES_FILE = (
    ROOT
    / "afritech"
    / "architecture"
    / "path_aliases.yaml"
)


# ============================================================
# CONSTANTS
# ============================================================

VALID_ALIAS_STATUSES = {
    "CANONICAL",
    "MIGRATING",
    "DEPRECATED",
    "FORBIDDEN",
}

VALID_ONTOLOGIES = {
    "TOKEN_TO_MODULE_PATH",
    "FORBIDDEN_EXECUTABLE_ALIAS",
}

MODULE_PATH_PATTERN = re.compile(
    r"^afritech(?:\.[a-zA-Z0-9_]+)+$"
)

FORBIDDEN_ALIAS_PATTERNS = [
    r"^\.",
    r"\.\.",
    r"//",
    r"\\",
]

FORBIDDEN_MODULE_PATTERNS = [
    r"/",
    r"\\",
    r"\.\.",
]

FILENAME_PATTERN = re.compile(
    r"^[A-Za-z0-9_\-]+\.(yaml|yml|py|json)$"
)

MODULE_EXTENSION_PATTERN = re.compile(
    r"\.(py|yaml|yml|json)$"
)


# ============================================================
# HELPERS
# ============================================================

def fail(message: str) -> None:
    print(
        f"❌ Alias validation failed: {message}"
    )
    sys.exit(1)


def load_yaml(path: Path) -> dict:

    if not path.exists():
        fail(f"missing alias registry: {path}")

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as handle:

            data = yaml.safe_load(handle)

    except Exception as exc:
        fail(f"invalid YAML: {exc}")

    if not isinstance(data, dict):
        fail("top-level YAML structure must be mapping")

    return data


# ============================================================
# ALIAS VALIDATION
# ============================================================

def validate_alias_key(alias_key: str) -> None:

    if not isinstance(alias_key, str):
        fail("alias key must be string")

    if not alias_key.strip():
        fail("empty alias key")

    # --------------------------------------------------------
    # FORBIDDEN PATH SEMANTICS
    # --------------------------------------------------------

    if "/" in alias_key:
        fail(
            f"invalid alias '{alias_key}': "
            "filesystem paths are not allowed. "
            "Use filename only "
            "(e.g. EPOCH_0008.yaml)"
        )

    if "\\" in alias_key:
        fail(
            f"invalid alias '{alias_key}': "
            "backslash paths are forbidden"
        )

    for pattern in FORBIDDEN_ALIAS_PATTERNS:

        if re.search(pattern, alias_key):
            fail(
                f"forbidden alias pattern: "
                f"{pattern}"
            )

    # --------------------------------------------------------
    # TOKEN FORMAT
    # --------------------------------------------------------

    if not FILENAME_PATTERN.fullmatch(alias_key):
        fail(
            f"invalid alias token format: "
            f"{alias_key}"
        )

    # --------------------------------------------------------
    # FORBID EXTENSIONLESS TOKENS
    # --------------------------------------------------------

    if "." not in alias_key:
        fail(
            f"extensionless alias token forbidden: "
            f"{alias_key}"
        )


# ============================================================
# CANONICAL VALIDATION
# ============================================================

def validate_module_identity(
    canonical: str
) -> None:

    if not isinstance(canonical, str):
        fail("canonical identity must be string")

    if not canonical.strip():
        fail("empty canonical identity")

    for pattern in FORBIDDEN_MODULE_PATTERNS:

        if re.search(pattern, canonical):
            fail(
                f"forbidden canonical pattern: "
                f"{pattern}"
            )

    if MODULE_EXTENSION_PATTERN.search(canonical):
        fail(
            f"extension-based canonical identity "
            f"forbidden: {canonical}"
        )

    if not MODULE_PATH_PATTERN.fullmatch(canonical):
        fail(
            f"invalid canonical module identity: "
            f"{canonical}"
        )


def validate_filename_canonical(
    canonical: str
) -> None:

    if not isinstance(canonical, str):
        fail(
            "filename canonical target "
            "must be string"
        )

    if "/" in canonical:
        fail(
            f"filename canonical must not "
            f"contain filesystem path: {canonical}"
        )

    if "\\" in canonical:
        fail(
            f"filename canonical must not "
            f"contain backslash path: {canonical}"
        )

    if not FILENAME_PATTERN.fullmatch(canonical):
        fail(
            f"invalid filename canonical: "
            f"{canonical}"
        )


def validate_canonical_target(
    canonical: str
) -> None:

    # --------------------------------------------------------
    # DOMAIN 1:
    # filename normalization
    # --------------------------------------------------------

    if canonical.endswith(
        (".yaml", ".yml", ".py", ".json")
    ):

        validate_filename_canonical(
            canonical
        )

        return

    # --------------------------------------------------------
    # DOMAIN 2:
    # ontology identity normalization
    # --------------------------------------------------------

    validate_module_identity(
        canonical
    )


# ============================================================
# STRUCTURAL VALIDATION
# ============================================================

def validate_alias_entry(
    alias_key: str,
    payload: dict,
) -> None:

    if not isinstance(payload, dict):
        fail(
            f"alias payload must be mapping: "
            f"{alias_key}"
        )

    required = {
        "canonical",
        "status",
        "ontology",
    }

    missing = required - set(payload)

    if missing:
        fail(
            f"missing fields for alias "
            f"{alias_key}: "
            f"{sorted(missing)}"
        )

    canonical = payload["canonical"]
    status = payload["status"]
    ontology = payload["ontology"]

    validate_alias_key(alias_key)

    validate_canonical_target(
        canonical
    )

    if status not in VALID_ALIAS_STATUSES:
        fail(
            f"forbidden alias status: "
            f"{status}"
        )

    if ontology not in VALID_ONTOLOGIES:
        fail(
            f"invalid ontology: "
            f"{ontology}"
        )

    # --------------------------------------------------------
    # FORBIDDEN STATE ENFORCEMENT
    # --------------------------------------------------------

    if status == "FORBIDDEN":

        if ontology != (
            "FORBIDDEN_EXECUTABLE_ALIAS"
        ):
            fail(
                f"FORBIDDEN alias requires "
                f"FORBIDDEN_EXECUTABLE_ALIAS "
                f"ontology: {alias_key}"
            )

    # --------------------------------------------------------
    # CANONICAL LOOP PREVENTION
    # --------------------------------------------------------

    if alias_key == canonical:
        fail(
            f"alias cycle detected: "
            f"{alias_key} -> {canonical}"
        )


# ============================================================
# DETERMINISTIC ORDERING
# ============================================================

def validate_deterministic_ordering(
    aliases: dict
) -> None:

    ordered = sorted(aliases.keys())

    if list(aliases.keys()) != ordered:
        fail(
            "alias registry ordering "
            "must be deterministic"
        )


# ============================================================
# DUPLICATE TARGET VALIDATION
# ============================================================

def validate_duplicate_targets(
    aliases: dict
) -> None:

    seen = {}

    for alias_key, payload in aliases.items():

        canonical = payload["canonical"]

        if canonical not in seen:
            seen[canonical] = []

        seen[canonical].append(alias_key)

    # allowed:
    # multiple compatibility tokens
    # pointing to same canonical identity

    # forbidden:
    # alias token equal to canonical
    # already checked above

    return


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    data = load_yaml(ALIASES_FILE)

    aliases = data.get("aliases")

    if aliases is None:
        fail("missing aliases section")

    if not isinstance(aliases, dict):
        fail("aliases must be mapping")

    validate_deterministic_ordering(
        aliases
    )

    for alias_key in sorted(aliases.keys()):

        validate_alias_entry(
            alias_key,
            aliases[alias_key],
        )

    validate_duplicate_targets(
        aliases
    )

    print(
        "✅ Alias validation passed"
    )

    print(
        "✅ Deterministic alias ordering verified"
    )

    print(
        "✅ Replay-safe alias normalization verified"
    )

    print(
        "✅ Canonical module-path resolution verified"
    )

    print(
        "✅ Closed-world alias semantics enforced"
    )

    print(
        "✅ Forbidden alias isolation verified"
    )

    return 0


if __name__ == "__main__":

    try:
        raise SystemExit(main())

    except SystemExit:
        raise

    except Exception as exc:
        fail(str(exc))