from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AfriRidePilotSignals:
    real_drivers_onboarded: bool = False
    real_trips_completed: bool = False
    raw_transaction_evidence_collected: bool = False
    trust_kernel_events_recorded: bool = False
    replay_verified: bool = False
    operator_review_complete: bool = False
    economic_activation_requested: bool = False


@dataclass(frozen=True)
class PilotActivationDecision:
    status: str
    authorized: bool
    missing_evidence: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    allowed_next_action: str


class PilotActivationBlocked(RuntimeError):
    """Raised when real-world pilot activation is requested before evidence."""


def evaluate_afriride_pilot(
    signals: AfriRidePilotSignals | None = None,
) -> PilotActivationDecision:
    signals = signals or AfriRidePilotSignals()
    missing = _missing(signals)
    forbidden = ("economic activation",) if signals.economic_activation_requested else ()
    authorized = not missing and not forbidden
    return PilotActivationDecision(
        status="READY_FOR_CONTROLLED_FIELD_EXECUTION" if authorized else "READY_BLOCKED",
        authorized=authorized,
        missing_evidence=missing,
        forbidden_actions=forbidden,
        allowed_next_action=(
            "run controlled AfriRide field execution"
            if authorized
            else "collect real-world pilot evidence only"
        ),
    )


def _missing(signals: AfriRidePilotSignals) -> tuple[str, ...]:
    missing: list[str] = []
    if not signals.real_drivers_onboarded:
        missing.append("real drivers onboarded")
    if not signals.real_trips_completed:
        missing.append("real trips completed")
    if not signals.raw_transaction_evidence_collected:
        missing.append("raw transaction evidence collected")
    if not signals.trust_kernel_events_recorded:
        missing.append("Trust Kernel events recorded")
    if not signals.replay_verified:
        missing.append("replay verified")
    if not signals.operator_review_complete:
        missing.append("operator review complete")
    return tuple(missing)
