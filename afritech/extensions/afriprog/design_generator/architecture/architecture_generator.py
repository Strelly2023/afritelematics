from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.architecture.dependency_mapper import (
    DependencyMap,
    DependencyMapper,
)
from afritech.extensions.afriprog.design_generator.architecture.module_generator import (
    ModuleGenerator,
    ModuleProposal,
)
from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
)


@dataclass(frozen=True)
class ArchitectureProposal:
    style: str
    modules: ModuleProposal
    dependencies: DependencyMap

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "style": self.style,
            "modules": self.modules.canonical_dict(),
            "dependencies": self.dependencies.canonical_dict(),
        }


class ArchitectureGenerator:
    """Generate proposal-only architecture from analyzed domain."""

    def __init__(
        self,
        module_generator: ModuleGenerator | None = None,
        dependency_mapper: DependencyMapper | None = None,
    ) -> None:
        self.module_generator = module_generator or ModuleGenerator()
        self.dependency_mapper = dependency_mapper or DependencyMapper()

    def generate(self, analysis: DomainAnalysis) -> ArchitectureProposal:
        modules = self.module_generator.generate(analysis)

        return ArchitectureProposal(
            style="layered_domain_application_infrastructure",
            modules=modules,
            dependencies=self.dependency_mapper.map(modules.modules),
        )
