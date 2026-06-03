from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MilestonePlan:
    milestones: tuple[dict[str, object], ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {"milestones": list(self.milestones)}


class MilestoneGenerator:
    """Generate implementation milestones."""

    def generate(self) -> MilestonePlan:
        return MilestonePlan(
            milestones=(
                {"phase": 1, "name": "Domain and contracts", "deliverables": ["domain models", "database contracts"]},
                {"phase": 2, "name": "Application and APIs", "deliverables": ["services", "REST endpoints"]},
                {"phase": 3, "name": "Validation and reporting", "deliverables": ["tests", "reports", "guards"]},
            )
        )
