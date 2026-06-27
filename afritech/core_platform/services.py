"""Deterministic services for the NovaTech core platform layers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from typing import Any, Mapping, Protocol

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
from afritech.core_platform.consensus import ValidatorConsensusEngine
from afritech.core_platform.payments.providers import provider_for
from afritech.core_platform.settlement import (
    SettlementRouter,
    build_settlement_corridor_matrix,
    build_settlement_status,
)
from afritech.core_platform.signing import kms_signing_status, signing_key_status
from afritech.core_platform.transfers import NovaPayTransferService
from afritech.platform_operations.policy import PolicyInput, VersionedPolicyEngine


CORE_FLOW = (
    "NovaID",
    "NovaPower",
    "NovaPay",
    "NovaTrust",
    "NovaScript",
    "NovaProgramming",
)


class SettlementLifecycleState(str, Enum):
    VALIDATED = "validated"
    COMPLIANCE_PASSED = "compliance_passed"
    PROVIDER_LOCKED = "provider_locked"
    SETTLEMENT_SUBMITTED = "settlement_submitted"
    SETTLED = "settled"
    RECEIPT_ISSUED = "receipt_issued"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class SettlementLifecycleEvent:
    state: SettlementLifecycleState
    intent_id: str
    organization_id: str
    provider: str | None = None
    payment_id: str | None = None
    route_id: str | None = None
    corridor: str | None = None
    settlement_status: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "intent_id": self.intent_id,
            "organization_id": self.organization_id,
            "provider": self.provider,
            "payment_id": self.payment_id,
            "route_id": self.route_id,
            "corridor": self.corridor,
            "settlement_status": self.settlement_status,
            "details": dict(self.details),
        }


class SettlementLifecycleHooks(Protocol):
    def on_transition(self, event: SettlementLifecycleEvent) -> None:
        ...


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

    def __init__(self, policy_engine: VersionedPolicyEngine | None = None) -> None:
        self.policy_engine = policy_engine or VersionedPolicyEngine()

    def evaluate(self, request: AuthorityRequest, identity: Identity) -> AuthorityDecision:
        result = self.policy_engine.evaluate(
            PolicyInput(
                tenant_id=request.organization_id,
                identity_tenant_id=identity.organization_id,
                actor_id=identity.identity_id,
                roles=identity.roles,
                scopes=identity.scopes,
                action=request.action,
                required_roles=request.required_roles,
                required_scopes=request.required_scopes,
                resource_owner_id=request.resource_owner_id,
                risk_score=request.risk_score,
                risk_score_max=request.risk_score_max,
            )
        )
        return AuthorityDecision(
            decision=result.decision,
            reason=result.reason,
            trace_id=result.trace_id,
            checks=result.checks,
        )


class NovaPayService:
    """Provider-neutral payment execution facade."""

    def __init__(
        self,
        *,
        settlement_router: SettlementRouter | None = None,
        event_bus: EventBus | None = None,
        lifecycle_hooks: SettlementLifecycleHooks | None = None,
    ) -> None:
        self.settlement_router = settlement_router or SettlementRouter()
        self.event_bus = event_bus or build_event_bus()
        self.lifecycle_hooks = lifecycle_hooks

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
        self._emit_settlement_transition(
            SettlementLifecycleState.VALIDATED,
            intent=intent,
            provider=provider,
            settlement=settlement.plan,
        )
        self._emit_settlement_transition(
            SettlementLifecycleState.COMPLIANCE_PASSED,
            intent=intent,
            provider=provider,
            settlement=settlement.plan,
        )
        self._emit_settlement_transition(
            SettlementLifecycleState.PROVIDER_LOCKED,
            intent=intent,
            provider=provider,
            settlement=settlement.plan,
        )
        payment_id = _new_id("pay")
        provider_adapter = provider_for(
            provider,
            live=live_provider,
            intent=provider_intent,
        )
        self._invoke_provider_hook(
            provider_adapter,
            "before_authorize",
            intent=provider_intent,
            settlement=settlement.plan,
        )
        self._emit_settlement_transition(
            SettlementLifecycleState.SETTLEMENT_SUBMITTED,
            intent=intent,
            provider=provider_adapter.name,
            settlement=settlement.plan,
        )
        try:
            provider_result = provider_adapter.authorize(provider_intent)
            self._invoke_provider_hook(
                provider_adapter,
                "after_authorize",
                intent=provider_intent,
                settlement=settlement.plan,
                result=provider_result,
            )
            self._emit_settlement_transition(
                SettlementLifecycleState.SETTLED,
                intent=intent,
                provider=provider_result.provider,
                payment_id=payment_id,
                settlement=settlement.plan,
                settlement_status=provider_result.settlement_status,
            )
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
            self._emit_settlement_transition(
                SettlementLifecycleState.RECEIPT_ISSUED,
                intent=intent,
                provider=provider_result.provider,
                payment_id=payment_id,
                settlement=settlement.plan,
                settlement_status=provider_result.settlement_status,
            )
            self._emit_settlement_transition(
                SettlementLifecycleState.COMPLETED,
                intent=intent,
                provider=provider_result.provider,
                payment_id=payment_id,
                settlement=settlement.plan,
                settlement_status=provider_result.settlement_status,
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
        except Exception as exc:
            self._emit_settlement_transition(
                SettlementLifecycleState.FAILED,
                intent=intent,
                provider=provider_adapter.name,
                payment_id=payment_id,
                settlement=settlement.plan,
                settlement_status="failed",
                details={
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
            )
            raise

    def _emit_settlement_transition(
        self,
        state: SettlementLifecycleState,
        *,
        intent: PaymentIntent,
        settlement: SettlementPlan,
        provider: str | None = None,
        payment_id: str | None = None,
        settlement_status: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        event = SettlementLifecycleEvent(
            state=state,
            intent_id=intent.intent_id,
            organization_id=intent.organization_id,
            provider=provider,
            payment_id=payment_id,
            route_id=settlement.route_id,
            corridor=settlement.corridor,
            settlement_status=settlement_status,
            details=details or {},
        )
        if self.lifecycle_hooks is not None:
            self.lifecycle_hooks.on_transition(event)
        self.event_bus.publish("novapay.settlement.transition", event.canonical())

    @staticmethod
    def _invoke_provider_hook(provider_adapter: Any, hook_name: str, **kwargs: Any) -> None:
        hook = getattr(provider_adapter, hook_name, None)
        if callable(hook):
            hook(**kwargs)


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
        self.transfers = NovaPayTransferService(
            payments=self.payments,
            settlement_router=self.payments.settlement_router,
        )
        self.trust = trust or NovaTrustService()
        self.intelligence = intelligence or NovaScriptService()
        self.programming = programming or NovaProgrammingService()
        self.validator_consensus = ValidatorConsensusEngine()

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
        "philosophy": (
            "Identity -> Authority -> Execution -> Payment -> Proof -> "
            "Intelligence -> Evolution"
        ),
        "modules": modules,
        "deployment": {
            "settlement": build_settlement_status(),
            "corridor_matrix": build_settlement_corridor_matrix(),
        },
        "product_applications_included": False,
    }
