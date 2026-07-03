from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.main import app
from afriride_system.globalization.readiness import GlobalReadinessService


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token('global-ops', 'OPERATOR')}"}


def candidate(driver_id: str, region_id: str, distance: float, **extra) -> dict:
    return {
        "driver_id": driver_id,
        "region_id": region_id,
        "distance_km": distance,
        "traffic_factor": 1,
        "driver_rating": 4.9,
        "vehicle_type": "standard",
        "acceptance_rate": 0.95,
        "trust_score": 95,
        "battery_level": 90,
        "estimated_arrival_minutes": distance * 2,
        "surge_demand": 0.2,
        **extra,
    }


def test_region_catalog_carries_currency_locale_timezone_and_compliance() -> None:
    service = GlobalReadinessService()
    regions = service.regions()
    assert {item["country_code"] for item in regions} == {"AU", "UG", "KE", "NG", "ZA"}
    assert {item["currency"] for item in regions} == {"AUD", "UGX", "KES", "NGN", "ZAR"}
    for region in regions:
        assert region["locales"]
        assert region["time_zone"]
        assert region["data_residency"]
        assert region["compliance"]


def test_configurable_pricing_caps_surge_and_returns_local_time() -> None:
    quote = GlobalReadinessService().quote(
        region_id="au-mel",
        distance_km=Decimal("10"),
        duration_minutes=Decimal("20"),
        surge_multiplier=Decimal("9"),
    )
    assert quote["currency"] == "AUD"
    assert quote["surge_multiplier"] == "2.00"
    assert quote["total_minor"] > quote["subtotal_minor"]
    assert quote["quoted_at"]["time_zone"] == "Australia/Melbourne"
    assert quote["quoted_at"]["utc"].endswith("Z")


def test_tenant_branding_and_region_allowlist(monkeypatch) -> None:
    monkeypatch.setenv(
        "AFRIRIDE_TENANT_CONFIG_JSON",
        '{"fleet-a":{"regions":["ke-nbo"],"brand":{"name":"Safari Fleet","primary_color":"#112233"}}}',
    )
    service = GlobalReadinessService()
    config = service.resolve(
        organization_id="fleet-a", region_id="ke-nbo", locale="sw-KE"
    )
    assert config["contract"] == "afriride.global.v1"
    assert config["brand"]["name"] == "Safari Fleet"
    assert config["locale"] == "sw-KE"
    try:
        service.resolve(organization_id="fleet-a", region_id="ug-kla", locale=None)
    except PermissionError:
        pass
    else:
        raise AssertionError("tenant region allowlist was not enforced")


def test_country_compliance_blocks_incomplete_driver() -> None:
    result = GlobalReadinessService().compliance_check(
        region_id="ke-nbo",
        actor_type="driver",
        documents=["driving_licence", "insurance"],
    )
    assert result["compliant"] is False
    assert result["dispatch_eligible"] is False
    assert "psv_badge" in result["missing_documents"]


def test_dispatch_never_assigns_cross_region_or_noncompliant_driver() -> None:
    response = TestClient(app).post(
        "/v1/operations/dispatch/optimize",
        headers=auth(),
        json={
            "ride_id": "ride-global",
            "region_id": "ug-kla",
            "requested_vehicle_type": "standard",
            "candidates": [
                candidate("regional-driver", "ug-kla", 3),
                candidate("cross-region-driver", "ke-nbo", 0.1),
                candidate("noncompliant-driver", "ug-kla", 0.1, country_compliant=False),
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["selected_driver_id"] == "regional-driver"
    assert response.json()["region_id"] == "ug-kla"


def test_mobile_runtime_caches_localization_currency_timezone_and_brand() -> None:
    runtime = read("afriride_system/mobile/shared/globalRuntime.js")
    for contract in (
        "AsyncStorage",
        "Intl.NumberFormat",
        "Intl.DateTimeFormat",
        "primary_color",
        "sw: {",
        "zu: {",
    ):
        assert contract in runtime
    for app in ("rider_app", "driver_app"):
        source = read(f"{app}/App.tsx")
        assert "useGlobalRuntime" in source
        assert "globalRuntime.brand.name" in source
        assert "globalRuntime.region.currency" in source
        assert "brandColor={globalRuntime.brand.primary_color}" in source
