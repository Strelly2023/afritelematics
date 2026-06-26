"""Core NovaTech platform API surfaces."""

from __future__ import annotations

from decimal import Decimal
import hashlib
from html import escape
import json
import os
from typing import Any, Callable, Mapping, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
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
from afritech.core_platform.cbdc import cbdc_status
from afritech.core_platform.consensus import build_validator_consensus_status
from afritech.core_platform.cryptographic_consensus import (
    build_cryptographic_consensus_status,
    run_cryptographic_consensus,
)
from afritech.core_platform.mobile_verifier import verify_scanned_receipt
from afritech.core_platform.qr_proof import build_qr_artifact, build_qr_png
from afritech.core_platform.proof_receipts import (
    build_proof_receipt,
    verify_proof_receipt,
)
from afritech.core_platform.smart_contract_verification import (
    build_onchain_verification_bundle,
    solidity_verifier_source,
)
from afritech.core_platform.distributed_verification import (
    build_trust_seal,
    build_validator_node_health,
    validate_distributed_consensus,
)
from afritech.core_platform.anchoring import anchor_packet, build_optional_blockchain_anchor
from afritech.core_platform.audit_export import render_audit_pdf
from afritech.core_platform.auditor_dashboard import build_auditor_dashboard
from afritech.core_platform.event_bus import build_event_bus_status
from afritech.core_platform.compliance_report import build_enterprise_audit_report
from afritech.core_platform.export_bundle import build_auditor_zip
from afritech.core_platform.migration_system import build_migration_plan
from afritech.core_platform.settlement import build_settlement_status
from afritech.core_platform.payments.mobile_money import mobile_money_catalog
from afritech.core_platform.payments.providers import payid_status
from afritech.core_platform.persistence import (
    InMemoryCorePlatformStore,
    PostgresCorePlatformStore,
)
from afritech.core_platform.qr import render_qr_png
from afritech.core_platform.signing import (
    AuditSignature,
    build_key_rotation_plan,
    sign_packet,
    signing_key_ready,
    signing_key_status,
    verify_packet_signature,
)
from afritech.core_platform.trust_node import (
    build_trust_node_network_status,
    TrustNodeEnvelope,
    federation_readiness,
    import_trust_envelope,
)
from afritech.fintech.webhook_security import verify_webhook
from afritech.fintech.webhooks import normalize_payment_webhook
from afritech.platform_contracts.federation import local_federation_manifest
from afritech.platform_contracts.registry import (
    ContractRegistryError,
    architecture_metrics,
    capability_graph,
    load_platform_contract,
    load_schema,
    negotiate_headers,
    schema_publication,
    schema_registry_manifest,
    current_version_vector,
    validate_contract_payload,
)
from afritech.platform_operations.registry import operations_readiness


def _build_store() -> InMemoryCorePlatformStore | PostgresCorePlatformStore:
    dsn = os.environ.get("NOVATECH_CORE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if dsn and dsn.startswith(("postgres://", "postgresql://")):
        return PostgresCorePlatformStore(dsn)
    return InMemoryCorePlatformStore()


CORE_PLATFORM_STORE = _build_store()


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


class DistributedValidatorEnvelopePayload(BaseModel):
    node_id: str
    packet: dict[str, Any]
    signature: dict[str, str]
    replay_status: str | None = None
    protocol_version: str = "novatrust-validator-v1"
    observed_at: str | None = None


class DistributedConsensusValidationPayload(BaseModel):
    packet: dict[str, Any]
    validators: list[DistributedValidatorEnvelopePayload]
    total_nodes: int | None = None
    trusted_public_keys: dict[str, str] = Field(default_factory=dict)


class CryptographicConsensusVotePayload(BaseModel):
    node_id: str
    packet: dict[str, Any]
    signature: dict[str, str]
    replay_status: str | None = None
    public_key_id: str | None = None


class CryptographicConsensusPayload(BaseModel):
    packet: dict[str, Any]
    votes: list[CryptographicConsensusVotePayload]
    total_nodes: int | None = None
    trusted_public_keys: dict[str, str] = Field(default_factory=dict)


class TrustSealPayload(BaseModel):
    certificate: dict[str, Any]
    node_health: dict[str, Any] | None = None


class ProofReceiptPayload(BaseModel):
    trust_seal: dict[str, Any]
    issuer: str = "novatrust-proof-service"
    issued_at: str | None = None


class ProofReceiptVerifyPayload(BaseModel):
    receipt: dict[str, Any]
    group_public_keys: list[str] = Field(default_factory=list)


class ProofReceiptQrPayload(BaseModel):
    trust_seal: dict[str, Any]
    issuer: str = "novatrust-proof-service"
    issued_at: str | None = None


class ProofReceiptMobileVerifyPayload(BaseModel):
    qr_data: str


class ProofReceiptOnchainPayload(BaseModel):
    receipt: dict[str, Any]


class NodeHealthPayload(BaseModel):
    configured_nodes: int = 1
    healthy_nodes: int = 1
    quorum: int | None = None
    disagreeing_nodes: list[str] = Field(default_factory=list)
    quarantined_nodes: list[str] = Field(default_factory=list)


class ExplainPayload(BaseModel):
    subject: str


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


class ContractValidationPayload(BaseModel):
    schema_name: str
    payload: dict[str, Any]


class GovernedRequestPayload(BaseModel):
    request_id: str = Field(min_length=1)
    operation: str = Field(pattern=r"^[a-z][a-z0-9_.-]+$")
    tenant_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8, max_length=255)
    contract_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    correlation_id: str | None = Field(default=None, min_length=1)
    payload: dict[str, Any]

    class Config:
        extra = "forbid"


def _identity_from_claims(claims: JWTClaims) -> Any:
    return NovaIDService().bind_identity(
        identity_id=claims.sub,
        organization_id=claims.organization_id,
        email=f"{claims.sub}@novatech.local",
        roles=(claims.role,),
        scopes=(
            "identity:read",
            "authority:evaluate",
            "payments:write",
            "trust:read",
            "ai:explain",
            "programming:propose",
        ),
        devices=("authenticated-session",),
    )


def _stored_signature(identifier: str, packet: dict[str, Any]) -> AuditSignature:
    getter = getattr(CORE_PLATFORM_STORE, "get_signature", None)
    stored = getter(identifier) if callable(getter) else None
    if stored is None:
        return sign_packet(packet)
    if not isinstance(stored, Mapping):
        return sign_packet(packet)
    stored_signature = dict(cast(Mapping[str, str], stored))
    return AuditSignature(**stored_signature)


def _existing_intent(organization_id: str, intent_id: str) -> dict[str, Any] | None:
    getter = getattr(CORE_PLATFORM_STORE, "get_by_intent", None)
    packet = getter(organization_id, intent_id) if callable(getter) else None
    if packet is None:
        return None
    if not isinstance(packet, Mapping):
        return None
    return dict(cast(Mapping[str, Any], packet))


def _store_get_flow(identifier: str) -> Any | None:
    get_flow = getattr(CORE_PLATFORM_STORE, "get_flow", None)

    if callable(get_flow):
        return cast(Callable[[str], Any | None], get_flow)(identifier)

    flows = getattr(CORE_PLATFORM_STORE, "flows", {})
    if isinstance(flows, dict):
        return flows.get(identifier)

    return None


def _normalize_packet_from_flow(packet: dict[str, Any]) -> dict[str, Any]:
    if "trust" in packet and "identity" in packet:
        return packet

    result = packet.get("result")
    if isinstance(result, dict):
        return {
            "identity": result.get("identity", {}),
            "decision": result.get("decision", {}),
            "payment": result.get("payment", {}),
            "trust": result.get("trust", {}),
            "explanation": result.get("explanation", {}),
            "proposal": result.get("proposal", {}),
        }

    return packet


def _timeline(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "label": "Actor",
            "status": "verified",
            "value": packet.get("identity", {}).get("identity_id"),
        },
        {
            "label": "Authority",
            "status": packet.get("decision", {}).get("decision"),
        },
        {
            "label": "Payment",
            "status": packet.get("payment", {}).get("status"),
        },
        {
            "label": "Proof",
            "status": packet.get("trust", {}).get("replay_status"),
        },
    ]


def _explorer_payload(identifier: str, raw: dict[str, Any]) -> dict[str, Any]:
    packet = _normalize_packet_from_flow(raw)

    return {
        "view": "public_trust_explorer",
        "identifier": identifier,
        "packet": packet,
        "timeline": _timeline(packet),
        "replay_result": packet.get("trust", {}).get("replay_status", "unknown"),
        "public": True,
    }


def _lookup_packet(identifier: str) -> dict[str, Any] | None:
    packet = CORE_PLATFORM_STORE.get_trust_packet(identifier)

    if packet is not None:
        return _normalize_packet_from_flow(packet)

    flow = _store_get_flow(identifier)
    if flow is not None and hasattr(flow, "canonical"):
        return _normalize_packet_from_flow(flow.canonical())

    return None


def build_core_platform_router() -> APIRouter:
    router = APIRouter(prefix="/v1/core-platform", tags=["core-platform"])

    @router.get("/contracts")
    def contract_browser() -> dict[str, Any]:
        contract = load_platform_contract()
        return {
            "view": "novatech_contract_browser",
            "contract": contract,
            "schema_registry": schema_registry_manifest(),
            "architecture": capability_graph(),
            "metrics": architecture_metrics(),
            "sdk_downloads": {
                "python": "/docs/sdk/generated/novatech_contracts.py",
                "typescript": "/docs/sdk/generated/novatech-contracts.ts",
                "kotlin": "/docs/sdk/generated/NovaTechContracts.kt",
                "swift": "/docs/sdk/generated/NovaTechContracts.swift",
            },
            "execution_authority": False,
        }

    @router.get("/contracts/schemas/{schema_name}")
    def contract_schema(schema_name: str) -> dict[str, Any]:
        try:
            return {
                "schema": load_schema(schema_name),
                "publication": schema_publication(schema_name),
            }
        except ContractRegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/contracts/validate")
    def validate_contract(
        payload: ContractValidationPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        try:
            validate_contract_payload(payload.schema_name, payload.payload)
        except ContractRegistryError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "valid": True,
            "schema_name": payload.schema_name,
            "publication": schema_publication(payload.schema_name),
        }

    @router.post("/contracts/admit")
    def admit_governed_request(
        payload: GovernedRequestPayload,
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        request_payload = (
            payload.model_dump(exclude_none=True)
            if hasattr(payload, "model_dump")
            else payload.dict(exclude_none=True)
        )
        try:
            validate_contract_payload("request", request_payload)
        except ContractRegistryError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if payload.tenant_id != claims.organization_id:
            raise HTTPException(status_code=403, detail="tenant_context_mismatch")
        if payload.actor_id != claims.sub:
            raise HTTPException(status_code=403, detail="actor_context_mismatch")
        vector = current_version_vector()
        contract_result = negotiate_headers(
            {"accept-contract-version": payload.contract_version}
        )
        if contract_result["status"] != "COMPATIBLE":
            raise HTTPException(status_code=426, detail=contract_result)
        operation_id = "op_" + hashlib.sha256(
            json.dumps(request_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:24]
        response = {
            "request_id": payload.request_id,
            "operation_id": operation_id,
            "status": "ACCEPTED",
            "tenant_id": claims.organization_id,
            "trust_level": 2,
            "version_vector": vector.canonical(),
            "data": {
                "operation": payload.operation,
                "admitted": True,
                "execution_authority": False,
            },
            "links": {
                "contract": "/v1/core-platform/contracts",
                "schema": "/v1/core-platform/contracts/schemas/request",
            },
        }
        validate_contract_payload("response", response)
        return response

    @router.get("/contracts/negotiate")
    def negotiate_contracts(
        accept_contract_version: str | None = Header(
            default=None, alias="Accept-Contract-Version"
        ),
        accept_replay_version: str | None = Header(
            default=None, alias="Accept-Replay-Version"
        ),
        accept_evidence_version: str | None = Header(
            default=None, alias="Accept-Evidence-Version"
        ),
        accept_signature_version: str | None = Header(
            default=None, alias="Accept-Signature-Version"
        ),
    ) -> dict[str, Any]:
        try:
            result = negotiate_headers(
                {
                    "accept-contract-version": accept_contract_version,
                    "accept-replay-version": accept_replay_version,
                    "accept-evidence-version": accept_evidence_version,
                    "accept-signature-version": accept_signature_version,
                }
            )
        except ContractRegistryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if result["status"] != "COMPATIBLE":
            raise HTTPException(status_code=426, detail=result)
        return result

    @router.get("/federation/manifest")
    def federation_manifest() -> dict[str, Any]:
        return local_federation_manifest().canonical()

    @router.get("/operations/readiness")
    def platform_operations_readiness(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return operations_readiness()

    @router.get("/console")
    def console(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, object]:
        return core_platform_console_payload()

    @router.get("/identity/me")
    def identity_me(
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return {
            "view": "core_platform_identity",
            "layer": "NovaID / AfriID",
            "identity": _identity_from_claims(claims).canonical(),
            "secures_downstream_layers": True,
        }

    @router.post("/authority/evaluate")
    def authority_evaluate(
        payload: AuthorityEvaluationPayload,
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
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
    def execute(
        payload: PaymentExecutionPayload,
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        platform = NovaTechCorePlatform()
        identity = _identity_from_claims(claims)

        existing = _existing_intent(identity.organization_id, payload.intent_id)
        if existing is not None:
            trust = existing.get("trust", {})
            trust_id = (
                str(trust.get("trust_id", ""))
                if isinstance(trust, dict)
                else ""
            )
            return {
                "result": existing,
                "idempotent_replay": True,
                "trust_explorer": f"/trust/explorer/{trust_id}",
            }

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
            request=AuthorityRequest(
                action=payload.action,
                organization_id=identity.organization_id,
                required_roles=tuple(payload.required_roles),
                required_scopes=tuple(payload.required_scopes),
                resource_owner_id=identity.identity_id,
                risk_score=payload.risk_score,
                risk_score_max=payload.risk_score_max,
                metadata=payload.metadata,
            ),
            payment_intent=intent,
            provider=payload.provider,
            live_provider=payload.live_provider,
        )

        try:
            CORE_PLATFORM_STORE.save_flow(result)
        except Exception:
            existing = _existing_intent(identity.organization_id, payload.intent_id)
            if existing is None:
                raise
            return {
                "result": existing,
                "idempotent_replay": True,
                "trust_explorer": (
                    f"/trust/explorer/{existing.get('trust', {}).get('trust_id', '')}"
                ),
            }

        return {
            "view": "core_platform_payment_flow",
            "layer": "NovaPay / AfriPay",
            "result": result.canonical(),
            "idempotent_replay": False,
            "trust_explorer": f"/trust/explorer/{result.trust.trust_id}",
        }

    @router.post("/trust/replay")
    def trust_replay(
        payload: TrustReplayPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        platform = NovaTechCorePlatform()
        receipt = platform.trust.record(
            subject_id=str(payload.packet.get("subject_id", "manual-subject")),
            organization_id=str(payload.packet.get("organization_id", "manual-org")),
            event_type=str(payload.packet.get("event_type", "manual.event")),
            packet=payload.packet,
        )
        save_receipt = getattr(CORE_PLATFORM_STORE, "save_trust_receipt", None)
        if callable(save_receipt):
            save_receipt(receipt)
        return {
            "view": "core_platform_trust_replay",
            "layer": "NovaTrust",
            "receipt": receipt.canonical(),
            "replay_valid": platform.trust.replay(receipt),
            "trust_explorer": f"/trust/explorer/{receipt.trust_id}",
        }

    @router.get("/trust/explorer/{identifier}")
    def private_explorer(identifier: str) -> dict[str, Any]:
        packet = _lookup_packet(identifier)
        if packet is None:
            raise HTTPException(status_code=404, detail="trust_not_found")
        return {**_explorer_payload(identifier, packet), "execution_authority": False}

    @router.get("/trust/explorer/{identifier}/audit.pdf")
    def private_audit_pdf(identifier: str) -> Response:
        return _audit_pdf_response(identifier)

    @router.post("/auditor/dashboard")
    def private_auditor_dashboard(
        payload: AuditorDashboardPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        packets = []
        for identifier in payload.identifiers:
            packet = _lookup_packet(identifier) or _demo_packet(identifier)
            packets.append((identifier, packet))
        return build_auditor_dashboard(packets)

    @router.get("/signing/status")
    def signing_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return {
            "view": "novatrust_signing_status",
            "status": signing_key_status().canonical(),
            "ready": signing_key_ready(),
            "rotation_plan": build_key_rotation_plan(),
        }

    @router.get("/persistence/status")
    def persistence_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return {
            "view": "core_platform_persistence_status",
            "active_store": type(CORE_PLATFORM_STORE).__name__,
            "postgres_adapter": "available",
            "postgres_table": "novatech_core_trust_packets",
            "migration_system": build_migration_plan(),
        }

    @router.get("/payments/providers/status")
    def providers_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        stripe_live = os.environ.get("STRIPE_LIVE_MODE", "").lower() in {
            "1",
            "true",
            "yes",
        }
        stripe_key = bool(os.environ.get("STRIPE_API_KEY"))
        return {
            "view": "core_platform_payment_provider_status",
            "providers": {
                "payid": payid_status(),
                "stripe": {
                    "available": True,
                    "live_mode_enabled": stripe_live,
                    "api_key_configured": stripe_key,
                    "ready_for_real_charge": stripe_live and stripe_key,
                },
                "mobile_money": mobile_money_catalog(),
                "cbdc": cbdc_status(),
            },
            "settlement": build_settlement_status(),
            "event_bus": build_event_bus_status(),
        }

    @router.get("/payments/settlement/status")
    def settlement_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_settlement_status()

    @router.get("/trust/node/network/status")
    def trust_node_network_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_trust_node_network_status()

    @router.get("/trust/consensus/status")
    def trust_consensus_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_validator_consensus_status()

    @router.get("/trust/consensus/cryptographic/status")
    def trust_cryptographic_consensus_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_cryptographic_consensus_status()

    @router.get("/trust/nodes/health")
    def trust_nodes_health(
        configured_nodes: int = 1,
        healthy_nodes: int = 1,
        quorum: int | None = None,
        disagreeing_nodes: list[str] | None = Query(default=None),
        quarantined_nodes: list[str] | None = Query(default=None),
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_validator_node_health(
            configured_nodes=configured_nodes,
            healthy_nodes=healthy_nodes,
            quorum=quorum,
            disagreeing_nodes=disagreeing_nodes,
            quarantined_nodes=quarantined_nodes,
        )

    @router.post("/trust/consensus/validate")
    def trust_consensus_validate(
        payload: DistributedConsensusValidationPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return validate_distributed_consensus(
            packet=payload.packet,
            validators=[validator.model_dump() for validator in payload.validators],
            total_nodes=payload.total_nodes,
            trusted_public_keys=payload.trusted_public_keys or None,
        )

    @router.post("/trust/consensus/cryptographic")
    @router.post("/trust/consensus/bls")
    def trust_cryptographic_consensus(
        payload: CryptographicConsensusPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return run_cryptographic_consensus(
            payload.packet,
            [vote.model_dump() for vote in payload.votes],
            total_nodes=payload.total_nodes,
            trusted_public_keys=payload.trusted_public_keys or None,
        )

    @router.post("/trust/seal")
    def trust_seal(
        payload: TrustSealPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_trust_seal(
            certificate=payload.certificate,
            node_health=payload.node_health,
        )

    @router.post("/trust/consensus/proof-receipt")
    def trust_proof_receipt(
        payload: ProofReceiptPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return build_proof_receipt(
            payload.trust_seal,
            issuer=payload.issuer,
            issued_at=payload.issued_at,
        )

    @router.post("/trust/consensus/proof-receipt/qr")
    def trust_proof_receipt_qr(
        payload: ProofReceiptQrPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        receipt = build_proof_receipt(
            payload.trust_seal,
            issuer=payload.issuer,
            issued_at=payload.issued_at,
        )
        artifact = build_qr_artifact(receipt)
        return {"receipt": receipt, **artifact}

    @router.post("/trust/consensus/proof-receipt/qr.png")
    def trust_proof_receipt_qr_png(
        payload: ProofReceiptQrPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> Response:
        receipt = build_proof_receipt(
            payload.trust_seal,
            issuer=payload.issuer,
            issued_at=payload.issued_at,
        )
        return Response(build_qr_png(receipt), media_type="image/png")

    @router.post("/trust/consensus/proof-receipt/mobile-verify")
    def trust_proof_receipt_mobile_verify(
        payload: ProofReceiptMobileVerifyPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return verify_scanned_receipt(payload.qr_data)

    @router.post("/trust/consensus/proof-receipt/verify")
    def trust_proof_receipt_verify(
        payload: ProofReceiptVerifyPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return verify_proof_receipt(
            payload.receipt,
            group_public_keys=payload.group_public_keys,
        )

    @router.post("/trust/consensus/proof-receipt/onchain")
    def trust_proof_receipt_onchain(
        payload: ProofReceiptOnchainPayload,
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        bundle = build_onchain_verification_bundle(payload.receipt)
        return {
            "bundle": bundle,
            "solidity_verifier_source": solidity_verifier_source(),
        }

    @router.get("/payments/mobile-money/catalog")
    def mobile_money_status(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        return mobile_money_catalog()

    @router.get("/readiness")
    def readiness(
        _: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        configured_nodes = int(os.environ.get("NOVATRUST_FEDERATION_NODES", "1"))
        healthy_nodes = int(
            os.environ.get("NOVATRUST_FEDERATION_HEALTHY_NODES", "1")
        )
        federation = federation_readiness(
            configured_nodes=configured_nodes,
            healthy_nodes=healthy_nodes,
        )
        consensus = build_validator_consensus_status(
            configured_nodes=configured_nodes,
            healthy_nodes=healthy_nodes,
        )
        distributed = build_validator_node_health(
            configured_nodes=configured_nodes,
            healthy_nodes=healthy_nodes,
            quorum=consensus["validator_quorum"],
        )
        cryptographic = build_cryptographic_consensus_status(
            configured_nodes=configured_nodes,
            healthy_nodes=healthy_nodes,
        )
        persistent = isinstance(CORE_PLATFORM_STORE, PostgresCorePlatformStore)
        return {
            "classification": "bounded_production_readiness",
            "layers": {
                "execution": "ready",
                "persistence": "ready" if persistent else "development_only",
                "explorer": "ready",
                "audit": "ready",
                "signature": "ready" if signing_key_ready() else "blocked",
                "replay": "ready",
                "import": build_trust_node_network_status()["import_layer"],
                "federation": federation["federation_layer"],
                "consensus": consensus["consensus_layer"],
                "distributed_verification": (
                    "ready" if distributed["consensus_ready"] else "future_non_authoritative"
                ),
                "cryptographic_consensus": cryptographic["consensus_layer"],
            },
            "capabilities": {
                "persistent_trust_layer": persistent,
                "cryptographic_trust_layer": signing_key_ready(),
                "public_verification_active": True,
                "auditor_mode_active": True,
                "federation_ready": federation["federation_ready"],
                "multi_node_consensus_ready": consensus["multi_node_consensus_ready"],
                "distributed_verification_ready": distributed["consensus_ready"],
                "cryptographic_consensus_ready": cryptographic["cryptographic_consensus_ready"],
                "settlement_routing_ready": True,
                "fx_engine_ready": True,
                "event_bus_ready": build_event_bus_status()["event_bus"]["ready"],
                "cbdc_adapter_ready": cbdc_status()["ready_for_real_charge"],
            },
            "fintech": {
                "provider_abstraction": True,
                "authenticated_webhook_contract": True,
                "trust_node_protocol": True,
                "node_propagation_endpoint": True,
                "audit_ready_settlement_events": True,
                "provider_integration_ready": True,
                "licensed_live_payments": payid_status()["ready_for_real_charge"],
                "settlement_router": build_settlement_status(),
                "event_bus": build_event_bus_status(),
                "trust_node_network": build_trust_node_network_status(),
                "trust_consensus": consensus,
                "distributed_verification": distributed,
                "cryptographic_consensus": cryptographic,
                "mobile_money": {
                    "countries": ["BI", "CD", "KE"],
                    "controlled_pilot_ready": True,
                    "operator_contracts_required_for_live": True,
                },
                "cbdc": cbdc_status(),
            },
            "authority_boundary": federation["authority_boundary"],
        }

    @router.post("/ai/explain")
    def ai_explain(
        payload: ExplainPayload,
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
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
            packet={"subject": payload.subject},
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

    @router.post("/programming/proposals")
    def programming_proposal(
        payload: ProposalPayload,
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        platform = NovaTechCorePlatform()
        identity = _identity_from_claims(claims)
        decision = platform.authority.evaluate(
            AuthorityRequest(
                action="programming.propose",
                organization_id=identity.organization_id,
                required_roles=(claims.role,),
                required_scopes=("programming:propose",),
                resource_owner_id=identity.identity_id,
                risk_score=(
                    Decimal("0")
                    if payload.risk_level.upper() == "LOW"
                    else Decimal("0.80")
                ),
            ),
            identity,
        )
        trust = platform.trust.record(
            subject_id=identity.identity_id,
            organization_id=identity.organization_id,
            event_type="core.programming.proposal",
            packet={"title": payload.title},
        )
        explanation = platform.intelligence.explain(
            subject=payload.title,
            decision=decision,
            trust=trust,
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

    @router.post("/pilot/flow")
    def pilot_flow(
        payload: PilotFlowPayload,
        claims: JWTClaims = Depends(
            require_roles("OPERATOR", "VERIFIER", "DEVELOPER")
        ),
    ) -> dict[str, Any]:
        executed = execute(
            PaymentExecutionPayload(
                intent_id=payload.intent_id,
                amount=payload.amount,
                currency=payload.currency,
                destination=payload.destination,
                provider=payload.provider,
                live_provider=payload.live_provider,
            ),
            claims,
        )
        return {"status": "deployed", **executed}

    return router


def build_public_trust_explorer_router() -> APIRouter:
    router = APIRouter(tags=["core-platform-public-trust"])

    @router.get("/trust/sandbox/demo")
    def sandbox() -> dict[str, Any]:
        identifier = "sandbox-demo"
        return {
            "view": "novatrust_public_sandbox",
            "identifier": identifier,
            "links": {
                "explorer": f"/trust/explorer/{identifier}",
                "audit_pdf": f"/trust/explorer/{identifier}/audit.pdf",
                "signature": f"/trust/explorer/{identifier}/signature",
                "compliance_report": (
                    f"/trust/explorer/{identifier}/compliance-report"
                ),
                "anchor": f"/trust/explorer/{identifier}/anchor",
                "qr_png": f"/trust/explorer/{identifier}/qr.png",
                "bundle_zip": f"/trust/explorer/{identifier}/bundle.zip",
            },
            "classification": "deterministic_public_demo",
        }

    @router.get("/trust/explorer/{identifier}")
    def explorer(identifier: str, request: Request) -> Response:
        packet = (
            _demo_packet(identifier)
            if identifier == "sandbox-demo"
            else _lookup_packet(identifier)
        )

        if packet is None:
            return JSONResponse(
                {"error": "trust_not_found", "identifier": identifier},
                status_code=404,
            )

        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(_explorer_payload(identifier, packet))

        return Response(
            _render_html(identifier, packet),
            media_type="text/html",
        )

    @router.get("/trust/explorer/{identifier}/qr.png")
    def qr(identifier: str) -> Response:
        if identifier != "sandbox-demo" and _lookup_packet(identifier) is None:
            raise HTTPException(status_code=404, detail="trust_not_found")
        return Response(
            render_qr_png(
                f"https://api.afritechnology.com/trust/explorer/{identifier}"
            ),
            media_type="image/png",
        )

    @router.get("/trust/explorer/{identifier}/signature")
    def signature(identifier: str) -> dict[str, Any]:
        packet = _lookup_packet(identifier)

        if packet is None:
            raise HTTPException(status_code=404, detail="trust_not_found")

        sig = _stored_signature(identifier, packet)

        return {
            "signature": sig.canonical(),
            "verified": verify_packet_signature(packet, sig),
            "source": (
                "postgresql"
                if isinstance(CORE_PLATFORM_STORE, PostgresCorePlatformStore)
                else "memory"
            ),
        }

    @router.get("/trust/explorer/{identifier}/audit.pdf")
    def audit_pdf(identifier: str) -> Response:
        return _audit_pdf_response(identifier)

    @router.get("/trust/explorer/{identifier}/compliance-report")
    def compliance_report(identifier: str) -> dict[str, Any]:
        packet = _required_packet(identifier)
        return build_enterprise_audit_report(packet)

    @router.get("/trust/explorer/{identifier}/anchor")
    def deterministic_anchor(identifier: str) -> dict[str, Any]:
        packet = _required_packet(identifier)
        return {
            "view": "novatrust_chain_anchor",
            "identifier": identifier,
            "anchor": anchor_packet(packet).canonical(),
        }

    @router.get("/trust/explorer/{identifier}/anchor/blockchain")
    def blockchain_anchor(identifier: str) -> dict[str, Any]:
        packet = _required_packet(identifier)
        return {
            "view": "novatrust_optional_blockchain_anchor",
            "identifier": identifier,
            "anchor": build_optional_blockchain_anchor(packet).canonical(),
        }

    @router.get("/trust/explorer/{identifier}/bundle.zip")
    def bundle(identifier: str) -> Response:
        packet = _required_packet(identifier)
        verification_url = (
            f"https://api.afritechnology.com/trust/explorer/{identifier}"
        )
        return Response(
            build_auditor_zip(
                identifier=identifier,
                packet=packet,
                verification_url=verification_url,
            ),
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="novatrust-{identifier}.zip"'
                )
            },
        )

    @router.get("/trust/auditor/dashboard")
    def public_auditor_dashboard(ids: str = "") -> dict[str, Any]:
        identifiers = [item.strip() for item in ids.split(",") if item.strip()]
        packets = [
            (identifier, _lookup_packet(identifier) or _demo_packet(identifier))
            for identifier in identifiers
        ]
        return build_auditor_dashboard(packets)

    @router.get("/trust/audit/{identifier}")
    def trust_audit(identifier: str) -> dict[str, Any]:
        packet = _required_packet(identifier)
        signature = _stored_signature(identifier, packet)
        return {
            "identifier": identifier,
            "source": (
                "postgresql"
                if isinstance(CORE_PLATFORM_STORE, PostgresCorePlatformStore)
                else "memory"
            ),
            "record": packet,
            "signature_valid": verify_packet_signature(packet, signature),
            "replay_result": packet.get("trust", {}).get(
                "replay_status", "unknown"
            ),
            "auditor_mode": True,
        }

    @router.post("/trust/node/propagate")
    def propagate(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            envelope = TrustNodeEnvelope.from_payload(payload)
            configured_keys = os.environ.get(
                "NOVATRUST_FEDERATION_NODE_KEYS_JSON", ""
            )
            trusted_keys = (
                {
                    str(node_id): str(public_key)
                    for node_id, public_key in json.loads(configured_keys).items()
                }
                if configured_keys
                else None
            )
            if (
                os.environ.get("AFRITECH_ENV", "development").lower()
                in {"production", "prod"}
                and trusted_keys is None
            ):
                raise ValueError("federation_node_keys_not_configured")
            result = import_trust_envelope(
                envelope,
                store=CORE_PLATFORM_STORE,
                trusted_public_keys=trusted_keys,
            )
        except ValueError as exc:
            return {"status": "rejected", "reason": str(exc)}
        return result.canonical()

    @router.get("/trust/federation/status")
    def federation_status() -> dict[str, Any]:
        configured_nodes = int(os.environ.get("NOVATRUST_FEDERATION_NODES", "1"))
        healthy_nodes = int(
            os.environ.get("NOVATRUST_FEDERATION_HEALTHY_NODES", "1")
        )
        return federation_readiness(
            configured_nodes=configured_nodes,
            healthy_nodes=healthy_nodes,
        )

    @router.post("/webhooks/payments")
    def payment_webhook(
        payload: dict[str, Any],
        x_novapay_timestamp: str = Header(default=""),
        x_novapay_signature: str = Header(default=""),
    ) -> dict[str, Any]:
        provider_name = str(payload.get("provider", "")).strip().upper()
        provider_secret_name = (
            "NOVAPAY_"
            + "".join(character if character.isalnum() else "_" for character in provider_name)
            + "_WEBHOOK_SECRET"
        )
        secret = os.environ.get(provider_secret_name) or os.environ.get(
            "NOVAPAY_WEBHOOK_SECRET",
            "",
        )
        try:
            verified = verify_webhook(
                payload,
                timestamp=x_novapay_timestamp,
                signature=x_novapay_signature,
                secret=secret,
            )
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        event = normalize_payment_webhook(payload)
        settlement_status = event.settlement_status.lower()
        if settlement_status not in {
            "pending",
            "processing",
            "settled",
            "failed",
            "reversed",
        }:
            raise HTTPException(
                status_code=400,
                detail="invalid_settlement_status",
            )
        find_payment = getattr(CORE_PLATFORM_STORE, "find_payment", None)
        payment = (
            find_payment(
                payment_id=event.payment_id,
                provider_reference=event.provider_reference,
            )
            if callable(find_payment)
            else None
        )
        if payment is None:
            raise HTTPException(status_code=404, detail="payment_not_found")
        if not isinstance(payment, Mapping):
            raise HTTPException(status_code=404, detail="payment_not_found")
        payment_record = dict(cast(Mapping[str, Any], payment))
        if str(payment_record.get("provider", "")) != event.provider:
            raise HTTPException(status_code=409, detail="payment_provider_mismatch")

        evidence = {
            "event_id": verified.event_id,
            "provider": event.provider,
            "provider_reference": event.provider_reference,
            "payment_id": event.payment_id,
            "status": event.status,
            "settlement_status": settlement_status,
        }
        signature = sign_packet(evidence)
        trust_receipt = NovaTechCorePlatform().trust.record(
            subject_id=str(payment_record.get("actor_id", "payment-provider")),
            organization_id=str(payment_record.get("organization_id", "afritech-core")),
            event_type=f"core.payment.{settlement_status}",
            packet={
                "payment": dict(payment_record),
                "settlement": evidence,
                "provider_callback_authenticated": True,
                "settlement_authority": False,
            },
        )
        save_settlement = getattr(CORE_PLATFORM_STORE, "save_settlement_event", None)
        if not callable(save_settlement):
            raise HTTPException(
                status_code=503,
                detail="settlement_trust_store_unavailable",
            )
        if not save_settlement(
            provider=verified.provider,
            event_id=verified.event_id,
            payment_id=event.payment_id,
            provider_reference=event.provider_reference,
            settlement_status=settlement_status,
            payload=payload,
            receipt=trust_receipt,
        ):
            return {
                "status": "duplicate",
                "event_id": verified.event_id,
                "provider": verified.provider,
                "trust_action": "none",
            }
        return {
            "status": "received",
            "event_type": "payment.webhook.received",
            **evidence,
            "signature": signature.canonical(),
            "signature_verified": verify_packet_signature(evidence, signature),
            "trust_action": "settlement_event_ready",
            "settlement_authority": False,
            "settlement_trust": trust_receipt.canonical(),
            "trust_explorer": f"/trust/explorer/{trust_receipt.trust_id}",
        }

    return router


def _required_packet(identifier: str) -> dict[str, Any]:
    if identifier == "sandbox-demo":
        return _demo_packet(identifier)
    packet = _lookup_packet(identifier)
    if packet is None:
        raise HTTPException(status_code=404, detail="trust_not_found")
    return packet


def _audit_pdf_response(identifier: str) -> Response:
    packet = _required_packet(identifier)
    verification_url = f"https://api.afritechnology.com/trust/explorer/{identifier}"
    return Response(
        render_audit_pdf(packet, verification_url=verification_url),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="novatrust-{identifier}.pdf"'
        },
    )


def _demo_packet(identifier: str) -> dict[str, Any]:
    return {
        "identity": {
            "identity_id": "public-demo",
            "organization_id": "novatech-core",
        },
        "decision": {
            "decision": "ALLOW",
            "reason": "Public deterministic demo",
            "trace_id": identifier,
        },
        "payment": {
            "receipt_id": identifier,
            "status": "completed",
            "provider": "controlled-pilot",
        },
        "trust": {
            "trust_id": identifier,
            "replay_status": "verified",
            "event_hash": identifier,
        },
        "explanation": {"risk_level": "LOW", "recommended_action": "continue"},
        "proposal": {
            "lifecycle_state": "ready_for_validation",
            "proposal_id": "public-demo-proposal",
        },
    }


def _render_html(identifier: str, packet: dict[str, Any]) -> str:
    normalized = _normalize_packet_from_flow(packet)

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>NovaTrust Explorer</title>
</head>
<body>
  <h1>NovaTrust Explorer</h1>
  <p><strong>Identifier:</strong> {escape(identifier)}</p>
  <pre>{escape(str(normalized))}</pre>
</body>
</html>
"""


__all__ = [
    "CORE_PLATFORM_STORE",
    "build_core_platform_router",
    "build_public_trust_explorer_router",
    "core_platform_console_payload",
]
