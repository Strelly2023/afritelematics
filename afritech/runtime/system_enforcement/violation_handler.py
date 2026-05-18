from dataclasses import dataclass

from afritech.semantic_engine.ir.schema import SystemInvalid


@dataclass(frozen=True)
class Violation:
    reason: str
    severity: str = "CRITICAL"
    action: str = "SYSTEM_INVALID"


def handle_violation(reason: str) -> Violation:
    return Violation(reason=reason)


def raise_violation(reason: str) -> None:
    raise SystemInvalid(reason)
