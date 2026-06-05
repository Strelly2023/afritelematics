from __future__ import annotations

from dataclasses import dataclass

from afritech.distributed.trust.reputation_store import ReputationStore


@dataclass(frozen=True)
class SlashingPolicy:
    temporary_ban_threshold: float = 25.0
    permanent_ban_threshold: float = 5.0


class SlashingEngine:
    def __init__(
        self,
        store: ReputationStore,
        policy: SlashingPolicy | None = None,
    ) -> None:
        self.store = store
        self.policy = policy or SlashingPolicy()

    def apply_if_needed(self, node_id: str) -> None:
        record = self.store.get(node_id)
        if record.trust_score <= self.policy.permanent_ban_threshold:
            self.store.ban(node_id, "permanent_exclusion")
        elif record.trust_score <= self.policy.temporary_ban_threshold:
            self.store.ban(node_id, "temporary_ban")
