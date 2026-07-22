"""NovaRide environment gates and production startup assertions."""

from __future__ import annotations

import os
from urllib.parse import urlparse


NON_PRODUCTION_ENVIRONMENTS = frozenset({"local", "development", "test", "qa"})
PRODUCTION_ENVIRONMENTS = frozenset({"production", "prod"})
PLACEHOLDER_SECRETS = frozenset(
    {"secret", "password", "changeme", "change-me", "default-secret", "pilot-secret", "test"}
)


def app_environment() -> str:
    return os.environ.get("AFRIRIDE_ENV", "development").strip().lower()


def internal_qa_routes_enabled() -> bool:
    requested = os.environ.get("ENABLE_INTERNAL_QA_ROUTES", "false").lower() in {"1", "true", "yes"}
    environment = app_environment()
    if requested and environment in PRODUCTION_ENVIRONMENTS:
        raise RuntimeError("internal_qa_routes_forbidden_in_production")
    return requested and environment in NON_PRODUCTION_ENVIRONMENTS


def allowed_origins() -> list[str]:
    configured = [value.strip() for value in os.environ.get("AFRIRIDE_ALLOWED_ORIGINS", "").split(",") if value.strip()]
    if configured:
        return configured
    if app_environment() in PRODUCTION_ENVIRONMENTS:
        return []
    return ["http://localhost:5173", "http://localhost:3000"]


def assert_secure_startup() -> None:
    if app_environment() not in PRODUCTION_ENVIRONMENTS:
        return
    failures: list[str] = []
    secret = os.environ.get("AFRIRIDE_JWT_SECRET", "")
    if len(secret) < 32 or secret.lower() in PLACEHOLDER_SECRETS:
        failures.append("secure_jwt_signing_secret_required")
    if not os.environ.get("AFRIRIDE_JWT_ISSUER", "").strip():
        failures.append("jwt_issuer_required")
    if not os.environ.get("AFRIRIDE_JWT_AUDIENCE", "").strip():
        failures.append("jwt_audience_required")
    if os.environ.get("ENABLE_INTERNAL_QA_ROUTES", "false").lower() in {"1", "true", "yes"}:
        failures.append("internal_qa_routes_forbidden")
    if os.environ.get("AFRIRIDE_ENABLE_DEV_TOKEN_ISSUANCE", "false").lower() in {"1", "true", "yes"}:
        failures.append("development_token_issuance_forbidden")
    if os.environ.get("AFRIRIDE_DEBUG", "false").lower() in {"1", "true", "yes"}:
        failures.append("debug_mode_forbidden")
    if not os.environ.get("AFRIRIDE_IDENTITY_RECORDS_JSON", "").strip():
        failures.append("authoritative_identity_store_required")
    for name in ("AFRIRIDE_PUBLIC_URL", "AFRIRIDE_NOVAID_CALLBACK_URL", "AFRIRIDE_NOVAPAY_CALLBACK_URL"):
        value = os.environ.get(name, "").strip()
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.hostname in {"localhost", "127.0.0.1"}:
            failures.append(f"secure_{name.lower()}_required")
    origins = allowed_origins()
    if not origins or any(urlparse(origin).scheme != "https" for origin in origins):
        failures.append("https_allowed_origins_required")
    if failures:
        raise RuntimeError("insecure_production_configuration:" + ",".join(sorted(set(failures))))
