"""Persistent orchestration execution and operator control."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from afritech.afritpps.orchestration import (
    AfriTPPSOrchestrationIntent,
    AfriTPPSOrchestrationOutcome,
    OrchestrationStep,
    execute_orchestration,
)
from afritech.models import (
    OperatorActionLog,
    OrchestrationStepState,
    PersistentOrchestration,
)


class OperatorControlError(RuntimeError):
    """Raised when operator flow control would violate AfriTPPS invariants."""


def create_persistent_orchestration(
    intent: AfriTPPSOrchestrationIntent,
) -> PersistentOrchestration:
    orchestration, _ = PersistentOrchestration.objects.get_or_create(
        orchestration_id=intent.orchestration_id,
        defaults={
            "name": intent.name,
            "status": "CREATED",
            "policy_context": intent.policy_context,
        },
    )
    for step in intent.operations:
        OrchestrationStepState.objects.get_or_create(
            orchestration=orchestration,
            step_id=step.step_id,
            defaults={
                "domain": step.domain,
                "operation": step.operation,
                "dependencies": list(step.dependencies),
                "status": "PENDING",
            },
        )
    return orchestration


def execute_persistent_orchestration(
    intent: AfriTPPSOrchestrationIntent,
) -> AfriTPPSOrchestrationOutcome:
    orchestration = create_persistent_orchestration(intent)
    _set_orchestration_status(orchestration, "RUNNING")
    try:
        outcome = execute_orchestration(intent)
    except Exception as exc:
        _set_orchestration_status(orchestration, "FAILED")
        _mark_remaining_failed(orchestration, str(exc))
        raise

    for step_id, step_outcome in outcome.step_results.items():
        OrchestrationStepState.objects.filter(
            orchestration=orchestration,
            step_id=step_id,
        ).update(
            status="VERIFIED",
            event_id=step_outcome.event_id,
            evidence_bundle_hash=step_outcome.evidence_bundle_hash,
            verified=True,
            error="",
            last_updated=timezone.now(),
        )
    PersistentOrchestration.objects.filter(pk=orchestration.pk).update(
        status="COMPLETED",
        final_state_hash=outcome.final_state_hash,
        fully_verified=outcome.fully_verified,
        last_updated=timezone.now(),
    )
    return outcome


def pause_orchestration(
    orchestration_id: str,
    *,
    operator_id: str,
    reason: str = "",
) -> PersistentOrchestration:
    orchestration = _get_orchestration(orchestration_id)
    if orchestration.status in {"COMPLETED", "ABORTED", "FAILED"}:
        raise OperatorControlError("terminal orchestration cannot be paused")
    _operator_action(orchestration, operator_id, "PAUSE", reason)
    _set_orchestration_status(orchestration, "PAUSED")
    orchestration.refresh_from_db()
    return orchestration


def resume_orchestration(
    orchestration_id: str,
    *,
    operator_id: str,
    reason: str = "",
) -> PersistentOrchestration:
    orchestration = _get_orchestration(orchestration_id)
    if orchestration.status != "PAUSED":
        raise OperatorControlError("only paused orchestration can be resumed")
    _operator_action(orchestration, operator_id, "RESUME", reason)
    _set_orchestration_status(orchestration, "PARTIAL_PROGRESS")
    orchestration.refresh_from_db()
    return orchestration


def abort_orchestration(
    orchestration_id: str,
    *,
    operator_id: str,
    reason: str = "",
) -> PersistentOrchestration:
    orchestration = _get_orchestration(orchestration_id)
    if orchestration.status == "COMPLETED":
        raise OperatorControlError("completed orchestration cannot be aborted")
    _operator_action(orchestration, operator_id, "ABORT", reason)
    _set_orchestration_status(orchestration, "ABORTED")
    OrchestrationStepState.objects.filter(
        orchestration=orchestration,
        verified=False,
    ).update(status="SKIPPED", last_updated=timezone.now())
    orchestration.refresh_from_db()
    return orchestration


def _get_orchestration(orchestration_id: str) -> PersistentOrchestration:
    return PersistentOrchestration.objects.get(orchestration_id=orchestration_id)


def _set_orchestration_status(
    orchestration: PersistentOrchestration,
    status: str,
) -> None:
    PersistentOrchestration.objects.filter(pk=orchestration.pk).update(
        status=status,
        last_updated=timezone.now(),
    )


def _operator_action(
    orchestration: PersistentOrchestration,
    operator_id: str,
    action: str,
    reason: str,
) -> None:
    OperatorActionLog.objects.create(
        orchestration=orchestration,
        operator_id=operator_id,
        action=action,
        reason=reason,
    )


def _mark_remaining_failed(
    orchestration: PersistentOrchestration,
    error: str,
) -> None:
    OrchestrationStepState.objects.filter(
        orchestration=orchestration,
        verified=False,
    ).update(status="FAILED", error=error, last_updated=timezone.now())
