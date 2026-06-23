"""Core NovaTech platform API surfaces.

The router is FastAPI-native, while the payload builder stays framework-neutral
so Django or other gateways can expose the same contract later.
"""

from __future__ import annotations

from decimal import Decimal
from html import escape
import os
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.core_platform import (
    AuthorityRequest,
    NovaIDService,
    NovaTechCorePlatform,
    PaymentIntent,
    build_core_platform_overview,
)
from afritech.core_platform.audit_export import render_audit_pdf
from afritech.core_platform.auditor_dashboard import build_auditor_dashboard
from afritech.core_platform.anchoring import anchor_packet, build_optional_blockchain_anchor
from afritech.core_platform.compliance_report import build_enterprise_audit_report
from afritech.core_platform.export_bundle import build_auditor_zip
from afritech.core_platform.migration_system import build_migration_plan
from afritech.core_platform.persistence import InMemoryCorePlatformStore
from afritech.core_platform.qr import render_qr_png
from afritech.core_platform.signing import (
    build_key_rotation_plan,
    sign_packet,
    signing_key_status,
    verify_packet_signature,
)


CORE_PLATFORM_STORE = InMemoryCorePlatformStore()


def core_platform_console_payload() -> dict[str, object]:
    return build_core_platform_overview()


class AuthorityEvaluationPayload(BaseModel):
    action: str = "payment.execute"
    organization_id: str
    required_roles: list[str] = Field(default_factory=list)
    required_scopes: list[str] = Field(default_factory=list)
    resource_owner_id: str | None = None
    risk_score: Decimal = Decimal("0")
    risk_score_max: Decimal = Decimal("0.70")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaymentExecutionPayload(BaseModel):
    intent_id: str
    amount: Decimal
    currency: str = "AUD"
    destination: str
    action: str = "payment.execute"
    required_roles: list[str] = Field(default_factory=lambda: ["OPERATOR"])
    required_scopes: list[str] = Field(default_factory=lambda: ["payments:write"])
    risk_score: Decimal = Decimal("0")
    risk_score_max: Decimal = Decimal("0.70")
    provider: str = "payid"
    live_provider: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrustReplayPayload(BaseModel):
    packet: dict[str, Any]


class ExplainPayload(BaseModel):
    subject: str
    decision: str = "ALLOW"
    reason: str = "All core constraints passed"
    trace_id: str = "manual-trace"
    trust_id: str = "manual-trust"


class ProposalPayload(BaseModel):
    title: str
    risk_level: str = "LOW"
    evidence_refs: list[str] = Field(default_factory=list)


class PilotFlowPayload(BaseModel):
    intent_id: str = "pilot-core-payment-001"
    amount: Decimal = Decimal("25.00")
    currency: str = "AUD"
    destination: str = "pilot-merchant"
    provider: str = "payid"
    live_provider: bool = False


class AuditorDashboardPayload(BaseModel):
    identifiers: list[str] = Field(default_factory=list)


def _identity_from_claims(claims: JWTClaims) -> Any:
    return NovaIDService().bind_identity(
        identity_id=claims.sub,
        email=f"{claims.sub}@novatech.local",
        roles=(claims.role,),
        organization_id=claims.organization_id,
        scopes=(
            "identity:read",
            "authority:evaluate",
            "payments:write",
            "trust:read",
            "ai:explain",
            "programming:propose",
        ),
        devices=("authenticated-session",),
        kyc_status="verified",
    )


def _trust_explorer_payload(identifier: str, packet: dict[str, Any]) -> dict[str, object]:
    return {
        "view": "public_trust_explorer",
        "layer": "NovaTrust",
        "identifier": identifier,
        "packet": packet,
        "timeline": _explorer_timeline(packet),
        "replay_result": "verified" if packet.get("trust") else "demo_packet",
        "public": True,
        "execution_authority": False,
    }


def build_core_platform_router() -> APIRouter:
    router = APIRouter(prefix="/v1/core-platform", tags=["core-platform"])

    @router.get("/console")
    def console_overview(
        _: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        return core_platform_console_payload()

    @router.get("/identity/me")
    def identity_me(
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        identity = _identity_from_claims(claims)
        return {
            "view": "core_platform_identity",
            "layer": "NovaID / AfriID",
            "identity": identity.canonical(),
            "secures_downstream_layers": True,
        }

    @router.post("/authority/evaluate")
    def authority_evaluate(
        payload: AuthorityEvaluationPayload,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, object]:
        identity = _identity_from_claims(claims)
        request = AuthorityRequest(
            action=payload.action,
            organization_id=payload.organization_id,
            required_roles=tuple(payload.required_roles),
            required_scopes=tuple(payload.required_scopes),
            resource_owner_id=payload.resource_owner_id,
            risk_score=payload.risk_score,
            risk_score_max=payload.risk_score_max,
            metadata=payload.metadata,
        )
        decision = NovaTechCorePlatform().authority.evaluate(request, identity)
        return {
            "view": "core_platform_authority_decision",
            "layer": "NovaPower",
            "decision": decision.canonical(),
            "request": request.canonical(),
        }

    @router.post("/payments/execute")
    def payment_execute(
        payload: PaymentExecutionPayload,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, object]:
        platform = NovaTechCorePlatform()
        identity = _identity_from_claims(claims)
        request = AuthorityRequest(
            action=payload.action,
            organization_id=identity.organization_id,
            required_roles=tuple(payload.required_roles),
            required_scopes=tuple(payload.required_scopes),
            resource_owner_id=identity.identity_id,
            risk_score=payload.risk_score,
            risk_score_max=payload.risk_score_max,
            metadata=payload.metadata,
        )
        intent = PaymentIntent(
            intent_id=payload.intent_id,
            actor_id=identity.identity_id,
            organization_id=identity.organization_id,
            amount=payload.amount,
            currency=payload.currency,
            destination=payload.destination,
            metadata=payload.metadata,
        )
        result = platform.execute_payment_flow(
            identity=identity,
            request=request,
            payment_intent=intent,
            provider=payload.provider,
            live_provider=payload.live_provider,
        )
        CORE_PLATFORM_STORE.save_flow(result)
        return {
            "view": "core_platform_payment_flow",
            "layer": "NovaPay / AfriPay",
            "result": result.canonical(),
            "trust_explorer": f"/trust/explorer/{result.trust.trust_id}",
        }

    @router.post("/trust/replay")
    def trust_replay(
        payload: TrustReplayPayload,
        _: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        platform = NovaTechCorePlatform()
        receipt = platform.trust.record(
            subject_id=str(payload.packet.get("subject_id", "manual-subject")),
            organization_id=str(payload.packet.get("organization_id", "manual-org")),
            event_type=str(payload.packet.get("event_type", "manual.event")),
            packet=payload.packet,
        )
        CORE_PLATFORM_STORE.save_trust_receipt(receipt)
        return {
            "view": "core_platform_trust_replay",
            "layer": "NovaTrust",
            "receipt": receipt.canonical(),
            "replay_valid": platform.trust.replay(receipt),
            "trust_explorer": f"/trust/explorer/{receipt.trust_id}",
        }

    @router.get("/trust/explorer/{identifier}")
    def trust_explorer_packet(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return _trust_explorer_payload(identifier, packet)

    @router.get("/trust/explorer/{identifier}/audit.pdf")
    def trust_explorer_audit_pdf(identifier: str) -> Response:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        verification_url = f"/trust/explorer/{identifier}"
        return Response(
            content=render_audit_pdf(packet, verification_url=verification_url),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="novatrust-{identifier}.pdf"',
            },
        )

    @router.get("/trust/explorer/{identifier}/signature")
    def trust_explorer_signature(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        signature = sign_packet(packet)
        return {
            "view": "novatrust_signature",
            "identifier": identifier,
            "signature": signature.canonical(),
            "verified": verify_packet_signature(packet, signature),
        }

    @router.get("/trust/explorer/{identifier}/anchor")
    def trust_explorer_anchor(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return {
            "view": "novatrust_chain_anchor",
            "identifier": identifier,
            "anchor": anchor_packet(packet).canonical(),
        }

    @router.get("/trust/explorer/{identifier}/anchor/blockchain")
    def trust_explorer_blockchain_anchor(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return {
            "view": "novatrust_optional_blockchain_anchor",
            "identifier": identifier,
            "anchor": build_optional_blockchain_anchor(packet).canonical(),
        }

    @router.get("/trust/explorer/{identifier}/qr.png")
    def trust_explorer_qr(identifier: str) -> Response:
        verification_url = f"/trust/explorer/{identifier}"
        return Response(content=render_qr_png(verification_url), media_type="image/png")

    @router.get("/trust/explorer/{identifier}/bundle.zip")
    def trust_explorer_bundle(identifier: str) -> Response:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        verification_url = f"/trust/explorer/{identifier}"
        return Response(
            content=build_auditor_zip(
                identifier=identifier,
                packet=packet,
                verification_url=verification_url,
            ),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="novatrust-{identifier}.zip"',
            },
        )

    @router.get("/trust/explorer/{identifier}/compliance-report")
    def trust_explorer_compliance_report(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return build_enterprise_audit_report(packet)

    @router.post("/auditor/dashboard")
    def auditor_dashboard(
        payload: AuditorDashboardPayload,
        _: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        identifiers = payload.identifiers or ["demo-receipt"]
        packets = [
            (identifier, CORE_PLATFORM_STORE.get_trust_packet(identifier) or _demo_explorer_packet(identifier))
            for identifier in identifiers
        ]
        return build_auditor_dashboard(packets)

    @router.get("/signing/status")
    def signing_status(
        _: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        return {
            "view": "novatrust_signing_status",
            "status": signing_key_status().canonical(),
            "rotation_plan": build_key_rotation_plan(),
        }

    @router.get("/persistence/status")
    def persistence_status(
        _: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        return {
            "view": "core_platform_persistence_status",
            "default_store": "in_memory",
            "postgres_adapter": "available",
            "postgres_table": "novatech_core_trust_packets",
            "durable_target": "PostgreSQL JSONB proof packet store",
            "migration_system": build_migration_plan(),
        }

    @router.get("/payments/providers/status")
    def payment_provider_status(
        _: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, object]:
        stripe_live = os.environ.get("STRIPE_LIVE_MODE", "").lower() in {"1", "true", "yes"}
        stripe_key_configured = bool(os.environ.get("STRIPE_API_KEY"))
        return {
            "view": "core_platform_payment_provider_status",
            "providers": {
                "payid": {
                    "available": True,
                    "mode": "deterministic_pilot",
                },
                "stripe": {
                    "available": True,
                    "live_mode_enabled": stripe_live,
                    "api_key_configured": stripe_key_configured,
                    "ready_for_real_charge": stripe_live and stripe_key_configured,
                },
            },
        }

    @router.post("/ai/explain")
    def ai_explain(
        payload: ExplainPayload,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, object]:
        platform = NovaTechCorePlatform()
        identity = _identity_from_claims(claims)
        decision = platform.authority.evaluate(
            AuthorityRequest(
                action="ai.explain",
                organization_id=identity.organization_id,
                required_roles=(claims.role,),
                required_scopes=("ai:explain",),
                resource_owner_id=identity.identity_id,
            ),
            identity,
        )
        trust = platform.trust.record(
            subject_id=identity.identity_id,
            organization_id=identity.organization_id,
            event_type="core.ai.explain",
            packet={
                "subject": payload.subject,
                "input_decision": payload.decision,
                "input_reason": payload.reason,
                "input_trace_id": payload.trace_id,
                "input_trust_id": payload.trust_id,
            },
        )
        explanation = platform.intelligence.explain(
            subject=payload.subject,
            decision=decision,
            trust=trust,
        )
        return {
            "view": "core_platform_ai_explanation",
            "layer": "NovaScript",
            "explanation": explanation.canonical(),
        }

    @router.post("/pilot/flow")
    def pilot_flow(
        payload: PilotFlowPayload,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, object]:
        platform = NovaTechCorePlatform()
        identity = _identity_from_claims(claims)
        request = AuthorityRequest(
            action="payment.execute",
            organization_id=identity.organization_id,
            required_roles=(claims.role,),
            required_scopes=("payments:write",),
            resource_owner_id=identity.identity_id,
            risk_score=Decimal("0.12"),
        )
        intent = PaymentIntent(
            intent_id=payload.intent_id,
            actor_id=identity.identity_id,
            organization_id=identity.organization_id,
            amount=payload.amount,
            currency=payload.currency,
            destination=payload.destination,
            metadata={"pilot": "core_platform_live_flow"},
        )
        result = platform.execute_payment_flow(
            identity=identity,
            request=request,
            payment_intent=intent,
            provider=payload.provider,
            live_provider=payload.live_provider,
        )
        CORE_PLATFORM_STORE.save_flow(result)
        return {
            "view": "core_platform_real_pilot_flow",
            "status": "deployed",
            "flow": [
                "NovaID",
                "NovaPower",
                "NovaPay",
                "NovaTrust",
                "NovaScript",
                "NovaProgramming",
            ],
            "result": result.canonical(),
            "trust_explorer": f"/trust/explorer/{result.trust.trust_id}",
        }

    @router.post("/programming/proposals")
    def programming_proposal(
        payload: ProposalPayload,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, object]:
        platform = NovaTechCorePlatform()
        explanation = platform.intelligence.explain(
            subject=payload.title,
            decision=platform.authority.evaluate(
                AuthorityRequest(
                    action="programming.propose",
                    organization_id=claims.organization_id,
                    required_roles=(claims.role,),
                    required_scopes=("programming:propose",),
                    resource_owner_id=claims.sub,
                    risk_score=Decimal("0") if payload.risk_level.upper() == "LOW" else Decimal("0.80"),
                ),
                _identity_from_claims(claims),
            ),
            trust=platform.trust.record(
                subject_id=claims.sub,
                organization_id=claims.organization_id,
                event_type="core.programming.proposal",
                packet={"title": payload.title, "evidence_refs": payload.evidence_refs},
            ),
        )
        proposal = platform.programming.create_proposal(
            title=payload.title,
            explanation=explanation,
            evidence_refs=tuple(payload.evidence_refs),
        )
        return {
            "view": "core_platform_programming_proposal",
            "layer": "NovaProgramming",
            "proposal": proposal.canonical(),
        }

    return router


def build_public_trust_explorer_router() -> APIRouter:
    router = APIRouter(tags=["core-platform-public-trust"])

    @router.get("/trust/sandbox/demo")
    def public_trust_sandbox_demo() -> dict[str, object]:
        identifier = "sandbox-demo"
        packet = _demo_explorer_packet(identifier)
        return {
            "view": "novatrust_public_sandbox",
            "identifier": identifier,
            "description": "Read-only public sandbox trust explorer demo.",
            "links": {
                "explorer": f"/trust/explorer/{identifier}",
                "packet_json": f"/trust/explorer/{identifier}",
                "audit_pdf": f"/trust/explorer/{identifier}/audit.pdf",
                "signature": f"/trust/explorer/{identifier}/signature",
                "compliance_report": f"/trust/explorer/{identifier}/compliance-report",
                "anchor": f"/trust/explorer/{identifier}/anchor",
                "optional_blockchain_anchor": f"/trust/explorer/{identifier}/anchor/blockchain",
                "qr_png": f"/trust/explorer/{identifier}/qr.png",
                "bundle_zip": f"/trust/explorer/{identifier}/bundle.zip",
            },
            "payload": _trust_explorer_payload(identifier, packet),
        }

    @router.get("/trust/explorer/{identifier}")
    def public_trust_explorer(identifier: str, request: Request) -> Response:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            return JSONResponse(_trust_explorer_payload(identifier, packet))
        return Response(
            content=_render_trust_explorer_html(identifier=identifier, packet=packet),
            media_type="text/html",
        )

    @router.get("/trust/explorer/{identifier}/audit.pdf")
    def public_trust_explorer_pdf(identifier: str) -> Response:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        verification_url = f"/trust/explorer/{identifier}"
        return Response(
            content=render_audit_pdf(packet, verification_url=verification_url),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="novatrust-{identifier}.pdf"',
            },
        )

    @router.get("/trust/explorer/{identifier}/signature")
    def public_trust_explorer_signature(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        signature = sign_packet(packet)
        return {
            "view": "novatrust_signature",
            "identifier": identifier,
            "signature": signature.canonical(),
            "verified": verify_packet_signature(packet, signature),
        }

    @router.get("/trust/explorer/{identifier}/anchor")
    def public_trust_explorer_anchor(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return {
            "view": "novatrust_chain_anchor",
            "identifier": identifier,
            "anchor": anchor_packet(packet).canonical(),
        }

    @router.get("/trust/explorer/{identifier}/anchor/blockchain")
    def public_trust_explorer_blockchain_anchor(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return {
            "view": "novatrust_optional_blockchain_anchor",
            "identifier": identifier,
            "anchor": build_optional_blockchain_anchor(packet).canonical(),
        }

    @router.get("/trust/explorer/{identifier}/qr.png")
    def public_trust_explorer_qr(identifier: str) -> Response:
        verification_url = f"/trust/explorer/{identifier}"
        return Response(content=render_qr_png(verification_url), media_type="image/png")

    @router.get("/trust/explorer/{identifier}/bundle.zip")
    def public_trust_explorer_bundle(identifier: str) -> Response:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        verification_url = f"/trust/explorer/{identifier}"
        return Response(
            content=build_auditor_zip(
                identifier=identifier,
                packet=packet,
                verification_url=verification_url,
            ),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="novatrust-{identifier}.zip"',
            },
        )

    @router.get("/trust/explorer/{identifier}/compliance-report")
    def public_trust_explorer_compliance_report(identifier: str) -> dict[str, object]:
        packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)
        if packet is None:
            packet = _demo_explorer_packet(identifier)
        return build_enterprise_audit_report(packet)

    @router.get("/trust/auditor/dashboard")
    def public_auditor_dashboard(ids: str = "demo-receipt") -> dict[str, object]:
        identifiers = [item.strip() for item in ids.split(",") if item.strip()]
        packets = [
            (identifier, CORE_PLATFORM_STORE.get_trust_packet(identifier) or _demo_explorer_packet(identifier))
            for identifier in identifiers
        ]
        return build_auditor_dashboard(packets)

    return router


def _explorer_timeline(packet: dict[str, object]) -> list[dict[str, object]]:
    identity = packet.get("identity") if isinstance(packet.get("identity"), dict) else {}
    decision = packet.get("decision") if isinstance(packet.get("decision"), dict) else {}
    payment = packet.get("payment") if isinstance(packet.get("payment"), dict) else {}
    trust = packet.get("trust") if isinstance(packet.get("trust"), dict) else {}
    explanation = packet.get("explanation") if isinstance(packet.get("explanation"), dict) else {}
    proposal = packet.get("proposal") if isinstance(packet.get("proposal"), dict) else {}
    return [
        {"label": "Actor", "status": "verified", "value": identity.get("identity_id", "demo-actor")},
        {"label": "Authority", "status": decision.get("decision", "ALLOW"), "value": decision.get("reason", "demo")},
        {"label": "Payment", "status": payment.get("status", "demo"), "value": payment.get("receipt_id", "demo-receipt")},
        {"label": "Proof", "status": trust.get("replay_status", "verified"), "value": trust.get("trust_id", "demo-trust")},
        {"label": "Intelligence", "status": explanation.get("risk_level", "LOW"), "value": explanation.get("recommended_action", "continue")},
        {"label": "Evolution", "status": proposal.get("lifecycle_state", "ready_for_validation"), "value": proposal.get("proposal_id", "demo-proposal")},
    ]


def _demo_explorer_packet(identifier: str) -> dict[str, object]:
    return {
        "identity": {"identity_id": "public-demo", "organization_id": "novatech-core"},
        "decision": {"decision": "ALLOW", "reason": "Public demo packet", "trace_id": identifier},
        "payment": {"receipt_id": identifier, "status": "completed", "provider": "payid"},
        "trust": {"trust_id": identifier, "replay_status": "verified", "event_hash": identifier},
        "explanation": {"risk_level": "LOW", "recommended_action": "continue"},
        "proposal": {"lifecycle_state": "ready_for_validation", "proposal_id": "public-demo-proposal"},
    }


def _render_trust_explorer_html(*, identifier: str, packet: dict[str, object]) -> str:
    timeline = _explorer_timeline(packet)
    rows = "".join(
        "<article>"
        f"<strong>{escape(str(item['label']))}</strong>"
        f"<span>{escape(str(item['status']))}</span>"
        f"<p>{escape(str(item['value']))}</p>"
        "</article>"
        for item in timeline
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>NovaTrust Explorer</title>
    <style>
      body {{ margin: 0; font-family: Inter, Arial, sans-serif; background: #f7fafc; color: #102033; }}
      main {{ max-width: 1040px; margin: 0 auto; padding: 32px 20px; }}
      section {{ background: white; border: 1px solid #d8e2ec; border-radius: 8px; padding: 20px; margin-bottom: 18px; }}
      h1 {{ margin: 0; font-size: 30px; }}
      .muted {{ color: #5b6b7e; line-height: 1.5; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
      article {{ border: 1px solid #d8e2ec; border-radius: 8px; padding: 14px; background: #fbfdff; }}
      article strong, article span {{ display: block; }}
      article span {{ color: #0f766e; margin-top: 4px; }}
      code {{ background: #edf4f7; border-radius: 4px; padding: 2px 6px; }}
    </style>
  </head>
  <body>
    <main>
      <section>
        <div class="muted">Public verification surface</div>
        <h1>NovaTrust Explorer</h1>
        <p class="muted">Receipt or trust identifier: <code>{escape(identifier)}</code></p>
        <p class="muted">This page exposes proof, replay, payment, authority, and explanation context without granting execution authority.</p>
      </section>
      <section>
        <h2>Verification Timeline</h2>
        <div class="grid">{rows}</div>
      </section>
    </main>
  </body>
</html>"""


__all__ = [
    "build_core_platform_router",
    "build_public_trust_explorer_router",
    "core_platform_console_payload",
]
