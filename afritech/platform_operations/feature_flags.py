"""Governed, tenant-scoped feature flags with mandatory expiry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class FeatureFlag:
    key: str
    owner: str
    tenant_ids: tuple[str, ...]
    enabled: bool
    expires_at: datetime
    rollout_percent: int = 100

    def __post_init__(self) -> None:
        if not self.key or not self.owner or not self.tenant_ids:
            raise ValueError("feature_flag_identity_owner_and_scope_required")
        if not 0 <= self.rollout_percent <= 100:
            raise ValueError("feature_flag_rollout_percent_invalid")
        if self.expires_at.tzinfo is None:
            raise ValueError("feature_flag_expiry_must_be_timezone_aware")


def flag_enabled(
    flag: FeatureFlag,
    *,
    tenant_id: str,
    allocation: int = 0,
    now: datetime | None = None,
) -> bool:
    current = now or datetime.now(timezone.utc)
    if current >= flag.expires_at:
        return False
    return (
        flag.enabled
        and tenant_id in flag.tenant_ids
        and 0 <= allocation < flag.rollout_percent
    )
