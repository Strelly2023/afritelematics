from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
)


@dataclass(frozen=True)
class DatabaseContractSet:
    tables: tuple[dict[str, object], ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {"tables": list(self.tables)}


class DatabaseContractGenerator:
    """Generate database table contract proposals."""

    BASE_COLUMNS = ("id", "created_at", "updated_at")

    def generate(self, analysis: DomainAnalysis) -> DatabaseContractSet:
        tables = tuple(
            {
                "name": _table_name(entity),
                "entity": entity,
                "columns": list(self.BASE_COLUMNS + _domain_columns(entity)),
            }
            for entity in analysis.entities
        )

        return DatabaseContractSet(tables=tables)


def _table_name(entity: str) -> str:
    pieces = []
    for index, character in enumerate(entity):
        if character.isupper() and index:
            pieces.append("_")
        pieces.append(character.lower())
    value = "".join(pieces)
    if value.endswith("y"):
        return value[:-1] + "ies"
    if value.endswith("s"):
        return value
    return value + "s"


def _domain_columns(entity: str) -> tuple[str, ...]:
    mapping = {
        "Bird": ("flock_id", "tag", "breed", "status"),
        "Flock": ("name", "location", "started_on"),
        "FeedInventory": ("feed_type", "quantity_kg", "threshold_kg"),
        "WaterLog": ("flock_id", "liters", "logged_at"),
        "Vaccination": ("bird_id", "vaccine", "scheduled_for", "administered_at"),
        "EggProduction": ("flock_id", "egg_count", "collected_on"),
        "ProductionReport": ("period_start", "period_end", "summary_hash"),
    }
    return mapping.get(entity, ("name", "status"))
