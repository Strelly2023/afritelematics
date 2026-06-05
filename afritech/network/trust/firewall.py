from __future__ import annotations

from afritech.distributed.trust.trust_engine import TrustEngine


class TrustFirewall:
    def __init__(self, trust_engine: TrustEngine, minimum_score: float = 1.0) -> None:
        self.trust_engine = trust_engine
        self.minimum_score = minimum_score

    def allow_peer(self, node_id: str) -> bool:
        if not isinstance(node_id, str) or not node_id:
            return False
        return self.trust_engine.is_allowed(node_id, self.minimum_score)
