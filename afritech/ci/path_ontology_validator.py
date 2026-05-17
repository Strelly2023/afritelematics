import re
import yaml
import traceback

from pathlib import Path
from fnmatch import fnmatch


CONFIG_PATH = Path("afritech/constitution/path_ontology.yaml")
ROOT = Path("ecosystems")


# =========================================================
# CONFIG
# =========================================================
def load_config():
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Missing config: {CONFIG_PATH}")

    data = yaml.safe_load(CONFIG_PATH.read_text())

    if not isinstance(data, dict) or "rules" not in data:
        raise RuntimeError("Invalid path ontology config")

    return data["rules"]


# =========================================================
# HELPERS
# =========================================================
def matches_any(path_str, patterns):
    return any(fnmatch(path_str, p) for p in patterns)


def matches_pattern(name, pattern):
    pattern = pattern.replace("*", ".*")
    return re.fullmatch(pattern, name) is not None


def validate_snake_case(stem):
    return re.fullmatch(r"[a-z0-9_]+", stem) is not None


def validate_extension(suffix, allowed_extensions):
    if suffix == "":
        return True
    return suffix in allowed_extensions


def validate_governance_name(name, rules):
    structured_patterns = rules.get("structured_patterns", [])
    registry_patterns = rules.get("registry_patterns", [])

    for pattern in structured_patterns:
        if re.fullmatch(pattern, name):
            return True

    for pattern in registry_patterns:
        if re.fullmatch(pattern, name):
            return True

    return False


# =========================================================
# VALIDATOR CORE
# =========================================================
def run_validation():
    config = load_config()
    errors = []

    for path in ROOT.rglob("*"):

        name = path.name
        path_str = str(path)

        # -----------------------------
        # IGNORE
        # -----------------------------
        if any(
            matches_pattern(name, p)
            for p in config.get("ignore_patterns", [])
        ):
            continue

        # -----------------------------
        # EXCEPTIONS
        # -----------------------------
        if name in config.get("allowed_exceptions", []):
            continue

        # =====================================================
        # STRICT PATHS
        # =====================================================
        if matches_any(path_str, config.get("strict_paths", [])):

            rules = config["strict_rules"]

            # ------------------
            # DIRECTORIES
            # ------------------
            if path.is_dir():

                if rules.get("lowercase_only") and name != name.lower():
                    errors.append(f"Uppercase not allowed: {path}")
                    continue

                if rules.get("snake_case_only") and not validate_snake_case(name):
                    errors.append(f"Not snake_case: {path}")
                    continue

                if rules.get("no_spaces") and " " in name:
                    errors.append(f"Spaces not allowed: {path}")
                    continue

                continue

            # ------------------
            # FILES
            # ------------------
            stem = path.stem
            suffix = path.suffix

            if rules.get("lowercase_only") and name != name.lower():
                errors.append(f"Uppercase not allowed: {path}")
                continue

            allowed_extensions = rules.get("allowed_extensions", [".py"])

            if not validate_extension(suffix, allowed_extensions):
                errors.append(f"Extension not allowed: {path}")
                continue

            if rules.get("snake_case_only") and not validate_snake_case(stem):
                errors.append(f"Not snake_case: {path}")
                continue

            if rules.get("no_spaces") and " " in name:
                errors.append(f"Spaces not allowed: {path}")
                continue

            for pattern in rules.get("forbidden_patterns", []):
                if re.fullmatch(pattern, name):
                    errors.append(f"Forbidden pattern '{pattern}' in: {path}")
                    break

        # =====================================================
        # GOVERNANCE PATHS
        # =====================================================
        elif matches_any(path_str, config.get("governance_paths", [])):

            rules = config["governance_rules"]

            if path.is_dir() and rules.get("allow_directories", False):
                continue

            if path.suffix == ".py" and rules.get("allow_python", False):
                continue

            if path.suffix in [".md", ".txt"] and rules.get("allow_docs", False):
                continue

            if not validate_governance_name(name, rules):
                errors.append(f"Invalid governance naming: {path}")

        # =====================================================
        # DOC PATHS
        # =====================================================
        elif matches_any(path_str, config.get("docs_paths", [])):
            continue

    return errors


# =========================================================
# ENTRYPOINT (CONSTITUTIONAL CONTRACT)
# =========================================================
def main() -> int:
    """
    Constitutional entrypoint:
    MUST return:
        0  -> success
        !=0 -> failure
    """

    try:
        errors = run_validation()

        if errors:
            print("❌ Path ontology violations detected:\n")
            for e in errors:
                print(f" - {e}")
            return 1

        print("✅ Path ontology enforcement passed")
        return 0

    except Exception:
        print("❌ path ontology validator crashed:\n")
        print(traceback.format_exc())
        return 1