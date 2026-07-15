"""SLO and error-budget calculations for NovaRide operations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SLODefinition:
    service: str
    availability_target: Decimal
    latency_target_ms: int
    period_days: int = 30


SLO_DEFINITIONS: tuple[SLODefinition, ...] = (
    SLODefinition("Emergency/SOS", Decimal("99.999"), 500),
    SLODefinition("active_trip_tracking", Decimal("99.99"), 1000),
    SLODefinition("booking", Decimal("99.95"), 1500),
    SLODefinition("dispatch", Decimal("99.95"), 1500),
    SLODefinition("payment_orchestration", Decimal("99.95"), 2000),
    SLODefinition("support", Decimal("99.9"), 2500),
    SLODefinition("analytics", Decimal("99.5"), 5000),
)


def calculate_slo(service: str, *, successful: int, total: int, latency_compliant: int) -> dict[str, str | bool]:
    definition = next((item for item in SLO_DEFINITIONS if item.service == service), None)
    if definition is None:
        raise ValueError("unknown_slo_service")
    availability = Decimal("100") if total == 0 else (Decimal(successful) / Decimal(total)) * Decimal("100")
    latency = Decimal("100") if total == 0 else (Decimal(latency_compliant) / Decimal(total)) * Decimal("100")
    error_budget = Decimal("100") - definition.availability_target
    consumed = max(Decimal("0"), definition.availability_target - availability)
    burn_rate = Decimal("0") if error_budget == 0 else consumed / error_budget
    return {
        "service": service,
        "availability": format(availability.quantize(Decimal("0.001")), "f"),
        "latency_compliance": format(latency.quantize(Decimal("0.001")), "f"),
        "target": format(definition.availability_target, "f"),
        "error_budget": format(error_budget, "f"),
        "burn_rate": format(burn_rate.quantize(Decimal("0.001")), "f"),
        "breaching": availability < definition.availability_target,
    }


def all_slos() -> list[dict[str, str | bool]]:
    return [calculate_slo(definition.service, successful=1000, total=1000, latency_compliant=995) for definition in SLO_DEFINITIONS]
