# afritech/replay/ci/enforce_authority_consistency.py

"""
AfriTech CI Enforcement
Authority Consistency Validation

Purpose:
Ensure that all authority definitions are consistent across:
- registry authority catalog
- inference authority profiles (execution layer)

This enforces:
- single source of authority identity truth
- no undeclared authority usage
- no drift between registry and execution

Failure → CI FAIL
"""

import sys
import yaml
from typing import Set


class AuthorityConsistencyError(Exception):
    """Raised when authority inconsistency is detected"""
    pass


# ---------------------------------------------------------------------
# FILE PATHS (CANONICAL)
# ---------------------------------------------------------------------

REGISTRY_AUTHORITY_PATH = "afritech/registry/authority_profiles.yaml"
INFERENCE_AUTHORITY_PATH = "afritech/inference/authority_profiles.yaml"


# ---------------------------------------------------------------------
# LOAD HELPERS
# ---------------------------------------------------------------------

def load_yaml(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise AuthorityConsistencyError(f"missing_file: {path}")
    except Exception as e:
        raise AuthorityConsistencyError(f"invalid_yaml: {path} → {e}")


# ---------------------------------------------------------------------
# EXTRACTION
# ---------------------------------------------------------------------

def extract_registry_authorities(data: dict) -> Set[str]:
    """
    Extract authority IDs from registry authority catalog.
    """
    try:
        authorities = data.get("authorities", {})
        if not isinstance(authorities, dict):
            raise AuthorityConsistencyError("invalid_registry_authorities_structure")

        return set(authorities.keys())

    except Exception as e:
        raise AuthorityConsistencyError(f"registry_extraction_error: {e}")


def extract_inference_authorities(data: dict) -> Set[str]:
    """
    Extract authority IDs from inference authority profiles.
    """
    try:
        profiles = data.get("authority_profiles", [])

        if not isinstance(profiles, list):
            raise AuthorityConsistencyError("invalid_inference_profiles_structure")

        ids = set()

        for profile in profiles:
            if "id" not in profile:
                raise AuthorityConsistencyError("missing_authority_id_in_profile")

            ids.add(profile["id"])

        return ids

    except Exception as e:
        raise AuthorityConsistencyError(f"inference_extraction_error: {e}")


# ---------------------------------------------------------------------
# VALIDATION LOGIC
# ---------------------------------------------------------------------

def validate_subset(inference_ids: Set[str], registry_ids: Set[str]):
    """
    Ensure inference authorities are declared in registry.
    """
    missing = inference_ids - registry_ids

    if missing:
        raise AuthorityConsistencyError(
            f"undeclared_authorities_in_inference: {sorted(missing)}"
        )


def validate_coverage(registry_ids: Set[str], inference_ids: Set[str]):
    """
    Ensure every registry authority is defined in inference layer.
    """
    missing = registry_ids - inference_ids

    if missing:
        raise AuthorityConsistencyError(
            f"registry_authorities_missing_execution_profiles: {sorted(missing)}"
        )


def validate_forbidden_authority(inference_ids: Set[str]):
    """
    Prevent unauthorized fallback or undefined authority usage.
    """
    if "UNAUTHORIZED" in inference_ids:
        return  # allowed as explicit denial profile

    # future extension: enforce explicit denial presence if required


# ---------------------------------------------------------------------
# MAIN ENFORCEMENT
# ---------------------------------------------------------------------

def enforce_authority_consistency() -> None:
    """
    Main CI enforcement entrypoint.
    """

    registry_data = load_yaml(REGISTRY_AUTHORITY_PATH)
    inference_data = load_yaml(INFERENCE_AUTHORITY_PATH)

    registry_ids = extract_registry_authorities(registry_data)
    inference_ids = extract_inference_authorities(inference_data)

    # -------------------------------------------------------------
    # VALIDATION STEPS
    # -------------------------------------------------------------

    validate_subset(inference_ids, registry_ids)
    validate_coverage(registry_ids, inference_ids)
    validate_forbidden_authority(inference_ids)

    # -------------------------------------------------------------
    # SUCCESS OUTPUT
    # -------------------------------------------------------------

    print("[CI-AUTHORITY] ✅ Authority consistency verified")
    print(f"[CI-AUTHORITY] Registry authorities: {sorted(registry_ids)}")
    print(f"[CI-AUTHORITY] Inference authorities: {sorted(inference_ids)}")


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        enforce_authority_consistency()

    except AuthorityConsistencyError as e:
        print(f"[CI-AUTHORITY] ❌ FAILURE: {str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"[CI-AUTHORITY] ❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)

    sys.exit(0)