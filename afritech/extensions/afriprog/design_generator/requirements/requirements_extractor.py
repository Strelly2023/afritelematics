from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
    DomainAnalyzer,
)


@dataclass(frozen=True)
class RequirementSet:
    functional: tuple[str, ...]
    non_functional: tuple[str, ...]
    constraints: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "functional": list(self.functional),
            "non_functional": list(self.non_functional),
            "constraints": list(self.constraints),
        }


class RequirementsExtractor:
    """Generate proposal requirements from domain analysis."""

    def __init__(self, analyzer: DomainAnalyzer | None = None) -> None:
        self.analyzer = analyzer or DomainAnalyzer()

    def extract(self, intent: str) -> tuple[DomainAnalysis, RequirementSet]:
        analysis = self.analyzer.analyze(intent)
        functional = tuple(
            f"Support {workflow.replace('_', ' ')}"
            for workflow in analysis.workflows
        )

        return (
            analysis,
            RequirementSet(
                functional=functional,
                non_functional=(
                    "Deterministic audit trail",
                    "Role-aware access boundaries",
                    "Replay-safe reporting",
                    "Mobile-friendly operational workflows",
                ),
                constraints=(
                    "Proposal-only design output",
                    "No repository mutation",
                    "No authority creation",
                    "Constitutional guards must remain authoritative",
                ),
            ),
        )
