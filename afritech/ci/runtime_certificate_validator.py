# afritech/ci/runtime_certificate_validator.py

"""
AfriTech Runtime Certificate Validator

Purpose
-------
Enforce constitutional runtime admission.

Guarantees
----------
- No runtime execution without valid certificate
- Deterministic replay-safe certificate validation
- Closed-world admission enforcement
- Attestation + epoch alignment
- Cryptographic integrity verification
- Structured runtime identity validation
"""

from __future__ import annotations

import hashlib
import json
import sys

from pathlib import Path
from typing import Any, Dict


# ============================================================
# ROOTS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CERTIFICATE_PATH = (
    PROJECT_ROOT
    / "afritech/proof/runtime_certificate.yaml"
)

ATTESTATION_PATH = (
    PROJECT_ROOT
    / "afritech/registry/attestation.yaml"
)


# ============================================================
# FAILURE
# ============================================================

def fail(message: str) -> None:
    raise RuntimeError(message)


# ============================================================
# LOAD YAML
# ============================================================

def load_yaml(path: Path) -> Dict[str, Any]:

    import yaml

    if not path.exists():
        fail(f"missing required file: {path}")

    data = yaml.safe_load(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        fail(f"invalid yaml structure: {path}")

    return data


# ============================================================
# REQUIRED FIELDS
# ============================================================

REQUIRED_CERTIFICATE_FIELDS = [

    "certificate_id",

    "epoch",

    "constitutional_binding",

    "runtime_identity",

    "signature",
]

REQUIRED_SIGNATURE_FIELDS = [

    "payload_hash",

    "signature",

    "certificate_root",
]


# ============================================================
# HASH (DETERMINISTIC)
# ============================================================

def compute_hash(
    payload: Dict[str, Any]
) -> str:

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ============================================================
# STRUCTURE VALIDATION
# ============================================================

def validate_structure(
    cert: Dict[str, Any]
) -> None:

    for field in REQUIRED_CERTIFICATE_FIELDS:

        if field not in cert:

            fail(
                f"missing certificate field: {field}"
            )

    signature = cert.get("signature", {})

    if not isinstance(signature, dict):
        fail("signature must be object")

    for field in REQUIRED_SIGNATURE_FIELDS:

        if field not in signature:

            fail(
                f"missing signature field: {field}"
            )


# ============================================================
# PAYLOAD HASH VALIDATION
# ============================================================

def validate_payload_hash(
    cert: Dict[str, Any]
) -> None:

    signature = cert["signature"]

    # remove signature before hashing
    payload = dict(cert)

    payload.pop("signature", None)

    computed = compute_hash(payload)

    expected = signature["payload_hash"]

    if computed != expected:

        fail(
            "payload hash mismatch "
            "(non-deterministic certificate)"
        )


# ============================================================
# ATTESTATION VALIDATION
# ============================================================

def validate_attestation(
    cert: Dict[str, Any]
) -> None:

    attestation = load_yaml(
        ATTESTATION_PATH
    )

    if "status" not in attestation:

        fail(
            "attestation missing status"
        )

    if attestation["status"] != "SEALED":

        fail(
            "attestation not sealed "
            "(closed-world violation)"
        )

    cert_epoch = str(
        cert.get("epoch")
    )

    attestation_epoch = str(
        attestation.get("epoch")
    )

    if cert_epoch != attestation_epoch:

        fail(
            "certificate epoch mismatch "
            "with attestation"
        )

    # optional binding hash
    binding = cert.get(
        "constitutional_binding",
        {},
    )

    attestation_hash = attestation.get(
        "hash"
    )

    if (
        attestation_hash
        and binding.get("attestation_hash")
        != attestation_hash
    ):

        fail(
            "certificate not bound to "
            "attestation "
            "(binding violation)"
        )


# ============================================================
# CLOSED-WORLD VALIDATION
# ============================================================

def validate_closed_world(
    cert: Dict[str, Any]
) -> None:

    runtime_identity = cert.get(
        "runtime_identity"
    )

    if not runtime_identity:

        fail(
            "missing runtime identity"
        )

    # --------------------------------------------------------
    # MODERN STRUCTURED RUNTIME IDENTITY
    # --------------------------------------------------------

    if isinstance(runtime_identity, dict):

        runtime_version = (
            runtime_identity.get(
                "runtime_version"
            )
        )

        if not runtime_version:

            fail(
                "runtime identity missing "
                "runtime_version"
            )

        execution_context_hash = (
            runtime_identity.get(
                "execution_context_hash"
            )
        )

        if not execution_context_hash:

            fail(
                "missing execution context hash"
            )

        environment = (
            runtime_identity.get(
                "environment",
                {},
            )
        )

        if not isinstance(environment, dict):

            fail(
                "runtime environment "
                "must be object"
            )

        if not environment.get(
            "deterministic_mode",
            False,
        ):

            fail(
                "runtime not deterministic"
            )

        if (
            environment.get(
                "environment_mutability"
            )
            != "FORBIDDEN"
        ):

            fail(
                "environment mutability "
                "violation"
            )

        if (
            environment.get(
                "system_time_access"
            )
            != "FORBIDDEN"
        ):

            fail(
                "system time access violation"
            )

        if (
            environment.get(
                "external_io_access"
            )
            != "FORBIDDEN"
        ):

            fail(
                "external IO access violation"
            )

        return

    # --------------------------------------------------------
    # LEGACY STRING MODE
    # --------------------------------------------------------

    if isinstance(runtime_identity, str):

        if not runtime_identity.startswith(
            "afritech."
        ):

            fail(
                "non-canonical runtime identity "
                "(closed-world violation)"
            )

        return

    fail(
        "invalid runtime identity structure"
    )


# ============================================================
# DETERMINISM CHECK
# ============================================================

def validate_determinism(
    cert: Dict[str, Any]
) -> None:

    constraints = cert.get(
        "replay_constraints",
        {},
    )

    if not isinstance(constraints, dict):

        fail(
            "replay_constraints must be object"
        )

    deterministic_only = constraints.get(
        "deterministic_only",
        False,
    )

    replay_required = constraints.get(
        "replay_required",
        False,
    )

    if not deterministic_only:

        fail(
            "certificate not replay deterministic"
        )

    if not replay_required:

        fail(
            "certificate missing replay requirement"
        )


# ============================================================
# SIGNATURE STRUCTURE VALIDATION
# ============================================================

def validate_signature_structure(
    cert: Dict[str, Any]
) -> None:

    signature = cert.get(
        "signature",
        {},
    )

    algorithm = signature.get(
        "algorithm"
    )

    if algorithm != "ED25519":

        fail(
            "unsupported signature algorithm"
        )

    signature_version = signature.get(
        "signature_version"
    )

    if signature_version != "v1":

        fail(
            "unsupported signature version"
        )


# ============================================================
# MAIN VALIDATOR
# ============================================================

def main() -> int:

    try:

        cert_doc = load_yaml(
            CERTIFICATE_PATH
        )

        cert = cert_doc.get(
            "runtime_certificate"
        )

        if cert is None:

            fail(
                "missing runtime_certificate root"
            )

        # ----------------------------------------------------
        # STRICT VALIDATION ORDER
        # ----------------------------------------------------

        validate_structure(cert)

        validate_payload_hash(cert)

        validate_attestation(cert)

        validate_closed_world(cert)

        validate_determinism(cert)

        validate_signature_structure(cert)

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print(
            "✅ Runtime certificate "
            "structure validated"
        )

        print(
            "✅ Payload hash integrity verified"
        )

        print(
            "✅ Attestation binding verified"
        )

        print(
            "✅ Closed-world runtime "
            "identity verified"
        )

        print(
            "✅ Deterministic replay "
            "constraints verified"
        )

        print(
            "✅ Signature structure verified"
        )

        print(
            "✅ Runtime admission "
            "constitutionally valid"
        )

        return 0

    except Exception as exc:

        print(
            "❌ Runtime certificate "
            f"validation failed: {exc}"
        )

        return 1


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())

    #afritech/ci/import_topology_validator.py