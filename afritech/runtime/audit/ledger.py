from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

from afritech.runtime.kernel.execute import ExecutionContext


class AuditLedger:
    """
    Sovereign Audit Ledger.

    Responsibilities:
    - Record every execution event
    - Ensure deterministic hashing of results
    - Preserve immutable trace (in-memory for now)
    """

    def __init__(self) -> None:
        # ✅ Strong typing
        self.records: List[Dict[str, Any]] = []

    # -----------------------------------------------------
    # Record execution
    # -----------------------------------------------------
    def record(
        self,
        fn_name: str,
        result: Any,
        context: ExecutionContext,
    ) -> None:
        """
        Record an execution event.

        Guarantees:
        - Timestamped entry
        - Deterministic result hashing
        - Epoch traceability
        """

        if not isinstance(fn_name, str):
            raise TypeError("Function name must be a string")

        if not isinstance(context, ExecutionContext):
            raise TypeError("Invalid ExecutionContext")

        # ✅ Safe epoch extraction
        epoch_number = context.epoch_snapshot.semantic_epoch.number

        entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "function": fn_name,
            "result_hash": self._hash(result),
            "epoch": epoch_number,
        }

        self.records.append(entry)

    # -----------------------------------------------------
    # Deterministic hash
    # -----------------------------------------------------
    def _hash(self, data: Any) -> str:
        """
        Deterministic hashing of execution result.

        Rules:
        - JSON serialization (string safe)
        - Stable encoding
        """

        try:
            serialized = json.dumps(
                data,
                sort_keys=True,   # ✅ ensures determinism
                default=str       # ✅ fallback for non-serializable
            )
        except Exception:
            # Fallback safety (never fail audit)
            serialized = str(data)

        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # -----------------------------------------------------
    # Accessors (optional but useful)
    # -----------------------------------------------------
    def get_records(self) -> List[Dict[str, Any]]:
        """
        Return all audit records.
        """
        return self.records

    def clear(self) -> None:
        """
        Clear ledger (useful for testing only).
        """
        self.records.clear()