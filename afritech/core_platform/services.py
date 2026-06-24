"""Deterministic services for the NovaTech core platform layers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

from afritech.core_platform.models import (
    AuthorityDecision,
    AuthorityRequest,
    CorePlatformFlowResult,
    Identity,
    PaymentIntent,
    PaymentReceipt,
    ProgrammingProposal,
    ScriptExplanation,
    SettlementPlan,
    TrustReceipt,
)
from afritech.core_platform.event_bus import EventBus, build_event_bus
from afritech.core_platform.payments.providers import provider_for
from afritech.core_platform.settlement import SettlementRouter
from afritech.core_platform.signing import kms_signing_status, signing_key_status


CORE_FLOW = (
    "NovaID",
    "NovaPower",
    "NovaPay",
    "NovaTrust",
    "NovaScript",
    "NovaProgramming",
)


def _stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


class NovaIDService:
    """Identity boundary for all downstream platform operations."""

    def bind_identity(
        self,
        *,
        identity_id: str,
        email: str,
        roles: tuple[str, ...],
        organization_id: str,
        scopes: tuple[str, ...] = (),
        devices: tuple[str, ...] = (),
        kyc_status: str = "verified",
    ) -> Identity:
        if not identity_id or not organization_id:
            raise ValueError("identity_id and organization_id are required")
        return Identity(
            identity_id=identity_id,
            email=email,
            roles=tuple(sorted(set(roles))),
            organization_id=organization_id,
            scopes=tuple(sorted(set(scopes))),
            devices=tuple(sorted(set(devices))),
            kyc_status=kyc_status,
        )


class NovaPowerEngine:
    """Policy engine for role, scope, tenant, ownership, and risk checks."""

    def evaluate(self, request: AuthorityRequest, identity: Identity) -> AuthorityDecision:
        checks: list[str] = []
        failures: list[str] = []

        if request.organization_id == identity.organization_id:
            checks.append("tenant_aligned")
        else:
            failures.append("tenant_mismatch")

        if not request.required_roles or set(request.required_roles).intersection(identity.roles):
            checks.append("role_allowed")
        else:
            failures.append("role_missing")

        if set(request.required_scopes).issubset(identity.scopes):
            checks.append("scope_allowed")
        else:
            failures.append("scope_missing")

        if request.resource_owner_id in {None, identity.identity_id}:
            checks.append("ownership_valid")
        else:
            failures.append("ownership_mismatch")

        if request.risk_score <= request.risk_score_max:
            checks.append("risk_within_policy")
        else:
            failures.append("risk_above_policy")

        decision = "ALLOW" if not failures else "DENY"
        reason = "All core constraints passed" if not failures else ", ".join(failures)
        trace_id = _stable_hash({"request": request.canonical(), "identity": identity.canonical()})[:24]
        return AuthorityDecision(
            decision=decision,
            reason=reason,
            trace_id=trace_id,
            checks=tuple(checks + failures),
        )


class NovaPayService:
    """Provider-neutral payment execution facade."""

    def __init__(
        self,
        *,
        settlement_router: SettlementRouter | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.settlement_router = settlement_router or SettlementRouter()
        self.event_bus = event_bus or build_event_bus()

    def execute(
        self,
        intent: PaymentIntent,
        *,
        identity: Identity,
        decision: AuthorityDecision,
        provider: str = "payid",
        live_provider: bool = False,
    ) -> PaymentReceipt:
        if intent.actor_id != identity.identity_id:
            raise ValueError("payment intent actor must match NovaID subject")
        if intent.organization_id != identity.organization_id:
            raise ValueError("payment intent tenant must match NovaID tenant")
        if not decision.allowed:
            raise PermissionError(f"NovaPower rejected payment: {decision.reason}")
        if intent.amount <= Decimal("0"):
            raise ValueError("payment amount must be positive")

        settlement = self.settlement_router.plan(
            intent,
            provider=provider,
            live_provider=live_provider,
        )
        provider_intent = settlement.intent
        provider_result = provider_for(
            provider,
            live=live_provider,
            intent=provider_intent,
        ).authorize(provider_intent)
        payment_id = _new_id("pay")
        payload = {
            "intent": intent.canonical(),
            "settlement": settlement.plan.canonical(),
            "settlement_intent": provider_intent.canonical(),
            "decision": decision.canonical(),
            "provider": provider_result.provider,
            "provider_reference": provider_result.provider_reference,
            "provider_status": provider_result.status,
            "payment_id": payment_id,
            "security": {
                "signing": signing_key_status().canonical(),
                "kms": kms_signing_status().canonical(),
                "event_bus": self.event_bus.status(),
            },
        }
        proof_hash = _stable_hash(payload)
        self.event_bus.publish(
            "novapay.payment.executed",
            {
                "intent_id": intent.intent_id,
                "organization_id": intent.organization_id,
                "payment_id": payment_id,
                "provider": provider_result.provider,
                "settlement_status": provider_result.settlement_status,
                "corridor": settlement.plan.corridor,
                "route_class": settlement.plan.route_class,
            },
        )
        return PaymentReceipt(
            receipt_id=_new_id("receipt"),
            payment_id=payment_id,
            status=provider_result.status,
            actor_id=identity.identity_id,
            organization_id=identity.organization_id,
            amount=provider_intent.amount,
            currency=provider_intent.currency.upper(),
            provider=provider_result.provider,
            proof_hash=proof_hash,
            provider_reference=provider_result.provider_reference,
            settlement_status=provider_result.settlement_status,
        )


class NovaTrustService:
    """Proof packet and replay validation layer."""

    def record(
        self,
        *,
        subject_id: str,
        organization_id: str,
        event_type: str,
        packet: dict[str, object],
    ) -> TrustReceipt:
        event_hash = _stable_hash(packet)
        return TrustReceipt(
            trust_id=_new_id("trust"),
            subject_id=subject_id,
            organization_id=organization_id,
            event_type=event_type,
            event_hash=event_hash,
            replay_status="verified",
            packet={**packet, "event_hash": event_hash},
        )

    def replay(self, receipt: TrustReceipt) -> bool:
        packet = dict(receipt.packet)
        packet.pop("event_hash", None)
        return _stable_hash(packet) == receipt.event_hash


class NovaScriptService:
    """Explainable intelligence facade for core platform state."""

    def explain(
        self,
        *,
        subject: str,
        decision: AuthorityDecision,
        trust: TrustReceipt,
    ) -> ScriptExplanation:
        if decision.allowed and trust.replay_status == "verified":
            risk_level = "LOW"
            recommended_action = "continue"
            summary = f"{subject} passed NovaPower policy and NovaTrust replay."
        else:
            risk_level = "HIGH"
            recommended_action = "review"
            summary = f"{subject} requires review: {decision.reason}."

        return ScriptExplanation(
            explanation_id=_new_id("explain"),
            subject=subject,
            summary=summary,
            risk_level=risk_level,
            recommended_action=recommended_action,
            evidence_refs=(trust.trust_id, decision.trace_id),
        )


class NovaProgrammingService:
    """Governed engineering proposal surface for platform evolution."""

    def create_proposal(
        self,
        *,
        title: str,
        explanation: ScriptExplanation,
        evidence_refs: tuple[str, ...],
    ) -> ProgrammingProposal:
        state = "ready_for_validation" if explanation.risk_level == "LOW" else "requires_review"
        return ProgrammingProposal(
            proposal_id=_new_id("proposal"),
            title=title,
            lifecycle_state=state,
            validators=("test_suite", "risk_scan", "trust_replay"),
            evidence_refs=tuple(sorted(set(evidence_refs + explanation.evidence_refs))),
        )


class NovaTechCorePlatform:
    """Composable core platform orchestration facade."""

    def __init__(
        self,
        *,
        identity: NovaIDService | None = None,
        authority: NovaPowerEngine | None = None,
        payments: NovaPayService | None = None,
        trust: NovaTrustService | None = None,
        intelligence: NovaScriptService | None = None,
        programming: NovaProgrammingService | None = None,
    ) -> None:
        self.identity = identity or NovaIDService()
        self.authority = authority or NovaPowerEngine()
        self.payments = payments or NovaPayService()
        self.trust = trust or NovaTrustService()
        self.intelligence = intelligence or NovaScriptService()
        self.programming = programming or NovaProgrammingService()

    def execute_payment_flow(
        self,
        *,
        identity: Identity,
        request: AuthorityRequest,
        payment_intent: PaymentIntent,
        provider: str = "payid",
        live_provider: bool = False,
    ) -> CorePlatformFlowResult:
        decision = self.authority.evaluate(request, identity)
        payment: PaymentReceipt | None = None
        settlement: SettlementPlan | None = None
        packet: dict[str, object] = {
            "identity": identity.canonical(),
            "authority": decision.canonical(),
            "payment_intent": payment_intent.canonical(),
            "flow": CORE_FLOW,
            "security": {
                "signing": signing_key_status().canonical(),
                "kms": kms_signing_status().canonical(),
                "event_bus": self.payments.event_bus.status(),
            },
        }

        if decision.allowed:
            payment = self.payments.execute(
                payment_intent,
                identity=identity,
                decision=decision,
                provider=provider,
                live_provider=live_provider,
            )
            settlement = self.payments.settlement_router.plan(
                payment_intent,
                provider=provider,
                live_provider=live_provider,
            ).plan
            packet["payment"] = payment.canonical()
            packet["settlement"] = settlement.canonical()
            event_type = "core.payment.completed"
        else:
            event_type = "core.payment.denied"

        trust = self.trust.record(
            subject_id=identity.identity_id,
            organization_id=identity.organization_id,
            event_type=event_type,
            packet=packet,
        )
        explanation = self.intelligence.explain(
            subject=payment_intent.intent_id,
            decision=decision,
            trust=trust,
        )
        proposal = None
        if not decision.allowed:
            proposal = self.programming.create_proposal(
                title=f"Review denied action {request.action}",
                explanation=explanation,
                evidence_refs=(trust.trust_id,),
            )
        else:
            proposal = self.programming.create_proposal(
                title=f"Validate core flow {request.action}",
                explanation=replace(explanation, recommended_action="monitor"),
                evidence_refs=(trust.trust_id,),
            )

        return CorePlatformFlowResult(
            identity=identity,
            decision=decision,
            payment=payment,
            settlement=settlement,
            trust=trust,
            explanation=explanation,
            proposal=proposal,
        )


def build_core_platform_overview() -> dict[str, object]:
    """Return the dashboard/API contract for the core platform layers only."""

    modules = [
        {"key": "identity", "label": "NovaID / AfriID", "path": "/console/identity"},
        {"key": "authority", "label": "NovaPower", "path": "/console/authority"},
        {"key": "payments", "label": "NovaPay / AfriPay", "path": "/console/payments"},
        {"key": "trust", "label": "NovaTrust", "path": "/console/trust"},
        {"key": "intelligence", "label": "NovaScript", "path": "/console/intelligence"},
        {"key": "programming", "label": "NovaProgramming", "path": "/console/programming"},
    ]
    return {
        "platform": "NovaTechSol",
        "console": "Unified Trust Operating Console",
        "flow": list(CORE_FLOW),
        "philosophy": "Identity -> Authority -> Execution -> Payment -> Proof -> Intelligence -> Evolution",
        "modules": modules,
        "product_applications_included": False,
    }
