# afritech/runtime/activation/runtime_admission.py

"""
AfriTech Runtime Admission Validator

Purpose:
Constitutionally admit the runtime under a specific epoch by validating
registry, epoch, kernel, authority, replay, and certificate bindings.

IMPORTANT:
- Admission ONLY (no execution, no state mutation)
- Deterministic, replay-safe, seal-safe
- Any modification requires ADR → Epoch → Registry reseal
"""

from __future__ import annotations

import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from afritech.trace.trace_engine import TraceEngine


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
    """

    # =============================================================
    # INIT
    # =============================================================

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()

        # Core artifacts (ABSOLUTE, CANONICAL PATHS)
        self.registry_path = self.base_path / "registry/registry.yaml"
        self.attestation_path = self.base_path / "registry/attestation.yaml"
        self.surfaces_path = self.base_path / "governance/EXECUTION_SURFACES.yaml"
        self.authority_path = self.base_path / "inference/authority_profiles.yaml"
        self.certificate_path = (
            self.base_path
            / "proof/certificates/runtime_epoch_0006.cert"
        )

        # Loaded data
        self.registry: Optional[Dict[str, Any]] = None
        self.attestation: Optional[Dict[str, Any]] = None
        self.surfaces: Optional[Dict[str, Any]] = None
        self.authority: Optional[Dict[str, Any]] = None
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
    # YAML LOADING (SAFE)
    # =============================================================

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeAdmissionError(
                f"Failed to load YAML {path}: {e}"
            )

        if not isinstance(data, dict):
            raise RuntimeAdmissionError(
                f"Invalid YAML structure in {path}"
            )

        return data

    def _load_all(self) -> None:
        self._assert_exists(self.registry_path, "registry.yaml")
        self._assert_exists(self.attestation_path, "attestation.yaml")
        self._assert_exists(self.surfaces_path, "EXECUTION_SURFACES.yaml")
        self._assert_exists(self.authority_path, "authority_profiles.yaml")
        self._assert_exists(self.certificate_path, "runtime certificate")

        self.registry = self._load_yaml(self.registry_path)
        self.attestation = self._load_yaml(self.attestation_path)
        self.surfaces = self._load_yaml(self.surfaces_path)
        self.authority = self._load_yaml(self.authority_path)
        self.certificate = self._load_yaml(self.certificate_path)

    # =============================================================
    # CANONICAL HASHING
    # =============================================================

    @staticmethod
    def _canonical_yaml(data: Dict[str, Any]) -> str:
        """
        Strict deterministic YAML serialization.
        Prevents cross-environment drift.
        """
        return yaml.dump(
            data,
            sort_keys=True,
            allow_unicode=False,
            default_flow_style=False,
            width=4096,
        )

    def _sha256_yaml(self, path: Path) -> str:
        data = self._load_yaml(path)
        canonical = self._canonical_yaml(data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # =============================================================
    # HASH COMPUTATION
    # =============================================================

    def _compute_registry_hash(self) -> str:
        return self._sha256_yaml(self.registry_path)

    def _compute_surfaces_hash(self) -> str:
        return self._sha256_yaml(self.surfaces_path)

    def _compute_authority_hash(self) -> str:
        return self._sha256_yaml(self.authority_path)

    def _compute_epoch_hash(self) -> str:
        epoch_num = self.registry["epoch"]["current"]
        epoch_file = (
            self.base_path
            / f"registry/epochs/EPOCH_000{epoch_num}.yaml"
        )
        self._assert_exists(epoch_file, "epoch file")
        return self._sha256_yaml(epoch_file)

    # =============================================================
    # KERNEL ROOT HASH (ORDERED, STRICT)
    # =============================================================

    def _compute_kernel_root_hash(self) -> str:
        kernel_hashes = self.attestation["attestation"]["kernel_hashes"]

        order = [
            "lean",
            "kernel",
            "state",
            "guards",
            "runtime",
            "runtime_activation",
            "runtime_engine",
            "proof",
            "evaluation",
        ]

        try:
            joined = "".join(
                kernel_hashes[k]["hash"] for k in order
            ).encode("utf-8")
        except KeyError as e:
            raise RuntimeAdmissionError(
                f"Missing kernel hash entry: {e}"
            )

        return hashlib.sha256(joined).hexdigest()

    # =============================================================
    # REPLAY VERIFIER HASH
    # =============================================================

    def _compute_replay_verifier_hash(self) -> str:
        verifier_root = self.base_path / "verify"

        if not verifier_root.exists():
            raise RuntimeAdmissionError(
                "Missing replay verifier directory"
            )

        hasher = hashlib.sha256()

        for path in sorted(verifier_root.glob("**/*.py")):
            if "tests" in path.parts:
                continue
            with open(path, "rb") as f:
                hasher.update(f.read())

        return hasher.hexdigest()

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
            raise RuntimeAdmissionError(
                "Signature scope mismatch"
            )

        payload = {k: cert[k] for k in actual_scope}

        computed = hashlib.sha256(
            self._canonical_yaml(payload).encode("utf-8")
        ).hexdigest()

        if computed != sig["signed_payload_hash"]:
            raise RuntimeAdmissionError(
                "Signature payload hash mismatch"
            )

    # =============================================================
    # CONSTITUTIONAL BINDINGS
    # =============================================================

    def _validate_bindings(self) -> None:
        binding = self.certificate["runtime_certificate"]["constitutional_binding"]

        if binding["epoch"] != self.registry["epoch"]["current"]:
            raise RuntimeAdmissionError("Epoch mismatch")

        if binding["registry_hash"] != self._compute_registry_hash():
            raise RuntimeAdmissionError("Registry hash mismatch")

        if binding["epoch_hash"] != self._compute_epoch_hash():
            raise RuntimeAdmissionError("Epoch hash mismatch")

        if binding["execution_surfaces_hash"] != self._compute_surfaces_hash():
            raise RuntimeAdmissionError("Execution surfaces hash mismatch")

        if binding["authority_profiles_hash"] != self._compute_authority_hash():
            raise RuntimeAdmissionError("Authority profiles mismatch")

        if binding["kernel_root_hash"] != self._compute_kernel_root_hash():
            raise RuntimeAdmissionError("Kernel hash mismatch")

        if binding["verifier_hash"] != self._compute_replay_verifier_hash():
            raise RuntimeAdmissionError("Replay verifier mismatch")

    # =============================================================
    # SURFACE ADMISSION
    # =============================================================

    def _validate_execution_surfaces(self) -> None:
        allowed = self.surfaces.get("allowed_execution_surfaces", {})

        required = [
            "runtime_activation",
            "runtime_engine",
            "proof",
            "evaluation",
        ]

        for surface in required:
            if surface not in allowed:
                raise RuntimeAdmissionError(
                    f"Undeclared execution surface: {surface}"
                )

    # =============================================================
    # PUBLIC ENTRY
    # =============================================================

    def validate(
        self,
        trace: Optional[TraceEngine] = None,
    ) -> bool:
        """
        Perform full constitutional runtime admission.

        TRACE:
        - Admission events MAY be traced
        - Execution MUST NOT occur here
        """

        if trace:
            trace.record("runtime_admission", {"status": "begin"})

        self._load_all()
        self._validate_certificate()
        self._validate_bindings()
        self._validate_execution_surfaces()

        if trace:
            trace.complete(
                "runtime_admission",
                {"status": "admitted"},
            )

        return True

    # =============================================================
    # REQUEST VALIDATION (OPTIONAL)
    # =============================================================

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        Validate execution request metadata (pre-admission).
        """

        if "authority_profile" not in request:
            raise RuntimeAdmissionError("Missing authority_profile")

        if "replay_requirements" not in request:
            raise RuntimeAdmissionError("Missing replay_requirements")

        if request["authority_profile"] not in self.authority["authority_profiles"]:
            raise RuntimeAdmissionError("Invalid authority profile")

        if not request["replay_requirements"].get("deterministic", False):
            raise RuntimeAdmissionError(
                "Non-deterministic request forbidden"
            )

        return True