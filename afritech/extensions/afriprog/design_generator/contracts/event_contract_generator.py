from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
)


@dataclass(frozen=True)
class EventContractSet:
    events: tuple[dict[str, str], ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {"events": list(self.events)}


class EventContractGenerator:
    """Generate domain event contract proposals."""

    def generate(self, analysis: DomainAnalysis) -> EventContractSet:
        events = tuple(
            {
                "name": f"{workflow.upper()}_RECORDED",
                "source": analysis.domain,
                "authority": "observational_only",
            }
            for workflow in analysis.workflows
        )

        return EventContractSet(events=events)
