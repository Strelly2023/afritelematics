from __future__ import annotations

from afritech.core_platform.geo_routing import adjust_sla_capacity, select_region


def test_select_region_prefers_country_mapping_when_healthy() -> None:
    decision = select_region(
        client_country="DE",
        trust_level="enterprise",
        health_map={"AU": "healthy", "EU": "healthy", "US": "healthy"},
        latency_map={"AU": 110, "EU": 40, "US": 180},
    )

    assert decision["region"] == "EU"
    assert decision["geo_source"] == "country"
    assert decision["routing_reason"] == "country_mapping"
    assert decision["failover_region"] == "AU"


def test_select_region_falls_back_to_lowest_latency_when_target_is_unhealthy() -> None:
    decision = select_region(
        client_country="US",
        trust_level="sandbox",
        health_map={"AU": "healthy", "EU": "healthy", "US": "down"},
        latency_map={"AU": 120, "EU": 45, "US": 20},
    )

    assert decision["region"] == "EU"
    assert decision["geo_source"] == "latency"
    assert decision["routing_reason"] == "lowest_latency"


def test_adjust_sla_capacity_reduces_under_high_latency() -> None:
    assert adjust_sla_capacity(300, 180, "enterprise") == 210
    assert adjust_sla_capacity(300, 180, "sandbox") == 150
