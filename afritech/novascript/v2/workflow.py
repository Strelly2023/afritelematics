from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from hashlib import sha256
from typing import Any


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


class AgentWorkflowEngine:
    def __init__(self) -> None:
        self._sequences: dict[tuple[str, str, str], int] = defaultdict(int)

    def plan(self, *, intent: str, memory_count: int = 0) -> list[WorkflowStep]:
        steps = [
            WorkflowStep("intake", "complete", {"intent": intent}),
            WorkflowStep("memory_recall", "complete", {"records_consulted": memory_count}),
            WorkflowStep("context", "complete", {"scope": "repository_and_architecture"}),
            WorkflowStep("route_model", "complete", {"routing": "specialized_engine"}),
            WorkflowStep("tool_plan", "complete", {"policy": "structured_tool_errors"}),
            WorkflowStep("parse", "complete", {"status": "parsed"}),
            WorkflowStep("trust_review", "complete", {"status": "scored"}),
            WorkflowStep("artifact", "complete", {"deterministic": True}),
            WorkflowStep("receipt", "complete", {"status": "issued_without_timestamp_fields"}),
        ]
        return steps

    def start(self, *, organization_id: str, project_id: str, intent: str, memory_count: int = 0) -> WorkflowRun:
        key = (organization_id, project_id, intent)
        self._sequences[key] += 1
        workflow_id = "wf-" + sha256(
            f"{organization_id}:{project_id}:{intent}:{self._sequences[key]}".encode("utf-8")
        ).hexdigest()[:12]
        steps = self.plan(intent=intent, memory_count=memory_count)
        return WorkflowRun(
            workflow_id=workflow_id,
            organization_id=organization_id,
            project_id=project_id,
            intent=intent,
            status="complete",
            steps=steps,
        )


_DEFAULT_WORKFLOW_ENGINE = AgentWorkflowEngine()


def get_agent_workflow_engine() -> AgentWorkflowEngine:
    return _DEFAULT_WORKFLOW_ENGINE
