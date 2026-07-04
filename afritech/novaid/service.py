"""Governed NovaID ecosystem service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from afritech.core_platform.models import AuthorityRequest, Identity
from afritech.core_platform.services import NovaIDService, NovaPowerEngine, NovaTrustService

from .repository import NovaIDRecord, NovaIDRepository
from .standards import build_standards_catalog
from .surfaces import build_app_surfaces


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _money(value: Decimal | int | str) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.01')):.2f}"


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _record(record: NovaIDRecord) -> dict[str, Any]:
    return {
        "record_type": record.record_type,
        "record_id": record.record_id,
        "organization_id": record.organization_id,
        "status": record.status,
        "payload": record.payload,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        **record.payload,
    }


class NovaIDEcosystem:
    def __init__(
        self,
        repository: NovaIDRepository | None = None,
        *,
        novaid: NovaIDService | None = None,
        novapower: NovaPowerEngine | None = None,
        novatrust: NovaTrustService | None = None,
    ) -> None:
        self.repository = repository or NovaIDRepository(Path(":memory:"))
        self.novaid = novaid or NovaIDService()
        self.novapower = novapower or NovaPowerEngine()
        self.novatrust = novatrust or NovaTrustService()

    @classmethod
    def default(cls) -> "NovaIDEcosystem":
        return cls()

    def register_identity(
        self,
        *,
        identity_id: str,
        organization_id: str,
        email: str | None = None,
        display_name: str | None = None,
        identity_type: str = "person",
        roles: tuple[str, ...] = (),
        scopes: tuple[str, ...] = (),
        kyc_status: str = "pending",
        device_ids: tuple[str, ...] = (),
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = self.novaid.bind_identity(
            identity_id=identity_id,
            email=email or f"{identity_id}@novaid.local",
            roles=roles or (identity_type.upper(),),
            organization_id=organization_id,
            scopes=scopes,
            devices=device_ids,
            kyc_status=kyc_status,
        )
        payload = {
            "identity_id": identity_id,
            "identity": identity.canonical(),
            "display_name": display_name or identity_id,
            "identity_type": identity_type,
            "attributes": attributes or {},
            "verification_status": "unverified" if kyc_status != "verified" else "verified",
            "lifecycle_state": "active" if kyc_status == "verified" else "pending",
        }
        return _record(
            self.repository.upsert(
                "novaid_identities",
                record_id=identity_id,
                organization_id=organization_id,
                status=payload["lifecycle_state"],
                payload=payload,
            )
        )

    def verify_identity(
        self,
        *,
        identity_id: str,
        organization_id: str,
        method: str = "document+biometric",
        evidence_refs: tuple[str, ...] = (),
        verified_by: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = self.identity(identity_id)
        if identity is None:
            raise ValueError("identity_not_found")
        payload = dict(identity.payload)
        payload.update(
            {
                "verification_status": "verified",
                "lifecycle_state": "verified",
                "kyc_status": "verified",
                "verification_method": method,
                "verified_by": verified_by,
                "evidence_refs": list(evidence_refs),
                "metadata": metadata or {},
            }
        )
        trust = self.novatrust.record(
            subject_id=identity_id,
            organization_id=organization_id,
            event_type="novaid.identity.verified",
            packet={
                "identity_id": identity_id,
                "method": method,
                "evidence_refs": list(evidence_refs),
                "verified_by": verified_by,
                "metadata": metadata or {},
            },
        )
        payload["trust_receipt"] = trust.canonical()
        return _record(
            self.repository.upsert(
                "novaid_identities",
                record_id=identity_id,
                organization_id=organization_id,
                status="verified",
                payload=payload,
            )
        )

    def register_passkey(
        self,
        *,
        identity_id: str,
        organization_id: str,
        credential_id: str,
        public_key: str,
        user_handle: str | None = None,
        rp_id: str = "novaid.afritech.local",
        transport: str = "platform",
        attestation: str = "none",
    ) -> dict[str, Any]:
        payload = {
            "identity_id": identity_id,
            "credential_id": credential_id,
            "public_key": public_key,
            "user_handle": user_handle or identity_id,
            "rp_id": rp_id,
            "transport": transport,
            "attestation": attestation,
            "status": "active",
        }
        return _record(
            self.repository.upsert(
                "novaid_passkeys",
                record_id=credential_id,
                organization_id=organization_id,
                status="active",
                payload=payload,
            )
        )

    def verify_biometric(
        self,
        *,
        identity_id: str,
        organization_id: str,
        modality: str,
        confidence: Decimal | int | str,
        verified: bool = True,
        verifier: str = "device",
    ) -> dict[str, Any]:
        payload = {
            "identity_id": identity_id,
            "modality": modality,
            "confidence": _money(confidence),
            "verified": verified,
            "verifier": verifier,
        }
        return _record(
            self.repository.upsert(
                "novaid_biometric_events",
                record_id=f"bio-{identity_id}-{modality}",
                organization_id=organization_id,
                status="verified" if verified else "rejected",
                payload=payload,
            )
        )

    def register_device(
        self,
        *,
        identity_id: str,
        organization_id: str,
        device_id: str,
        public_key: str | None = None,
        device_type: str = "mobile",
        attested: bool = True,
        trust_level: str = "trusted",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = self.identity(identity_id)
        if identity is None:
            raise ValueError("identity_not_found")
        devices = set(identity.payload.get("identity", {}).get("devices", []))
        devices.add(device_id)
        payload = {
            "identity_id": identity_id,
            "device_id": device_id,
            "device_type": device_type,
            "public_key": public_key,
            "attested": attested,
            "trust_level": trust_level,
            "metadata": metadata or {},
        }
        self.repository.upsert(
            "novaid_identities",
            record_id=identity_id,
            organization_id=organization_id,
            status=identity.status,
            payload={**identity.payload, "identity": {**identity.payload["identity"], "devices": sorted(devices)}},
        )
        return _record(
            self.repository.upsert(
                "novaid_devices",
                record_id=device_id,
                organization_id=organization_id,
                status=trust_level,
                payload=payload,
            )
        )

    def issue_credential(
        self,
        *,
        subject_id: str,
        organization_id: str,
        credential_type: str,
        claims: dict[str, Any],
        issuer: str = "NovaID",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        credential_id = f"cred-{uuid4().hex[:12]}"
        packet = {
            "credential_id": credential_id,
            "subject_id": subject_id,
            "organization_id": organization_id,
            "credential_type": credential_type,
            "claims": claims,
            "issuer": issuer,
            "metadata": metadata or {},
            "status": "issued",
        }
        trust = self.novatrust.record(
            subject_id=subject_id,
            organization_id=organization_id,
            event_type="novaid.credential.issued",
            packet=packet,
        )
        packet["trust_receipt"] = trust.canonical()
        return _record(
            self.repository.upsert(
                "novaid_credentials",
                record_id=credential_id,
                organization_id=organization_id,
                status="issued",
                payload=packet,
            )
        )

    def revoke_credential(
        self,
        *,
        credential_id: str,
        organization_id: str,
        reason: str = "user_request",
    ) -> dict[str, Any]:
        credential = self.repository.get("novaid_credentials", credential_id)
        if credential is None:
            raise ValueError("credential_not_found")
        payload = dict(credential.payload)
        payload.update({"status": "revoked", "revoked_reason": reason, "revoked_at": _now()})
        return _record(
            self.repository.upsert(
                "novaid_credentials",
                record_id=credential_id,
                organization_id=organization_id,
                status="revoked",
                payload=payload,
            )
        )

    def grant_consent(
        self,
        *,
        subject_id: str,
        organization_id: str,
        purpose: str,
        scopes: tuple[str, ...],
        attributes: tuple[str, ...] = (),
        recipient: str | None = None,
        consent_id: str | None = None,
    ) -> dict[str, Any]:
        consent_id = consent_id or f"consent-{uuid4().hex[:12]}"
        payload = {
            "subject_id": subject_id,
            "purpose": purpose,
            "scopes": list(scopes),
            "attributes": list(attributes),
            "recipient": recipient,
            "status": "granted",
            "granted_at": _now(),
        }
        return _record(
            self.repository.upsert(
                "novaid_consents",
                record_id=consent_id,
                organization_id=organization_id,
                status="granted",
                payload=payload,
            )
        )

    def revoke_consent(
        self,
        *,
        consent_id: str,
        organization_id: str,
        reason: str = "user_request",
    ) -> dict[str, Any]:
        consent = self.repository.get("novaid_consents", consent_id)
        if consent is None:
            raise ValueError("consent_not_found")
        payload = dict(consent.payload)
        payload.update({"status": "revoked", "revoked_reason": reason, "revoked_at": _now()})
        return _record(
            self.repository.upsert(
                "novaid_consents",
                record_id=consent_id,
                organization_id=organization_id,
                status="revoked",
                payload=payload,
            )
        )

    def share_attributes(
        self,
        *,
        subject_id: str,
        organization_id: str,
        consent_id: str,
        attributes: dict[str, Any],
        recipient: str,
    ) -> dict[str, Any]:
        consent = self.repository.get("novaid_consents", consent_id)
        if consent is None or consent.status != "granted":
            raise ValueError("consent_required")
        selected = {
            key: value
            for key, value in attributes.items()
            if key in set(consent.payload.get("attributes", []))
            or key in set(consent.payload.get("scopes", []))
        }
        payload = {
            "subject_id": subject_id,
            "consent_id": consent_id,
            "recipient": recipient,
            "attributes": selected,
            "shared_at": _now(),
            "status": "shared",
        }
        trust = self.novatrust.record(
            subject_id=subject_id,
            organization_id=organization_id,
            event_type="novaid.attributes.shared",
            packet=payload,
        )
        payload["trust_receipt"] = trust.canonical()
        return payload

    def run_kyc(
        self,
        *,
        subject_id: str,
        organization_id: str,
        risk_score: Decimal | int | str,
        checks: tuple[str, ...],
        status: str = "verified",
    ) -> dict[str, Any]:
        payload = {
            "subject_id": subject_id,
            "checks": list(checks),
            "risk_score": _money(risk_score),
            "status": status,
            "reviewed_at": _now(),
        }
        identity = self.identity(subject_id)
        base_payload = identity.payload if identity else {}
        return _record(
            self.repository.upsert(
                "novaid_identities",
                record_id=subject_id,
                organization_id=organization_id,
                status="verified" if status == "verified" else "pending",
                payload={**base_payload, "kyc": payload},
            )
        )

    def run_kyb(
        self,
        *,
        subject_id: str,
        organization_id: str,
        risk_score: Decimal | int | str,
        checks: tuple[str, ...],
        status: str = "verified",
    ) -> dict[str, Any]:
        payload = {
            "subject_id": subject_id,
            "checks": list(checks),
            "risk_score": _money(risk_score),
            "status": status,
            "reviewed_at": _now(),
        }
        identity = self.identity(subject_id)
        base_payload = identity.payload if identity else {}
        return _record(
            self.repository.upsert(
                "novaid_identities",
                record_id=subject_id,
                organization_id=organization_id,
                status="verified" if status == "verified" else "pending",
                payload={**base_payload, "kyb": payload},
            )
        )

    def provision_employee(
        self,
        *,
        employee_id: str,
        organization_id: str,
        employer_id: str,
        department: str,
        access_roles: tuple[str, ...] = (),
        expense_wallet_enabled: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = self.register_identity(
            identity_id=employee_id,
            organization_id=organization_id,
            identity_type="employee",
            roles=("CUSTOMER",),
            kyc_status="verified",
            display_name=employee_id,
        )
        payload = {
            "identity_id": employee_id,
            "employer_id": employer_id,
            "department": department,
            "access_roles": list(access_roles),
            "expense_wallet_enabled": expense_wallet_enabled,
            "status": "provisioned",
            "metadata": metadata or {},
            "identity": identity,
        }
        return _record(
            self.repository.upsert(
                "novaid_directory_entries",
                record_id=employee_id,
                organization_id=organization_id,
                status="provisioned",
                payload=payload,
            )
        )

    def register_partner_certificate(
        self,
        *,
        partner_id: str,
        organization_id: str,
        certificate_name: str,
        scopes: tuple[str, ...],
        valid_until: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        certificate_id = f"partner-cert-{uuid4().hex[:12]}"
        payload = {
            "partner_id": partner_id,
            "certificate_name": certificate_name,
            "scopes": list(scopes),
            "valid_until": valid_until,
            "status": "active",
            "metadata": metadata or {},
        }
        trust = self.novatrust.record(
            subject_id=partner_id,
            organization_id=organization_id,
            event_type="novaid.partner.certificate.issued",
            packet=payload,
        )
        payload["trust_receipt"] = trust.canonical()
        return _record(
            self.repository.upsert(
                "novaid_credentials",
                record_id=certificate_id,
                organization_id=organization_id,
                status="active",
                payload=payload,
            )
        )

    def verify_inspector_offline(
        self,
        *,
        inspector_id: str,
        organization_id: str,
        certificate_id: str,
        device_id: str,
        evidence_hash: str,
    ) -> dict[str, Any]:
        certificate = self.repository.get("novaid_credentials", certificate_id)
        verified = bool(certificate and certificate.status == "active")
        payload = {
            "inspector_id": inspector_id,
            "certificate_id": certificate_id,
            "device_id": device_id,
            "evidence_hash": evidence_hash,
            "verified": verified,
            "offline_mode": True,
            "verified_at": _now(),
        }
        trust = self.novatrust.record(
            subject_id=inspector_id,
            organization_id=organization_id,
            event_type="novaid.inspector.offline.verification",
            packet=payload,
        )
        payload["trust_receipt"] = trust.canonical()
        return payload

    def register_oauth_client(
        self,
        *,
        organization_id: str,
        client_name: str,
        redirect_uris: tuple[str, ...],
        scopes: tuple[str, ...],
        grant_types: tuple[str, ...] = ("authorization_code", "refresh_token"),
        pkce_required: bool = True,
        client_type: str = "confidential",
    ) -> dict[str, Any]:
        client_id = f"client-{uuid4().hex[:12]}"
        client_secret = f"secret-{uuid4().hex[:24]}"
        payload = {
            "client_name": client_name,
            "redirect_uris": list(redirect_uris),
            "scopes": list(scopes),
            "grant_types": list(grant_types),
            "pkce_required": pkce_required,
            "client_type": client_type,
            "client_secret_hint": client_secret[:6],
            "status": "active",
        }
        return _record(
            self.repository.upsert(
                "novaid_oauth_clients",
                record_id=client_id,
                organization_id=organization_id,
                status="active",
                payload=payload,
            )
        )

    def openid_configuration(self) -> dict[str, Any]:
        return {
            "issuer": "https://identity.afritech.local/v1/novaid",
            "authorization_endpoint": "/v1/novaid/auth",
            "token_endpoint": "/v1/novaid/auth",
            "userinfo_endpoint": "/v1/novaid/identities",
            "jwks_uri": "/v1/novaid/developer/jwks.json",
            "response_types_supported": ["code", "id_token", "code id_token"],
            "subject_types_supported": ["public"],
            "scopes_supported": ["openid", "profile", "email", "phone", "offline_access"],
            "claims_supported": ["sub", "email", "name", "given_name", "family_name", "phone_number", "updated_at"],
            "pkce_required": True,
        }

    def saml_metadata(self) -> dict[str, Any]:
        xml = """<EntityDescriptor entityID="https://identity.afritech.local/v1/novaid/saml">
  <SPSSODescriptor>
    <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</NameIDFormat>
    <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:persistent</NameIDFormat>
  </SPSSODescriptor>
</EntityDescriptor>"""
        return {
            "entity_id": "https://identity.afritech.local/v1/novaid/saml",
            "assertion_consumer_service": "/v1/novaid/federation/saml/acs",
            "single_logout_service": "/v1/novaid/federation/saml/slo",
            "name_id_formats": [
                "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
            ],
            "metadata_xml": xml,
        }

    def create_session(
        self,
        *,
        identity_id: str,
        organization_id: str,
        device_id: str,
        auth_method: str,
        trust_level: str = "trusted",
        expires_in_seconds: int = 43_200,
    ) -> dict[str, Any]:
        session_id = f"session-{uuid4().hex[:12]}"
        payload = {
            "identity_id": identity_id,
            "device_id": device_id,
            "auth_method": auth_method,
            "trust_level": trust_level,
            "status": "active",
            "last_seen_at": _now(),
            "expires_in_seconds": expires_in_seconds,
        }
        return _record(
            self.repository.upsert(
                "novaid_sessions",
                record_id=session_id,
                organization_id=organization_id,
                status="active",
                payload=payload,
            )
        )

    def monitor_sessions(self, *, organization_id: str, subject_id: str | None = None) -> dict[str, Any]:
        sessions = self.repository.list("novaid_sessions", organization_id=organization_id)
        if subject_id is not None:
            sessions = [session for session in sessions if session.payload.get("identity_id") == subject_id]
        return {
            "view": "novaid_session_monitoring",
            "organization_id": organization_id,
            "sessions": [session.payload for session in sessions],
            "active_sessions": sum(1 for session in sessions if session.status == "active"),
        }

    def recover_identity(
        self,
        *,
        identity_id: str,
        organization_id: str,
        recovery_method: str,
        evidence_refs: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        identity = self.identity(identity_id)
        if identity is None:
            raise ValueError("identity_not_found")
        payload = dict(identity.payload)
        payload.update(
            {
                "recovery": {
                    "method": recovery_method,
                    "evidence_refs": list(evidence_refs),
                    "recovered_at": _now(),
                    "status": "verified",
                },
                "lifecycle_state": "recovered",
                "verification_status": "verified",
            }
        )
        trust = self.novatrust.record(
            subject_id=identity_id,
            organization_id=organization_id,
            event_type="novaid.identity.recovered",
            packet=payload["recovery"],
        )
        payload["recovery"]["trust_receipt"] = trust.canonical()
        return _record(
            self.repository.upsert(
                "novaid_recovery_events",
                record_id=f"recovery-{identity_id}",
                organization_id=organization_id,
                status="verified",
                payload=payload["recovery"],
            )
        )

    def risk_explanation(
        self,
        *,
        identity_id: str,
        organization_id: str,
    ) -> dict[str, Any]:
        identity = self.identity(identity_id)
        if identity is None:
            raise ValueError("identity_not_found")
        kyc = identity.payload.get("kyc", {})
        risk_score = Decimal(str(kyc.get("risk_score", "0.25")))
        reasons = []
        if identity.status != "verified":
            reasons.append("identity_not_verified")
            risk_score += Decimal("0.25")
        if not identity.payload.get("identity", {}).get("devices"):
            reasons.append("no_trusted_device")
            risk_score += Decimal("0.10")
        if not identity.payload.get("consents"):
            reasons.append("no_active_consents")
            risk_score += Decimal("0.05")
        confidence = min(Decimal("0.99"), Decimal("0.70") + (Decimal("0.05") * len(reasons)))
        summary = "Identity is low risk." if not reasons else "Identity requires review."
        payload = {
            "identity_id": identity_id,
            "risk_score": _money(risk_score),
            "reasons": reasons,
            "summary": summary,
            "confidence": _money(confidence),
        }
        self.repository.upsert(
            "novaid_risk_events",
            record_id=f"risk-{identity_id}",
            organization_id=organization_id,
            status="review" if reasons else "clear",
            payload=payload,
        )
        return payload

    def command_center(self, *, organization_id: str) -> dict[str, Any]:
        identities = self.repository.list("novaid_identities", organization_id=organization_id)
        devices = self.repository.list("novaid_devices", organization_id=organization_id)
        passkeys = self.repository.list("novaid_passkeys", organization_id=organization_id)
        sessions = self.repository.list("novaid_sessions", organization_id=organization_id)
        return {
            "view": "novaid_command_center",
            "organization_id": organization_id,
            "verified_identities": sum(1 for identity in identities if identity.status == "verified"),
            "devices": len(devices),
            "passkeys": len(passkeys),
            "active_sessions": sum(1 for session in sessions if session.status == "active"),
            "trust_status": "healthy" if identities else "idle",
        }

    def developer_portal(self, *, organization_id: str) -> dict[str, Any]:
        clients = self.repository.list("novaid_oauth_clients", organization_id=organization_id)
        return {
            "view": "novaid_developer_portal",
            "organization_id": organization_id,
            "standards": build_standards_catalog(),
            "oauth_clients": [client.payload for client in clients],
        }

    def government_portal(self, *, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novaid_government_portal",
            "organization_id": organization_id,
            "registry": self.repository.list("novaid_identities", organization_id=organization_id),
            "lifecycle": "governed",
        }

    def enterprise_portal(self, *, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novaid_enterprise_portal",
            "organization_id": organization_id,
            "directory": [entry.payload for entry in self.repository.list("novaid_directory_entries", organization_id=organization_id)],
            "sessions": [session.payload for session in self.repository.list("novaid_sessions", organization_id=organization_id)],
        }

    def inspector_portal(self, *, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novaid_inspector_portal",
            "organization_id": organization_id,
            "offline_verification": True,
            "certificate_validation": True,
            "inspection_records": [record.payload for record in self.repository.list("novaid_credentials", organization_id=organization_id)],
        }

    def trust_receipt(self, *, subject_id: str, organization_id: str, event_type: str, packet: dict[str, Any]) -> dict[str, Any]:
        receipt = self.novatrust.record(
            subject_id=subject_id,
            organization_id=organization_id,
            event_type=event_type,
            packet=packet,
        )
        payload = {
            "receipt": receipt.canonical(),
            "verified": self.novatrust.replay(receipt),
        }
        self.repository.upsert(
            "novaid_trust_events",
            record_id=receipt.trust_id,
            organization_id=organization_id,
            status="verified" if payload["verified"] else "failed",
            payload={
                "subject_id": subject_id,
                "event_type": event_type,
                "packet": packet,
                "receipt": receipt.canonical(),
                "verified": payload["verified"],
            },
        )
        return payload

    def authorize_action(
        self,
        *,
        identity_id: str,
        organization_id: str,
        action: str,
        required_roles: tuple[str, ...] = (),
        required_scopes: tuple[str, ...] = (),
        resource_owner_id: str | None = None,
        risk_score: Decimal | int | str = "0",
    ) -> dict[str, Any]:
        identity_record = self.identity(identity_id)
        if identity_record is None:
            raise ValueError("identity_not_found")
        identity_data = dict(identity_record.payload.get("identity", {}))
        identity = Identity(
            identity_id=str(identity_data.get("identity_id", identity_record.record_id)),
            email=str(identity_data.get("email", "")),
            roles=tuple(identity_data.get("roles", ())),
            organization_id=str(identity_data.get("organization_id", organization_id)),
            scopes=tuple(identity_data.get("scopes", ())),
            devices=tuple(identity_data.get("devices", ())),
            kyc_status=str(identity_data.get("kyc_status", "unverified")),
        )
        request = AuthorityRequest(
            action=action,
            organization_id=organization_id,
            required_roles=required_roles,
            required_scopes=required_scopes,
            resource_owner_id=resource_owner_id,
            risk_score=Decimal(str(risk_score)),
        )
        decision = self.novapower.evaluate(request, identity=identity)
        return {"request": request.canonical(), "decision": decision.canonical()}

    def ai_advice(self, *, subject_id: str, topic: str, context: dict[str, Any]) -> dict[str, Any]:
        identity = self.identity(subject_id)
        if identity is None:
            raise ValueError("identity_not_found")
        recommendation = "Review and continue"
        if topic == "risk":
            recommendation = "Verify evidence before any approval"
        elif topic == "recovery":
            recommendation = "Escalate to the recovery workflow"
        return {
            "view": "novaid_ai_advisory",
            "subject_id": subject_id,
            "topic": topic,
            "recommendation": recommendation,
            "confidence": "0.91",
            "context": context,
            "advisory_only": True,
        }

    def identity(self, identity_id: str) -> NovaIDRecord | None:
        return self.repository.get("novaid_identities", identity_id)

    def surfaces(self) -> list[dict[str, Any]]:
        return build_app_surfaces()
