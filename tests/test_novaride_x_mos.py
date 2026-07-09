from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_novaride_x_core_contract_exists() -> None:
    source = (ROOT / "packages/novaride-core/src/index.ts").read_text()
    for symbol in [
        "MobilityResource",
        "MOSCapability",
        "EventEnvelope",
        "AIDecisionTrace",
        "MobilityCloudLayer",
        "MobilityCloudService",
        "MobilityGraphEdge",
        "AIGovernanceDecision",
        "CityOperatingInsight",
        "FederationNode",
        "EventTaxonomyPrefix",
        "MobilityCloudReadiness",
        "DigitalTwinAsset",
        "EnergyPlan",
        "SustainabilityScore",
        "ReliabilityObjective",
        "MOSReadinessSnapshot",
        "NOVARIDE_X_CAPABILITIES",
        "NOVARIDE_X_CLOUD_LAYERS",
        "NOVARIDE_X_CLOUD_SERVICES",
        "NOVARIDE_X_DECISION_PIPELINE",
        "NOVARIDE_X_EVENT_TAXONOMY",
        "NOVARIDE_X_READINESS",
        "NOVARIDE_X_MOBILITY_CLOUD_READINESS",
        "createDecisionTrace",
    ]:
        assert symbol in source
    for stage in [
        "identity",
        "context",
        "demand_prediction",
        "supply_prediction",
        "pricing",
        "matching",
        "risk_analysis",
        "route_optimization",
        "dispatch",
        "learning",
    ]:
        assert stage in source
    for event_prefix in ["identity", "trip", "fleet", "energy", "transit", "robot", "drone", "city", "simulation", "audit"]:
        assert event_prefix in source


def test_novaride_x_app_surfaces_are_visible() -> None:
    app_sources = {
        "rider": (ROOT / "rider_app/App.tsx").read_text(),
        "driver": (ROOT / "driver_app/App.tsx").read_text(),
        "operator": (ROOT / "novaride_operator_app/App.tsx").read_text(),
        "fleet": (ROOT / "novaride_fleet_app/App.tsx").read_text(),
    }
    for source in app_sources.values():
        assert "NOVARIDE_X" in source

    assert "AI Journey Agent" in app_sources["rider"]
    assert "Digital Twin ETA" in app_sources["rider"]
    assert "Driver Agent" in app_sources["driver"]
    assert "Charging Recommendations" in app_sources["driver"]
    assert "Smart Dispatch Engine" in app_sources["operator"]
    assert "Event Mesh Monitor" in app_sources["operator"]
    assert "National Federation" in app_sources["operator"]
    assert "Autonomous Fleet Orchestration" in app_sources["fleet"]
    assert "Energy-Aware Charging" in app_sources["fleet"]
    assert "Mobility Graph" in app_sources["fleet"]


def test_novaride_x_blueprint_is_tracked() -> None:
    blueprint = ROOT / "docs/vision/NovaRide_X_2035_Mobility_Operating_System.md"
    text = blueprint.read_text()
    for section in [
        "Platform Evolution",
        "Operating Principles",
        "Platform Layers",
        "Mobility Resource Model",
        "Mobility Graph",
        "AI Decision Pipeline",
        "City Operating Layer",
        "National Federation",
        "Unified Event Taxonomy",
        "App Upgrade Scope",
        "Shared Core Additions",
        "Reliability Targets",
    ]:
        assert section in text
