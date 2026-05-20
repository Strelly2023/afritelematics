"""
afritech/runtime/activation/runtime_admission.py

AfriTech Runtime Admission Validator

Purpose:
Constitutionally admit the runtime under a specific epoch by validating
registry, attestation, epoch semantics, kernel integrity, authority,
replay verifier binding, and runtime certificate.

CONSTITUTIONAL RULES:
- Admission ONLY (no execution, no state mutation)
- MUST NOT parse epoch YAML
- MUST NOT parse semantic YAML
- MUST consume only:
    • sealed registry (loader)
    • registry attestation (sealed)
    • EpochSnapshot
    • compiled SemanticEpoch
    • runtime certificate
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from afritech.trace.trace_engine import TraceEngine
from afritech.registry.loader import load_registry
from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import SemanticEpoch


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class RuntimeAdmissionError(Exception):
    """Raised when constitutional runtime admission fails"""
    pass


# -----------------------------------------------------------------
# VALIDATOR
# -----------------------------------------------------------------

class RuntimeAdmissionValidator:
    """
    Constitutional runtime admission validator.

    NOTE:
    This validator performs NO execution and NO mutation.
    """

    # =============================================================
    # INIT
    # =============================================================

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()

        # Runtime certificate is the ONLY file read directly
        self.certificate_path = (
            self.base_path
            / "proof/certificates/runtime_epoch_0006.cert"
        )

        self.registry: Optional[Dict[str, Any]] = None
        self.attestation: Optional[Dict[str, Any]] = None
        self.certificate: Optional[Dict[str, Any]] = None

    # =============================================================
    # FILE SAFETY
    # =============================================================

    @staticmethod
    def _assert_exists(path: Path, name: str) -> None:
        if not path.exists():
            raise RuntimeAdmissionError(
                f"Missing required artifact: {name}"
            )

    # =============================================================
    # CERTIFICATE LOADING (ONLY ALLOWED YAML)
    # =============================================================

    def _load_certificate(self) -> None:
        self._assert_exists(self.certificate_path, "runtime certificate")

        # Certificate loader is assumed to be safe & deterministic
        from afritech.proof.certificates.loader import load_runtime_certificate

        self.certificate = load_runtime_certificate(self.certificate_path)

        if not isinstance(self.certificate, dict):
            raise RuntimeAdmissionError("Invalid runtime certificate format")

    # =============================================================
    # REGISTRY & ATTESTATION (SEALED ONLY)
    # =============================================================

    def _load_registry_and_attestation(self) -> None:
        self.registry = load_registry()

        if not self.registry:
            raise RuntimeAdmissionError("Registry missing")

        self.attestation = self.registry.get("attestation")

        if not self.attestation:
            raise RuntimeAdmissionError("Registry attestation missing")

        if self.attestation.get("status") != "SEALED":
            raise RuntimeAdmissionError("Registry attestation is not SEALED")

    # =============================================================
    # CERTIFICATE VALIDATION
    # =============================================================

    def _validate_certificate(self) -> None:
        cert = self.certificate.get("runtime_certificate")

        if not isinstance(cert, dict):
            raise RuntimeAdmissionError("Missing RuntimeCertificate")

        required_keys = [
            "constitutional_binding",
            "admission",
            "guarantees",
            "execution_constraints",
            "non_observability",
            "signature",
        ]

        for key in required_keys:
            if key not in cert:
                raise RuntimeAdmissionError(
                    f"Malformed certificate: missing {key}"
                )

        sig = cert["signature"]
        expected_scope = sig["signature_scope"]["includes"]

        actual_scope = [
            "constitutional_binding",
            "admission",
            "guarantees",
            "execution_constraints",
            "non_observability",
        ]

        if set(expected_scope) != set(actual_scope):
            raise RuntimeAdmissionError("Signature scope mismatch")

        payload = {k: cert[k] for k in actual_scope}

        computed = hashlib.sha256(
            _canonical_json(payload).encode("utf-8")
        ).hexdigest()

        if computed != sig["signed_payload_hash"]:
            raise RuntimeAdmissionError("Signature payload hash mismatch")

    # =============================================================
    # CONSTITUTIONAL BINDINGS (NO YAML)
    # =============================================================

    def _validate_bindings(
        self,
        epoch_snapshot: EpochSnapshot,
    ) -> None:
        binding = self.certificate["runtime_certificate"]["constitutional_binding"]

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise RuntimeAdmissionError("EpochSnapshot required")

        semantic_epoch: SemanticEpoch = epoch_snapshot.semantic_epoch

        if not isinstance(semantic_epoch, SemanticEpoch):
            raise RuntimeAdmissionError("Compiled SemanticEpoch required")

        # Epoch identity
        if binding["epoch"] != semantic_epoch.number:
            raise RuntimeAdmissionError("Epoch number mismatch")

        # Registry binding
        if binding["registry_hash"] != self.registry.get("registry_hash"):
            raise RuntimeAdmissionError("Registry hash mismatch")

        # Attested epoch binding (NO YAML)
        if binding["epoch_hash"] != epoch_snapshot.epoch_hash:
            raise RuntimeAdmissionError("Epoch hash mismatch")

        # Execution surfaces
        if (
            binding["execution_surfaces_hash"]
            != self.attestation.get("execution_surface_hash")
        ):
            raise RuntimeAdmissionError("Execution surfaces hash mismatch")

        # Kernel surface
        if (
            binding["kernel_root_hash"]
            != self.attestation.get("kernel_surface_hash")
        ):
            raise RuntimeAdmissionError("Kernel surface hash mismatch")

        # Replay verifier
        if (
            binding["verifier_hash"]
            != self.attestation.get("replay_verifier_hash")
        ):
            raise RuntimeAdmissionError("Replay verifier mismatch")

    # =============================================================
    # SURFACE ADMISSION
    # =============================================================

    def _validate_execution_surfaces(self) -> None:
        if not self.attestation.get("execution_surface_hash"):
            raise RuntimeAdmissionError(
                "Attestation missing execution_surface_hash"
            )

    # =============================================================
    # PUBLIC ENTRY
    # =============================================================

    def validate(
        self,
        *,
        epoch_snapshot: EpochSnapshot,
        trace: Optional[TraceEngine] = None,
    ) -> bool:
        """
        Perform full constitutional runtime admission.

        Admission ONLY:
        - no execution
        - no mutation
        """

        if trace:
            trace.record("runtime_admission", {"status": "begin"})

        self._load_registry_and_attestation()
        self._load_certificate()
        self._validate_certificate()
        self._validate_bindings(epoch_snapshot)
        self._validate_execution_surfaces()

        if trace:
            trace.complete(
                "runtime_admission",
                {"status": "admitted"},
            )

        return True


# =============================================================
# UTILITIES
# =============================================================

def _canonical_json(obj: Any) -> str:
    import json
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)