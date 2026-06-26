"""Service objectives and error-budget release decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceObjective:
    service: str
    availability_target: float
    latency_p95_ms: int
    window_days: int
    rto_minutes: int
    rpo_minutes: int
    fast_burn_threshold: float = 14.4
    slow_burn_threshold: float = 2.0

    @property
    def error_budget_ratio(self) -> float:
        return 1.0 - self.availability_target


@dataclass(frozen=True)
class ErrorBudgetDecision:
    release_allowed: bool
    burn_rate: float
    budget_remaining_ratio: float
    reason: str


def evaluate_error_budget(
    objective: ServiceObjective,
    *,
    observed_requests: int,
    failed_requests: int,
) -> ErrorBudgetDecision:
    if observed_requests <= 0 or failed_requests < 0 or failed_requests > observed_requests:
        raise ValueError("invalid_service_observation")
    observed_error_ratio = failed_requests / observed_requests
    burn_rate = (
        observed_error_ratio / objective.error_budget_ratio
        if objective.error_budget_ratio > 0
        else float("inf")
    )
    consumed = min(1.0, burn_rate)
    remaining = max(0.0, 1.0 - consumed)
    allowed = burn_rate <= objective.slow_burn_threshold and remaining > 0
    return ErrorBudgetDecision(
        release_allowed=allowed,
        burn_rate=round(burn_rate, 6),
        budget_remaining_ratio=round(remaining, 6),
        reason="within_error_budget" if allowed else "error_budget_exhausted_or_burning",
    )
