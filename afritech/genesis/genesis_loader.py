# afritech/genesis/genesis_loader.py

"""
AfriTech Genesis Loader

Purpose:
Load, validate, and provide access to Genesis artifact.

Responsibilities:
- load from file (YAML)
- enforce full validation (non-negotiable)
- ensure replay-safe structure
- cache validated genesis
- expose safe access to system

This is the single entry point for SYSTEM ORIGIN.
"""

import os
import yaml
from typing import Dict, Any, Optional

from afritech.genesis.genesis_validator import (
    GenesisValidator,
    GenesisValidationError,
)
from afritech.genesis.genesis_hash import (
    compute_genesis_hash,
    compute_extended_genesis_hash,
)
from afritech.genesis.genesis_trust_root import (
    compute_trust_anchor,
    trust_fingerprint,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class GenesisLoaderError(Exception):
    """Raised when genesis loading or validation fails"""
    pass


# -----------------------------------------------------------------
# LOADER
# -----------------------------------------------------------------

class GenesisLoader:

    def __init__(self, path: str):
        self.path = path
        self._genesis: Optional[Dict[str, Any]] = None
        self._fingerprint: Optional[str] = None
        self._loaded = False

    # -----------------------------------------------------------------
    # LOAD
    # -----------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        """
        Load + validate genesis (MANDATORY)

        This MUST succeed or system cannot exist.
        """

        if self._loaded:
            return self._genesis

        # ---------------------------------------------------------
        # FILE EXISTENCE
        # ---------------------------------------------------------

        if not os.path.exists(self.path):
            raise GenesisLoaderError(f"genesis_not_found: {self.path}")

        # ---------------------------------------------------------
        # LOAD YAML
        # ---------------------------------------------------------

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception as e:
            raise GenesisLoaderError(f"invalid_yaml: {e}")

        # ---------------------------------------------------------
        # SCHEMA VALIDATION
        # ---------------------------------------------------------

        if not isinstance(raw, dict) or "genesis" not in raw:
            raise GenesisLoaderError("invalid_genesis_schema")

        genesis = raw["genesis"]

        if not isinstance(genesis, dict):
            raise GenesisLoaderError("invalid_genesis_structure")

        # ---------------------------------------------------------
        # FULL VALIDATION (CRITICAL)
        # ---------------------------------------------------------

        try:
            GenesisValidator.validate(genesis)
        except GenesisValidationError as e:
            raise GenesisLoaderError(f"genesis_validation_failed: {e}")

        # ---------------------------------------------------------
        # CACHE
        # ---------------------------------------------------------

        self._genesis = genesis
        self._fingerprint = trust_fingerprint(genesis)
        self._loaded = True

        return self._genesis

    # -----------------------------------------------------------------
    # GET
    # -----------------------------------------------------------------

    def get(self) -> Dict[str, Any]:
        """
        Safe accessor (ensures loaded)
        """

        if not self._loaded:
            raise GenesisLoaderError("genesis_not_loaded")

        return self._genesis

    # -----------------------------------------------------------------
    # HASHES
    # -----------------------------------------------------------------

    def payload_hash(self) -> str:
        if not self._loaded:
            raise GenesisLoaderError("genesis_not_loaded")
        return compute_genesis_hash(self._genesis)

    def extended_hash(self) -> str:
        if not self._loaded:
            raise GenesisLoaderError("genesis_not_loaded")
        return compute_extended_genesis_hash(self._genesis)

    def trust_anchor(self) -> str:
        if not self._loaded:
            raise GenesisLoaderError("genesis_not_loaded")
        return compute_trust_anchor(self._genesis)

    def fingerprint(self) -> str:
        if not self._loaded:
            raise GenesisLoaderError("genesis_not_loaded")
        return self._fingerprint

    # -----------------------------------------------------------------
    # VERIFY AGAINST CURRENT FILE (DRIFT DETECTION)
    # -----------------------------------------------------------------

    def verify_integrity(self) -> bool:
        """
        Re-load file and compare with cached version
        """

        if not self._loaded:
            raise GenesisLoaderError("genesis_not_loaded")

        current = self._read_raw_genesis()

        try:
            GenesisValidator.validate(current)
        except Exception:
            raise GenesisLoaderError("current_genesis_invalid")

        # Compare trust anchors
        original_anchor = compute_trust_anchor(self._genesis)
        current_anchor = compute_trust_anchor(current)

        if original_anchor != current_anchor:
            raise GenesisLoaderError("genesis_drift_detected")

        return True

    # -----------------------------------------------------------------
    # INTERNAL RAW LOAD
    # -----------------------------------------------------------------

    def _read_raw_genesis(self) -> Dict[str, Any]:

        if not os.path.exists(self.path):
            raise GenesisLoaderError("genesis_file_missing")

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception as e:
            raise GenesisLoaderError(f"read_failed: {e}")

        if not isinstance(raw, dict) or "genesis" not in raw:
            raise GenesisLoaderError("invalid_structure")

        return raw["genesis"]

    # -----------------------------------------------------------------
    # TRY LOAD (SAFE)
    # -----------------------------------------------------------------

    def try_load(self) -> Optional[Dict[str, Any]]:
        try:
            return self.load()
        except Exception:
            return None

    # -----------------------------------------------------------------
    # DEBUG
    # -----------------------------------------------------------------

    def __repr__(self):
        return (
            f"<GenesisLoader loaded={self._loaded} "
            f"fingerprint={self._fingerprint}>"
        )