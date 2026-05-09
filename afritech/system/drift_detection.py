# afritech/system/drift_detection.py

"""
AfriTech Drift Detection Engine

Purpose:
Detect divergence between:

- identity.yaml (declared system state)
- registry.yaml (source of truth)
- attestation.yaml (sealed state)
- RuntimeCertificate (execution admission)

Failure → constitutional drift detected → system invalid
"""

import os
import yaml
import hashlib
import sys
from typing import Dict, Any


class DriftError(Exception):
    """Raised when drift is detected"""
    pass


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

IDENTITY_PATH = "afritech/system/identity.yaml"
REGISTRY_PATH = "afritech/registry/registry.yaml"
ATTESTATION_PATH = "afritech/registry/attestation.yaml"
CERTIFICATE_DIR = "afritech/proof/certificates/"


# ---------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------

def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise DriftError(f"missing_file: {path}")

    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise DriftError(f"invalid_yaml: {path} → {e}")


def compute_hash(path: str) -> str:
    if not os.path.exists(path):
        raise DriftError(f"missing_file: {path}")

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_latest_certificate_path() -> str:
    if not os.path.exists(CERTIFICATE_DIR):
        raise DriftError("missing_certificate_directory")

    certs = [
        os.path.join(CERTIFICATE_DIR, f)
        for f in os.listdir(CERTIFICATE_DIR)
        if f.endswith(".cert")
    ]

    if not certs:
        raise DriftError("no_certificates_found")

    # choose latest by name (epoch-based naming assumed)
    return sorted(certs)[-1]


# ---------------------------------------------------------------------
# DRIFT CHECKS
# ---------------------------------------------------------------------

def check_identity_vs_registry(identity, registry):
    expected_epoch = identity["system"]["state"]["constitutional_epoch"]
    actual_epoch = registry.get("epoch")

    if expected_epoch != actual_epoch:
        raise DriftError(
            f"epoch_drift: identity={expected_epoch} registry={actual_epoch}"
        )


def check_attestation_vs_registry(attestation, registry):
    att_epoch = attestation["attestation"]["epoch"]
    reg_epoch = registry.get("epoch")

    if att_epoch != reg_epoch:
        raise DriftError(
            f"attestation_registry_epoch_mismatch: {att_epoch} vs {reg_epoch}"
        )

    if attestation["attestation"]["status"] != "SEALED":
        raise DriftError("attestation_not_sealed")


def check_certificate_vs_attestation(certificate, attestation):
    cert = certificate["runtime_certificate"]
    att = attestation["attestation"]

    if cert["epoch"] != att["epoch"]:
        raise DriftError("certificate_epoch_mismatch")

    cert_binding = cert["constitutional_binding"]
    att_binding = att["bindings"]

    for key in att_binding:

        if key not in cert_binding:
            raise DriftError(f"missing_binding_in_certificate: {key}")

        if "<" in str(cert_binding[key]):
            raise DriftError(f"unresolved_binding: {key}")

        # optional strict match (if hashes available)
        if key in cert_binding and key in att_binding:
            if att_binding[key] != cert_binding[key]:
                raise DriftError(f"binding_drift: {key}")


def check_registry_hash(attestation):
    expected = attestation["attestation"]["bindings"]["registry_hash"]
    actual = compute_hash(REGISTRY_PATH)

    if expected != actual:
        raise DriftError("registry_hash_drift")


def check_execution_surface_hash(attestation):
    path = "afritech/governance/EXECUTION_SURFACES.yaml"

    expected = attestation["attestation"]["bindings"]["execution_surfaces_hash"]
    actual = compute_hash(path)

    if expected != actual:
        raise DriftError("execution_surfaces_hash_drift")


def check_authority_profiles_hash(attestation):
    path = "afritech/inference/authority_profiles.yaml"

    expected = attestation["attestation"]["bindings"]["authority_profiles_hash"]
    actual = compute_hash(path)

    if expected != actual:
        raise DriftError("authority_profiles_hash_drift")


# ---------------------------------------------------------------------
# MAIN ENGINE
# ---------------------------------------------------------------------

def detect_drift():

    identity = load_yaml(IDENTITY_PATH)
    registry = load_yaml(REGISTRY_PATH)
    attestation = load_yaml(ATTESTATION_PATH)

    cert_path = get_latest_certificate_path()
    certificate = load_yaml(cert_path)

    # -------------------------------------------------------------
    # DRIFT CHECK PIPELINE
    # -------------------------------------------------------------

    check_identity_vs_registry(identity, registry)
    check_attestation_vs_registry(attestation, registry)
    check_certificate_vs_attestation(certificate, attestation)

    check_registry_hash(attestation)
    check_execution_surface_hash(attestation)
    check_authority_profiles_hash(attestation)

    # -------------------------------------------------------------
    # SUCCESS
    # -------------------------------------------------------------

    print("[DRIFT] ✅ No drift detected")
    print("[DRIFT] ✅ identity ↔ registry aligned")
    print("[DRIFT] ✅ attestation ↔ registry aligned")
    print("[DRIFT] ✅ certificate ↔ attestation aligned")
    print("[DRIFT] ✅ hash integrity verified")


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        detect_drift()

    except DriftError as e:
        print(f"[DRIFT] ❌ FAILURE: {str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"[DRIFT] ❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)

    sys.exit(0)
