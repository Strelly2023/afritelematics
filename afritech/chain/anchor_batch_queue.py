"""In-process V2 anchor batching queue.

Production deployments can replace this queue with Celery, Redis, or a database
outbox. The interface stays intentionally small so API code can enqueue anchors
without coupling itself to a specific worker runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Iterable

from afritech.chain.anchor_publisher import publish_anchor_batch_v2
from afritech.chain.types import ChainReceipt


@dataclass(frozen=True)
class QueuedAnchor:
    anchor_id: str
    proof_hash: str
    context: str = "GENERAL"

    def as_contract_payload(self) -> dict[str, str]:
        return {
            "anchor_id": self.anchor_id,
            "proof_hash": self.proof_hash,
            "context": self.context,
        }


class AnchorBatchQueue:
    def __init__(self, *, max_batch_size: int = 50) -> None:
        if max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
        self.max_batch_size = max_batch_size
        self._items: list[QueuedAnchor] = []
        self._lock = threading.Lock()

    def enqueue(self, anchor_id: str, proof_hash: str, context: str = "GENERAL") -> int:
        if not anchor_id:
            raise ValueError("anchor_id is required")
        if not proof_hash:
            raise ValueError("proof_hash is required")
        with self._lock:
            self._items.append(QueuedAnchor(anchor_id, proof_hash, context))
            return len(self._items)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._items)

    def drain(self, limit: int | None = None) -> list[QueuedAnchor]:
        batch_size = limit or self.max_batch_size
        with self._lock:
            batch = self._items[:batch_size]
            self._items = self._items[batch_size:]
            return batch

    def requeue_front(self, items: Iterable[QueuedAnchor]) -> None:
        with self._lock:
            self._items = list(items) + self._items

    def flush(
        self,
        *,
        profile_name: str | None = None,
        require_live: bool = False,
    ) -> ChainReceipt | None:
        batch = self.drain()
        if not batch:
            return None
        try:
            return publish_anchor_batch_v2(
                [item.as_contract_payload() for item in batch],
                profile_name=profile_name,
                require_live=require_live,
            )
        except Exception:
            self.requeue_front(batch)
            raise


DEFAULT_ANCHOR_BATCH_QUEUE = AnchorBatchQueue()
