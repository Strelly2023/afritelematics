from .guardian import (
    GuardianAction,
    GuardianDecision,
    GuardianMonitor,
    GuardianPolicy,
    InMemoryGuardianDecisionRepository,
    TripSafetyObservation,
)

__all__ = [
    "SafetyService",
    "GuardianAction",
    "GuardianDecision",
    "GuardianMonitor",
    "GuardianPolicy",
    "InMemoryGuardianDecisionRepository",
    "TripSafetyObservation",
]


def __getattr__(name: str):
    # Avoid a package-initialization cycle when services imports Guardian.
    if name == "SafetyService":
        from afritech.novaride_runtime.services import SafetyService

        return SafetyService
    raise AttributeError(name)
