from __future__ import annotations

from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class RetentionService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def ensure_defaults(self, organization_id: str) -> dict[str, Any]:
        return self.repository.retention_check(organization_id=organization_id)

    def list_policies(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_retention_policies(organization_id=organization_id)

    def set_policy(
        self,
        *,
        organization_id: str,
        record_type: str,
        retention_days: int,
        legal_hold: bool,
        deletion_allowed: bool,
    ) -> dict[str, Any]:
        return self.repository.store_retention_policy(
            organization_id=organization_id,
            record_type=record_type,
            retention_days=retention_days,
            legal_hold=legal_hold,
            deletion_allowed=deletion_allowed,
        )

    def check(self, organization_id: str | None = None) -> dict[str, Any]:
        return self.repository.retention_check(organization_id=organization_id)
