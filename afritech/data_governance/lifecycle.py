"""Classification, residency, retention, and deletion enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class RetentionClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    OPERATIONAL = "OPERATIONAL"
    AUDIT = "AUDIT"
    LEGAL_HOLD = "LEGAL_HOLD"


RETENTION_DAYS = {
    RetentionClass.TRANSIENT: 1,
    RetentionClass.OPERATIONAL: 90,
    RetentionClass.AUDIT: 2555,
    RetentionClass.LEGAL_HOLD: None,
}


@dataclass(frozen=True)
class DataLifecyclePolicy:
    resource: str
    classification: DataClassification
    retention: RetentionClass
    allowed_regions: tuple[str, ...]
    deletion_requires_approval: bool


@dataclass(frozen=True)
class DeletionDecision:
    allowed: bool
    reason: str
    tombstone_required: bool
    evidence_required: bool


def validate_residency(policy: DataLifecyclePolicy, region: str) -> None:
    if region not in policy.allowed_regions:
        raise ValueError(f"data_residency_violation:{policy.resource}:{region}")


def retention_deadline(
    policy: DataLifecyclePolicy,
    *,
    created_at: datetime,
) -> datetime | None:
    days = RETENTION_DAYS[policy.retention]
    return None if days is None else created_at + timedelta(days=days)


def evaluate_deletion(
    policy: DataLifecyclePolicy,
    *,
    created_at: datetime,
    now: datetime | None = None,
    approved: bool = False,
) -> DeletionDecision:
    current = now or datetime.now(timezone.utc)
    deadline = retention_deadline(policy, created_at=created_at)
    if deadline is None:
        return DeletionDecision(False, "legal_hold_active", True, True)
    if current < deadline:
        return DeletionDecision(False, "retention_period_active", True, True)
    if policy.deletion_requires_approval and not approved:
        return DeletionDecision(False, "deletion_approval_required", True, True)
    return DeletionDecision(True, "retention_satisfied", True, True)
