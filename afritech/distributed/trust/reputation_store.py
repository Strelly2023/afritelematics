from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ReputationRecord:
    node_id: str
    trust_score: float = 100.0
    penalties: List[str] = field(default_factory=list)
    banned: bool = False


class ReputationStore:
    def __init__(self) -> None:
        self._records: Dict[str, ReputationRecord] = {}

    def get(self, node_id: str) -> ReputationRecord:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("node_id must be non-empty")
        if node_id not in self._records:
            self._records[node_id] = ReputationRecord(node_id=node_id)
        return self._records[node_id]

    def adjust(self, node_id: str, delta: float, reason: str = "") -> ReputationRecord:
        record = self.get(node_id)
        record.trust_score = max(0.0, min(100.0, record.trust_score + delta))
        if reason:
            record.penalties.append(reason)
        return record

    def ban(self, node_id: str, reason: str) -> ReputationRecord:
        record = self.get(node_id)
        record.banned = True
        if reason:
            record.penalties.append(reason)
        return record

    def is_allowed(self, node_id: str, minimum_score: float = 1.0) -> bool:
        record = self.get(node_id)
        return not record.banned and record.trust_score >= minimum_score

    def snapshot(self) -> Dict[str, dict]:
        return {
            node_id: {
                "node_id": record.node_id,
                "trust_score": record.trust_score,
                "penalties": list(record.penalties),
                "banned": record.banned,
            }
            for node_id, record in sorted(self._records.items())
        }
