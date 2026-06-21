from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Callable
from uuid import uuid4

from afritech.afroprog_workspace.models import ProjectWorkspace, afroprog_seed_projects

from afritech.novascript.v2.graph import get_repository_graph_intelligence
from afritech.novascript.v2.knowledge import get_architecture_knowledge_base


ToolHandler = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ToolResult:
    name: str
    output: dict[str, Any]
    status: str = "ok"


class ToolRegistry:
    def __init__(self) -> None:
        self._graph = get_repository_graph_intelligence()
        self._kb = get_architecture_knowledge_base()
        self._tools: dict[str, ToolHandler] = {
            "repository_graph": self._tool_repository_graph,
            "architecture_kb": self._tool_architecture_kb,
            "multi_file_generation": self._tool_multi_file_generation,
            "debt_analysis": self._tool_technical_debt,
            "trust_review": self._tool_trust_review,
            "prompt_registry": self._tool_prompt_registry,
        }

    def list(self) -> list[dict[str, Any]]:
        return [{"name": name} for name in sorted(self._tools)]

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        if name not in self._tools:
            return ToolResult(
                name=name,
                status="error",
                output={
                    "status": "tool_error",
                    "error": {
                        "type": "unknown_tool",
                        "tool_name": name,
                        "message": f"Tool is not registered: {name}",
                        "available_tools": [item["name"] for item in self.list()],
                    },
                },
            )
        try:
            return ToolResult(name=name, output=self._tools[name](**kwargs))
        except Exception as exc:
            return ToolResult(
                name=name,
                status="error",
                output={
                    "status": "tool_error",
                    "error": {
                        "type": exc.__class__.__name__,
                        "tool_name": name,
                        "message": str(exc),
                    },
                },
            )

    def execute_many(self, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for call in calls:
            name = str(call.get("name", "")).strip()
            arguments = call.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            result = self.execute(name, **arguments)
            results.append({"name": result.name, "status": result.status, "output": result.output})
        return results

    def _tool_repository_graph(
        self,
        *,
        project: ProjectWorkspace | None = None,
        project_id: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        project = _resolve_project(project=project, project_id=project_id)
        return self._graph.summarize(project)

    def _tool_architecture_kb(
        self,
        *,
        prompt: str,
        project: ProjectWorkspace | None = None,
        project_id: str | None = None,
        intent: str,
        **_: Any,
    ) -> dict[str, Any]:
        project = _resolve_project(project=project, project_id=project_id)
        matches = self._kb.match(f"{prompt} {intent} {project.stack} {project.description}")
        return {
            "entries": matches,
            "project_stack": project.stack,
            "recommendation": _recommendation_from_matches(matches),
        }

    def _tool_multi_file_generation(
        self,
        *,
        prompt: str,
        project: ProjectWorkspace | None = None,
        project_id: str | None = None,
        intent: str,
        language: str,
        mode: str,
        architecture: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        project = _resolve_project(project=project, project_id=project_id)
        return {
            "generated_files": _generate_files(
                prompt=prompt,
                project=project,
                intent=intent,
                language=language,
                mode=mode,
                architecture=architecture or {},
            ),
            "workspace_id": f"workspace-{project.project_id}",
        }

    def _tool_technical_debt(
        self,
        *,
        project: ProjectWorkspace | None = None,
        project_id: str | None = None,
        graph: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        project = _resolve_project(project=project, project_id=project_id)
        technical_debt = graph.get("technical_debt", {})
        score = int(technical_debt.get("score", 0))
        findings = list(technical_debt.get("findings", []))
        review = "approve" if score < 60 else "revise"
        return {
            "score": score,
            "level": technical_debt.get("level", "low"),
            "findings": findings,
            "review": review,
            "project_id": project.project_id,
        }

    def _tool_trust_review(
        self,
        *,
        prompt: str,
        graph: dict[str, Any],
        debt: dict[str, Any],
        architecture: dict[str, Any],
        project_id: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        score = max(
            0,
            100
            - int(debt.get("score", 0))
            + len(graph.get("nodes", [])) * 2
            + len(architecture.get("entries", [])) * 3,
        )
        status = "approved" if score >= 70 else "needs_review"
        return {
            "trust_score": score,
            "status": status,
            "reason": "reviewed against graph, debt, and architecture knowledge",
            "prompt_digest": prompt[:80],
        }

    def _tool_prompt_registry(self, *, prompt_registry: list[dict[str, Any]], **_: Any) -> dict[str, Any]:
        return {"templates": prompt_registry}


def _recommendation_from_matches(matches: list[dict[str, Any]]) -> str:
    categories = {str(match.get("category", "")) for match in matches}
    if "delivery" in categories:
        return "Include build and deployment automation"
    if "trust" in categories:
        return "Attach governance receipts and verification"
    if "frontend" in categories:
        return "Separate UI components from service adapters"
    return "Keep modules small and testable"


def _resolve_project(
    *,
    project: ProjectWorkspace | None = None,
    project_id: str | None = None,
) -> ProjectWorkspace:
    if project is not None:
        return project
    if project_id:
        projects = {item.project_id: item for item in afroprog_seed_projects()}
        if project_id in projects:
            return projects[project_id]
    return next(iter(afroprog_seed_projects()))


def _generate_files(
    *,
    prompt: str,
    project: ProjectWorkspace,
    intent: str,
    language: str,
    mode: str,
    architecture: dict[str, Any],
) -> list[dict[str, Any]]:
    lowered = f"{prompt} {intent} {project.description}".lower()
    files: list[dict[str, Any]] = [
        {
            "path": "app/main.py",
            "language": "python",
            "purpose": "Application entrypoint",
            "content": dedent(
                """
                from fastapi import FastAPI

                app = FastAPI(title="NovaScript Generated Service")


                @app.get("/health")
                def health() -> dict[str, str]:
                    return {"status": "ok"}
                """
            ).strip(),
        },
        {
            "path": "app/schemas.py",
            "language": "python",
            "purpose": "Request/response contracts",
            "content": dedent(
                """
                from pydantic import BaseModel


                class ExampleRequest(BaseModel):
                    prompt: str
                """
            ).strip(),
        },
    ]
    if any(token in lowered for token in ("test", "pytest", "qa")):
        files.append(
            {
                "path": "tests/test_generated.py",
                "language": "python",
                "purpose": "Regression tests",
                "content": "def test_generated_contract() -> None:\n    assert True\n",
            }
        )
    if any(token in lowered for token in ("auth", "identity", "security")):
        files.append(
            {
                "path": "app/core/security.py",
                "language": "python",
                "purpose": "Security boundary",
                "content": "def require_auth() -> bool:\n    return True\n",
            }
        )
    if any(token in lowered for token in ("docker", "deploy", "ci", "cicd", "release")):
        files.append(
            {
                "path": "Dockerfile",
                "language": "dockerfile",
                "purpose": "Container build",
                "content": "FROM python:3.12-slim\n",
            }
        )
    if any(token in lowered for token in ("react", "frontend", "ui")):
        files.append(
            {
                "path": "src/App.tsx",
                "language": "typescript",
                "purpose": "Frontend shell",
                "content": "export default function App() {\n  return <main>NovaScript Generated UI</main>;\n}\n",
            }
        )
    if architecture.get("entries"):
        files.append(
            {
                "path": "README.md",
                "language": "markdown",
                "purpose": "Implementation notes",
                "content": f"# Generated by NovaScript\n\nPrompt: {prompt}\n",
            }
        )
    return files


_DEFAULT_TOOL_REGISTRY = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return _DEFAULT_TOOL_REGISTRY
