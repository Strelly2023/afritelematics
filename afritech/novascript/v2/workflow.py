from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowRun:
    workflow_id: str
    organization_id: str
    project_id: str
    intent: str
    status: str
    steps: list[WorkflowStep]
    created_at: str


class AgentWorkflowEngine:
    def start(self, *, organization_id: str, project_id: str, intent: str) -> WorkflowRun:
        workflow_id = f"wf-{uuid4().hex[:12]}"
        steps = [
            WorkflowStep("intake", "complete", {"intent": intent}),
            WorkflowStep("context", "complete", {"project_id": project_id}),
            WorkflowStep("model", "complete", {"provider": "local-reasoning"}),
            WorkflowStep("tools", "complete", {"status": "executed"}),
            WorkflowStep("parse", "complete", {"status": "parsed"}),
            WorkflowStep("receipt", "complete", {"status": "issued"}),
        ]
        return WorkflowRun(
            workflow_id=workflow_id,
            organization_id=organization_id,
            project_id=project_id,
            intent=intent,
            status="complete",
            steps=steps,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


_DEFAULT_WORKFLOW_ENGINE = AgentWorkflowEngine()


def get_agent_workflow_engine() -> AgentWorkflowEngine:
    return _DEFAULT_WORKFLOW_ENGINE
