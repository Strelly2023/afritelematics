# afritech/replay/ci/enforce_authority_scope_integrity.py

"""
AfriTech CI Enforcement
Authority Scope Integrity Validation

Purpose:
Ensure that all authority profiles strictly enforce
their declared scope of operations.

This validates:
- permitted_operations correctness
- prohibited_operations enforcement
- scope constraints completeness
- alignment with constitutional request schema

Failure → CI FAIL
"""

import sys
import yaml
from typing import Dict, List


class AuthorityScopeError(Exception):
    """Raised when authority scope violation is detected"""
    pass


# ---------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------

AUTHORITY_PROFILES_PATH = "afritech/inference/authority_profiles.yaml"
REQUEST_SCHEMA_PATH = "afritech/inference/constitutional_request.yaml"


# ---------------------------------------------------------------------
# LOADING
# ---------------------------------------------------------------------

def load_yaml(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise AuthorityScopeError(f"missing_file: {path}")
    except Exception as e:
        raise AuthorityScopeError(f"invalid_yaml: {path} → {e}")


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def validate_profile_structure(profile: Dict):
    required_fields = [
        "id",
        "permitted_operations",
        "prohibited_operations",
    ]

    for field in required_fields:
        if field not in profile:
            raise AuthorityScopeError(
                f"missing_required_field: {profile.get('id')} → {field}"
            )


def validate_no_overlap(profile_id: str, permitted: List[str], prohibited: List[str]):
    overlap = set(permitted) & set(prohibited)

    if overlap:
        raise AuthorityScopeError(
            f"operation_overlap: {profile_id} → {sorted(overlap)}"
        )


def validate_prohibited_precedence(profile_id: str, prohibited: List[str]):
    if "*" in prohibited:
        # wildcard prohibition must be exclusive
        if len(prohibited) > 1:
            raise AuthorityScopeError(
                f"invalid_wildcard_prohibition: {profile_id}"
            )


def validate_scope_constraints(profile_id: str, profile: Dict):
    constraints = profile.get("scope_constraints", {})

    if not constraints:
        raise AuthorityScopeError(
            f"missing_scope_constraints: {profile_id}"
        )


def validate_replay_constraints(profile_id: str, profile: Dict):
    replay = profile.get("replay_constraints", {})

    if "deterministic_only" not in replay:
        raise AuthorityScopeError(
            f"missing_replay_constraint: {profile_id}"
        )


def validate_against_request_schema(profile_id: str, profile: Dict, schema: Dict):
    """
    Ensure authority operations align with request schema allowances.
    """

    schema_ops = set(
        schema["constitutional_request"]["permissible_operations"]["allowed_values"]
    )

    profile_ops = set(profile.get("permitted_operations", []))

    invalid_ops = profile_ops - schema_ops

    if invalid_ops:
        raise AuthorityScopeError(
            f"invalid_permitted_operation: {profile_id} → {sorted(invalid_ops)}"
        )


# ---------------------------------------------------------------------
# CORE VALIDATION
# ---------------------------------------------------------------------

def enforce_scope_integrity():

    authority_data = load_yaml(AUTHORITY_PROFILES_PATH)
    schema_data = load_yaml(REQUEST_SCHEMA_PATH)

    profiles = authority_data.get("authority_profiles", [])

    if not profiles:
        raise AuthorityScopeError("no_authority_profiles_found")

    for profile in profiles:

        profile_id = profile.get("id")

        if not profile_id:
            raise AuthorityScopeError("profile_missing_id")

        permitted = profile.get("permitted_operations", [])
        prohibited = profile.get("prohibited_operations", [])

        # ---------------------------------------------------------
        # VALIDATIONS
        # ---------------------------------------------------------

        validate_profile_structure(profile)
        validate_no_overlap(profile_id, permitted, prohibited)
        validate_prohibited_precedence(profile_id, prohibited)
        validate_scope_constraints(profile_id, profile)
        validate_replay_constraints(profile_id, profile)
        validate_against_request_schema(profile_id, profile, schema_data)

    print("[CI-SCOPE] ✅ Authority scope integrity verified")


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        enforce_scope_integrity()

    except AuthorityScopeError as e:
        print(f"[CI-SCOPE] ❌ FAILURE: {str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"[CI-SCOPE] ❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)

    sys.exit(0)
