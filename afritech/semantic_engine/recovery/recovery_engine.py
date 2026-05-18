from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryDecision:
    status: str
    reason: str


def refuse_recovery(reason: str) -> RecoveryDecision:
    return RecoveryDecision(status="SYSTEM_INVALID", reason=reason)


def recover(reason: str) -> RecoveryDecision:
    return refuse_recovery(reason)
