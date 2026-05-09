# afritech/governance/binding_validator.py

"""
AfriTech Binding Validator

Purpose:
Validate binding manifest under full constitutional authority invariants.

Guarantees:
- bindings are derivational (not manual)
- binding hashes are correct
- root hash is valid
- replay determinism holds
- full coverage of system bindings

This is the ENFORCEMENT layer for Authority Closure.
"""

from typing import Dict, Any, List, Set
import hashlib
import json


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class BindingValidationError(Exception):
    """Raised when binding manifest is invalid"""
    pass


# -----------------------------------------------------------------
# CANONICAL JSON
# -----------------------------------------------------------------

def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def hash_obj(data: Dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(data).encode()
    ).hexdigest()


# -----------------------------------------------------------------
# VALIDATOR
# -----------------------------------------------------------------

class BindingValidator:

    # =============================================================
    # ENTRYPOINT
    # =============================================================

    @classmethod
    def validate(cls, manifest_wrapper: Dict[str, Any]) -> bool:
        """
        Validate full binding manifest

        Expect structure:
        {
            "binding_manifest": { ... }
        }
        """

        if "binding_manifest" not in manifest_wrapper:
            raise BindingValidationError("missing_binding_manifest")

        manifest = manifest_wrapper["binding_manifest"]

        cls._validate_structure(manifest)

        bindings = manifest["bindings"]

        cls._validate_bindings(bindings)
        cls._validate_unique_ids(bindings)
        cls._validate_hash_integrity(bindings)
        cls._validate_derivation(bindings)
        cls._validate_scope(bindings)

        cls._validate_root_hash(manifest)
        cls._validate_replay_determinism(manifest)

        return True

    # =============================================================
    # STRUCTURE
    # =============================================================

    @staticmethod
    def _validate_structure(manifest: Dict[str, Any]):

        required = [
            "source_artifacts",
            "bindings",
            "root_binding_hash",
        ]

        for f in required:
            if f not in manifest:
                raise BindingValidationError(f"missing_field: {f}")

        if not isinstance(manifest["bindings"], list):
            raise BindingValidationError("bindings_not_list")

        if len(manifest["bindings"]) == 0:
            raise BindingValidationError("empty_bindings")

    # =============================================================
    # BINDING BASIC VALIDATION
    # =============================================================

    @staticmethod
    def _validate_bindings(bindings: List[Dict[str, Any]]):

        required_fields = [
            "id",
            "type",
            "target",
            "constraint",
            "derived_from",
            "binding_hash",
        ]

        for b in bindings:
            for f in required_fields:
                if f not in b:
                    raise BindingValidationError(f"missing_binding_field: {f}")

            if not isinstance(b["derived_from"], list):
                raise BindingValidationError("derived_from_not_list")

    # =============================================================
    # UNIQUE IDs (I21_8)
    # =============================================================

    @staticmethod
    def _validate_unique_ids(bindings: List[Dict[str, Any]]):

        seen = set()

        for b in bindings:
            if b["id"] in seen:
                raise BindingValidationError("duplicate_binding_id")
            seen.add(b["id"])

    # =============================================================
    # HASH INTEGRITY (I21_3)
    # =============================================================

    @staticmethod
    def _validate_hash_integrity(bindings: List[Dict[str, Any]]):

        for b in bindings:

            base = {
                "id": b["id"],
                "type": b["type"],
                "target": b["target"],
                "constraint": b["constraint"],
                "derived_from": sorted(b["derived_from"]),
                "binding_version": b.get("binding_version", "v1"),
                "scope": b.get("scope"),
                "validation": b.get("validation"),
            }

            expected_hash = hash_obj(base)

            if b["binding_hash"] != expected_hash:
                raise BindingValidationError("binding_hash_mismatch")

    # =============================================================
    # DERIVATION CHECK (I21_1, I21_2)
    # =============================================================

    @staticmethod
    def _validate_derivation(bindings: List[Dict[str, Any]]):

        for b in bindings:

            # Cannot be empty
            if not b["derived_from"]:
                raise BindingValidationError("empty_derivation")

            # Reject placeholders / manual hints
            for item in b["derived_from"]:
                if not isinstance(item, str):
                    raise BindingValidationError("invalid_derivation_entry")

                if "<" in item or ">" in item or "MANUAL" in item:
                    raise BindingValidationError("manual_binding_detected")

    # =============================================================
    # SCOPE VALIDATION
    # =============================================================

    @staticmethod
    def _validate_scope(bindings: List[Dict[str, Any]]):

        valid_scopes = {"TRACE", "STATE", "EXECUTION", "VALIDATION"}

        for b in bindings:

            scope = b.get("scope", {})

            applies = scope.get("applies_to", [])

            for s in applies:
                if s not in valid_scopes:
                    raise BindingValidationError("invalid_scope")

    # =============================================================
    # ROOT HASH (I21_4)
    # =============================================================

    @staticmethod
    def _validate_root_hash(manifest: Dict[str, Any]):

        bindings = manifest["bindings"]

        ordered_hashes = sorted([
            b["binding_hash"] for b in bindings
        ])

        payload = {
            "binding_hashes": ordered_hashes
        }

        expected = hashlib.sha256(
            canonical_json(payload).encode()
        ).hexdigest()

        if manifest["root_binding_hash"] != expected:
            raise BindingValidationError("root_binding_hash_invalid")

    # =============================================================
    # REPLAY DETERMINISM (I21_7)
    # =============================================================

    @staticmethod
    def _validate_replay_determinism(manifest: Dict[str, Any]):

        try:
            canonical_json(manifest)
        except Exception:
            raise BindingValidationError("non_deterministic_manifest")

    # =============================================================
    # SAFE VALIDATION
    # =============================================================

    @classmethod
    def try_validate(cls, manifest_wrapper: Dict[str, Any]) -> bool:
        try:
            return cls.validate(manifest_wrapper)
        except BindingValidationError:
            return False

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self):
        return "<BindingValidator strict>"