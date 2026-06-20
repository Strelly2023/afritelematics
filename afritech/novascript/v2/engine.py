from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from afritech.afroprog_workspace.models import afroprog_seed_projects, ProjectWorkspace
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID
from afritech.novascript.v2.graph import get_repository_graph_intelligence
from afritech.novascript.v2.knowledge import get_architecture_knowledge_base
from afritech.novascript.v2.memory import get_workspace_memory_store
from afritech.novascript.v2.parser import get_structured_output_parser
from afritech.novascript.v2.prompts import get_prompt_registry
from afritech.novascript.v2.providers import ModelProviderLayer, PromptExecutionRequest
from afritech.novascript.v2.receipts import get_governance_receipt_store
from afritech.novascript.v2.tools import get_tool_registry
from afritech.novascript.v2.workflow import get_agent_workflow_engine


class NovaScriptV2Engine:
    def __init__(self) -> None:
        self.prompts = get_prompt_registry()
        self.provider_layer = ModelProviderLayer()
        self.tools = get_tool_registry()
        self.memory = get_workspace_memory_store()
        self.graph = get_repository_graph_intelligence()
        self.knowledge = get_architecture_knowledge_base()
        self.parser = get_structured_output_parser()
        self.receipts = get_governance_receipt_store()
        self.workflow = get_agent_workflow_engine()

    def status(self, organization_id: str | None = None) -> dict[str, Any]:
        return {
            "model_layer": {
                "provider": self.provider_layer.provider.name,
                "model_name": self.provider_layer.model_name,
                "available": True,
            },
            "workspace_memory": True,
            "tool_calling": True,
            "repository_graph_intelligence": True,
            "agent_workflow": True,
            "prompt_registry": True,
            "governance_receipts": True,
            "structured_output_parser": True,
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        }

    def execute(
        self,
        *,
        prompt: str,
        project_id: str | None = None,
        organization_id: str | None = None,
        language: str = "python",
        mode: str = "code",
        intent: str = "generate",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        org_id = organization_id or DEFAULT_ORGANIZATION_ID
        project = _select_project(project_id)
        request = PromptExecutionRequest(
            intent=intent,
            prompt=prompt,
            project=project,
            organization_id=org_id,
            language=language,
            mode=mode,
            context=context or {},
        )
        workflow = self.workflow.start(organization_id=org_id, project_id=project.project_id, intent=intent)
        provider_result = self.provider_layer.execute(request)
        graph_summary = self.graph.summarize(project)
        architecture = self.tools.execute(
            "architecture_kb",
            prompt=prompt,
            project=project,
            intent=intent,
        ).output
        multi_file = self.tools.execute(
            "multi_file_generation",
            prompt=prompt,
            project=project,
            intent=intent,
            language=language,
            mode=mode,
            architecture=architecture,
        ).output
        debt = self.tools.execute(
            "debt_analysis",
            project=project,
            graph=graph_summary,
        ).output
        trust = self.tools.execute(
            "trust_review",
            prompt=prompt,
            graph=graph_summary,
            debt=debt,
            architecture=architecture,
        ).output
        parsed = self.parser.parse(provider_result.raw_output).data
        tool_calls = parsed.get("tool_calls", [])
        tool_results = self.tools.execute_many(tool_calls if isinstance(tool_calls, list) else [])
        output_payload = {
            "provider": provider_result.provider_name,
            "model_name": provider_result.model_name,
            "intent": parsed.get("intent", intent),
            "project_id": project.project_id,
            "organization_id": org_id,
            "prompt": prompt,
            "language": language,
            "mode": mode,
            "parsed_output": parsed,
            "tool_results": tool_results,
            "repository_graph": graph_summary,
            "architecture_knowledge": architecture,
            "generated_files": multi_file.get("generated_files", []),
            "technical_debt": debt,
            "trust_review": trust,
            "workflow": {
                "workflow_id": workflow.workflow_id,
                "status": workflow.status,
                "steps": [asdict(step) for step in workflow.steps],
            },
        }
        receipt = self.receipts.issue(
            organization_id=org_id,
            project_id=project.project_id,
            prompt=prompt,
            output=output_payload,
            trust_score=int(trust.get("trust_score", 0)),
            status=str(trust.get("status", "needs_review")),
        )
        memory_record = self.memory.append(
            organization_id=org_id,
            project_id=project.project_id,
            intent=intent,
            prompt=prompt,
            summary={
                "provider": provider_result.provider_name,
                "intent": parsed.get("intent", intent),
                "trust_status": trust.get("status", "needs_review"),
                "trust_score": trust.get("trust_score", 0),
            },
            receipts=[receipt.canonical_dict()],
        )
        output_payload.update(
            {
                "memory": memory_record.__dict__,
                "governance_receipt": receipt.canonical_dict(),
                "receipt_id": receipt.receipt_id,
                "response_hash": sha256(
                    f"{prompt}:{project.project_id}:{language}:{mode}:{provider_result.model_name}".encode("utf-8")
                ).hexdigest(),
                "execution_preview": {
                    "sandboxed": True,
                    "mutation_allowed": False,
                    "next_step": "governance review in NovaProgramming",
                },
            }
        )
        return output_payload

    def explain(
        self,
        *,
        code: str,
        context: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Explain the provided code.\nContext: {context}\nCode:\n{code}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="explain",
            context={"code": code, "context": context},
        )

    def debug(
        self,
        *,
        code: str = "",
        error: str = "",
        context: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Debug the failure.\nError: {error}\nContext: {context}\nCode:\n{code}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="debug",
            context={"code": code, "error": error, "context": context},
        )

    def architecture(
        self,
        *,
        description: str,
        stack: str,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Design architecture.\nDescription: {description}\nStack: {stack}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="architecture",
            context={"description": description, "stack": stack},
        )

    def tests(
        self,
        *,
        target: str,
        framework: str = "pytest",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Generate tests for {target} using {framework}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="tests",
            context={"target": target, "framework": framework},
        )

    def docs(
        self,
        *,
        topic: str,
        audience: str = "developer",
        format: str = "README",
        metadata: dict[str, Any] | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Write documentation for {topic}."
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="docs",
            context={"topic": topic, "audience": audience, "format": format, "metadata": metadata or {}},
        )

    def repository_intelligence(
        self,
        *,
        project_id: str | None = None,
        focus: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        project = _select_project(project_id)
        return self.execute(
            prompt=f"Analyze repository intelligence for {project.name}. Focus: {focus}",
            project_id=project.project_id,
            organization_id=organization_id,
            intent="repo_intelligence",
            context={"focus": focus},
        )

    def memory_snapshot(self, *, organization_id: str, project_id: str) -> dict[str, Any]:
        return self.memory.snapshot(organization_id=organization_id, project_id=project_id)

    def prompt_catalog(self) -> list[dict[str, Any]]:
        return self.prompts.list()

    def receipt_history(self, *, organization_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        return self.receipts.recent(organization_id=organization_id, project_id=project_id)


def _select_project(project_id: str | None) -> ProjectWorkspace:
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    if project_id and project_id in projects:
        return projects[project_id]
    return next(iter(projects.values()))


_DEFAULT_ENGINE = NovaScriptV2Engine()


def get_novascript_v2_engine() -> NovaScriptV2Engine:
    return _DEFAULT_ENGINE
