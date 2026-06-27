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
    NovaPayService,
    NovaPowerEngine,
    PayIDProvider,
    PaymentIntent,
    StripeProvider,
    SettlementLifecycleState,
)
from afritech.core_platform.audit_export import render_audit_pdf
from afritech.core_platform.compliance_report import build_enterprise_audit_report
from afritech.core_platform.anchoring import anchor_packet, build_optional_blockchain_anchor
from afritech.core_platform.cbdc import cbdc_status
from afritech.core_platform.consensus import (
    ValidatorConsensusEngine,
    ValidatorConsensusConflictError,
    build_validator_consensus_status,
)
from afritech.core_platform.distributed_verification import (
    build_trust_seal,
    build_validator_node_health,
    validate_distributed_consensus,
)
from afritech.core_platform import cryptographic_consensus as cryptographic_consensus_module
from afritech.core_platform.cryptographic_consensus import (
    build_cryptographic_consensus_status,
    run_cryptographic_consensus,
)
from afritech.core_platform.proof_receipts import (
    build_proof_receipt,
    verify_proof_receipt,
)
from afritech.core_platform import qr_proof as qr_proof_module
from afritech.core_platform.qr_proof import build_qr_artifact, decode_qr_payload
from afritech.core_platform.mobile_verifier import verify_scanned_receipt
from afritech.core_platform.smart_contract_verification import (
    build_onchain_verification_bundle,
    solidity_verifier_source,
)
from afritech.core_platform import threshold_bls as threshold_bls_module
from afritech.core_platform.event_bus import build_event_bus_status
from afritech.core_platform.export_bundle import build_auditor_zip
from afritech.core_platform.migration_system import build_migration_plan, list_migrations
from afritech.core_platform.orm import CoreTrustPacketRecord
from afritech.core_platform.qr import render_qr_png
from afritech.core_platform.settlement import (
    SettlementRouter,
    build_settlement_corridor_matrix,
    build_settlement_status,
)
from afritech.core_platform.signing import sign_packet, verify_packet_signature
from afritech.core_platform.signing import build_key_rotation_plan, signing_key_status
from afritech.core_platform.trust_node import build_trust_node_network_status
from afritech.core_platform.payments.contracts import PaymentProviderResult


@pytest.fixture(autouse=True)
def _reset_cryptographic_slashing_engine() -> None:
    from afritech.distributed.trust.reputation_store import ReputationStore

    cryptographic_consensus_module.SLASHING_ENGINE.store = ReputationStore()


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


def test_novapay_service_emits_settlement_lifecycle_and_provider_hooks(monkeypatch) -> None:
    transitions: list[str] = []
    provider_calls: list[tuple[str, str]] = []

    class RecordingHooks:
        def on_transition(self, event) -> None:
            transitions.append(event.state.value)

    class StubProvider:
        name = "payid"

        def before_authorize(self, *, intent, settlement) -> None:
            provider_calls.append(("before", intent.intent_id))

        def after_authorize(self, *, intent, settlement, result) -> None:
            provider_calls.append(("after", result.provider_reference))

        def authorize(self, intent):
            provider_calls.append(("authorize", intent.intent_id))
            return PaymentProviderResult(
                provider="payid",
                provider_reference=f"PAYID-{intent.intent_id}",
                status="completed",
                settlement_status="settlement_confirmed",
                raw={"mode": "stubbed"},
            )

    monkeypatch.setattr(
        "afritech.core_platform.services.provider_for",
        lambda *args, **kwargs: StubProvider(),
    )

    service = NovaPayService(lifecycle_hooks=RecordingHooks())
    identity = NovaIDService().bind_identity(
        identity_id="user-lifecycle",
        email="lifecycle@novatech.local",
        roles=("admin",),
        organization_id="org-lifecycle",
        scopes=("payments:write",),
    )
    decision = NovaPowerEngine().evaluate(
        AuthorityRequest(
            action="payment.execute",
            organization_id="org-lifecycle",
            required_roles=("admin",),
            required_scopes=("payments:write",),
            resource_owner_id="user-lifecycle",
            risk_score=Decimal("0.10"),
        ),
        identity,
    )
    intent = PaymentIntent(
        intent_id="intent-lifecycle-001",
        actor_id="user-lifecycle",
        organization_id="org-lifecycle",
        amount=Decimal("15.00"),
        currency="AUD",
        destination="merchant-lifecycle",
    )

    receipt = service.execute(
        intent,
        identity=identity,
        decision=decision,
        provider="payid",
        live_provider=False,
    )

    assert receipt.provider == "payid"
    assert transitions == [
        SettlementLifecycleState.VALIDATED.value,
        SettlementLifecycleState.COMPLIANCE_PASSED.value,
        SettlementLifecycleState.PROVIDER_LOCKED.value,
        SettlementLifecycleState.SETTLEMENT_SUBMITTED.value,
        SettlementLifecycleState.SETTLED.value,
        SettlementLifecycleState.RECEIPT_ISSUED.value,
        SettlementLifecycleState.COMPLETED.value,
    ]
    assert provider_calls == [
        ("before", "intent-lifecycle-001"),
        ("authorize", "intent-lifecycle-001"),
        ("after", "PAYID-intent-lifecycle-001"),
    ]


def test_novapay_service_emits_failed_settlement_transition(monkeypatch) -> None:
    transitions: list[str] = []

    class RecordingHooks:
        def on_transition(self, event) -> None:
            transitions.append(event.state.value)

    class FailingProvider:
        name = "payid"

        def before_authorize(self, *, intent, settlement) -> None:
            return None

        def authorize(self, intent):
            raise RuntimeError("provider_outage")

    monkeypatch.setattr(
        "afritech.core_platform.services.provider_for",
        lambda *args, **kwargs: FailingProvider(),
    )

    service = NovaPayService(lifecycle_hooks=RecordingHooks())
    identity = NovaIDService().bind_identity(
        identity_id="user-failure",
        email="failure@novatech.local",
        roles=("admin",),
        organization_id="org-failure",
        scopes=("payments:write",),
    )
    decision = NovaPowerEngine().evaluate(
        AuthorityRequest(
            action="payment.execute",
            organization_id="org-failure",
            required_roles=("admin",),
            required_scopes=("payments:write",),
            resource_owner_id="user-failure",
            risk_score=Decimal("0.10"),
        ),
        identity,
    )
    intent = PaymentIntent(
        intent_id="intent-failure-001",
        actor_id="user-failure",
        organization_id="org-failure",
        amount=Decimal("15.00"),
        currency="AUD",
        destination="merchant-failure",
    )

    with pytest.raises(RuntimeError, match="provider_outage"):
        service.execute(
            intent,
            identity=identity,
            decision=decision,
            provider="payid",
            live_provider=False,
        )

    assert transitions[-1] == SettlementLifecycleState.FAILED.value


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
    consensus = build_validator_consensus_status(configured_nodes=3, healthy_nodes=3)

    assert settlement["available"] is True
    assert settlement["cross_border_supported"] is True
    assert event_bus["event_bus"]["ready"] is True
    assert trust_nodes["distributed_validation_ready"] is True
    assert trust_nodes["consensus_layer"] == "future_non_authoritative"
    assert cbdc["available"] is True
    assert consensus["multi_node_consensus_ready"] is False
    assert consensus["consensus_layer"] == "future_non_authoritative"


def test_core_platform_settlement_rollout_config_is_observable(monkeypatch) -> None:
    monkeypatch.setenv("NOVAPAY_ROLLOUT_MODE", "canary")
    monkeypatch.setenv("NOVAPAY_PRIMARY_CORRIDOR", "AU->KE")
    monkeypatch.setenv("NOVAPAY_CORRIDORS", "AU->KE,AU->BI,AU->CD,USA->KE")
    monkeypatch.setenv("NOVAPAY_SETTLEMENT_MODE", "pre_funded")
    monkeypatch.setenv("NOVAPAY_MOBILE_MONEY_LIVE_ENABLED", "true")
    monkeypatch.setenv("NOVAPAY_COMPLIANCE_PROVIDER", "sumsub")
    monkeypatch.setenv("NOVAPAY_COMPLIANCE_LIVE_ENABLED", "false")

    settlement = build_settlement_status()

    assert settlement["rollout"]["mode"] == "canary"
    assert settlement["rollout"]["primary_corridor"] == "AU->KE"
    assert settlement["rollout"]["corridors"] == ["AU->KE", "AU->BI", "AU->CD", "USA->KE"]
    assert settlement["rollout"]["settlement_mode"] == "pre_funded"
    assert settlement["rollout"]["mobile_money_live_enabled"] is True
    assert settlement["rollout"]["compliance_provider"] == "sumsub"


def test_core_platform_settlement_corridor_matrix_reflects_rollout(monkeypatch) -> None:
    monkeypatch.setenv("NOVAPAY_ROLLOUT_MODE", "pilot")
    monkeypatch.setenv("NOVAPAY_PRIMARY_CORRIDOR", "AU->BI")
    monkeypatch.setenv("NOVAPAY_CORRIDORS", "AU->KE,AU->BI,AU->CD,USA->KE")
    monkeypatch.setenv("NOVAPAY_SETTLEMENT_MODE", "pre_funded")
    monkeypatch.setenv("NOVAPAY_MOBILE_MONEY_LIVE_ENABLED", "true")
    monkeypatch.setenv("NOVAPAY_COMPLIANCE_PROVIDER", "sumsub")
    monkeypatch.setenv("NOVAPAY_COMPLIANCE_LIVE_ENABLED", "true")

    matrix = build_settlement_corridor_matrix()

    assert [row["corridor"] for row in matrix] == [
        "AU->KE",
        "AU->BI",
        "AU->CD",
        "USA->KE",
    ]
    assert matrix[0]["provider"] == "mpesa_ke"
    assert matrix[1]["provider"] == "lumicash_bi"
    assert matrix[2]["provider"] == "orange_money_cd"
    assert matrix[3]["provider"] == "mpesa_ke"
    assert matrix[1]["primary"] is True
    assert matrix[0]["execution_state"] == "live_ready"
    assert matrix[3]["execution_state"] == "live_ready"
    assert matrix[0]["mobile_money_ready"] is True
    assert matrix[1]["mobile_money_ready"] is True
    assert matrix[2]["mobile_money_ready"] is True
    assert matrix[3]["settlement_country"] == "KE"
    assert matrix[3]["settlement_currency"] == "KES"


def test_validator_consensus_engine_requires_matching_validator_votes() -> None:
    engine = ValidatorConsensusEngine(
        trusted_public_keys={
            "validator-a": "R1//12616KShUeqYnTEa8B/ebDSIA2F8/6tDzal0vW8=",
            "validator-b": "R1//12616KShUeqYnTEa8B/ebDSIA2F8/6tDzal0vW8=",
            "validator-c": "R1//12616KShUeqYnTEa8B/ebDSIA2F8/6tDzal0vW8=",
        }
    )
    packet = {
        "trust": {
            "trust_id": "trust-consensus-001",
            "replay_status": "verified",
        },
        "payment": {"payment_id": "pay-consensus-001"},
        "event_hash": "abc123",
    }
    signature = sign_packet(packet).canonical()
    envelopes = [
        {"node_id": "validator-a", "packet": packet, "signature": signature},
        {"node_id": "validator-b", "packet": packet, "signature": signature},
        {"node_id": "validator-c", "packet": packet, "signature": signature},
    ]

    certificate = engine.decide(envelopes, total_nodes=3)

    assert certificate.consensus_reached is True
    assert certificate.accepted_votes == 3
    assert certificate.quorum == 2
    assert certificate.trust_id == "trust-consensus-001"


def test_validator_consensus_engine_rejects_conflicting_packets() -> None:
    engine = ValidatorConsensusEngine()
    packet_a = {
        "trust_id": "trust-consensus-002",
        "replay_status": "verified",
        "payload": "A",
    }
    packet_b = {
        "trust_id": "trust-consensus-002",
        "replay_status": "verified",
        "payload": "B",
    }
    signature_a = sign_packet(packet_a).canonical()
    signature_b = sign_packet(packet_b).canonical()

    with pytest.raises(ValidatorConsensusConflictError):
        engine.decide(
            [
                {"node_id": "validator-a", "packet": packet_a, "signature": signature_a},
                {"node_id": "validator-b", "packet": packet_b, "signature": signature_b},
                {"node_id": "validator-c", "packet": packet_a, "signature": signature_a},
            ],
            total_nodes=3,
        )


def test_distributed_verification_builds_health_and_seal() -> None:
    packet = {
        "trust_id": "trust-consensus-003",
        "replay_status": "verified",
        "payload": "distributed",
    }
    signature = sign_packet(packet).canonical()
    validators = [
        {"node_id": "validator-a", "packet": packet, "signature": signature},
        {"node_id": "validator-b", "packet": packet, "signature": signature},
        {"node_id": "validator-c", "packet": packet, "signature": signature},
    ]

    result = validate_distributed_consensus(
        packet=packet,
        validators=validators,
        total_nodes=3,
    )

    assert result["consensus"]["consensus_reached"] is True
    assert result["node_health"]["status"] == "healthy"
    assert result["trust_seal"]["trust_id"] == "trust-consensus-003"
    assert len(result["trust_seal"]["seal_hash"]) == 64

    degraded = build_validator_node_health(
        configured_nodes=3,
        healthy_nodes=2,
        quorum=2,
        disagreeing_nodes=["validator-z"],
        quarantined_nodes=["validator-z"],
    )
    assert degraded["status"] == "quarantined"
    assert degraded["consensus_ready"] is False

    seal = build_trust_seal(
        certificate=result["consensus"],
        node_health=result["node_health"],
    )
    assert seal["trust_id"] == "trust-consensus-003"
    assert seal["node_health_status"] == "healthy"


def test_cryptographic_consensus_builds_aggregate_seal_and_slashing() -> None:
    packet = {
        "trust_id": "trust-consensus-004",
        "replay_status": "verified",
        "payload": {"sequence": 4},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)

    assert result["consensus"]["consensus_reached"] is True
    assert result["consensus"]["aggregate_signature_scheme"] == "deterministic-aggregate"
    assert result["trust_seal"]["cryptographic_consensus"] is True
    assert result["node_health"]["consensus_ready"] is True
    assert len(result["trust_seal"]["seal_hash"]) == 64
    assert build_cryptographic_consensus_status(
        configured_nodes=3,
        healthy_nodes=3,
    )["cryptographic_consensus_ready"] is True


def test_cryptographic_consensus_rejects_packet_hash_mismatch_and_slashes_node() -> None:
    packet = {
        "trust_id": "trust-consensus-005",
        "replay_status": "verified",
        "payload": {"sequence": 5},
    }
    other_packet = {
        "trust_id": "trust-consensus-005",
        "replay_status": "verified",
        "payload": {"sequence": 999},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": other_packet,
            "signature": sign_packet(other_packet).canonical(),
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)

    assert result["consensus"]["consensus_reached"] is True
    assert any(vote["reason"] == "hash_mismatch" for vote in result["consensus"]["votes"])
    assert any(entry["status"] == "quarantined" for entry in result["slashing"])


def test_cryptographic_consensus_deduplicates_validator_votes_and_exposes_vote_set() -> None:
    packet = {
        "trust_id": "trust-consensus-006",
        "replay_status": "verified",
        "payload": {"sequence": 6},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)

    assert result["consensus"]["consensus_reached"] is True
    assert result["trust_seal"]["accepted_validators"] == ["validator-a", "validator-b"]
    assert result["trust_seal"]["rejected_validators"] == []
    assert result["trust_seal"]["total_votes_raw"] == 3
    assert result["trust_seal"]["total_votes_effective"] == 2
    assert len(result["trust_seal"]["violations_hash"]) == 64
    assert len(result["trust_seal"]["consensus_root"]) == 64
    assert len(result["trust_seal"]["validator_root"]) == 64
    assert result["trust_seal"]["seal_hash"] == cryptographic_consensus_module._hash(
        cryptographic_consensus_module._canonicalize_seal(result["trust_seal"]),
        domain="seal",
    )
    assert result["consensus"]["node_ids"] == ["validator-a", "validator-b"]


def test_cryptographic_consensus_preserves_double_sign_evidence_before_deduplication() -> None:
    packet = {
        "trust_id": "trust-consensus-007",
        "replay_status": "verified",
        "payload": {"sequence": 7},
    }
    alternate_packet = {
        "trust_id": "trust-consensus-007",
        "replay_status": "verified",
        "payload": {"sequence": 700},
    }
    signature = sign_packet(packet).canonical()
    alternate_signature = sign_packet(alternate_packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-a",
            "packet": alternate_packet,
            "signature": alternate_signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)

    assert result["consensus"]["consensus_reached"] is True
    assert any(violation["type"] == "double_sign" for violation in result["violations"])
    assert result["trust_seal"]["total_votes_raw"] == 3
    assert result["trust_seal"]["total_votes_effective"] == 2
    assert len(result["trust_seal"]["violations_hash"]) == 64
    assert any(
        entry["node_id"] == "validator-a" and entry["status"] == "quarantined"
        for entry in result["slashing"]
    )


def test_cryptographic_consensus_seal_hash_is_order_invariant_for_validator_lists() -> None:
    packet = {
        "trust_id": "trust-consensus-008",
        "replay_status": "verified",
        "payload": {"sequence": 8},
    }
    signature = sign_packet(packet).canonical()
    votes_forward = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]
    votes_reverse = list(reversed(votes_forward))

    forward = run_cryptographic_consensus(packet, votes_forward, total_nodes=3)
    reverse = run_cryptographic_consensus(packet, votes_reverse, total_nodes=3)

    assert forward["trust_seal"]["seal_hash"] == reverse["trust_seal"]["seal_hash"]


def test_cryptographic_consensus_canonicalization_preserves_list_order() -> None:
    seal_one = {
        "seal_hash": "ignored",
        "seal_id": "ignored",
        "ordered": [{"id": "a"}, {"id": "b"}],
    }
    seal_two = {
        "seal_hash": "ignored",
        "seal_id": "ignored",
        "ordered": [{"id": "b"}, {"id": "a"}],
    }

    canonical_one = cryptographic_consensus_module._canonicalize_seal(seal_one)
    canonical_two = cryptographic_consensus_module._canonicalize_seal(seal_two)

    assert canonical_one["ordered"] == [{"id": "a"}, {"id": "b"}]
    assert canonical_two["ordered"] == [{"id": "b"}, {"id": "a"}]
    assert canonical_one != canonical_two


def test_proof_receipt_builds_and_verifies_from_trust_seal() -> None:
    packet = {
        "trust_id": "trust-consensus-009",
        "replay_status": "verified",
        "payload": {"sequence": 9},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    receipt = build_proof_receipt(result["trust_seal"], issuer="test-issuer")
    verification = verify_proof_receipt(receipt)

    assert receipt["receipt_id"].startswith("receipt-")
    assert len(receipt["receipt_hash"]) == 64
    assert receipt["signer_set"] == result["trust_seal"]["signer_set"]
    assert verification["valid"] is True
    assert verification["reason"] == "receipt_verified"


def test_bls_verify_aggregate_uses_fast_aggregate_verify(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    class _FakeBls:
        @staticmethod
        def FastAggregateVerify(public_keys, message, signature):
            calls.append(("fast", (list(public_keys), message, signature)))
            return True

        @staticmethod
        def AggregateVerify(*_args, **_kwargs):
            calls.append(("aggregate", None))
            return False

    monkeypatch.setattr(threshold_bls_module, "_bls", _FakeBls())

    assert (
        threshold_bls_module.bls_verify_aggregate(
            [b"pk-1", b"pk-2"],
            "consensus-root",
            b"signature",
        )
        is True
    )
    assert calls and calls[0][0] == "fast"
    assert all(call[0] != "aggregate" for call in calls)


def test_proof_receipt_rejects_empty_signer_set_for_bls_scheme() -> None:
    receipt = build_proof_receipt(
        {
            "seal_id": "seal-001",
            "seal_hash": "a" * 64,
            "trust_id": "trust-empty-signer-set",
            "packet_hash": "b" * 64,
            "consensus_root": "c" * 64,
            "validator_root": "d" * 64,
            "aggregate_signature": "e" * 128,
            "aggregate_signature_scheme": "bls-threshold",
            "signature_threshold": 1,
            "accepted_validators": ["validator-a"],
            "rejected_validators": [],
            "violations_hash": "f" * 64,
            "cryptographic_consensus": True,
            "total_votes_raw": 1,
            "total_votes_effective": 1,
            "node_health_hash": "1" * 64,
            "node_health_status": "healthy",
            "signer_set": [],
            "signer_pop_proofs": [],
        },
        issuer="test",
        issued_at="2026-06-26T00:00:00+00:00",
    )

    verification = verify_proof_receipt(receipt)

    assert verification["valid"] is False
    assert verification["reason"] == "empty_signer_set"


def test_qr_mobile_and_onchain_proof_exports_round_trip() -> None:
    packet = {
        "trust_id": "trust-consensus-010",
        "replay_status": "verified",
        "payload": {"sequence": 10},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    receipt = build_proof_receipt(result["trust_seal"], issuer="test-issuer")

    qr_artifact = build_qr_artifact(receipt)
    decoded = decode_qr_payload(qr_artifact["qr_payload"])
    mobile = verify_scanned_receipt(qr_artifact["qr_payload"])
    onchain = build_onchain_verification_bundle(receipt)
    verifier_source = solidity_verifier_source()

    assert decoded["receipt_hash"] == receipt["receipt_hash"]
    assert mobile["status"] is True
    assert mobile["trust_level"] == "PARTIAL"
    assert mobile["verification"]["valid"] is True
    assert onchain["receipt_hash"] == receipt["receipt_hash"]
    assert onchain["signer_set_hash"]
    assert onchain["bundle_hash"]
    assert "contract NovaTrustVerifier" in verifier_source


def test_qr_payload_rejects_tampering_and_size_abuse(monkeypatch) -> None:
    packet = {
        "trust_id": "trust-consensus-011",
        "replay_status": "verified",
        "payload": {"sequence": 11},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    receipt = build_proof_receipt(result["trust_seal"], issuer="test-issuer")
    artifact = build_qr_artifact(receipt)

    decoded = decode_qr_payload(artifact["qr_payload"])
    assert decoded["receipt_hash"] == receipt["receipt_hash"]

    import base64
    import json
    import zlib

    compressed = base64.urlsafe_b64decode(artifact["qr_payload"].encode("utf-8"))
    wrapper = json.loads(zlib.decompress(compressed).decode("utf-8"))
    wrapper["receipt"]["issuer"] = "tampered-issuer"
    tampered_payload = base64.urlsafe_b64encode(
        zlib.compress(json.dumps(wrapper, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"), level=9)
    ).decode("utf-8")

    with pytest.raises(ValueError, match="qr_integrity_failure"):
        decode_qr_payload(tampered_payload)

    invalid_timestamp_wrapper = json.loads(zlib.decompress(compressed).decode("utf-8"))
    invalid_timestamp_wrapper["receipt"]["issued_at"] = "not-a-real-date"
    invalid_timestamp_wrapper["qr_hash"] = qr_proof_module._qr_hash(invalid_timestamp_wrapper)
    invalid_timestamp_payload = base64.urlsafe_b64encode(
        zlib.compress(json.dumps(invalid_timestamp_wrapper, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"), level=9)
    ).decode("utf-8")
    with pytest.raises(ValueError, match="qr_invalid_timestamp"):
        decode_qr_payload(invalid_timestamp_payload)

    wrapper_missing_ts = json.loads(zlib.decompress(compressed).decode("utf-8"))
    del wrapper_missing_ts["receipt"]["issued_at"]
    wrapper_missing_ts["qr_hash"] = qr_proof_module._qr_hash(wrapper_missing_ts)
    missing_timestamp_payload = base64.urlsafe_b64encode(
        zlib.compress(json.dumps(wrapper_missing_ts, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"), level=9)
    ).decode("utf-8")
    with pytest.raises(ValueError, match="qr_missing_issued_at"):
        decode_qr_payload(missing_timestamp_payload)

    tampered_missing_timestamp = json.loads(zlib.decompress(compressed).decode("utf-8"))
    del tampered_missing_timestamp["receipt"]["issued_at"]
    with pytest.raises(ValueError, match="qr_integrity_failure"):
        decode_qr_payload(
            base64.urlsafe_b64encode(
                zlib.compress(
                    json.dumps(
                        tampered_missing_timestamp,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ).encode("utf-8"),
                    level=9,
                    )
                ).decode("utf-8")
        )

    extended_wrapper = json.loads(zlib.decompress(compressed).decode("utf-8"))
    extended_wrapper["network_id"] = "mainnet"
    extended_wrapper["qr_hash"] = qr_proof_module._qr_hash(
        {k: v for k, v in extended_wrapper.items() if k != "qr_hash"}
    )
    extended_payload = base64.urlsafe_b64encode(
        zlib.compress(
            json.dumps(
                extended_wrapper,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8"),
            level=9,
        )
    ).decode("utf-8")
    extended_decoded = decode_qr_payload(extended_payload)
    assert extended_decoded["receipt_hash"] == receipt["receipt_hash"]

    invalid_hash_wrapper = json.loads(zlib.decompress(compressed).decode("utf-8"))
    invalid_hash_wrapper["qr_hash"] = None
    invalid_hash_payload = base64.urlsafe_b64encode(
        zlib.compress(
            json.dumps(
                invalid_hash_wrapper,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8"),
            level=9,
        )
    ).decode("utf-8")
    with pytest.raises(ValueError, match="qr_invalid_hash"):
        decode_qr_payload(invalid_hash_payload)

    with pytest.raises(ValueError, match="qr_invalid_base64"):
        decode_qr_payload("%%%%%%%INVALID%%%%%%%")

    invalid_compression_payload = base64.b64encode(b"not-zlib-data").decode("ascii")
    with pytest.raises(ValueError, match="qr_invalid_compression"):
        decode_qr_payload(invalid_compression_payload)

    invalid_utf8_payload = base64.urlsafe_b64encode(
        zlib.compress(b"\xff\xfe\xfd", level=9)
    ).decode("utf-8")
    with pytest.raises(ValueError, match="qr_invalid_encoding"):
        decode_qr_payload(invalid_utf8_payload)

    invalid_json_payload = base64.urlsafe_b64encode(
        zlib.compress(b"not-json", level=9)
    ).decode("utf-8")
    with pytest.raises(ValueError, match="qr_invalid_json"):
        decode_qr_payload(invalid_json_payload)

    truncated_compressed = base64.b64decode(
        artifact["qr_payload"].encode("utf-8"),
        altchars=b"-_",
        validate=True,
    )[:-5]
    truncated_payload = base64.urlsafe_b64encode(truncated_compressed).decode("utf-8")
    with pytest.raises(ValueError, match="qr_truncated_compression"):
        decode_qr_payload(truncated_payload)

    exact_limit_payload = artifact["qr_payload"]
    exact_limit_raw = zlib.decompress(
        base64.b64decode(exact_limit_payload.encode("utf-8"), altchars=b"-_", validate=True)
    )
    original_max_qr_decompressed_bytes = qr_proof_module.MAX_QR_DECOMPRESSED_BYTES
    monkeypatch.setattr(
        qr_proof_module,
        "MAX_QR_DECOMPRESSED_BYTES",
        len(exact_limit_raw),
    )
    decoded_exact_limit = decode_qr_payload(exact_limit_payload)
    assert decoded_exact_limit["receipt_hash"] == receipt["receipt_hash"]

    monkeypatch.setattr(
        qr_proof_module,
        "MAX_QR_DECOMPRESSED_BYTES",
        max(1, len(exact_limit_raw) - 1),
    )
    with pytest.raises(ValueError, match="qr_decompressed_too_large"):
        decode_qr_payload(exact_limit_payload)

    monkeypatch.setattr(
        qr_proof_module,
        "MAX_QR_DECOMPRESSED_BYTES",
        original_max_qr_decompressed_bytes,
    )

    original_max_qr_payload_bytes = qr_proof_module.MAX_QR_PAYLOAD_BYTES
    monkeypatch.setattr(qr_proof_module, "MAX_QR_PAYLOAD_BYTES", 1)
    with pytest.raises(ValueError, match="qr_payload_too_large"):
        decode_qr_payload(artifact["qr_payload"])

    monkeypatch.setattr(
        qr_proof_module,
        "MAX_QR_PAYLOAD_BYTES",
        original_max_qr_payload_bytes,
    )
    monkeypatch.setattr(qr_proof_module, "MAX_QR_AGE_SECONDS", -1)
    with pytest.raises(ValueError, match="qr_expired"):
        decode_qr_payload(artifact["qr_payload"])


def test_mobile_verifier_hides_receipt_on_failed_verification(monkeypatch) -> None:
    receipt = {
        "type": "novatrust-qr-proof",
        "version": "1.0",
        "receipt": {
            "receipt_hash": "x" * 64,
        },
        "qr_hash": "y" * 64,
    }

    monkeypatch.setattr(
        "afritech.core_platform.mobile_verifier.decode_qr_payload",
        lambda _data: receipt["receipt"],
    )
    monkeypatch.setattr(
        "afritech.core_platform.mobile_verifier.verify_proof_receipt",
        lambda *_args, **_kwargs: {"valid": False, "reason": "bad_signature"},
    )

    result = verify_scanned_receipt("payload")

    assert result["status"] is False
    assert result["receipt"] is None


def test_mobile_verifier_returns_safe_error_for_invalid_qr_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "afritech.core_platform.mobile_verifier.decode_qr_payload",
        lambda _data: (_ for _ in ()).throw(ValueError("qr_invalid_timestamp")),
    )

    result = verify_scanned_receipt("payload")

    assert result["status"] is False
    assert result["reason"] == "qr_invalid_timestamp"
    assert result["trust_level"] == "UNTRUSTED"
    assert result["receipt"] is None
    assert result["verification"]["valid"] is False


def test_bls_receipt_verification_rejects_mismatched_group_public_keys(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "afritech.core_platform.proof_receipts.BLS_AVAILABLE",
        True,
    )
    monkeypatch.setattr(
        "afritech.core_platform.proof_receipts.bls_pop_verify",
        lambda _public_key, _proof: True,
    )
    monkeypatch.setattr(
        "afritech.core_platform.proof_receipts.bls_verify_aggregate",
        lambda _public_keys, _message, _signature: True,
    )

    receipt = build_proof_receipt(
        {
            "seal_id": "seal-bls-001",
            "seal_hash": "a" * 64,
            "trust_id": "trust-bls-001",
            "packet_hash": "b" * 64,
            "consensus_root": "c" * 64,
            "validator_root": "d" * 64,
            "aggregate_signature": "e" * 128,
            "aggregate_signature_scheme": "bls-threshold",
            "signature_threshold": 1,
            "accepted_validators": ["validator-a"],
            "rejected_validators": [],
            "violations_hash": "f" * 64,
            "cryptographic_consensus": True,
            "total_votes_raw": 1,
            "total_votes_effective": 1,
            "node_health_hash": "1" * 64,
            "node_health_status": "healthy",
            "signer_set": ["00" * 48],
            "signer_pop_proofs": ["11" * 48],
        },
        issuer="test",
        issued_at="2026-06-26T00:00:00+00:00",
    )

    verification = verify_proof_receipt(
        receipt,
        group_public_keys=[bytes.fromhex("22" * 48)],
    )

    assert verification["valid"] is False
    assert verification["reason"] == "signer_set_mismatch"
