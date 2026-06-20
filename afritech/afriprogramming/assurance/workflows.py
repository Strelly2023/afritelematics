from __future__ import annotations

from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


DEFAULT_WORKFLOW_STEPS = {
    "deployment": ("requested", "approved", "deployed", "verified", "certified"),
    "assurance": ("collected", "recomputed", "checked", "alerted", "closed"),
    "federation": ("registered", "validated", "published", "verified"),
}


class WorkflowService:
    """Deterministic, Temporal-style workflow surface."""

    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def _definition_for(self, workflow_name: str, steps: list[str] | None = None) -> dict[str, Any]:
        return {
            "workflow_name": workflow_name,
            "steps": tuple(steps or DEFAULT_WORKFLOW_STEPS.get(workflow_name, ("start", "finish"))),
        }

    def start(
        self,
        *,
        organization_id: str,
        workflow_name: str,
        input_payload: dict[str, Any],
        steps: list[str] | None = None,
    ) -> dict[str, Any]:
        definition = self._definition_for(workflow_name, steps)
        workflow = self.repository.store_workflow_instance(
            organization_id=organization_id,
            workflow_name=workflow_name,
            definition=definition,
            input_payload=input_payload,
            state="running",
            current_step=definition["steps"][0],
        )
        self.repository.store_workflow_step(
            workflow_id=workflow["workflow_id"],
            organization_id=organization_id,
            step_name=definition["steps"][0],
            step_index=0,
            status="running",
            input_payload=input_payload,
            output_payload={},
        )
        return workflow

    def signal(
        self,
        *,
        organization_id: str,
        workflow_id: str,
        signal_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        workflow = self.repository.get_workflow_instance(
            workflow_id=workflow_id,
            organization_id=organization_id,
        )
        if workflow is None:
            raise KeyError(workflow_id)
        definition = workflow["definition"]
        steps = tuple(definition.get("steps", ("start", "finish")))
        try:
            index = steps.index(signal_name)
        except ValueError:
            index = len(self.repository.list_workflow_steps(workflow_id=workflow_id, organization_id=organization_id))
        completed = index >= len(steps) - 1
        self.repository.store_workflow_step(
            workflow_id=workflow_id,
            organization_id=organization_id,
            step_name=signal_name,
            step_index=index,
            status="completed" if completed else "running",
            input_payload=payload,
            output_payload={"signal": signal_name, **payload},
        )
        return self.repository.update_workflow_instance(
            workflow_id=workflow_id,
            organization_id=organization_id,
            state="completed" if completed else "running",
            current_step=signal_name,
            output_payload={"signal": signal_name, **payload},
            completed=completed,
        )

    def status(self, *, organization_id: str, workflow_id: str) -> dict[str, Any]:
        workflow = self.repository.get_workflow_instance(
            workflow_id=workflow_id,
            organization_id=organization_id,
        )
        if workflow is None:
            raise KeyError(workflow_id)
        workflow["steps"] = self.repository.list_workflow_steps(
            organization_id=organization_id,
            workflow_id=workflow_id,
        )
        return workflow

    def history(self, *, organization_id: str, workflow_id: str) -> list[dict[str, Any]]:
        return self.repository.list_workflow_steps(organization_id=organization_id, workflow_id=workflow_id)

    def instances(self, *, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_workflow_instances(organization_id=organization_id, limit=limit)


__all__ = ["WorkflowService", "DEFAULT_WORKFLOW_STEPS"]
