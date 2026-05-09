# afritech/trace/trace_store.py

"""
AfriTech Trace Store

Purpose:
Persist and retrieve trace artifacts with integrity guarantees.

Responsibilities:
- save/load trace deterministically
- enforce canonical serialization
- verify integrity on load
- maintain optional storage metadata
- support multiple storage backends (file-first)

This module ensures TRACE persistence remains:
    deterministic
    replay-safe
    tamper-detectable
"""

import json
import os
from typing import Dict, Any, Optional

from afritech.trace.trace_hash import (
    canonical_json,
    compute_trace_root,
)
from afritech.trace.trace_validator import TraceValidator, TraceValidationError


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class TraceStoreError(Exception):
    pass


# -----------------------------------------------------------------
# STORE
# -----------------------------------------------------------------

class TraceStore:

    # -----------------------------------------------------------------
    # SAVE TRACE
    # -----------------------------------------------------------------

    @staticmethod
    def save(
        trace: Dict[str, Any],
        path: str,
        overwrite: bool = False,
    ) -> None:
        """
        Persist trace to disk using canonical serialization
        """

        if os.path.exists(path) and not overwrite:
            raise TraceStoreError(f"file_exists: {path}")

        # ✅ Validate before save (non-negotiable)
        try:
            TraceValidator.validate(trace)
        except TraceValidationError as e:
            raise TraceStoreError(f"invalid_trace: {e}")

        # ✅ Canonical serialization (CRITICAL)
        serialized = canonical_json(trace)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(serialized)
        except Exception as e:
            raise TraceStoreError(f"write_failed: {e}")

    # -----------------------------------------------------------------
    # LOAD TRACE
    # -----------------------------------------------------------------

    @staticmethod
    def load(
        path: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Load trace from disk and optionally validate
        """

        if not os.path.exists(path):
            raise TraceStoreError(f"file_not_found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise TraceStoreError(f"load_failed: {e}")

        if validate:
            try:
                TraceValidator.validate(data)
            except TraceValidationError as e:
                raise TraceStoreError(f"invalid_trace_on_load: {e}")

        return data

    # -----------------------------------------------------------------
    # SAFE LOAD (NO EXCEPTION)
    # -----------------------------------------------------------------

    @staticmethod
    def try_load(path: str) -> Optional[Dict[str, Any]]:
        try:
            return TraceStore.load(path)
        except Exception:
            return None

    # -----------------------------------------------------------------
    # DELETE TRACE
    # -----------------------------------------------------------------

    @staticmethod
    def delete(path: str) -> None:
        if not os.path.exists(path):
            raise TraceStoreError("file_not_found")

        try:
            os.remove(path)
        except Exception as e:
            raise TraceStoreError(f"delete_failed: {e}")

    # -----------------------------------------------------------------
    # EXISTS
    # -----------------------------------------------------------------

    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)

    # -----------------------------------------------------------------
    # HASH FILE (INTEGRITY CHECK)
    # -----------------------------------------------------------------

    @staticmethod
    def file_hash(path: str) -> str:
        """
        Compute SHA256 of stored file
        """

        import hashlib

        if not os.path.exists(path):
            raise TraceStoreError("file_not_found")

        h = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)

        return h.hexdigest()

    # -----------------------------------------------------------------
    # VERIFY STORED TRACE (STRONG CHECK)
    # -----------------------------------------------------------------

    @staticmethod
    def verify(path: str) -> bool:
        """
        Validate and re-check root hash
        """

        trace = TraceStore.load(path, validate=True)

        events = trace["events"]

        expected_root = compute_trace_root(events)

        if trace["trace_root_hash"] != expected_root:
            raise TraceStoreError("trace_root_mismatch")

        return True

    # -----------------------------------------------------------------
    # SAVE WITH METADATA WRAPPER
    # -----------------------------------------------------------------

    @staticmethod
    def save_with_metadata(
        trace: Dict[str, Any],
        path: str,
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Save trace with additional metadata wrapper
        """

        package = {
            "trace": trace,
            "metadata": metadata or {},
        }

        serialized = canonical_json(package)

        if os.path.exists(path) and not overwrite:
            raise TraceStoreError("file_exists")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(serialized)
        except Exception as e:
            raise TraceStoreError(f"write_failed: {e}")

    # -----------------------------------------------------------------
    # LOAD WITH METADATA
    # -----------------------------------------------------------------

    @staticmethod
    def load_with_metadata(path: str) -> Dict[str, Any]:
        """
        Load wrapped trace package
        """

        if not os.path.exists(path):
            raise TraceStoreError("file_not_found")

        try:
            with open(path, "r", encoding="utf-8") as f:
                package = json.load(f)
        except Exception as e:
            raise TraceStoreError(f"load_failed: {e}")

        if "trace" not in package:
            raise TraceStoreError("invalid_package_format")

        TraceValidator.validate(package["trace"])

        return package

    # -----------------------------------------------------------------
    # EXPORT (PORTABILITY)
    # -----------------------------------------------------------------

    @staticmethod
    def export(trace: Dict[str, Any]) -> str:
        """
        Return canonical string representation
        """

        try:
            TraceValidator.validate(trace)
            return canonical_json(trace)
        except Exception as e:
            raise TraceStoreError(f"export_failed: {e}")

    # -----------------------------------------------------------------
    # IMPORT (SAFE)
    # -----------------------------------------------------------------

    @staticmethod
    def import_trace(serialized: str) -> Dict[str, Any]:
        """
        Parse and validate canonical trace string
        """

        try:
            trace = json.loads(serialized)
        except Exception as e:
            raise TraceStoreError(f"invalid_json: {e}")

        try:
            TraceValidator.validate(trace)
        except TraceValidationError as e:
            raise TraceStoreError(f"invalid_trace: {e}")

        return trace

    # -----------------------------------------------------------------
    # DEBUG
    # -----------------------------------------------------------------

    def __repr__(self):
        return "<TraceStore deterministic-persistence>"