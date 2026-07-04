"""NovaID interoperability standards manifests."""

from __future__ import annotations

from typing import Any


OAUTH_21_PROFILE: dict[str, Any] = {
    "name": "OAuth 2.1",
    "supported_grants": [
        "authorization_code",
        "refresh_token",
        "client_credentials",
        "device_code",
    ],
    "pkce_required": True,
    "token_endpoint_auth_methods": ["client_secret_basic", "private_key_jwt", "tls_client_auth"],
}

OPENID_CONNECT_PROFILE: dict[str, Any] = {
    "name": "OpenID Connect",
    "issuer_template": "https://identity.afritech.local/v1/novaid",
    "response_types_supported": ["code", "id_token", "code id_token"],
    "subject_types_supported": ["public"],
    "scopes_supported": ["openid", "profile", "email", "phone", "offline_access"],
    "claims_supported": [
        "sub",
        "email",
        "email_verified",
        "name",
        "given_name",
        "family_name",
        "phone_number",
        "address",
        "updated_at",
    ],
}

SAML_20_PROFILE: dict[str, Any] = {
    "name": "SAML 2.0",
    "entity_id": "https://identity.afritech.local/v1/novaid/saml",
    "bindings_supported": ["HTTP-Redirect", "HTTP-POST"],
    "name_id_formats": [
        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
    ],
}

FIDO2_WEBAUTHN_PROFILE: dict[str, Any] = {
    "name": "FIDO2 / WebAuthn",
    "resident_key_required": True,
    "user_verification": "required",
    "authenticator_attachment": ["platform", "cross-platform"],
    "attestation_formats": ["packed", "none"],
}

VERIFIABLE_CREDENTIALS_PROFILE: dict[str, Any] = {
    "name": "Verifiable Credentials",
    "credential_formats": ["jwt_vc", "sd-jwt-vc"],
    "proof_types": ["Ed25519Signature2020", "jwt"],
    "revocation_supported": True,
    "selective_disclosure_supported": True,
}


def build_standards_catalog() -> list[dict[str, Any]]:
    return [
        dict(OAUTH_21_PROFILE),
        dict(OPENID_CONNECT_PROFILE),
        dict(SAML_20_PROFILE),
        dict(FIDO2_WEBAUTHN_PROFILE),
        dict(VERIFIABLE_CREDENTIALS_PROFILE),
    ]
