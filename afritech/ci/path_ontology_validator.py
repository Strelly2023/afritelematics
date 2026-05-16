import re
import sys
import yaml

from pathlib import Path
from fnmatch import fnmatch


CONFIG_PATH = Path("afritech/constitution/path_ontology.yaml")
ROOT = Path("ecosystems")


# =========================================================
# CONFIG
# =========================================================
def load_config():
    return yaml.safe_load(CONFIG_PATH.read_text())["rules"]


# =========================================================
# HELPERS
# =========================================================
def matches_any(path_str, patterns):
    return any(fnmatch(path_str, p) for p in patterns)


def matches_pattern(name, pattern):
    pattern = pattern.replace("*", ".*")
    return re.fullmatch(pattern, name) is not None


def validate_snake_case(stem):
    """
    Valid:
        foo
        foo_bar
        runtime_registry
        deterministic_execution
    """

    return re.fullmatch(r"[a-z0-9_]+", stem) is not None


def validate_extension(suffix, allowed_extensions):
    """
    Empty suffix allowed for directories.
    """

    if suffix == "":
        return True

    return suffix in allowed_extensions


def validate_governance_name(name, rules):
    """
    Governance artifacts support:
      - structured constitutional artifacts
      - registry-style yaml artifacts
    """

    structured_patterns = rules.get(
        "structured_patterns",
        []
    )

    registry_patterns = rules.get(
        "registry_patterns",
        []
    )

    for pattern in structured_patterns:
        if re.fullmatch(pattern, name):
            return True

    for pattern in registry_patterns:
        if re.fullmatch(pattern, name):
            return True

    return False


# =========================================================
# VALIDATOR
# =========================================================
def validate():

    config = load_config()
    errors = []

    for path in ROOT.rglob("*"):

        name = path.name
        path_str = str(path)

        # =====================================================
        # IGNORE
        # =====================================================
        if any(
            matches_pattern(name, p)
            for p in config.get("ignore_patterns", [])
        ):
            continue

        # =====================================================
        # EXPLICIT EXCEPTIONS
        # =====================================================
        if name in config.get(
            "allowed_exceptions",
            []
        ):
            continue

        # =====================================================
        # STRICT PATHS
        # =====================================================
        if matches_any(
            path_str,
            config.get("strict_paths", [])
        ):

            rules = config["strict_rules"]

            # -------------------------------------------------
            # DIRECTORIES
            # -------------------------------------------------
            if path.is_dir():

                # lowercase
                if (
                    rules.get("lowercase_only")
                    and name != name.lower()
                ):
                    errors.append(
                        f"Uppercase not allowed: {path}"
                    )
                    continue

                # snake_case
                if (
                    rules.get("snake_case_only")
                    and not validate_snake_case(name)
                ):
                    errors.append(
                        f"Not snake_case: {path}"
                    )
                    continue

                # spaces
                if (
                    rules.get("no_spaces")
                    and " " in name
                ):
                    errors.append(
                        f"Spaces not allowed: {path}"
                    )
                    continue

                continue

            # -------------------------------------------------
            # FILES
            # -------------------------------------------------
            stem = path.stem
            suffix = path.suffix

            # lowercase
            if (
                rules.get("lowercase_only")
                and name != name.lower()
            ):
                errors.append(
                    f"Uppercase not allowed: {path}"
                )
                continue

            # extension validation
            allowed_extensions = rules.get(
                "allowed_extensions",
                [".py"]
            )

            if not validate_extension(
                suffix,
                allowed_extensions
            ):
                errors.append(
                    f"Extension not allowed: {path}"
                )
                continue

            # snake_case validation
            if (
                rules.get("snake_case_only")
                and not validate_snake_case(stem)
            ):
                errors.append(
                    f"Not snake_case: {path}"
                )
                continue

            # spaces
            if (
                rules.get("no_spaces")
                and " " in name
            ):
                errors.append(
                    f"Spaces not allowed: {path}"
                )
                continue

            # forbidden patterns
            for pattern in rules.get(
                "forbidden_patterns",
                []
            ):

                if re.fullmatch(pattern, name):
                    errors.append(
                        f"Forbidden pattern "
                        f"'{pattern}' in: {path}"
                    )
                    break

        # =====================================================
        # GOVERNANCE PATHS
        # =====================================================
        elif matches_any(
            path_str,
            config.get("governance_paths", [])
        ):

            rules = config["governance_rules"]

            # -------------------------------------------------
            # DIRECTORIES
            # -------------------------------------------------
            if (
                path.is_dir()
                and rules.get(
                    "allow_directories",
                    False
                )
            ):
                continue

            # -------------------------------------------------
            # PYTHON FILES
            # -------------------------------------------------
            if (
                path.suffix == ".py"
                and rules.get(
                    "allow_python",
                    False
                )
            ):
                continue

            # -------------------------------------------------
            # DOC FILES
            # -------------------------------------------------
            if (
                path.suffix in [".md", ".txt"]
                and rules.get(
                    "allow_docs",
                    False
                )
            ):
                continue

            # -------------------------------------------------
            # GOVERNANCE STRUCTURE VALIDATION
            # -------------------------------------------------
            if not validate_governance_name(
                name,
                rules
            ):
                errors.append(
                    f"Invalid governance naming: {path}"
                )

        # =====================================================
        # DOCS
        # =====================================================
        elif matches_any(
            path_str,
            config.get("docs_paths", [])
        ):
            continue

        # =====================================================
        # DEFAULT
        # =====================================================
        else:
            continue

    # =========================================================
    # FINAL RESULT
    # =========================================================
    if errors:

        print(
            "❌ Path ontology violations detected:\n"
        )

        for error in errors:
            print(f" - {error}")

        sys.exit(1)

    print(
        "✅ Path ontology enforcement passed"
    )


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    validate()