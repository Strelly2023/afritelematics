# afritech/system/health_validator.py

"""
AfriTech System Health Validator

Purpose:
Validate that the system state conforms to identity.yaml.

This verifies:
- constitutional integrity
- runtime readiness
- attestation alignment
- enforcement completeness

This is NOT execution logic.
This is system integrity verification.

Failure → system is not constitutionally healthy.
"""

import os
import yaml
import sys


class SystemHealthError(Exception):
    pass


# ---------------------------------------------------------------------
# PATHS (DERIVED FROM IDENTITY)
# ---------------------------------------------------------------------

IDENTITY_PATH = "afritech/system/identity.yaml"


# ---------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------

def load_yaml(path: str):
    if not os.path.exists(path):
        raise SystemHealthError(f"missing_file: {path}")

    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise SystemHealthError(f"invalid_yaml: {path} → {e}")


def assert_exists(path: str):
    if not os.path.exists(path):
        raise SystemHealthError(f"missing_required_path: {path}")


# ---------------------------------------------------------------------
# VALIDATION MODULES
# ---------------------------------------------------------------------

def validate_core_identity(identity: dict):
    system = identity.get("system", {})

    if system.get("status") != "ACTIVE":
        raise SystemHealthError("system_not_active")

    if system.get("mode") != "CONSTITUTIONAL_RUNTIME":
        raise SystemHealthError("invalid_system_mode")


def validate_constitutional_root(identity: dict):
    root = identity["system"]["constitutional_root"]

    assert_exists(root["registry"])
    assert_exists(root["attestation"])


def validate_state(identity: dict):
    state = identity["system"]["state"]

    if state.get("registry_status") != "SEALED":
        raise SystemHealthError("registry_not_sealed")

    if state.get("attestation_status") != "SEALED":
        raise SystemHealthError("attestation_not_sealed")

    if not state.get("runtime_admission_required"):
        raise SystemHealthError("runtime_admission_not_required")

    if not state.get("replay_required"):
        raise SystemHealthError("replay_not_required")


def validate_execution_model(identity: dict):
    model = identity["system"]["execution_model"]

    if model.get("type") != "CLOSED_WORLD":
        raise SystemHealthError("invalid_execution_model")

    forbidden = model.get("forbidden", [])

    if not forbidden:
        raise SystemHealthError("missing_forbidden_execution_rules")


def validate_architecture(identity: dict):
    layers = identity["system"]["architecture"]["layers"]

    for layer in layers:
        path = layer.get("path")
        if not path:
            raise SystemHealthError(f"missing_layer_path: {layer}")

        if not os.path.exists(path):
            raise SystemHealthError(f"missing_layer_directory: {path}")


def validate_authority(identity: dict):
    auth = identity["system"]["authority"]

    assert_exists(auth["registry_source"])
    assert_exists(auth["execution_source"])


def validate_runtime_admission(identity: dict):
    admission = identity["system"]["runtime_admission"]

    if not admission.get("required"):
        raise SystemHealthError("runtime_admission_missing")

    cert_path = admission["certificate"]["path"]

    if not os.path.exists(cert_path):
        raise SystemHealthError(f"missing_certificate_directory: {cert_path}")

    assert_exists(admission["admission_engine"]["path"])


def validate_replay(identity: dict):
    replay = identity["system"]["replay"]

    if not replay.get("required"):
        raise SystemHealthError("replay_not_enabled")

    assert_exists(replay["transcript_schema"])
    assert_exists(replay["verifier"]["path"])


def validate_ci(identity: dict):
    ci = identity["system"]["ci_enforcement"]

    ci_path = ci.get("location")

    if not os.path.exists(ci_path):
        raise SystemHealthError("missing_ci_directory")

    rules = ci.get("enforced_rules", [])

    if not rules:
        raise SystemHealthError("no_ci_rules_defined")


def validate_non_observability(identity: dict):
    non_obs = identity["system"]["non_observability"]

    if not non_obs.get("enforced"):
        raise SystemHealthError("non_observability_not_enforced")


# ---------------------------------------------------------------------
# MAIN VALIDATION
# ---------------------------------------------------------------------

def validate_system():

    identity = load_yaml(IDENTITY_PATH)

    # -------------------------------------------------------------
    # VALIDATION PIPELINE
    # -------------------------------------------------------------

    validate_core_identity(identity)
    validate_constitutional_root(identity)
    validate_state(identity)
    validate_execution_model(identity)
    validate_architecture(identity)
    validate_authority(identity)
    validate_runtime_admission(identity)
    validate_replay(identity)
    validate_ci(identity)
    validate_non_observability(identity)

    # -------------------------------------------------------------
    # SUCCESS
    # -------------------------------------------------------------

    print("[SYSTEM-HEALTH] ✅ System integrity verified")
    print("[SYSTEM-HEALTH] ✅ Constitutional state is valid")
    print("[SYSTEM-HEALTH] ✅ Runtime admission path verified")
    print("[SYSTEM-HEALTH] ✅ Replay system active")
    print("[SYSTEM-HEALTH] ✅ CI enforcement detected")


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        validate_system()

    except SystemHealthError as e:
        print(f"[SYSTEM-HEALTH] ❌ FAILURE: {str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"[SYSTEM-HEALTH] ❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)

    sys.exit(0)
