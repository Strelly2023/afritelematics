"""Canonical NovaID domain catalog."""

from __future__ import annotations

CORE_DOMAINS: tuple[str, ...] = (
    "identity_lifecycle",
    "authentication",
    "passkeys",
    "biometrics",
    "device_trust",
    "credential_wallet",
    "credential_issuance",
    "credential_revocation",
    "consent",
    "identity_sharing",
    "kyc",
    "kyb",
    "federation",
    "directory",
    "recovery",
    "sessions",
    "risk",
    "audit",
)


def build_core_catalog() -> dict[str, object]:
    return {"view": "novaid_core_catalog", "domains": list(CORE_DOMAINS)}


__all__ = ["CORE_DOMAINS", "build_core_catalog"]
