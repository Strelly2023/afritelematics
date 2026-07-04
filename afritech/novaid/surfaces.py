"""Declarative NovaID surface manifests.

The surfaces are presentation-only. Identity authority stays in NovaID core.
"""

from __future__ import annotations

from typing import Any


APP_SURFACES: tuple[dict[str, Any], ...] = (
    {
        "name": "NovaID Personal App",
        "surface": "mobile",
        "role": "customer",
        "capabilities": [
            "digital_identity",
            "driver_licence",
            "passport",
            "national_id",
            "health_card",
            "student_card",
            "employee_id",
            "membership_cards",
            "credential_sharing",
            "biometric_login",
            "passkeys",
            "qr_authentication",
            "nfc_authentication",
            "consent_center",
            "device_trust",
            "login_history",
            "revocation",
        ],
        "endpoints": ["/v1/novaid/identities", "/v1/novaid/auth", "/v1/novaid/consent", "/v1/novaid/sharing"],
    },
    {
        "name": "NovaID Wallet",
        "surface": "mobile",
        "role": "customer",
        "capabilities": [
            "stored_credentials",
            "selective_disclosure",
            "trusted_sharing",
            "qr_login",
            "offline_wallet",
        ],
        "endpoints": ["/v1/novaid/credentials", "/v1/novaid/passkeys", "/v1/novaid/devices"],
    },
    {
        "name": "NovaID Business App",
        "surface": "web-mobile",
        "role": "client",
        "capabilities": [
            "company_identity",
            "kyb",
            "director_verification",
            "employee_verification",
            "business_certificates",
            "tax_identity",
            "digital_seal",
            "risk_profile",
        ],
        "endpoints": ["/v1/novaid/kyb", "/v1/novaid/enterprise", "/v1/novaid/directory"],
    },
    {
        "name": "NovaID Employee App",
        "surface": "mobile",
        "role": "customer",
        "capabilities": ["employee_id", "building_access", "attendance", "time_tracking", "hr_integration", "leave_requests", "corporate_wallet", "expense_claims"],
        "endpoints": ["/v1/novaid/identities", "/v1/novaid/enterprise", "/v1/novaid/sessions"],
    },
    {
        "name": "NovaID Partner App",
        "surface": "web-mobile",
        "role": "partner",
        "capabilities": ["organization_verification", "api_identity", "oauth_clients", "sdk_credentials", "partner_certificates", "trust_certificates"],
        "endpoints": ["/v1/novaid/developer", "/v1/novaid/federation", "/v1/novaid/trust"],
    },
    {
        "name": "NovaID Inspector App",
        "surface": "mobile",
        "role": "verifier",
        "capabilities": ["identity_verification", "qr_scanning", "offline_verification", "device_authentication", "certificate_validation", "inspection_records"],
        "endpoints": ["/v1/novaid/inspector", "/v1/novaid/trust", "/v1/novaid/devices"],
    },
    {
        "name": "NovaID Government Portal",
        "surface": "web",
        "role": "operator",
        "capabilities": ["citizen_registry", "population_management", "identity_verification", "elections_support", "social_services", "immigration", "licensing"],
        "endpoints": ["/v1/novaid/government", "/v1/novaid/directory", "/v1/novaid/identities"],
    },
    {
        "name": "NovaID Enterprise Portal",
        "surface": "web",
        "role": "client",
        "capabilities": ["identity_lifecycle", "user_provisioning", "access_control", "mfa", "device_trust", "federation", "directory", "rbac", "abac", "delegated_administration"],
        "endpoints": ["/v1/novaid/enterprise", "/v1/novaid/sessions", "/v1/novaid/risk"],
    },
    {
        "name": "NovaID Developer Portal",
        "surface": "web",
        "role": "developer",
        "capabilities": ["identity_apis", "oauth_management", "openid_connect", "sdks", "sandbox", "webhooks", "api_analytics", "contract_verification"],
        "endpoints": ["/v1/novaid/developer", "/v1/novaid/developer/openid-configuration", "/v1/novaid/developer/saml-metadata"],
    },
    {
        "name": "NovaID Command Center",
        "surface": "web",
        "role": "observer",
        "capabilities": ["verified_users", "organizations", "devices", "passkeys", "certificates", "risk_monitoring", "identity_events", "trust_status"],
        "endpoints": ["/v1/novaid/command-center", "/v1/novaid/trust", "/v1/novaid/risk"],
    },
)


def build_app_surfaces() -> list[dict[str, Any]]:
    return [dict(surface) for surface in APP_SURFACES]
