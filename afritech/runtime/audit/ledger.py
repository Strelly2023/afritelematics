from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from datetime import datetime
import time
from typing import Any, Dict, List

from afritech.runtime.kernel.execute import ExecutionContext


@dataclass(frozen=True)
class ExecutionBlock:
    index: int
    prev_hash: str
    proofs: List[Dict[str, Any]]
    timestamp: int
    hash: str

    @classmethod
    def build(
        cls,
        index: int,
        prev_hash: str,
        proofs: List[Dict[str, Any]],
        timestamp: int,
    ) -> "ExecutionBlock":
        block_hash = cls.compute_hash(index, prev_hash, proofs, timestamp)
        return cls(
            index=index,
            prev_hash=prev_hash,
            proofs=proofs,
            timestamp=timestamp,
            hash=block_hash,
        )

    @staticmethod
    def compute_hash(
        index: int,
        prev_hash: str,
        proofs: List[Dict[str, Any]],
        timestamp: int,
    ) -> str:
        payload = json.dumps(
            {
                "i": index,
                "prev": prev_hash,
                "proofs": proofs,
                "t": timestamp,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "proofs": list(self.proofs),
            "timestamp": self.timestamp,
            "hash": self.hash,
        }


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
        self._blocks: List[ExecutionBlock] = []

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
    # Block commit
    # -----------------------------------------------------
    def commit_block(self, proofs: List[Dict[str, Any]]) -> ExecutionBlock:
        if not isinstance(proofs, list):
            raise TypeError("proofs must be a list")

        index = len(self._blocks)
        prev_hash = self._blocks[-1].hash if self._blocks else "GENESIS"

        linked_proofs: List[Dict[str, Any]] = []
        for proof in proofs:
            if not isinstance(proof, dict):
                raise TypeError("each proof must be a dictionary")
            linked = dict(proof)
            linked["block_index"] = index
            linked_proofs.append(linked)

        block = ExecutionBlock.build(
            index=index,
            prev_hash=prev_hash,
            proofs=linked_proofs,
            timestamp=int(time.time()),
        )

        self._blocks.append(block)
        return block

    def verify_chain(self) -> bool:
        for index, block in enumerate(self._blocks):
            if block.index != index:
                return False

            expected_prev = self._blocks[index - 1].hash if index > 0 else "GENESIS"
            if block.prev_hash != expected_prev:
                return False

            expected_hash = ExecutionBlock.compute_hash(
                block.index,
                block.prev_hash,
                block.proofs,
                block.timestamp,
            )
            if block.hash != expected_hash:
                return False

        return True

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

    def get_blocks(self) -> List[Dict[str, Any]]:
        return [block.to_dict() for block in self._blocks]

    def clear(self) -> None:
        """
        Clear ledger (useful for testing only).
        """
        self.records.clear()
        self._blocks.clear()
