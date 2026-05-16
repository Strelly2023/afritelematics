"""
Shared runtime types

Rules:
- MUST NOT depend on runtime.engine
- MUST NOT depend on guards
- PURE data + deterministic logic only
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import hashlib
import json


class ExecutionResult:
    """
    Deterministic execution result with proof + trace binding
    """

    def __init__(
        self,
        success: bool,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        context=None,
        proof=None,
        zk_proof=None,
        trace_hash: Optional[str] = None,
    ):
        self.success = success
        self.output = output or {}
        self.error = error
        self.context = context
        self.proof = proof
        self.zk_proof = zk_proof
        self.trace_hash = trace_hash

        self.timestamp = (
            context.timestamp if context else "UNDEFINED_TIMESTAMP"
        )

        self.result_hash = self._compute_hash()

    # -------------------------------------------------------------
    # CANONICAL JSON
    # -------------------------------------------------------------
    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> str:
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    # -------------------------------------------------------------
    # HASH
    # -------------------------------------------------------------
    def _compute_hash(self) -> str:
        base = {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "trace_hash": self.trace_hash,
        }

        return hashlib.sha256(
            self._canonical_json(base).encode("utf-8")
        ).hexdigest()

    # -------------------------------------------------------------
    # VERIFY
    # -------------------------------------------------------------
    def verify(self) -> bool:
        return self.result_hash == self._compute_hash()

    # -------------------------------------------------------------
    # SERIALIZE
    # -------------------------------------------------------------
    def to_dict(self):
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "context": self.context.to_dict() if self.context else None,
            "result_hash": self.result_hash,
            "trace_hash": self.trace_hash,
            "timestamp": self.timestamp,
            "proof": self.proof.to_dict() if self.proof else None,
            "zk_proof": self.zk_proof.to_dict() if self.zk_proof else None,
        }

    def __repr__(self):
        return f"<ExecutionResult success={self.success} hash={self.result_hash[:10]}...>"
