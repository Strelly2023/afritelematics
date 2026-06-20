from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    summary: str
    template: str
    default_tools: tuple[str, ...]

    def render(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)


class PromptRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {
            "generate": PromptTemplate(
                name="generate",
                summary="Generate multi-file software systems",
                template=(
                    "You are NovaScript, NovaTech's AI engineering intelligence layer.\n"
                    "Design a production-ready software system from the prompt below.\n"
                    "Prompt: {prompt}\n"
                    "Project: {project_name}\n"
                    "Stack: {stack}\n"
                    "Language: {language}\n"
                    "Mode: {mode}\n"
                    "Return a JSON object with intent, confidence, tool_calls, summary, and review notes.\n"
                    "Never claim runtime authority."
                ),
                default_tools=("repository_graph", "architecture_kb", "multi_file_generation", "debt_analysis", "trust_review"),
            ),
            "explain": PromptTemplate(
                name="explain",
                summary="Explain code or scripts",
                template=(
                    "Explain the following code for a developer audience.\n"
                    "Context: {context}\n"
                    "Code:\n{code}\n"
                    "Return JSON with summary, signals, and risks."
                ),
                default_tools=("structured_output_parser",),
            ),
            "debug": PromptTemplate(
                name="debug",
                summary="Diagnose failures and propose fixes",
                template=(
                    "Diagnose the failure below and suggest deterministic fixes.\n"
                    "Error: {error}\n"
                    "Context: {context}\n"
                    "Code:\n{code}\n"
                    "Return JSON with findings, fixes, and confidence."
                ),
                default_tools=("structured_output_parser", "debt_analysis"),
            ),
            "architecture": PromptTemplate(
                name="architecture",
                summary="Design software architecture",
                template=(
                    "Design a system architecture.\n"
                    "Description: {description}\n"
                    "Stack: {stack}\n"
                    "Return JSON with components, boundaries, risks, and file plan."
                ),
                default_tools=("architecture_kb", "repository_graph"),
            ),
            "tests": PromptTemplate(
                name="tests",
                summary="Generate tests",
                template=(
                    "Generate tests for the target below.\n"
                    "Target: {target}\n"
                    "Framework: {framework}\n"
                    "Return JSON with assertions, cases, and file plan."
                ),
                default_tools=("multi_file_generation", "trust_review"),
            ),
            "docs": PromptTemplate(
                name="docs",
                summary="Generate documentation",
                template=(
                    "Write developer documentation.\n"
                    "Topic: {topic}\n"
                    "Audience: {audience}\n"
                    "Format: {format}\n"
                    "Return JSON with outline and artifacts."
                ),
                default_tools=("architecture_kb",),
            ),
            "repo_intelligence": PromptTemplate(
                name="repo_intelligence",
                summary="Analyze repository intelligence",
                template=(
                    "Analyze repository structure and engineering signals.\n"
                    "Project: {project_name}\n"
                    "Focus: {focus}\n"
                    "Return JSON with graph summary, dependency observations, and technical debt."
                ),
                default_tools=("repository_graph", "debt_analysis", "trust_review"),
            ),
        }

    def get(self, name: str) -> PromptTemplate:
        try:
            return self._templates[name]
        except KeyError as exc:
            raise KeyError(f"unknown prompt template: {name}") from exc

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": template.name,
                "summary": template.summary,
                "default_tools": list(template.default_tools),
            }
            for template in self._templates.values()
        ]


_DEFAULT_PROMPT_REGISTRY = PromptRegistry()


def get_prompt_registry() -> PromptRegistry:
    return _DEFAULT_PROMPT_REGISTRY
