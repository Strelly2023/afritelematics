from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.pki import PKIService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class SignedAuditChainService:
    """Store-backed signed audit chain helper."""

    def __init__(
        self,
        repository: PlatformStore | None = None,
        pki_service: PKIService | None = None,
    ) -> None:
        self.repository = repository or get_platform_store()
        self.pki_service = pki_service or PKIService(self.repository)

    def append(
        self,
        *,
        organization_id: str,
        event_type: str,
        actor_user_id: str,
        actor_role: str,
        target: str,
        status: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self.repository.record_audit_event(
            organization_id=organization_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=target,
            status=status,
            payload=payload,
        )

    def latest(self, organization_id: str | None = None) -> dict[str, Any] | None:
        events = self.repository.list_signed_audit_chain_events(organization_id=organization_id, limit=1)
        return events[0] if events else None

    def history(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_signed_audit_chain_events(organization_id=organization_id, limit=limit)

    def verify(self, organization_id: str | None = None) -> dict[str, Any]:
        valid = self.repository.verify_signed_audit_chain(organization_id=organization_id)
        history = self.history(organization_id=organization_id)
        return {
            "organization_id": organization_id or "all",
            "valid": valid,
            "count": len(history),
            "latest": history[0] if history else None,
        }


__all__ = ["SignedAuditChainService"]
