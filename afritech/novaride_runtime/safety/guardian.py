"""Deterministic, auditable trip-safety monitoring for NovaRide Guardian."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol


class GuardianAction(StrEnum):
    NORMAL = "NORMAL"
    OBSERVE = "OBSERVE"
    CHECK_IN = "CHECK_IN"
    OPERATOR_REVIEW = "OPERATOR_REVIEW"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class GuardianPolicy:
    stale_gps_seconds: int = 120
    stationary_check_in_seconds: int = 300
    stationary_review_seconds: int = 600
    route_deviation_review_metres: int = 800
    duration_anomaly_seconds: int = 1800


@dataclass(frozen=True)
class TripSafetyObservation:
    observation_id: str
    tenant_id: str
    trip_id: str
    observed_at: datetime
    gps_age_seconds: int = 0
    stationary_seconds: int = 0
    route_deviation_metres: int = 0
    duration_over_expected_seconds: int = 0
    rider_connected: bool = True
    driver_connected: bool = True
    manual_sos: bool = False


@dataclass(frozen=True)
class GuardianDecision:
    observation_id: str
    tenant_id: str
    trip_id: str
    action: GuardianAction
    reasons: tuple[str, ...]
    observed_at: datetime
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class GuardianDecisionRepository(Protocol):
    def find(self, *, tenant_id: str, observation_id: str) -> GuardianDecision | None: ...
    def save(self, decision: GuardianDecision) -> None: ...


class InMemoryGuardianDecisionRepository:
    """Test/development adapter; production composition must provide durability."""

    def __init__(self) -> None:
        self._decisions: dict[tuple[str, str], GuardianDecision] = {}

    def find(self, *, tenant_id: str, observation_id: str) -> GuardianDecision | None:
        return self._decisions.get((tenant_id, observation_id))

    def save(self, decision: GuardianDecision) -> None:
        self._decisions[(decision.tenant_id, decision.observation_id)] = decision


class GuardianMonitor:
    def __init__(self, repository: GuardianDecisionRepository, policy: GuardianPolicy | None = None) -> None:
        self._repository = repository
        self._policy = policy or GuardianPolicy()

    def evaluate(self, observation: TripSafetyObservation) -> GuardianDecision:
        self._validate(observation)
        existing = self._repository.find(
            tenant_id=observation.tenant_id,
            observation_id=observation.observation_id,
        )
        if existing is not None:
            if existing.trip_id != observation.trip_id:
                raise ValueError("observation id payload mismatch")
            return existing

        action, reasons = self._decide(observation)
        decision = GuardianDecision(
            observation_id=observation.observation_id,
            tenant_id=observation.tenant_id,
            trip_id=observation.trip_id,
            action=action,
            reasons=tuple(reasons),
            observed_at=observation.observed_at,
        )
        self._repository.save(decision)
        return decision

    def _decide(self, observation: TripSafetyObservation) -> tuple[GuardianAction, list[str]]:
        policy = self._policy
        reasons: list[str] = []
        action = GuardianAction.NORMAL

        def raise_to(candidate: GuardianAction, reason: str) -> None:
            nonlocal action
            order = list(GuardianAction)
            if order.index(candidate) > order.index(action):
                action = candidate
            reasons.append(reason)

        if observation.manual_sos:
            raise_to(GuardianAction.ESCALATE, "MANUAL_SOS")
        if observation.route_deviation_metres >= policy.route_deviation_review_metres:
            raise_to(GuardianAction.OPERATOR_REVIEW, "MATERIAL_ROUTE_DEVIATION")
        if observation.stationary_seconds >= policy.stationary_review_seconds:
            raise_to(GuardianAction.OPERATOR_REVIEW, "EXCESSIVE_STATIONARY_PERIOD")
        elif observation.stationary_seconds >= policy.stationary_check_in_seconds:
            raise_to(GuardianAction.CHECK_IN, "UNEXPECTED_STOP")
        if observation.gps_age_seconds >= policy.stale_gps_seconds:
            raise_to(GuardianAction.CHECK_IN, "STALE_GPS")
        if not observation.driver_connected:
            raise_to(GuardianAction.CHECK_IN, "DRIVER_CONNECTIVITY_LOSS")
        if not observation.rider_connected:
            raise_to(GuardianAction.OBSERVE, "RIDER_CONNECTIVITY_LOSS")
        if observation.duration_over_expected_seconds >= policy.duration_anomaly_seconds:
            raise_to(GuardianAction.OBSERVE, "TRIP_DURATION_ANOMALY")
        return action, reasons

    @staticmethod
    def _validate(observation: TripSafetyObservation) -> None:
        if not observation.observation_id or not observation.tenant_id or not observation.trip_id:
            raise ValueError("observation, tenant and trip identifiers are required")
        for value in (
            observation.gps_age_seconds,
            observation.stationary_seconds,
            observation.route_deviation_metres,
            observation.duration_over_expected_seconds,
        ):
            if value < 0:
                raise ValueError("safety signal values cannot be negative")


__all__ = [
    "GuardianAction",
    "GuardianDecision",
    "GuardianDecisionRepository",
    "GuardianMonitor",
    "GuardianPolicy",
    "InMemoryGuardianDecisionRepository",
    "TripSafetyObservation",
]
