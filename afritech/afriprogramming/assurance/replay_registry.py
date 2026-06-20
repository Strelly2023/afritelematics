from __future__ import annotations

from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class ReplayRegistry:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def register(
        self,
        *,
        organization_id: str,
        deployment_id: str,
        proof_id: str,
        receipt_id: str,
        audit_hash: str,
    ) -> dict[str, Any]:
        record = self.repository.store_replay_record(
            organization_id=organization_id,
            deployment_id=deployment_id,
            proof_id=proof_id,
            receipt_id=receipt_id,
            audit_hash=audit_hash,
        )
        self.repository.publish_trust_stream_event(
            organization_id=organization_id,
            event_type="replay.registered",
            payload=record,
        )
        return record

    def lookup(self, replay_id: str, *, organization_id: str | None = None) -> dict[str, Any] | None:
        return self.repository.get_replay_record(replay_id=replay_id, organization_id=organization_id)

    def latest(self, *, organization_id: str | None = None) -> dict[str, Any] | None:
        return self.repository.latest_replay_record(organization_id=organization_id)
