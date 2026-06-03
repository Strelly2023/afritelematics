"""
afritech.runtime.guard_executor

Guarded runtime execution boundary.

All runtime execution MUST pass through guard evaluation before any state
transition or execution callable is invoked.

Constitutional boundary:
- Guards may authorize, reject, quarantine, or halt.
- Guards must not mutate state directly.
- Execution is refused if guard validation fails.
- Execution result is hash-bound for deterministic replay inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Mapping, Protocol


class GuardExecutionError(ValueError):
    """Raised when guarded execution violates runtime guard rules."""


class GuardEngineProtocol(Protocol):
    def validate(self, context: Mapping[str, Any]) -> Any:
        ...


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    action: str
    reason: str
    guard_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise GuardExecutionError("allowed must be boolean")

        if self.action not in {"ALLOW", "REJECT", "QUARANTINE", "HALT"}:
            raise GuardExecutionError(f"unsupported guard action: {self.action}")

        _require_string(self.reason, "reason")
        _require_sha256(self.guard_hash, "guard_hash")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "allowed": self.allowed,
            "guard_hash": self.guard_hash,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class GuardedExecutionResult:
    executed: bool
    status: str
    guard_decision: GuardDecision
    output: Any
    execution_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.executed, bool):
            raise GuardExecutionError("executed must be boolean")

        if self.status not in {"EXECUTED", "REFUSED"}:
            raise GuardExecutionError(f"unsupported execution status: {self.status}")

        if not isinstance(self.guard_decision, GuardDecision):
            raise GuardExecutionError("guard_decision must be GuardDecision")

        _require_sha256(self.execution_hash, "execution_hash")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "execution_hash": self.execution_hash,
            "guard_decision": self.guard_decision.to_canonical_dict(),
            "output": self.output,
            "status": self.status,
        }


class GuardExecutor:
    """
    Executes a callable only after deterministic guard approval.

    The executor is intentionally small:
    - it does not define truth
    - it does not mutate guard decisions
    - it does not bypass guard failures
    """

    def __init__(self, guard_engine: GuardEngineProtocol | Callable[[Mapping[str, Any]], Any]) -> None:
        if not callable(guard_engine) and not hasattr(guard_engine, "validate"):
            raise GuardExecutionError(
                "guard_engine must be callable or expose validate(context)"
            )

        self._guard_engine = guard_engine

    def execute(
        self,
        *,
        context: Mapping[str, Any],
        operation: Callable[[Mapping[str, Any]], Any],
    ) -> GuardedExecutionResult:
        if not isinstance(context, Mapping):
            raise GuardExecutionError("context must be a mapping")

        if not callable(operation):
            raise GuardExecutionError("operation must be callable")

        decision = self._evaluate_guard(context)

        if not decision.allowed:
            return _refused_result(decision)

        try:
            output = operation(context)
        except Exception as exc:
            raise GuardExecutionError("guarded operation failed") from exc

        execution_hash = _canonical_hash(
            {
                "guard_decision": decision.to_canonical_dict(),
                "output": _json_safe(output),
                "status": "EXECUTED",
            }
        )

        return GuardedExecutionResult(
            executed=True,
            status="EXECUTED",
            guard_decision=decision,
            output=output,
            execution_hash=execution_hash,
        )

    def _evaluate_guard(self, context: Mapping[str, Any]) -> GuardDecision:
        if hasattr(self._guard_engine, "validate"):
            raw_decision = self._guard_engine.validate(context)  # type: ignore[attr-defined]
        else:
            raw_decision = self._guard_engine(context)  # type: ignore[misc]

        return normalize_guard_decision(raw_decision)


def normalize_guard_decision(raw_decision: Any) -> GuardDecision:
    if isinstance(raw_decision, GuardDecision):
        return raw_decision

    if isinstance(raw_decision, bool):
        payload = {
            "action": "ALLOW" if raw_decision else "REJECT",
            "allowed": raw_decision,
            "reason": "allowed" if raw_decision else "guard_rejected",
        }

        return GuardDecision(
            allowed=raw_decision,
            action=payload["action"],
            reason=payload["reason"],
            guard_hash=_canonical_hash(payload),
        )

    if isinstance(raw_decision, Mapping):
        allowed = bool(raw_decision.get("allowed", raw_decision.get("admitted", False)))

        action = str(
            raw_decision.get(
                "action",
                "ALLOW" if allowed else "REJECT",
            )
        )

        reason = str(
            raw_decision.get(
                "reason",
                "allowed" if allowed else "guard_rejected",
            )
        )

        payload = {
            "action": action,
            "allowed": allowed,
            "reason": reason,
        }

        return GuardDecision(
            allowed=allowed,
            action=action,
            reason=reason,
            guard_hash=_canonical_hash(payload),
        )

    raise GuardExecutionError("unsupported guard decision shape")


def execute_with_guards(
    *,
    context: Mapping[str, Any],
    operation: Callable[[Mapping[str, Any]], Any],
    guard_engine: GuardEngineProtocol | Callable[[Mapping[str, Any]], Any],
) -> GuardedExecutionResult:
    return GuardExecutor(guard_engine).execute(
        context=context,
        operation=operation,
    )


def _refused_result(decision: GuardDecision) -> GuardedExecutionResult:
    execution_hash = _canonical_hash(
        {
            "guard_decision": decision.to_canonical_dict(),
            "output": None,
            "status": "REFUSED",
        }
    )

    return GuardedExecutionResult(
        executed=False,
        status="REFUSED",
        guard_decision=decision,
        output=None,
        execution_hash=execution_hash,
    )


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
        return value
    except TypeError:
        return repr(value)


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=repr,
    )

    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise GuardExecutionError(f"{field_name} must be a non-empty string")


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise GuardExecutionError(f"{field_name} must be a SHA-256 hex string")

    try:
        int(value, 16)
    except ValueError as exc:
        raise GuardExecutionError(
            f"{field_name} must be a SHA-256 hex string"
        ) from exc