from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from textwrap import dedent
from typing import Any

from afritech.afroprog_workspace.models import afroprog_seed_projects
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID
from afritech.novascript.v2 import get_novascript_v2_engine


_V2_ENGINE = get_novascript_v2_engine()


@dataclass(frozen=True)
class NovaScriptService:
    """Deterministic AI engineering assistant surface.

    NovaScript is intentionally scoped to development-time assistance:
    generate, explain, debug, design, test, document, and inspect repositories.
    Runtime governance belongs to NovaProgramming.
    """

    default_project_id: str = "project-employee-rbac"

    def status(self, organization_id: str | None = None) -> dict[str, Any]:
        v2_status = _V2_ENGINE.status(organization_id=organization_id or DEFAULT_ORGANIZATION_ID)
        return {
            "product": "NovaScript",
            "category": "AI engineering intelligence system",
            "status": "ready",
            "product_ready": True,
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "role": "development_time_system_builder",
            "governed_by": "NovaProgramming",
            "builds_systems": True,
            "executes_systems": False,
            "model_layer": v2_status["model_layer"],
            "workspace_memory": v2_status["workspace_memory"],
            "tool_calling": v2_status["tool_calling"],
            "repository_graph_intelligence": v2_status["repository_graph_intelligence"],
            "agent_workflow": v2_status["agent_workflow"],
            "prompt_registry": v2_status["prompt_registry"],
            "governance_receipts": v2_status["governance_receipts"],
            "structured_output_parser": v2_status["structured_output_parser"],
            "relationship": {
                "builds": "NovaProgramming",
                "verifies": "NovaProgramming",
                "operates": "NovaProgramming",
            },
        }

    def catalog(self, organization_id: str | None = None) -> dict[str, Any]:
        v2_status = _V2_ENGINE.status(organization_id=organization_id or DEFAULT_ORGANIZATION_ID)
        return {
            "product": "NovaScript",
            "category": "AI engineering intelligence system",
            "positioning": (
                "Designs, generates, explains, debugs, tests, documents, and reasons "
                "about software systems before execution"
            ),
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "capabilities": [
                "code_generation",
                "code_explanation",
                "debugging",
                "architecture_design",
                "test_generation",
                "documentation_generation",
                "integration_planning",
                "repository_intelligence",
                "prompt_execution",
                "structured_output_parsing",
                "workspace_memory",
                "governance_receipts",
                "workflow_orchestration",
            ],
            "stack": {
                "languages": ["Python", "TypeScript", "JavaScript", "SQL", "Dart", "Shell"],
                "targets": ["FastAPI", "Django", "React", "Flutter", "Docker", "CI/CD"],
            },
            "model_layer": {
                "provider": v2_status["model_layer"]["provider"],
                "model_name": v2_status["model_layer"]["model_name"],
                "prompt_registry": _V2_ENGINE.prompt_catalog(),
            },
            "relationship": {
                "builds": "NovaProgramming",
                "governed_by": "NovaProgramming",
            },
            "read_only": True,
        }

    def model_status(self, organization_id: str | None = None) -> dict[str, Any]:
        return _V2_ENGINE.status(organization_id=organization_id or DEFAULT_ORGANIZATION_ID)

    def prompt_catalog(self) -> list[dict[str, Any]]:
        return _V2_ENGINE.prompt_catalog()

    def memory_snapshot(
        self,
        *,
        project_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        project = _select_project(project_id or self.default_project_id)
        return _V2_ENGINE.memory_snapshot(
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
            project_id=project.project_id,
        )

    def receipt_history(
        self,
        *,
        project_id: str | None = None,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        project = _select_project(project_id or self.default_project_id)
        return _V2_ENGINE.receipt_history(
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
            project_id=project.project_id,
        )

    def project_context(
        self,
        project_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        project = _select_project(project_id or self.default_project_id)
        v2 = _V2_ENGINE.memory_snapshot(
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
            project_id=project.project_id,
        )
        return {
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "project": project.canonical_dict(),
            "signals": _project_signals(project),
            "assistant_mode": "development_time",
            "memory": v2,
            "relationship": {
                "handoff": "NovaProgramming governance",
                "runtime_boundary": "no execution authority",
            },
        }

    def generate(
        self,
        *,
        prompt: str,
        project_id: str | None = None,
        language: str = "python",
        mode: str = "code",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        project = _select_project(project_id or self.default_project_id)
        intent = prompt.lower()
        generated_files = _generate_files(prompt=prompt, project=project, language=language, mode=mode)
        response_hash = sha256(
            f"{project.project_id}:{language}:{mode}:{prompt}".encode("utf-8")
        ).hexdigest()
        v2 = _V2_ENGINE.execute(
            prompt=prompt,
            project_id=project.project_id,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
            language=language,
            mode=mode,
            intent="generate",
        )
        return {
            "view": "novascript_generation",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "prompt": prompt,
            "mode": mode,
            "language": language,
            "project": project.canonical_dict(),
            "intent": _classify_intent(intent),
            "generated_files": v2.get("generated_files") or generated_files,
            "tool_results": v2.get("tool_results", []),
            "repository_graph": v2.get("repository_graph", {}),
            "architecture_knowledge": v2.get("architecture_knowledge", {}),
            "technical_debt": v2.get("technical_debt", {}),
            "trust_review": v2.get("trust_review", {}),
            "workflow": v2.get("workflow", {}),
            "memory": v2.get("memory", {}),
            "governance_receipt": v2.get("governance_receipt", {}),
            "receipt_id": v2.get("receipt_id"),
            "execution_preview": {
                "sandboxed": True,
                "mutation_allowed": False,
                "next_step": "review in NovaProgramming",
            },
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "response_hash": v2.get("response_hash", response_hash),
            "relationship": {
                "builds": "NovaProgramming",
                "governed_by": "NovaProgramming",
            },
            "read_only": True,
        }

    def explain(
        self,
        *,
        code: str,
        context: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        lines = code.splitlines()
        imports = [line.strip() for line in lines if line.strip().startswith(("import ", "from "))]
        functions = [line.strip() for line in lines if line.strip().startswith("def ")]
        classes = [line.strip() for line in lines if line.strip().startswith("class ")]
        v2 = _V2_ENGINE.explain(code=code, context=context, organization_id=organization_id or DEFAULT_ORGANIZATION_ID)
        return {
            "view": "novascript_explanation",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "context": context,
            "summary": {
                "line_count": len(lines),
                "import_count": len(imports),
                "function_count": len(functions),
                "class_count": len(classes),
                "purpose": _infer_purpose(code),
            },
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "signals": {
                "uses_async": any("async " in line for line in lines),
                "uses_router": any("router" in line.lower() for line in lines),
                "uses_tests": any("test" in line.lower() for line in lines),
            },
            "relationship": {"builds": "NovaProgramming", "governed_by": "NovaProgramming"},
            "read_only": True,
        }

    def debug(
        self,
        *,
        code: str = "",
        error: str = "",
        context: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        lowered = f"{code}\n{error}\n{context}".lower()
        v2 = _V2_ENGINE.debug(
            code=code,
            error=error,
            context=context,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        )
        findings = []
        fixes = []
        if "module not found" in lowered or "importerror" in lowered:
            findings.append("missing dependency or wrong import path")
            fixes.append("verify package layout and install dependencies")
        if "nameerror" in lowered:
            findings.append("undefined symbol referenced")
            fixes.append("check variable/function naming and scope")
        if "permission denied" in lowered or "forbidden" in lowered:
            findings.append("authorization or file permission issue")
            fixes.append("validate RBAC and filesystem permissions")
        if "timeout" in lowered or "deadline" in lowered:
            findings.append("operation may be slow or blocked")
            fixes.append("inspect external calls, queues, and retries")
        if not findings:
            findings.append("no direct failure signature detected")
            fixes.append("inspect surrounding context and reproduce locally")
        return {
            "view": "novascript_debugging",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "context": context,
            "findings": findings,
            "suggested_fixes": fixes,
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "read_only": True,
        }

    def architecture(self, *, description: str, stack: str, organization_id: str | None = None) -> dict[str, Any]:
        lowered = description.lower()
        components = ["api", "service", "data", "tests", "delivery"]
        if any(word in lowered for word in ("mobile", "flutter", "react native")):
            components.append("mobile-ui")
        if any(word in lowered for word in ("auth", "identity", "security")):
            components.append("identity")
        if any(word in lowered for word in ("queue", "stream", "event")):
            components.append("events")
        v2 = _V2_ENGINE.architecture(
            description=description,
            stack=stack,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        )
        return {
            "view": "novascript_architecture",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "description": description,
            "stack": stack,
            "recommended_components": sorted(set(components + list(v2.get("recommended_components", [])))),
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "relationship": {"builds": "NovaProgramming", "governed_by": "NovaProgramming"},
            "read_only": True,
        }

    def tests(self, *, target: str, framework: str = "pytest", organization_id: str | None = None) -> dict[str, Any]:
        v2 = _V2_ENGINE.tests(
            target=target,
            framework=framework,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        )
        return {
            "view": "novascript_tests",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "target": target,
            "framework": framework,
            "generated_tests": v2.get("generated_files") or _test_skeleton(target, framework),
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "read_only": True,
        }

    def docs(
        self,
        *,
        topic: str,
        audience: str = "developer",
        format: str = "README",
        metadata: dict[str, Any] | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        v2 = _V2_ENGINE.docs(
            topic=topic,
            audience=audience,
            format=format,
            metadata=metadata,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        )
        return {
            "view": "novascript_docs",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "topic": topic,
            "audience": audience,
            "format": format,
            "outline": v2.get("outline") or [
                f"Overview of {topic}",
                "Goals and scope",
                "Implementation notes",
                "Examples",
                "Validation checklist",
            ],
            "metadata": metadata,
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "read_only": True,
        }

    def repository_intelligence(
        self,
        *,
        project_id: str | None = None,
        focus: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        project = _select_project(project_id or self.default_project_id)
        signals = _project_signals(project)
        v2 = _V2_ENGINE.repository_intelligence(
            project_id=project.project_id,
            focus=focus,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        )
        repository_graph = v2.get("repository_graph", {})
        dependencies = sorted(
            {
                part
                for path in repository_graph.get("signals", {}).get("file_paths", signals["file_paths"])
                for part in path.split("/")
                if part
            }
        )
        return {
            "view": "novascript_repo_intelligence",
            "product": "NovaScript",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "project": project.canonical_dict(),
            "focus": focus,
            "signals": signals,
            "dependencies": dependencies,
            "repository_graph": repository_graph,
            "technical_debt": v2.get("technical_debt", {}),
            "model_layer": {
                "provider": v2.get("provider"),
                "model_name": v2.get("model_name"),
            },
            "insight": _classify_intent(focus.lower() or project.description.lower()),
            "relationship": {"builds": "NovaProgramming", "governed_by": "NovaProgramming"},
            "read_only": True,
        }


def get_novascript_service() -> NovaScriptService:
    return NovaScriptService()


def _select_project(project_id: str):
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    return projects.get(project_id, next(iter(projects.values())))


def _project_signals(project) -> dict[str, Any]:
    return {
        "file_count": len(project.files),
        "language_count": len({file.language for file in project.files}),
        "file_paths": [file.path for file in project.files],
        "tags": list(project.tags),
    }


def _classify_intent(text: str) -> str:
    if any(word in text for word in ("api", "endpoint", "route")):
        return "api_design"
    if any(word in text for word in ("test", "pytest", "spec")):
        return "test_generation"
    if any(word in text for word in ("deploy", "docker", "kubernetes", "ci/cd", "ci")):
        return "delivery_automation"
    if any(word in text for word in ("architecture", "design", "diagram")):
        return "architecture_reasoning"
    if any(word in text for word in ("debug", "error", "failure", "trace")):
        return "debugging"
    return "code_generation"


def _generate_files(*, prompt: str, project, language: str, mode: str) -> list[dict[str, Any]]:
    intent = _classify_intent(prompt.lower())
    files: list[dict[str, Any]] = []
    if intent in {"code_generation", "api_design", "architecture_reasoning"}:
        files.append(
            {
                "path": "app/main.py",
                "language": "python",
                "purpose": "FastAPI entrypoint",
                "content": dedent(
                    """
                    from fastapi import FastAPI

                    app = FastAPI(title="NovaScript-generated API")


                    @app.get("/health")
                    def health() -> dict[str, str]:
                        return {"status": "ok"}
                    """
                ).strip(),
            }
        )
    if intent in {"code_generation", "test_generation"}:
        files.append(
            {
                "path": "tests/test_generated.py",
                "language": "python",
                "purpose": "Regression coverage",
                "content": dedent(
                    """
                    def test_generated_contract() -> None:
                        assert True
                    """
                ).strip(),
            }
        )
    if any(word in prompt.lower() for word in ("docker", "deploy", "ci", "cicd")):
        files.append(
            {
                "path": "Dockerfile",
                "language": "dockerfile",
                "purpose": "Container packaging",
                "content": "FROM python:3.12-slim\n",
            }
        )
    if "react" in prompt.lower():
        files.append(
            {
                "path": "src/App.tsx",
                "language": "typescript",
                "purpose": "Frontend shell",
                "content": dedent(
                    """
                    export default function App() {
                      return <main>NovaScript generated UI</main>;
                    }
                    """
                ).strip(),
            }
        )
    if not files:
        files.append(
            {
                "path": f"{project.project_id}/README.md",
                "language": "markdown",
                "purpose": "Implementation notes",
                "content": f"# {project.name}\n\n{prompt}\n",
            }
        )
    return files


def _infer_purpose(code: str) -> str:
    lowered = code.lower()
    if "fastapi" in lowered or "router" in lowered:
        return "API surface or route handler"
    if "django" in lowered or "model" in lowered:
        return "Django data or view layer"
    if "pytest" in lowered or "assert" in lowered:
        return "test or validation code"
    if "docker" in lowered or "from " in lowered:
        return "build or deployment script"
    return "general-purpose application code"


def _test_skeleton(target: str, framework: str) -> list[str]:
    framework = framework.lower().strip()
    if framework == "pytest":
        return [
            f"def test_{target.replace('.', '_').replace('/', '_')}_smoke() -> None:",
            "    assert True",
        ]
    return [
        f"// {framework} test skeleton for {target}",
        "assert(true);",
    ]
