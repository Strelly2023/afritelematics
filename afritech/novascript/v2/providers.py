from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import json
import os

from afritech.afroprog_workspace.models import ProjectWorkspace
from afritech.novascript.v2.parser import get_structured_output_parser
from afritech.novascript.v2.prompts import get_prompt_registry


@dataclass(frozen=True)
class PromptExecutionRequest:
    intent: str
    prompt: str
    project: ProjectWorkspace
    organization_id: str
    language: str = "python"
    mode: str = "code"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionContext:
    prompt_name: str
    model_name: str
    prompt_text: str
    tool_names: tuple[str, ...]


@dataclass(frozen=True)
class PromptExecutionResult:
    provider_name: str
    model_name: str
    raw_output: str
    parsed_output: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    confidence: float
    orchestration: dict[str, Any]


class ModelProvider(Protocol):
    name: str
    def generate(self, request: PromptExecutionRequest, context: ExecutionContext) -> str: ...


class LocalReasoningProvider:
    name = "local-reasoning"

    def generate(self, request: PromptExecutionRequest, context: ExecutionContext) -> str:
        intent = request.intent
        if intent == "generate":
            intent = _classify(request.prompt)
        tool_calls = _tool_plan(intent, request, context)
        payload = {
            "provider": self.name,
            "model": context.model_name,
            "intent": intent,
            "prompt_name": context.prompt_name,
            "summary": _summary_for_intent(intent, request),
            "confidence": _confidence_for_intent(intent),
            "tool_calls": tool_calls,
            "structured_output": {
                "intent": intent,
                "system_boundary": "development_time",
                "governed_by": "NovaProgramming",
            },
        }
        return json.dumps(payload, sort_keys=True)


class LocalCodeProvider(LocalReasoningProvider):
    name = "local-code-engine"


class LocalArchitectureProvider(LocalReasoningProvider):
    name = "local-architecture-engine"


class LocalDebugProvider(LocalReasoningProvider):
    name = "local-debug-engine"


class LocalDocumentationProvider(LocalReasoningProvider):
    name = "local-documentation-engine"


class LocalRepositoryProvider(LocalReasoningProvider):
    name = "local-repository-intelligence-engine"


class OpenAIHybridProvider(LocalReasoningProvider):
    name = "openai-hybrid-engine"

    def generate(self, request: PromptExecutionRequest, context: ExecutionContext) -> str:
        if os.environ.get("NOVASCRIPT_OPENAI_ENABLED", "").lower() not in {"1", "true", "yes"}:
            return super().generate(request, context)
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            return super().generate(request, context)
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=os.environ.get("NOVASCRIPT_OPENAI_MODEL", "gpt-4.1-mini"),
                input=context.prompt_text,
            )
            text = getattr(response, "output_text", "") or super().generate(request, context)
        except Exception:
            return super().generate(request, context)
        payload = json.loads(super().generate(request, context))
        payload["provider"] = self.name
        payload["external_model"] = "openai"
        payload["external_output_digest"] = text[:120]
        return json.dumps(payload, sort_keys=True)


class ModelRouter:
    def __init__(self) -> None:
        self._routes: dict[str, tuple[str, ModelProvider]] = {
            "generate": ("novascript-v3-code", LocalCodeProvider()),
            "generate_code": ("novascript-v3-code", LocalCodeProvider()),
            "code_generation": ("novascript-v3-code", LocalCodeProvider()),
            "tests": ("novascript-v3-test", LocalCodeProvider()),
            "architecture": ("novascript-v3-architecture", LocalArchitectureProvider()),
            "design": ("novascript-v3-architecture", LocalArchitectureProvider()),
            "debug": ("novascript-v3-debug", LocalDebugProvider()),
            "docs": ("novascript-v3-docs", LocalDocumentationProvider()),
            "repo_intelligence": ("novascript-v3-repository", LocalRepositoryProvider()),
            "repository_intelligence": ("novascript-v3-repository", LocalRepositoryProvider()),
            "explain": ("novascript-v3-explain", LocalReasoningProvider()),
        }

    def route(self, intent: str) -> tuple[str, ModelProvider]:
        return self._routes.get(intent.lower().strip(), ("novascript-v3-general", LocalReasoningProvider()))

    def status(self) -> list[dict[str, str]]:
        return [
            {"intent": intent, "model_name": model_name, "provider": provider.name}
            for intent, (model_name, provider) in sorted(self._routes.items())
        ]


class MultiProviderOrchestrator:
    def __init__(self) -> None:
        self._external = OpenAIHybridProvider()

    def choose(
        self,
        *,
        intent: str,
        routed_provider: ModelProvider,
        overridden_provider: ModelProvider | None = None,
    ) -> tuple[ModelProvider, dict[str, Any]]:
        if overridden_provider is not None:
            provider = overridden_provider
            strategy = "explicit_provider_override"
        elif os.environ.get("NOVASCRIPT_PROVIDER_STRATEGY", "").lower() in {"hybrid", "openai"}:
            provider = self._external
            strategy = "openai_local_hybrid"
        else:
            provider = routed_provider
            strategy = "local_specialized"
        return provider, {
            "strategy": strategy,
            "intent": intent,
            "primary_provider": getattr(provider, "name", "unknown"),
            "fallback_provider": "local-reasoning",
            "external_model_configured": bool(os.environ.get("OPENAI_API_KEY")),
        }


class ModelProviderLayer:
    def __init__(self, provider: ModelProvider | None = None, model_name: str | None = None) -> None:
        self._provider_overridden = provider is not None
        self.provider = provider or _resolve_provider()
        self.model_name = model_name or os.environ.get("NOVASCRIPT_MODEL_NAME", "novascript-v3-general")
        self.router = ModelRouter()
        self.orchestrator = MultiProviderOrchestrator()
        self._registry = get_prompt_registry()
        self._parser = get_structured_output_parser()

    def execute(self, request: PromptExecutionRequest) -> PromptExecutionResult:
        routed_model_name, routed_provider = self.router.route(request.intent)
        overridden = self.provider if self._provider_overridden or os.environ.get("NOVASCRIPT_MODEL_PROVIDER") else None
        provider, orchestration = self.orchestrator.choose(
            intent=request.intent,
            routed_provider=routed_provider,
            overridden_provider=overridden,
        )
        model_name = os.environ.get("NOVASCRIPT_MODEL_NAME", routed_model_name)
        prompt_name = _prompt_name_for_intent(request.intent)
        template = self._registry.get(prompt_name)
        prompt_text = template.render(
            prompt=request.prompt,
            project_name=request.project.name,
            stack=request.project.stack,
            language=request.language,
            mode=request.mode,
            context=request.context.get("context", ""),
            code=request.context.get("code", ""),
            error=request.context.get("error", ""),
            description=request.context.get("description", request.prompt),
            target=request.context.get("target", request.project.project_id),
            framework=request.context.get("framework", "pytest"),
            topic=request.context.get("topic", request.prompt),
            audience=request.context.get("audience", "developer"),
            format=request.context.get("format", "README"),
            focus=request.context.get("focus", request.prompt),
        )
        context = ExecutionContext(
            prompt_name=prompt_name,
            model_name=model_name,
            prompt_text=prompt_text,
            tool_names=template.default_tools,
        )
        raw_output = provider.generate(request, context)
        parsed = self._parser.parse(raw_output).data
        tool_calls = parsed.get("tool_calls", [])
        if not isinstance(tool_calls, list):
            tool_calls = []
        confidence = float(parsed.get("confidence", 0.6))
        return PromptExecutionResult(
            provider_name=getattr(provider, "name", "local"),
            model_name=model_name,
            raw_output=raw_output,
            parsed_output=parsed,
            tool_calls=tool_calls,
            confidence=confidence,
            orchestration=orchestration,
        )

    def status(self) -> dict[str, Any]:
        return {
            "provider": "multi-model-router",
            "model_name": self.model_name,
            "available": True,
            "routing": self.router.status(),
            "orchestration": {
                "mode": "multi_provider",
                "providers": ["local_specialized", "openai_hybrid"],
                "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
                "strategy": os.environ.get("NOVASCRIPT_PROVIDER_STRATEGY", "local_specialized"),
            },
        }


def _resolve_provider() -> ModelProvider:
    provider_name = os.environ.get("NOVASCRIPT_MODEL_PROVIDER", "local").strip().lower()
    if provider_name in {"local", "deterministic", "default"}:
        return LocalReasoningProvider()
    return LocalReasoningProvider()


def _prompt_name_for_intent(intent: str) -> str:
    normalized = intent.lower().strip()
    mapping = {
        "generate": "generate",
        "generate_code": "generate",
        "code_generation": "generate",
        "explain": "explain",
        "debug": "debug",
        "architecture": "architecture",
        "design": "architecture",
        "tests": "tests",
        "test": "tests",
        "docs": "docs",
        "documentation": "docs",
        "repo_intelligence": "repo_intelligence",
        "repository_intelligence": "repo_intelligence",
    }
    return mapping.get(normalized, "generate")


def _tool_plan(intent: str, request: PromptExecutionRequest, context: ExecutionContext) -> list[dict[str, Any]]:
    base_tools = list(context.tool_names)
    calls: list[dict[str, Any]] = []
    if intent in {"generate", "generate_code", "code_generation", "architecture", "design"}:
        calls.extend(
            [
                {
                    "name": "repository_graph",
                    "arguments": {"project_id": request.project.project_id},
                },
                {
                    "name": "architecture_kb",
                    "arguments": {"prompt": request.prompt, "project_id": request.project.project_id, "intent": intent},
                },
            ]
        )
    if intent in {"generate", "generate_code", "code_generation", "tests"}:
        calls.append(
                {
                    "name": "multi_file_generation",
                    "arguments": {
                        "prompt": request.prompt,
                        "project_id": request.project.project_id,
                        "intent": intent,
                        "language": request.language,
                        "mode": request.mode,
                    },
                }
            )
    if intent in {"generate", "generate_code", "code_generation", "tests", "repo_intelligence", "debug"}:
        calls.append(
            {
                "name": "debt_analysis",
                "arguments": {"project_id": request.project.project_id, "graph": {"project_id": request.project.project_id}},
            }
        )
    calls.append(
        {
            "name": "trust_review",
            "arguments": {
                "prompt": request.prompt,
                "graph": {"nodes": [], "edges": []},
                "debt": {"score": 25},
                "architecture": {"entries": []},
                "project_id": request.project.project_id,
            },
        }
    )
    if "prompt_registry" in base_tools:
        calls.append({"name": "prompt_registry", "arguments": {"prompt_registry": get_prompt_registry().list()}})
    return calls


def _classify(prompt: str) -> str:
    lowered = prompt.lower()
    if any(word in lowered for word in ("test", "pytest", "spec")):
        return "tests"
    if any(word in lowered for word in ("doc", "readme", "document")):
        return "docs"
    if any(word in lowered for word in ("architecture", "design", "diagram")):
        return "architecture"
    if any(word in lowered for word in ("debug", "error", "bug", "fix")):
        return "debug"
    if any(word in lowered for word in ("repo", "graph", "dependency")):
        return "repo_intelligence"
    return "generate"


def _summary_for_intent(intent: str, request: PromptExecutionRequest) -> dict[str, Any]:
    return {
        "intent": intent,
        "project_id": request.project.project_id,
        "project_name": request.project.name,
        "stack": request.project.stack,
        "language": request.language,
        "mode": request.mode,
        "focus": request.prompt[:120],
    }


def _confidence_for_intent(intent: str) -> float:
    if intent in {"generate", "generate_code", "code_generation"}:
        return 0.8
    if intent in {"architecture", "tests", "docs"}:
        return 0.9
    if intent in {"debug", "repo_intelligence"}:
        return 0.76
    return 0.7
