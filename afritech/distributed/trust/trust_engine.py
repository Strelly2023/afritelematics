from __future__ import annotations

from typing import Dict

from afritech.distributed.trust.reputation_store import ReputationStore
from afritech.distributed.trust.scoring import TrustScoreRules
from afritech.distributed.trust.slashing import SlashingEngine, SlashingPolicy


class TrustEngine:
    def __init__(
        self,
        store: ReputationStore | None = None,
        rules: TrustScoreRules | None = None,
        slashing_policy: SlashingPolicy | None = None,
    ) -> None:
        self.store = store or ReputationStore()
        self.rules = rules or TrustScoreRules()
        self.slashing = SlashingEngine(self.store, slashing_policy)

    def record_event(self, node_id: str, event_type: str) -> Dict[str, object]:
        delta = self.rules.delta_for(event_type)
        record = self.store.adjust(node_id, delta, event_type)
        self.slashing.apply_if_needed(node_id)
        record = self.store.get(node_id)
        return {
            "node_id": record.node_id,
            "event_type": event_type,
            "delta": delta,
            "trust_score": record.trust_score,
            "banned": record.banned,
        }

    def is_allowed(self, node_id: str, minimum_score: float = 1.0) -> bool:
        return self.store.is_allowed(node_id, minimum_score)

    def snapshot(self) -> Dict[str, dict]:
        return self.store.snapshot()
