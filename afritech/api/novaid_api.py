"""NovaID ecosystem API surfaces."""

from __future__ import annotations

from decimal import Decimal
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novaid import NovaIDEcosystem, NovaIDRepository, build_core_catalog, build_standards_catalog


def _service() -> NovaIDEcosystem:
    db_path = Path(os.environ.get("NOVAID_DB_PATH", ":memory:"))
    return NovaIDEcosystem(NovaIDRepository(db_path))


class StrictPayload(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def _reject_float_boundary(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, float):
                    raise ValueError("float_not_allowed")
        return data


class IdentityRequest(StrictPayload):
    identity_id: str
    organization_id: str
    email: str | None = None
    display_name: str | None = None
    identity_type: str = "person"
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    kyc_status: str = "pending"
    device_ids: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class PasskeyRequest(StrictPayload):
    identity_id: str
    organization_id: str
    credential_id: str
    public_key: str
    user_handle: str | None = None
    rp_id: str = "novaid.afritech.local"
    transport: str = "platform"
    attestation: str = "none"


class BiometricRequest(StrictPayload):
    identity_id: str
    organization_id: str
    modality: str
    confidence: Decimal
    verified: bool = True
    verifier: str = "device"


class DeviceRequest(StrictPayload):
    identity_id: str
    organization_id: str
    device_id: str
    public_key: str | None = None
    device_type: str = "mobile"
    attested: bool = True
    trust_level: str = "trusted"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CredentialIssueRequest(StrictPayload):
    subject_id: str
    organization_id: str
    credential_type: str
    claims: dict[str, Any] = Field(default_factory=dict)
    issuer: str = "NovaID"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CredentialRevokeRequest(StrictPayload):
    credential_id: str
    organization_id: str
    reason: str = "user_request"


class ConsentRequest(StrictPayload):
    subject_id: str
    organization_id: str
    purpose: str
    scopes: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)
    recipient: str | None = None


class ConsentRevokeRequest(StrictPayload):
    consent_id: str
    organization_id: str
    reason: str = "user_request"


class SharingRequest(StrictPayload):
    subject_id: str
    organization_id: str
    consent_id: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    recipient: str


class KycRequest(StrictPayload):
    subject_id: str
    organization_id: str
    risk_score: Decimal
    checks: list[str] = Field(default_factory=list)
    status: str = "verified"


class RecoveryRequest(StrictPayload):
    identity_id: str
    organization_id: str
    recovery_method: str
    evidence_refs: list[str] = Field(default_factory=list)


class SessionRequest(StrictPayload):
    identity_id: str
    organization_id: str
    device_id: str
    auth_method: str
    trust_level: str = "trusted"


class RiskRequest(StrictPayload):
    identity_id: str
    organization_id: str


class OAuthClientRequest(StrictPayload):
    organization_id: str
    client_name: str
    redirect_uris: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    grant_types: list[str] = Field(default_factory=lambda: ["authorization_code", "refresh_token"])
    pkce_required: bool = True
    client_type: str = "confidential"


class TrustRequest(StrictPayload):
    subject_id: str
    organization_id: str
    event_type: str
    packet: dict[str, Any] = Field(default_factory=dict)


class AuthorizeRequest(StrictPayload):
    identity_id: str
    organization_id: str
    action: str
    required_roles: list[str] = Field(default_factory=list)
    required_scopes: list[str] = Field(default_factory=list)
    resource_owner_id: str | None = None
    risk_score: Decimal = Decimal("0")


def build_novaid_router(service: NovaIDEcosystem | None = None) -> APIRouter:
    ecosystem = service or _service()
    router = APIRouter(prefix="/v1/novaid", tags=["novaid"])

    personal = require_roles("CUSTOMER", "OPERATOR", "ADMIN")
    business = require_roles("CLIENT", "PARTNER", "OPERATOR", "ADMIN")
    employee = require_roles("CUSTOMER", "OPERATOR", "ADMIN")
    partner = require_roles("PARTNER", "OPERATOR", "ADMIN")
    inspector = require_roles("VERIFIER", "OBSERVER", "OPERATOR", "ADMIN")
    government = require_roles("OPERATOR", "ADMIN")
    enterprise = require_roles("CLIENT", "OPERATOR", "ADMIN")
    developer = require_roles("DEVELOPER", "OPERATOR", "ADMIN")
    command_center = require_roles("OBSERVER", "OPERATOR", "ADMIN")
    surface_index = {surface["name"]: surface for surface in ecosystem.surfaces()}

    def _surface(name: str, view: str) -> dict[str, Any]:
        surface = surface_index.get(name)
        if surface is None:
            raise HTTPException(status_code=404, detail="surface_not_found")
        return {"view": view, "surface": surface}

    @router.get("/personal")
    def personal_app(claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return _surface("NovaID Personal App", "novaid_personal_app")

    @router.get("/wallet")
    def wallet_app(claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return _surface("NovaID Wallet", "novaid_wallet")

    @router.get("/business")
    def business_app(claims: JWTClaims = Depends(business)) -> dict[str, Any]:
        return _surface("NovaID Business App", "novaid_business_app")

    @router.get("/employee")
    def employee_app(claims: JWTClaims = Depends(employee)) -> dict[str, Any]:
        return _surface("NovaID Employee App", "novaid_employee_app")

    @router.get("/partner")
    def partner_app(claims: JWTClaims = Depends(partner)) -> dict[str, Any]:
        return _surface("NovaID Partner App", "novaid_partner_app")

    @router.post("/identities")
    def create_identity(payload: IdentityRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.register_identity(**payload.model_dump())

    @router.get("/identities/{identity_id}")
    def get_identity(identity_id: str, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        record = ecosystem.identity(identity_id)
        if record is None:
            raise HTTPException(status_code=404, detail="identity_not_found")
        return {"view": "novaid_identity", **record.payload}

    @router.post("/auth")
    def authenticate(payload: SessionRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        session = ecosystem.create_session(**payload.model_dump())
        trust = ecosystem.trust_receipt(
            subject_id=payload.identity_id,
            organization_id=payload.organization_id,
            event_type="novaid.auth.session.created",
            packet=session,
        )
        return {"view": "novaid_authentication", "session": session, "trust": trust}

    @router.post("/passkeys")
    def passkeys(payload: PasskeyRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.register_passkey(
            identity_id=payload.identity_id,
            organization_id=payload.organization_id,
            credential_id=payload.credential_id,
            public_key=payload.public_key,
            user_handle=payload.user_handle,
            rp_id=payload.rp_id,
            transport=payload.transport,
            attestation=payload.attestation,
        )

    @router.post("/biometrics")
    def biometrics(payload: BiometricRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.verify_biometric(**payload.model_dump())

    @router.post("/devices")
    def devices(payload: DeviceRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.register_device(**payload.model_dump())

    @router.get("/credentials")
    def credentials(claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return {
            "view": "novaid_credentials",
            "organization_id": claims.organization_id,
            "credentials": [record.payload for record in ecosystem.repository.list("novaid_credentials", organization_id=claims.organization_id)],
        }

    @router.post("/credentials/issue")
    def issue_credential(payload: CredentialIssueRequest, claims: JWTClaims = Depends(enterprise)) -> dict[str, Any]:
        return ecosystem.issue_credential(**payload.model_dump())

    @router.post("/credentials/revoke")
    def revoke_credential(payload: CredentialRevokeRequest, claims: JWTClaims = Depends(enterprise)) -> dict[str, Any]:
        return ecosystem.revoke_credential(**payload.model_dump())

    @router.post("/consent")
    def consent(payload: ConsentRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.grant_consent(
            subject_id=payload.subject_id,
            organization_id=payload.organization_id,
            purpose=payload.purpose,
            scopes=tuple(payload.scopes),
            attributes=tuple(payload.attributes),
            recipient=payload.recipient,
        )

    @router.post("/consent/revoke")
    def consent_revoke(payload: ConsentRevokeRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.revoke_consent(
            consent_id=payload.consent_id,
            organization_id=payload.organization_id,
            reason=payload.reason,
        )

    @router.post("/sharing")
    def sharing(payload: SharingRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.share_attributes(**payload.model_dump())

    @router.post("/kyc")
    def kyc(payload: KycRequest, claims: JWTClaims = Depends(government)) -> dict[str, Any]:
        return ecosystem.run_kyc(
            subject_id=payload.subject_id,
            organization_id=payload.organization_id,
            risk_score=payload.risk_score,
            checks=tuple(payload.checks),
            status=payload.status,
        )

    @router.post("/kyb")
    def kyb(payload: KycRequest, claims: JWTClaims = Depends(business)) -> dict[str, Any]:
        return ecosystem.run_kyb(
            subject_id=payload.subject_id,
            organization_id=payload.organization_id,
            risk_score=payload.risk_score,
            checks=tuple(payload.checks),
            status=payload.status,
        )

    @router.post("/recovery")
    def recovery(payload: RecoveryRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.recover_identity(
            identity_id=payload.identity_id,
            organization_id=payload.organization_id,
            recovery_method=payload.recovery_method,
            evidence_refs=tuple(payload.evidence_refs),
        )

    @router.get("/sessions")
    def sessions(claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return ecosystem.monitor_sessions(organization_id=claims.organization_id)

    @router.post("/sessions")
    def create_session(payload: SessionRequest, claims: JWTClaims = Depends(personal)) -> dict[str, Any]:
        return ecosystem.create_session(**payload.model_dump())

    @router.get("/risk")
    def risk(claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return {
            "view": "novaid_risk",
            "organization_id": claims.organization_id,
            "risk_events": [record.payload for record in ecosystem.repository.list("novaid_risk_events", organization_id=claims.organization_id)],
        }

    @router.post("/risk")
    def risk_explanation(payload: RiskRequest, claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return ecosystem.risk_explanation(identity_id=payload.identity_id, organization_id=payload.organization_id)

    @router.get("/federation")
    def federation(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return {
            "view": "novaid_federation",
            "openid_configuration": ecosystem.openid_configuration(),
            "saml_metadata": ecosystem.saml_metadata(),
        }

    @router.get("/directory")
    def directory(claims: JWTClaims = Depends(enterprise)) -> dict[str, Any]:
        return {
            "view": "novaid_directory",
            "organization_id": claims.organization_id,
            "entries": [record.payload for record in ecosystem.repository.list("novaid_directory_entries", organization_id=claims.organization_id)],
        }

    @router.post("/directory")
    def directory_create(payload: dict[str, Any], claims: JWTClaims = Depends(enterprise)) -> dict[str, Any]:
        record_id = str(payload.get("record_id", f"entry-{claims.sub}"))
        return ecosystem.repository.upsert(
            "novaid_directory_entries",
            record_id=record_id,
            organization_id=str(payload.get("organization_id", claims.organization_id)),
            status=str(payload.get("status", "active")),
            payload=dict(payload),
        ).payload

    @router.get("/developer")
    def developer_portal_view(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.developer_portal(organization_id=claims.organization_id)

    @router.post("/developer")
    def developer_register(payload: OAuthClientRequest, claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.register_oauth_client(
            organization_id=payload.organization_id,
            client_name=payload.client_name,
            redirect_uris=tuple(payload.redirect_uris),
            scopes=tuple(payload.scopes),
            grant_types=tuple(payload.grant_types),
            pkce_required=payload.pkce_required,
            client_type=payload.client_type,
        )

    @router.get("/developer/openid-configuration")
    def openid_configuration(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.openid_configuration()

    @router.get("/developer/saml-metadata")
    def saml_metadata(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.saml_metadata()

    @router.get("/government")
    def government_portal(claims: JWTClaims = Depends(government)) -> dict[str, Any]:
        return ecosystem.government_portal(organization_id=claims.organization_id)

    @router.get("/enterprise")
    def enterprise_portal(claims: JWTClaims = Depends(enterprise)) -> dict[str, Any]:
        return ecosystem.enterprise_portal(organization_id=claims.organization_id)

    @router.get("/inspector")
    def inspector_portal(claims: JWTClaims = Depends(inspector)) -> dict[str, Any]:
        return ecosystem.inspector_portal(organization_id=claims.organization_id)

    @router.post("/inspector")
    def inspector_offline(payload: dict[str, Any], claims: JWTClaims = Depends(inspector)) -> dict[str, Any]:
        try:
            return ecosystem.verify_inspector_offline(
                inspector_id=str(payload["inspector_id"]),
                organization_id=str(payload.get("organization_id", claims.organization_id)),
                certificate_id=str(payload["certificate_id"]),
                device_id=str(payload["device_id"]),
                evidence_hash=str(payload["evidence_hash"]),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/command-center")
    def command_center_portal(claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return ecosystem.command_center(organization_id=claims.organization_id)

    @router.get("/core")
    def core_catalog(claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return build_core_catalog()

    @router.get("/standards")
    def standards_catalog(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return {"view": "novaid_standards", "standards": build_standards_catalog()}

    @router.get("/trust")
    def trust_portal(claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return {
            "view": "novaid_trust",
            "organization_id": claims.organization_id,
            "trust_receipts": [record.payload for record in ecosystem.repository.list("novaid_trust_events", organization_id=claims.organization_id)],
        }

    @router.post("/trust")
    def trust_record(payload: TrustRequest, claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return ecosystem.trust_receipt(
            subject_id=payload.subject_id,
            organization_id=payload.organization_id,
            event_type=payload.event_type,
            packet=payload.packet,
        )

    @router.get("/apps")
    def app_surfaces(claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return {"view": "novaid_surfaces", "surfaces": ecosystem.surfaces()}

    @router.post("/authorize")
    def authorize(payload: AuthorizeRequest, claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return ecosystem.authorize_action(
            identity_id=payload.identity_id,
            organization_id=payload.organization_id,
            action=payload.action,
            required_roles=tuple(payload.required_roles),
            required_scopes=tuple(payload.required_scopes),
            resource_owner_id=payload.resource_owner_id,
            risk_score=payload.risk_score,
        )

    @router.post("/ai/advice")
    def ai_advice(payload: dict[str, Any], claims: JWTClaims = Depends(command_center)) -> dict[str, Any]:
        return ecosystem.ai_advice(
            subject_id=str(payload["subject_id"]),
            topic=str(payload.get("topic", "risk")),
            context=dict(payload.get("context", {})),
        )

    return router


__all__ = ["build_novaid_router"]
