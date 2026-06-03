from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainAnalysis:
    intent: str
    domain: str
    entities: tuple[str, ...]
    workflows: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "domain": self.domain,
            "entities": list(self.entities),
            "workflows": list(self.workflows),
        }


class DomainAnalyzer:
    """Deterministically infer domain entities and workflows from intent."""

    def analyze(self, intent: str) -> DomainAnalysis:
        normalized = " ".join(intent.strip().split())
        lower = normalized.lower()

        if "poultry" in lower or "farm" in lower:
            return DomainAnalysis(
                intent=normalized,
                domain="poultry_management",
                entities=(
                    "Bird",
                    "Flock",
                    "FeedInventory",
                    "WaterLog",
                    "Vaccination",
                    "EggProduction",
                    "ProductionReport",
                ),
                workflows=(
                    "bird_intake",
                    "feed_tracking",
                    "water_monitoring",
                    "vaccination_scheduling",
                    "egg_collection",
                    "production_reporting",
                ),
            )

        if "health" in lower:
            return DomainAnalysis(
                intent=normalized,
                domain="health_management",
                entities=("Patient", "Visit", "TreatmentPlan", "ClinicalReport"),
                workflows=("patient_registration", "visit_tracking", "care_reporting"),
            )

        return DomainAnalysis(
            intent=normalized,
            domain="general_software_system",
            entities=("User", "Account", "Workflow", "Report"),
            workflows=("intake", "processing", "reporting"),
        )
