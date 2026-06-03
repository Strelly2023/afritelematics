from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
)


@dataclass(frozen=True)
class APIContractSet:
    endpoints: tuple[dict[str, str], ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {"endpoints": list(self.endpoints)}


class APIContractGenerator:
    """Generate REST API contract proposals."""

    def generate(self, analysis: DomainAnalysis) -> APIContractSet:
        endpoints: list[dict[str, str]] = []

        for entity in analysis.entities:
            resource = _resource(entity)
            endpoints.append({"method": "POST", "path": f"/{resource}", "purpose": f"Create {entity}"})
            endpoints.append({"method": "GET", "path": f"/{resource}/{{id}}", "purpose": f"Read {entity}"})

        if "ProductionReport" in analysis.entities:
            endpoints.append({"method": "GET", "path": "/reports/production", "purpose": "Read production report"})

        return APIContractSet(endpoints=tuple(endpoints))


def _resource(entity: str) -> str:
    result = []
    for index, character in enumerate(entity):
        if character.isupper() and index:
            result.append("-")
        result.append(character.lower())
    value = "".join(result)
    if value.endswith("y"):
        return value[:-1] + "ies"
    if value.endswith("s"):
        return value
    return value + "s"
