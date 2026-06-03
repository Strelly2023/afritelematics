from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
)


@dataclass(frozen=True)
class ModuleProposal:
    modules: tuple[str, ...]
    domain_models: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "modules": list(self.modules),
            "domain_models": list(self.domain_models),
        }


class ModuleGenerator:
    """Generate bounded module proposals from domain analysis."""

    def generate(self, analysis: DomainAnalysis) -> ModuleProposal:
        return ModuleProposal(
            modules=(
                "domain",
                "application",
                "infrastructure",
                "api",
                "ui",
                "tests",
                "validators",
            ),
            domain_models=analysis.entities,
        )
