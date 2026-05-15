from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

import yaml


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PATH_ONTOLOGY_PATH = (
    PROJECT_ROOT
    / "afritech"
    / "architecture"
    / "PATH_ONTOLOGY.yaml"
)

IMPLEMENTATION_REGISTRY_PATH = (
    PROJECT_ROOT
    / "afritech"
    / "architecture"
    / "implementation_registry.yaml"
)

ENFORCEMENT_MATRIX_PATH = (
    PROJECT_ROOT
    / "afritech"
    / "architecture"
    / "enforcement_matrix.yaml"
)


# ============================================================
# CANONICAL REGEX
# ============================================================

MODULE_PATH_PATTERN = re.compile(
    r"^afritech(\.[a-zA-Z0-9_]+)+$"
)

FILESYSTEM_PATH_PATTERN = re.compile(
    r"^afritech(/[a-zA-Z0-9_]+)+(\.py|\.yaml|\.json)?$"
)


# ============================================================
# VALIDATION RESULT
# ============================================================

class ValidationViolation:

    def __init__(
        self,
        category: str,
        file_path: Path,
        message: str,
    ) -> None:

        self.category = category
        self.file_path = file_path
        self.message = message

    def __str__(self) -> str:

        return (
            f"[{self.category}] "
            f"{self.file_path}: "
            f"{self.message}"
        )


# ============================================================
# YAML LOADING
# ============================================================

def load_yaml(
    path: Path,
) -> Optional[dict]:

    if not path.exists():
        return None

    try:

        raw = path.read_text(
            encoding="utf-8"
        )

        data = yaml.safe_load(raw)

        if isinstance(data, dict):
            return data

    except Exception:
        return None

    return None


# ============================================================
# PATH CLASSIFICATION
# ============================================================

def is_module_path(
    value: str,
) -> bool:

    return bool(
        MODULE_PATH_PATTERN.match(value)
    )


def is_filesystem_path(
    value: str,
) -> bool:

    return bool(
        FILESYSTEM_PATH_PATTERN.match(value)
    )


# ============================================================
# MODULE PATH NORMALIZATION
# ============================================================

def normalize_filesystem_to_module(
    path: str,
) -> str:

    normalized = path

    if normalized.endswith(".py"):
        normalized = normalized[:-3]

    if normalized.endswith(".yaml"):
        normalized = normalized[:-5]

    if normalized.endswith(".json"):
        normalized = normalized[:-5]

    normalized = normalized.replace("/", ".")

    return normalized


# ============================================================
# PATH VALIDATION
# ============================================================

def validate_identity_form(
    value: str,
    expected: str,
    file_path: Path,
) -> List[ValidationViolation]:

    violations: List[ValidationViolation] = []

    # --------------------------------------------------------
    # MODULE PATH EXPECTED
    # --------------------------------------------------------

    if expected == "module_path":

        if is_filesystem_path(value):

            violations.append(
                ValidationViolation(
                    category="PATH_ONTOLOGY",
                    file_path=file_path,
                    message=(
                        "filesystem path used where "
                        "canonical module path required: "
                        f"{value}"
                    ),
                )
            )

        elif not is_module_path(value):

            violations.append(
                ValidationViolation(
                    category="PATH_ONTOLOGY",
                    file_path=file_path,
                    message=(
                        "invalid canonical module path: "
                        f"{value}"
                    ),
                )
            )

    # --------------------------------------------------------
    # FILESYSTEM PATH EXPECTED
    # --------------------------------------------------------

    elif expected == "filesystem_path":

        if is_module_path(value):

            violations.append(
                ValidationViolation(
                    category="PATH_ONTOLOGY",
                    file_path=file_path,
                    message=(
                        "module path used where "
                        "filesystem path required: "
                        f"{value}"
                    ),
                )
            )

        elif not is_filesystem_path(value):

            violations.append(
                ValidationViolation(
                    category="PATH_ONTOLOGY",
                    file_path=file_path,
                    message=(
                        "invalid filesystem path: "
                        f"{value}"
                    ),
                )
            )

    return violations


# ============================================================
# IMPLEMENTATION REGISTRY VALIDATION
# ============================================================

def validate_implementation_registry(
    path: Path,
) -> List[ValidationViolation]:

    violations: List[ValidationViolation] = []

    data = load_yaml(path)

    if not data:
        return violations

    surfaces = data.get("surfaces", {})

    if not isinstance(surfaces, dict):
        return violations

    for surface in surfaces.keys():

        violations.extend(
            validate_identity_form(
                value=surface,
                expected="module_path",
                file_path=path,
            )
        )

    return violations


# ============================================================
# ENFORCEMENT MATRIX VALIDATION
# ============================================================

def validate_enforcement_matrix(
    path: Path,
) -> List[ValidationViolation]:

    violations: List[ValidationViolation] = []

    data = load_yaml(path)

    if not data:
        return violations

    enforcement = data.get("enforcement", {})

    if not isinstance(enforcement, dict):
        return violations

    for surface in enforcement.keys():

        if "." not in surface:
            continue

        violations.extend(
            validate_identity_form(
                value=surface,
                expected="module_path",
                file_path=path,
            )
        )

    return violations


# ============================================================
# GENERIC YAML WALKER
# ============================================================

def collect_strings(
    value,
    results: List[str],
) -> None:

    if isinstance(value, str):

        results.append(value)

    elif isinstance(value, dict):

        for child in value.values():
            collect_strings(child, results)

    elif isinstance(value, list):

        for child in value:
            collect_strings(child, results)


# ============================================================
# GLOBAL PATH ONTOLOGY VALIDATION
# ============================================================

def validate_yaml_file(
    path: Path,
) -> List[ValidationViolation]:

    violations: List[ValidationViolation] = []

    data = load_yaml(path)

    if not data:
        return violations

    strings: List[str] = []

    collect_strings(data, strings)

    for value in strings:

        # ----------------------------------------------------
        # FORBIDDEN FILESYSTEM PATHS
        # ----------------------------------------------------

        if is_filesystem_path(value):

            # allow only inside explicit hashing contexts
            allowed_contexts = (
                "manifest",
                "hash",
                "artifact",
                "filesystem_path",
            )

            serialized = str(data)

            if not any(
                token in serialized
                for token in allowed_contexts
            ):

                violations.append(
                    ValidationViolation(
                        category="PATH_ONTOLOGY",
                        file_path=path,
                        message=(
                            "filesystem identity detected "
                            "outside approved context: "
                            f"{value}"
                        ),
                    )
                )

    return violations


# ============================================================
# FILE DISCOVERY
# ============================================================

def discover_yaml_files() -> List[Path]:

    return sorted(
        (
            PROJECT_ROOT / "afritech"
        ).rglob("*.yaml")
    )


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_repository() -> List[ValidationViolation]:

    violations: List[ValidationViolation] = []

    # --------------------------------------------------------
    # PATH ONTOLOGY EXISTS
    # --------------------------------------------------------

    if not PATH_ONTOLOGY_PATH.exists():

        violations.append(
            ValidationViolation(
                category="PATH_ONTOLOGY",
                file_path=PATH_ONTOLOGY_PATH,
                message=(
                    "missing canonical "
                    "PATH_ONTOLOGY.yaml"
                ),
            )
        )

    # --------------------------------------------------------
    # IMPLEMENTATION REGISTRY
    # --------------------------------------------------------

    violations.extend(
        validate_implementation_registry(
            IMPLEMENTATION_REGISTRY_PATH
        )
    )

    # --------------------------------------------------------
    # ENFORCEMENT MATRIX
    # --------------------------------------------------------

    violations.extend(
        validate_enforcement_matrix(
            ENFORCEMENT_MATRIX_PATH
        )
    )

    # --------------------------------------------------------
    # GENERIC YAML VALIDATION
    # --------------------------------------------------------

    for yaml_file in discover_yaml_files():

        violations.extend(
            validate_yaml_file(yaml_file)
        )

    return violations


# ============================================================
# REPORTING
# ============================================================

def report_violations(
    violations: List[ValidationViolation],
) -> None:

    if not violations:

        print(
            "✅ Path ontology validation passed"
        )

        return

    print(
        "\n❌ PATH ONTOLOGY VIOLATIONS DETECTED\n"
    )

    for violation in violations:

        print(
            f"  - {violation}"
        )


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> None:

    violations = validate_repository()

    report_violations(violations)

    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()