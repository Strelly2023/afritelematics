from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.architecture.novaride_next_generation import (
    NOVARIDE_NEXT_GENERATION_VERSION,
    novaride_next_generation_manifest,
)


def test_novaride_next_generation_manifest_exposes_universal_driver_platform() -> None:
    manifest = novaride_next_generation_manifest()
    driver = manifest["driver"]

    assert manifest["version"] == NOVARIDE_NEXT_GENERATION_VERSION
    assert manifest["status"] == "runtime_capabilities_complete_release_candidate"
    assert "Africa" in manifest["markets"]
    assert "Australia" in manifest["markets"]
    assert "India" in manifest["markets"]
    assert "Europe" in manifest["markets"]
    assert "USA" in manifest["markets"]
    assert driver["positioning"] == "Universal Mobility Operations Platform"
    assert {
        "NovaID Identity",
        "Offline Engine",
        "AI Copilot",
        "Vehicle Hub",
        "Compliance",
        "Diagnostics",
    }.issubset(set(driver["modules"]))
    assert {service["category"] for service in driver["services"]} >= {
        "Ride Hailing",
        "African Transport",
        "Delivery",
        "Logistics",
    }
    assert driver["operations"]["availability_rule"].startswith("dispatchable_requires")
    assert driver["operations"]["offline_rule"] == (
        "safety_critical_operations_wait_for_authoritative_server_acknowledgement"
    )


def test_novaride_next_generation_manifest_exposes_rider_access_platform() -> None:
    rider = novaride_next_generation_manifest()["rider"]

    assert rider["surface_principle"] == "Where are you going?"
    assert rider["primary_navigation"] == ["Home", "Trips", "Wallet", "Safety", "Account"]
    assert "Family" in rider["secondary_services"]
    assert "Accessibility" in rider["secondary_services"]
    assert {service["category"] for service in rider["services"]} >= {
        "Ride-Hailing",
        "African Mobility",
        "Delivery",
        "Public and Multi-Modal Transport",
    }
    assert rider["offline"]["confirmation_rule"] == (
        "booking_is_not_confirmed_without_authoritative_server_confirmation"
    )
    assert "M-Pesa" in rider["payments"]["mobile_money"]
    assert "UPI" in rider["payments"]["global"]
    assert "Cash" in rider["payments"]["global"]
    assert "NovaPay Wallet" in rider["payments"]["global"]


def test_novaride_next_generation_manifest_exposes_operator_control_plane() -> None:
    operator = novaride_next_generation_manifest()["operator"]

    assert operator["positioning"] == "Mobility Operations Control Plane"
    assert operator["navigation"] == [
        "Command Center",
        "Live Map",
        "Trips",
        "Drivers",
        "Riders",
        "Dispatch",
        "Safety",
        "Incidents",
        "Support",
        "Payments",
        "Fleets",
        "Vehicles",
        "Regions",
        "Compliance",
        "Fraud",
        "Observability",
        "Evidence",
        "Reports",
        "Administration",
    ]
    assert "active_emergencies" in operator["command_center"]["signals"]
    assert "emergency_escalation" in operator["governed_interventions"]
    assert operator["ai_boundary"]["NovaAI"] == "advisory_only"
    assert "approve_payments" in operator["ai_boundary"]["prohibited_actions"]


def test_novaride_next_generation_backend_keeps_authoritative_core_boundaries() -> None:
    backend = novaride_next_generation_manifest()["backend"]
    authority = backend["authority_model"]

    assert "dispatch_decisions" in authority["rider_backend"]["does_not_own"]
    assert "payment_settlement" in authority["rider_backend"]["does_not_own"]
    assert authority["driver_backend"]["rule"] == (
        "driver_is_not_dispatchable_until_core_dispatch_confirms_eligibility"
    )
    assert "dispatch" in authority["core_backend"]["owns"]
    assert "pricing" in authority["core_backend"]["owns"]
    assert "safety" in authority["core_backend"]["owns"]
    assert authority["NovaPay"] == "payments_wallets_settlement_payouts_financial_ledger"
    assert authority["NovaAI"] == "recommendations_only"
    assert "Dispatch Engine" in backend["core_components"]
    assert "TripEvidenceFinalized" in backend["events"]["event_types"]
    assert "event_id" in backend["events"]["required_envelope_fields"]


def test_novaride_next_generation_frontend_and_regional_contracts_are_complete() -> None:
    manifest = novaride_next_generation_manifest()
    frontend = manifest["frontend"]
    regions = {region["region"]: set(region["capabilities"]) for region in manifest["regional_adaptation"]}

    assert set(frontend["apps"]) >= {
        "novaride-rider",
        "novaride-driver",
        "novaride-operator",
        "novaride-fleet",
        "novaride-support",
        "novaride-inspector",
    }
    assert set(frontend["shared_packages"]) >= {
        "novaride-design-system",
        "novaride-api-sdk",
        "novaride-auth",
        "novaride-maps",
        "novaride-offline",
        "novaride-safety",
        "novaride-payments-ui",
        "novaride-localization",
        "novaride-accessibility",
        "novaride-observability",
        "novaride-feature-flags",
    }
    assert "confirmed_booking" in frontend["state_authority"]["local_state_must_not_authorize"]
    assert "accept_trip" in frontend["offline_policy"]["authoritative_confirmation_required"]
    assert "mobile_money" in regions["Africa"]
    assert "offline_mode" in regions["Africa"]
    assert "UPI" in regions["India"]
    assert "GDPR_controls" in regions["Europe and United Kingdom"]


def test_novaride_next_generation_resilience_accessibility_and_availability_are_first_class() -> None:
    manifest = novaride_next_generation_manifest()
    resilience = manifest["resilience"]

    assert resilience["operating_principle"] == (
        "preserve_core_journey_when_networks_providers_maps_or_components_are_degraded"
    )
    assert set(resilience["platform_qualities"]) == {
        "flexibility",
        "accessibility",
        "reliability",
        "availability",
    }
    assert {"mobile_app", "whatsapp", "ussd", "sms", "call_center", "operator_assisted_booking"}.issubset(
        set(resilience["omni_channel_booking"])
    )
    assert "novapay_reconciliation" in resilience["hybrid_payment_flow"]
    assert "Onafriq corridors" in resilience["universal_payment_methods"]["mobile_money"]
    assert "Offline Queue" in resilience["resilience_layer"]["components"]
    assert {"if": "card_provider_unavailable", "then": "offer_mobile_money_wallet_or_cash"} in resilience[
        "resilience_layer"
    ]["graceful_degradation"]
    assert resilience["accessibility"]["standard"] == "WCAG_2_2_AA"
    assert "screen_reader" in resilience["accessibility"]["interface_modes"]
    assert any(target["service"] == "Emergency/SOS" and target["availability"] == "99.999%" for target in resilience["availability_targets"])
    assert "South Africa" in resilience["regional_expansion"][0]["countries"]
    assert "payment_provider_switch" in resilience["governed_high_impact_actions"]


def test_novaride_next_generation_resilience_operations_security_and_multi_zone_gates() -> None:
    resilience = novaride_next_generation_manifest()["resilience"]

    assert resilience["operations_window"]["name"] == "Resilience and Availability"
    assert {"open_circuit", "trigger_failover", "broadcast_outage_message"}.issubset(
        set(resilience["operations_window"]["quick_actions"])
    )
    assert "payment_provider_switch" in resilience["operations_window"]["approval_required"]
    assert resilience["multi_zone_topology"]["minimum_zones"] == 3
    assert "postgresql_multi_az" in resilience["multi_zone_topology"]["critical_dependencies"]
    assert "topology_spread_constraints" in resilience["multi_zone_topology"]["kubernetes_controls"]
    assert resilience["regional_isolation"]["global_control_plane_unavailable_rule"] == (
        "regional_booking_dispatch_active_trips_and_local_payment_fallback_continue"
    )
    assert {"signed_synchronization_requests", "tenant_isolation", "region_isolation"}.issubset(
        set(resilience["security_requirements"])
    )
    assert {"database_promotion_tests", "emergency_path_tests", "recovery_evidence_verification"}.issubset(
        set(resilience["production_gates"])
    )


def test_novaride_next_generation_api_route_returns_contract() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/next-generation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "novaride-next-generation-universal-mobility-platform"
    assert payload["driver"]["api_surface"]
    assert "POST /v1/rider/bookings" in payload["rider"]["api_surface"]
    assert "GET /v1/operator/command-center" in payload["operator"]["api_surface"]
    assert payload["authority_statement"].startswith("Rider, Driver, and Operator apps")
    assert {item["target_score"] for item in payload["target_maturity"]} == {10}
    assert payload["honest_status"] == "runtime_capabilities_complete_release_candidate"
    assert payload["runtime_metadata"]["governance_state"] == {
        "GA_ALLOWED": False,
        "GA_APPROVAL": "PENDING",
        "REAL_PAYMENTS_ENABLED": False,
        "REAL_PAYMENT_APPROVAL": "PENDING",
    }
