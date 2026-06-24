from __future__ import annotations

from decimal import Decimal
import httpx

import pytest

from afritech.api.core_platform_api import core_platform_console_payload
from afritech.core_platform import (
    AuthorityRequest,
    InMemoryCorePlatformStore,
    NovaIDService,
    NovaTechCorePlatform,
    PayIDProvider,
    PaymentIntent,
    StripeProvider,
)
from afritech.core_platform.audit_export import render_audit_pdf
from afritech.core_platform.compliance_report import build_enterprise_audit_report
from afritech.core_platform.anchoring import anchor_packet, build_optional_blockchain_anchor
from afritech.core_platform.cbdc import cbdc_status
from afritech.core_platform.event_bus import build_event_bus_status
from afritech.core_platform.export_bundle import build_auditor_zip
from afritech.core_platform.migration_system import build_migration_plan, list_migrations
from afritech.core_platform.orm import CoreTrustPacketRecord
from afritech.core_platform.qr import render_qr_png
from afritech.core_platform.settlement import SettlementRouter, build_settlement_status
from afritech.core_platform.signing import sign_packet, verify_packet_signature
from afritech.core_platform.signing import build_key_rotation_plan, signing_key_status
from afritech.core_platform.trust_node import build_trust_node_network_status


def test_core_platform_overview_is_product_app_free() -> None:
    payload = core_platform_console_payload()

    assert payload["platform"] == "NovaTechSol"
    assert payload["console"] == "Unified Trust Operating Console"
    assert payload["product_applications_included"] is False
    assert payload["flow"] == [
        "NovaID",
        "NovaPower",
        "NovaPay",
        "NovaTrust",
        "NovaScript",
        "NovaProgramming",
    ]
    assert [module["path"] for module in payload["modules"]] == [
        "/console/identity",
        "/console/authority",
        "/console/payments",
        "/console/trust",
        "/console/intelligence",
        "/console/programming",
    ]


def test_core_platform_allows_identity_bound_payment_and_records_proof() -> None:
    platform = NovaTechCorePlatform()
    identity = NovaIDService().bind_identity(
        identity_id="user-001",
        email="operator@novatech.local",
        roles=("admin",),
        organization_id="org-001",
        scopes=("payments:write", "trust:read"),
        devices=("macbook-air",),
    )
    request = AuthorityRequest(
        action="payment.execute",
        organization_id="org-001",
        required_roles=("admin", "finance"),
        required_scopes=("payments:write",),
        resource_owner_id="user-001",
        risk_score=Decimal("0.22"),
    )
    intent = PaymentIntent(
        intent_id="intent-001",
        actor_id="user-001",
        organization_id="org-001",
        amount=Decimal("24.50"),
        currency="aud",
        destination="merchant-001",
    )

    result = platform.execute_payment_flow(
        identity=identity,
        request=request,
        payment_intent=intent,
    )

    assert result.decision.decision == "ALLOW"
    assert result.payment is not None
    assert result.payment.status == "completed"
    assert result.payment.currency == "AUD"
    assert result.payment.provider == "payid"
    assert result.payment.provider_reference is not None
    assert result.trust.event_type == "core.payment.completed"
    assert platform.trust.replay(result.trust) is True
    assert result.explanation.risk_level == "LOW"
    assert result.proposal is not None
    assert result.proposal.lifecycle_state == "ready_for_validation"


def test_core_platform_cross_border_settlement_routes_through_fx_and_mobile_money() -> None:
    platform = NovaTechCorePlatform()
    identity = NovaIDService().bind_identity(
        identity_id="user-cross-border",
        email="cross-border@novatech.local",
        roles=("admin",),
        organization_id="org-cross-border",
        scopes=("payments:write", "trust:read"),
    )
    request = AuthorityRequest(
        action="payment.execute",
        organization_id="org-cross-border",
        required_roles=("admin",),
        required_scopes=("payments:write",),
        resource_owner_id="user-cross-border",
        risk_score=Decimal("0.15"),
    )
    intent = PaymentIntent(
        intent_id="intent-cross-border",
        actor_id="user-cross-border",
        organization_id="org-cross-border",
        amount=Decimal("10.00"),
        currency="AUD",
        destination="+254700000001",
        metadata={"country": "KE", "description": "cross-border test"},
    )

    planned = SettlementRouter().plan(
        intent,
        provider="mobile_money",
    )
    assert planned.plan.route_class == "cross_border"
    assert planned.plan.settlement_currency == "KES"

    result = platform.execute_payment_flow(
        identity=identity,
        request=request,
        payment_intent=intent,
        provider="mobile_money",
    )

    assert result.payment is not None
    assert result.payment.provider == "mpesa_ke"
    assert result.payment.currency == "KES"
    assert result.payment.status == "pending"
    assert result.settlement is not None
    assert result.settlement.route_class == "cross_border"
    assert result.settlement.settlement_country == "KE"
    assert result.settlement.settlement_currency == "KES"
    assert result.settlement.fx_locked is True
    assert result.trust.packet["settlement"]["settlement_currency"] == "KES"


def test_core_platform_denies_cross_tenant_payment_before_execution() -> None:
    platform = NovaTechCorePlatform()
    identity = NovaIDService().bind_identity(
        identity_id="user-002",
        email="analyst@novatech.local",
        roles=("analyst",),
        organization_id="org-a",
        scopes=("payments:write",),
    )
    request = AuthorityRequest(
        action="payment.execute",
        organization_id="org-b",
        required_roles=("admin",),
        required_scopes=("payments:write",),
        resource_owner_id="user-999",
        risk_score=Decimal("0.91"),
    )
    intent = PaymentIntent(
        intent_id="intent-002",
        actor_id="user-002",
        organization_id="org-a",
        amount=Decimal("100.00"),
        currency="aud",
        destination="merchant-002",
    )

    result = platform.execute_payment_flow(
        identity=identity,
        request=request,
        payment_intent=intent,
    )

    assert result.decision.decision == "DENY"
    assert result.payment is None
    assert "tenant_mismatch" in result.decision.checks
    assert "role_missing" in result.decision.checks
    assert "ownership_mismatch" in result.decision.checks
    assert "risk_above_policy" in result.decision.checks
    assert result.trust.event_type == "core.payment.denied"
    assert platform.trust.replay(result.trust) is True
    assert result.explanation.recommended_action == "review"
    assert result.proposal is not None
    assert result.proposal.lifecycle_state == "requires_review"


def test_payment_intent_must_remain_identity_bound() -> None:
    platform = NovaTechCorePlatform()
    identity = NovaIDService().bind_identity(
        identity_id="user-003",
        email="finance@novatech.local",
        roles=("admin",),
        organization_id="org-003",
        scopes=("payments:write",),
    )
    request = AuthorityRequest(
        action="payment.execute",
        organization_id="org-003",
        required_roles=("admin",),
        required_scopes=("payments:write",),
        resource_owner_id="user-003",
    )
    intent = PaymentIntent(
        intent_id="intent-003",
        actor_id="attacker",
        organization_id="org-003",
        amount=Decimal("10.00"),
        currency="aud",
        destination="merchant-003",
    )

    with pytest.raises(ValueError, match="actor must match"):
        platform.execute_payment_flow(
            identity=identity,
            request=request,
            payment_intent=intent,
        )


def test_payment_provider_adapters_support_payid_and_stripe_pilot_mode() -> None:
    intent = PaymentIntent(
        intent_id="intent-provider-001",
        actor_id="user-provider",
        organization_id="org-provider",
        amount=Decimal("12.00"),
        currency="aud",
        destination="merchant-provider",
    )

    payid = PayIDProvider().authorize(intent)
    assert payid.provider == "payid"
    assert payid.status == "completed"
    assert payid.provider_reference.startswith("PAYID-")
    assert payid.raw["mode"] == "controlled_pilot"

    stripe = StripeProvider(api_key=None, live=False).authorize(intent)
    assert stripe.provider == "stripe"
    assert stripe.status == "completed"
    assert stripe.settlement_status == "requires_live_provider"


def test_payment_provider_adapters_support_live_payid_gateway(monkeypatch) -> None:
    monkeypatch.setenv("NOVAPAY_PAYID_LIVE_ENABLED", "true")
    monkeypatch.setenv("NOVAPAY_PAYID_COLLECTION_URL", "https://payid.example.com/collections")
    monkeypatch.setenv("NOVAPAY_PAYID_API_TOKEN", "token-123")
    monkeypatch.setenv("NOVAPAY_PAYID_MERCHANT_ID", "merchant-123")
    monkeypatch.setenv("NOVAPAY_PAYID_CALLBACK_URL", "https://api.example.com/webhooks/payments")

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "transaction_id": "payid-live-001",
                "status": "confirmed",
                "settlement_status": "submitted",
            },
        )

    intent = PaymentIntent(
        intent_id="intent-payid-live-001",
        actor_id="user-provider",
        organization_id="org-provider",
        amount=Decimal("12.00"),
        currency="aud",
        destination="invoice@payid.example",
    )

    provider = PayIDProvider(live=True, transport=httpx.MockTransport(handler))
    result = provider.authorize(intent)

    assert result.provider == "payid"
    assert result.provider_reference == "payid-live-001"
    assert result.status == "confirmed"
    assert result.settlement_status == "submitted"
    assert requests[0].url.path == "/collections"
    assert requests[0].headers["idempotency-key"] == (
        "novapay:org-provider:intent-payid-live-001"
    )


def test_in_memory_persistence_retrieves_by_trust_and_receipt_id() -> None:
    platform = NovaTechCorePlatform()
    store = InMemoryCorePlatformStore()
    identity = NovaIDService().bind_identity(
        identity_id="user-store",
        email="store@novatech.local",
        roles=("admin",),
        organization_id="org-store",
        scopes=("payments:write",),
    )
    request = AuthorityRequest(
        action="payment.execute",
        organization_id="org-store",
        required_roles=("admin",),
        required_scopes=("payments:write",),
        resource_owner_id="user-store",
    )
    intent = PaymentIntent(
        intent_id="intent-store",
        actor_id="user-store",
        organization_id="org-store",
        amount=Decimal("5.00"),
        currency="aud",
        destination="merchant-store",
    )

    result = platform.execute_payment_flow(
        identity=identity,
        request=request,
        payment_intent=intent,
    )
    store.save_flow(result)

    assert store.get_trust_packet(result.trust.trust_id)["trust"]["trust_id"] == result.trust.trust_id
    assert result.payment is not None
    assert store.get_trust_packet(result.payment.receipt_id)["payment"]["receipt_id"] == result.payment.receipt_id


def test_core_platform_orm_record_and_pdf_audit_export() -> None:
    platform = NovaTechCorePlatform()
    identity = NovaIDService().bind_identity(
        identity_id="user-audit",
        email="audit@novatech.local",
        roles=("admin",),
        organization_id="org-audit",
        scopes=("payments:write",),
    )
    request = AuthorityRequest(
        action="payment.execute",
        organization_id="org-audit",
        required_roles=("admin",),
        required_scopes=("payments:write",),
        resource_owner_id="user-audit",
    )
    intent = PaymentIntent(
        intent_id="intent-audit",
        actor_id="user-audit",
        organization_id="org-audit",
        amount=Decimal("8.00"),
        currency="aud",
        destination="merchant-audit",
    )
    result = platform.execute_payment_flow(
        identity=identity,
        request=request,
        payment_intent=intent,
    )

    record = CoreTrustPacketRecord.from_flow(result)
    params = record.insert_params()
    assert params[0] == result.trust.trust_id
    assert params[1] == result.payment.receipt_id
    assert params[2] == "org-audit"

    pdf = render_audit_pdf(record.packet, verification_url="/trust/explorer/test")
    assert pdf.startswith(b"%PDF-1.4")
    assert b"NovaTech Core Platform Audit Export" in pdf
    assert b"Signature scheme: ed25519" in pdf
    assert b"Embedded verification QR:" in pdf

    signature = sign_packet(record.packet)
    assert verify_packet_signature(record.packet, signature) is True
    tampered = dict(record.packet)
    tampered["tampered"] = True
    assert verify_packet_signature(tampered, signature) is False

    report = build_enterprise_audit_report(record.packet)
    assert report["classification"] == "ISO_SOC2_REGULATOR_READY_PACKET"
    assert report["tamper_evident"] is True
    assert len(report["controls"]) >= 4

    status = signing_key_status()
    assert status.rotation_enabled is True
    assert build_key_rotation_plan()["steps"]

    qr = render_qr_png("/trust/explorer/test")
    assert qr.startswith(b"\x89PNG\r\n\x1a\n")

    anchor = anchor_packet(record.packet)
    assert anchor.anchor_id.startswith("anchor_")
    assert anchor.status == "anchored"

    disabled_external_anchor = build_optional_blockchain_anchor(record.packet)
    assert disabled_external_anchor.status == "disabled"

    published_anchor = build_optional_blockchain_anchor(
        record.packet,
        publisher=lambda payload: {
            "status": "published",
            "provider": "ethereum-test",
            "anchor_id": f"chain-{payload['payload_hash'][:12]}",
            "transaction_id": "0xtest",
            "network": "sepolia",
        },
    )
    assert published_anchor.status == "published"
    assert published_anchor.transaction_id == "0xtest"

    bundle = build_auditor_zip(
        identifier=result.trust.trust_id,
        packet=record.packet,
        verification_url=f"/trust/explorer/{result.trust.trust_id}",
    )
    assert bundle.startswith(b"PK")


def test_core_platform_migration_system_lists_sql_migrations() -> None:
    migrations = list_migrations()
    assert migrations
    assert migrations[0].version == "001_core_trust_packets"
    plan = build_migration_plan()
    assert plan["style"] == "alembic_compatible_linear_sql"
    assert "001_core_trust_packets" in plan["pending"]


def test_core_platform_settlement_event_bus_trust_node_and_cbdc_status() -> None:
    settlement = build_settlement_status()
    event_bus = build_event_bus_status()
    trust_nodes = build_trust_node_network_status(configured_nodes=3, healthy_nodes=3)
    cbdc = cbdc_status()

    assert settlement["available"] is True
    assert settlement["cross_border_supported"] is True
    assert event_bus["event_bus"]["ready"] is True
    assert trust_nodes["distributed_validation_ready"] is True
    assert trust_nodes["consensus_layer"] == "future_non_authoritative"
    assert cbdc["available"] is True
