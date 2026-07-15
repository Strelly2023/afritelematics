"""Incident integration for resilience operations."""

from __future__ import annotations

from dataclasses import dataclass, field

from afritech.novaride_runtime.common.clocks import utc_now


@dataclass(slots=True)
class IncidentRecord:
    incident_id: str
    severity: str
    region: str
    capability: str
    condition: str
    correlation_id: str
    degraded_mode: str
    selected_runbook: str
    timeline_events: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IncidentManager:
    incidents: dict[str, IncidentRecord] = field(default_factory=dict)

    def upsert(self, *, severity: str, region: str, capability: str, condition: str, correlation_id: str, degraded_mode: str, runbook: str) -> IncidentRecord:
        key = f"{region}:{capability}:{condition}"
        incident = self.incidents.get(key)
        timestamp = utc_now().isoformat()
        if incident is None:
            incident = IncidentRecord(
                incident_id=f"incident_{abs(hash(key))}",
                severity=severity,
                region=region,
                capability=capability,
                condition=condition,
                correlation_id=correlation_id,
                degraded_mode=degraded_mode,
                selected_runbook=runbook,
                timeline_events=[f"{timestamp}:detected"],
            )
            self.incidents[key] = incident
        else:
            incident.timeline_events.append(f"{timestamp}:updated")
        return incident
