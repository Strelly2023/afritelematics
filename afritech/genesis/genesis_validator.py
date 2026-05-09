# afritech/genesis/genesis_validator.py

"""
AfriTech Genesis Validator

Purpose:
Validate Genesis under full constitutional invariants.

Guarantees:
- structural correctness
- authority root enforcement
- payload hash correctness
- trust anchor integrity
- cryptographic authenticity (Ed25519)
- replay determinism

This is the FINAL AUTHORITY CHECKPOINT for system origin.
"""

from typing import Dict, Any

from afritech.genesis.genesis_hash import (
    compute_genesis_hash,
    validate_payload_hash,
    canonical_json,
)
from afritech.genesis.genesis_signature import (
    verify_genesis_signature,
)
from afritech.genesis.genesis_trust_root import (
    verify_trust_anchor,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class GenesisValidationError(Exception):
    """Raised when Genesis violates invariants"""
    pass


# -----------------------------------------------------------------
# VALIDATOR
# -----------------------------------------------------------------

class GenesisValidator:

    # -------------------------------------------------------------
    # ENTRYPOINT
    # -------------------------------------------------------------

    @classmethod
    def validate(cls, genesis: Dict[str, Any]) -> bool:

        cls._validate_structure(genesis)
        cls._validate_identity(genesis)
        cls._validate_authority_root(genesis)

        cls._validate_hash_binding(genesis)
        cls._validate_trust_anchor(genesis)
        cls._validate_signature(genesis)

        cls._validate_determinism(genesis)
        cls._validate_no_external_state(genesis)

        return True

    # -------------------------------------------------------------
    # STRUCTURE VALIDATION (I17_4)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_structure(genesis: Dict[str, Any]):

        required_fields = [
            "id",
            "issued_at",
            "constitutional_version",
            "initial_epoch",
            "authority_seed",
            "registry_origin_hash",
            "invariant_root_hash",
            "constitutional_surface_hash",
            "execution_surface_hash",
            "trust_anchor",
            "epoch_zero_signature",
        ]

        for field in required_fields:
            if field not in genesis:
                raise GenesisValidationError(f"missing_field: {field}")

        if not isinstance(genesis, dict):
            raise GenesisValidationError("invalid_genesis_structure")

    # -------------------------------------------------------------
    # IDENTITY VALIDATION
    # -------------------------------------------------------------

    @staticmethod
    def _validate_identity(genesis: Dict[str, Any]):

        if not isinstance(genesis["id"], str):
            raise GenesisValidationError("invalid_genesis_id")

        if not isinstance(genesis["constitutional_version"], int):
            raise GenesisValidationError("invalid_constitutional_version")

    # -------------------------------------------------------------
    # AUTHORITY ROOT (I17_2, I17_3)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_authority_root(genesis: Dict[str, Any]):

        if genesis["authority_seed"] != "REGISTRY":
            raise GenesisValidationError("invalid_authority_seed")

        if genesis["initial_epoch"] != 0:
            raise GenesisValidationError("invalid_initial_epoch")

    # -------------------------------------------------------------
    # HASH BINDING (I17_7)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_hash_binding(genesis: Dict[str, Any]):

        try:
            validate_payload_hash(genesis)
        except Exception as e:
            raise GenesisValidationError(f"payload_hash_invalid: {e}")

    # -------------------------------------------------------------
    # TRUST ANCHOR (I17_5)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_trust_anchor(genesis: Dict[str, Any]):

        try:
            verify_trust_anchor(genesis)
        except Exception as e:
            raise GenesisValidationError(f"trust_anchor_invalid: {e}")

    # -------------------------------------------------------------
    # SIGNATURE VALIDATION (I17_6)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_signature(genesis: Dict[str, Any]):

        if "epoch_zero_signature" not in genesis:
            raise GenesisValidationError("missing_signature")

        sig = genesis["epoch_zero_signature"]

        required = ["signature", "public_key", "payload_hash"]

        for f in required:
            if f not in sig:
                raise GenesisValidationError(f"missing_signature_field: {f}")

        try:
            valid = verify_genesis_signature(genesis)
        except Exception as e:
            raise GenesisValidationError(f"signature_verification_failed: {e}")

        if not valid:
            raise GenesisValidationError("invalid_signature")

    # -------------------------------------------------------------
    # DETERMINISTIC SERIALIZATION (I17_8)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_determinism(genesis: Dict[str, Any]):

        try:
            canonical_json(genesis)
        except Exception:
            raise GenesisValidationError("non_deterministic_serialization")

    # -------------------------------------------------------------
    # NO EXTERNAL STATE (I17_9)
    # -------------------------------------------------------------

    @staticmethod
    def _validate_no_external_state(genesis: Dict[str, Any]):

        # Enforce no dynamic references
        forbidden_patterns = ["<", ">", "TO_BE_", "UNRESOLVED"]

        serialized = str(genesis)

        for pattern in forbidden_patterns:
            if pattern in serialized:
                raise GenesisValidationError("unresolved_placeholder_detected")

    # -------------------------------------------------------------
    # SAFE VALIDATION
    # -------------------------------------------------------------

    @classmethod
    def try_validate(cls, genesis: Dict[str, Any]) -> bool:
        try:
            return cls.validate(genesis)
        except GenesisValidationError:
            return False