# afritech/runtime/admission/admission_engine.py

import os
import hashlib
import yaml
import json
from typing import Any, Dict, Optional

from afritech.system.health_validator import (
    validate_system,
    SystemHealthError,
)

from afritech.system.drift_detection import (
    detect_drift,
    DriftError,
)

from afritech.core.runtime.guards.proof_validator import (
    ProofValidator,
    ProofValidationError,
)

from afritech.proof.proof_artifact import ProofArtifact
from afritech.security.ed25519 import verify


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class AdmissionError(Exception):
    """Raised when constitutional admission fails"""
    pass


# -----------------------------------------------------------------
# ENGINE
# -----------------------------------------------------------------

class RuntimeAdmissionEngine:
    """
    Constitutional Runtime Admission Engine (Proof + Crypto Enforced)

    Guarantees:
    - deterministic environment
    - immutable system bindings
    - replay-safe execution model
    - proof-carrying execution
    - cryptographic authenticity (Ed25519)
    """

    def __init__(self, certificate_path: str):
        self.certificate_path = certificate_path
        self.certificate: Optional[Dict[str, Any]] = None

    # -----------------------------------------------------------------
    # ENTRYPOINT
    # -----------------------------------------------------------------

    def admit(self) -> bool:

        self._validate_system_health()
        self._validate_drift()

        self._load_certificate()

        self._validate_signature()
        self._validate_constitutional_binding()
        self._validate_admission_guarantees()

        self._validate_execution_scope()
        self._validate_environment()
        self._validate_replay_constraints()

        self._validate_proof_requirements()
        self._validate_expiry()

        return True

    # -----------------------------------------------------------------
    # SYSTEM HEALTH
    # -----------------------------------------------------------------

    def _validate_system_health(self):
        try:
            validate_system()
        except SystemHealthError as e:
            raise AdmissionError(f"system_health_failure: {e}")

    # -----------------------------------------------------------------
    # DRIFT
    # -----------------------------------------------------------------

    def _validate_drift(self):
        try:
            detect_drift()
        except DriftError as e:
            raise AdmissionError(f"drift_detected: {e}")
        except Exception as e:
            raise AdmissionError(f"drift_validation_failed: {e}")

    # -----------------------------------------------------------------
    # CERTIFICATE LOAD
    # -----------------------------------------------------------------

    def _load_certificate(self):
        if not os.path.exists(self.certificate_path):
            raise AdmissionError("missing_certificate")

        try:
            with open(self.certificate_path, "r") as f:
                raw = yaml.safe_load(f)
        except Exception as e:
            raise AdmissionError(f"invalid_certificate_yaml: {e}")

        if not isinstance(raw, dict):
            raise AdmissionError("invalid_certificate_structure")

        cert = raw.get("runtime_certificate")
        if not isinstance(cert, dict):
            raise AdmissionError("invalid_certificate_schema")

        self.certificate = cert

    # -----------------------------------------------------------------
    # SIGNATURE (CRYPTO VERIFIED)
    # -----------------------------------------------------------------

    def _validate_signature(self):
        sig = self._require("signature")

        required_fields = [
            "payload_hash",
            "signature",
            "certificate_root"
        ]

        for f in required_fields:
            if f not in sig:
                raise AdmissionError(f"missing_signature_field: {f}")

        # Reject placeholders or empty values
        if any(not str(v) or "<" in str(v) or ">" in str(v) for v in sig.values()):
            raise AdmissionError("invalid_signature_fields")

        # Reconstruct payload
        payload = {
            k: v for k, v in self.certificate.items()
            if k != "signature"
        }

        payload_bytes = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        computed_hash = hashlib.sha256(payload_bytes).hexdigest()

        if sig["payload_hash"] != computed_hash:
            raise AdmissionError("payload_hash_mismatch")

        # ✅ VERIFY ED25519 SIGNATURE
        valid = verify(
            payload_bytes,
            sig["signature"],
            sig["certificate_root"],
        )

        if not valid:
            raise AdmissionError("invalid_signature")

    # -----------------------------------------------------------------
    # CONSTITUTIONAL BINDING
    # -----------------------------------------------------------------

    def _validate_constitutional_binding(self):
        binding = self._require("constitutional_binding")

        required = [
            "registry_hash",
            "execution_surfaces_hash",
            "authority_profiles_hash",
        ]

        for field in required:
            if field not in binding:
                raise AdmissionError(f"missing_binding: {field}")

        self._assert_hash("afritech/registry/registry.yaml", binding["registry_hash"])
        self._assert_hash("afritech/governance/EXECUTION_SURFACES.yaml", binding["execution_surfaces_hash"])
        self._assert_hash("afritech/inference/authority_profiles.yaml", binding["authority_profiles_hash"])

    # -----------------------------------------------------------------
    # ADMISSION GUARANTEES
    # -----------------------------------------------------------------

    def _validate_admission_guarantees(self):
        guarantees = self._require("admission_guarantees")

        for k, v in guarantees.items():
            if v is not True:
                raise AdmissionError(f"guarantee_failed: {k}")

    # -----------------------------------------------------------------
    # EXECUTION SCOPE
    # -----------------------------------------------------------------

    def _validate_execution_scope(self):
        scope = self._require("execution_scope")

        surfaces = scope.get("allowed_execution_surfaces")

        if not isinstance(surfaces, list) or not surfaces:
            raise AdmissionError("invalid_execution_surface_structure")

        if not scope.get("forbidden_surfaces_enforced", False):
            raise AdmissionError("forbidden_surfaces_not_enforced")

    # -----------------------------------------------------------------
    # ENVIRONMENT
    # -----------------------------------------------------------------

    def _validate_environment(self):
        runtime = self._require("runtime_identity")
        env = runtime.get("environment", {})

        required_flags = [
            "deterministic_mode",
            "single_runtime_assumed",
            "excludes_federation_variance",
        ]

        for flag in required_flags:
            if not env.get(flag, False):
                raise AdmissionError(f"environment_violation: {flag}")

    # -----------------------------------------------------------------
    # REPLAY
    # -----------------------------------------------------------------

    def _validate_replay_constraints(self):
        replay = self._require("replay_constraints")

        required_flags = [
            "replay_required",
            "deterministic_only",
            "transcript_required",
            "authority_isolation_enforced",
        ]

        for flag in required_flags:
            if not replay.get(flag, False):
                raise AdmissionError(f"replay_constraint_violation: {flag}")

    # -----------------------------------------------------------------
    # PROOF VALIDATION
    # -----------------------------------------------------------------

    def _validate_proof_requirements(self):
        guarantees = self._require("admission_guarantees")

        if not guarantees.get("proof_carrying_execution", False):
            raise AdmissionError("proof_carrying_execution_required")

        proof_template = self.certificate.get("proof_template")

        if proof_template:
            try:
                proof = ProofArtifact.from_certificate(proof_template)

                ProofValidator.validate(
                    proof,
                    expected_input_hash=proof.input_hash,
                    expected_output_hash=proof.output_hash,
                )

            except (ProofValidationError, KeyError) as e:
                raise AdmissionError(f"invalid_proof_template: {e}")

    # -----------------------------------------------------------------
    # EXPIRY / REVOCATION
    # -----------------------------------------------------------------

    def _validate_expiry(self):
        validity = self.certificate.get("validity", {})

        if not validity:
            return

        if validity.get("expired"):
            raise AdmissionError("certificate_expired")

        if validity.get("revoked"):
            raise AdmissionError("certificate_revoked")

    # -----------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------

    def _require(self, key: str):
        if not self.certificate or key not in self.certificate:
            raise AdmissionError(f"missing_section: {key}")
        return self.certificate[key]

    def _compute_sha256(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            raise AdmissionError(f"file_not_found: {filepath}")

        h = hashlib.sha256()

        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)

        return h.hexdigest()

    def _assert_hash(self, filepath: str, expected_hash: str):
        actual = self._compute_sha256(filepath)

        if actual != expected_hash:
            raise AdmissionError(f"hash_mismatch: {filepath}")
