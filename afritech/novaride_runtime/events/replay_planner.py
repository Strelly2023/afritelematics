"""Replay planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.identifiers import new_id


class ReplayMode(StrEnum):
    AGGREGATE = "aggregate"
    CORRELATION_ID = "correlation_id"
    TENANT = "tenant"
    REGION = "region"
    EVENT_TYPE_RANGE = "event_type_range"
    TIMESTAMP_RANGE = "timestamp_range"
    FULL_PROJECTION_REBUILD = "full_projection_rebuild"
    DRY_RUN = "dry_run"
    SHADOW_REBUILD = "shadow_rebuild"


class ReplayOutcomeState(StrEnum):
    PLANNED = "PLANNED"
    VALIDATING = "VALIDATING"
    REBUILDING = "REBUILDING"
    COMPARING = "COMPARING"
    MATCHED = "MATCHED"
    DIVERGED = "DIVERGED"
    PROMOTION_PENDING = "PROMOTION_PENDING"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ReplayPlan:
    mode: ReplayMode
    scope: dict[str, str]
    operator_id: str
    reason: str
    approval_reference: str | None
    replay_id: str = field(default_factory=lambda: new_id("replay"))
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    state: ReplayOutcomeState = ReplayOutcomeState.PLANNED

    @property
    def scope_key(self) -> str:
        return f"{self.mode.value}:{self.scope}"


def plan_replay(
    *,
    mode: ReplayMode,
    scope: dict[str, str],
    operator_id: str,
    reason: str,
    approval_reference: str | None = None,
) -> ReplayPlan:
    if not reason:
        raise ValueError("replay_reason_required")
    if not scope:
        raise ValueError("replay_scope_required")
    return ReplayPlan(mode=mode, scope=scope, operator_id=operator_id, reason=reason, approval_reference=approval_reference)
