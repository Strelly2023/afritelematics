import json

import pytest

from afritech.novaid.runtime import validate_runtime_environment


BASE = {
    "NOVAID_DATABASE_URL": "postgresql://localhost/novaid",
    "NOVAID_JWT_ISSUER": "novaid",
    "NOVAID_JWT_AUDIENCE": "novaid-clients",
    "NOVAID_SIGNING_KEYS_JSON": json.dumps(
        {
            "2026-q2": "previous-signing-key-with-32-bytes-minimum",
            "2026-q3": "active-signing-key-with-at-least-32-bytes",
        }
    ),
    "NOVAID_ACTIVE_SIGNING_KEY_ID": "2026-q3",
    "NOVAID_TOKEN_ALGORITHM": "HS256",
    "NOVAID_REDIS_REQUIRED": "true",
    "NOVAID_REDIS_URL": "redis://localhost:56379/15",
}


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("NOVAID_DATABASE_URL", "", "missing_novaid_postgres_url"),
        ("NOVAID_DATABASE_URL", "sqlite:///unsafe.db", "invalid_novaid_postgres_url"),
        ("NOVAID_JWT_ISSUER", "", "missing_novaid_issuer"),
        ("NOVAID_JWT_AUDIENCE", "", "missing_novaid_audience"),
        ("NOVAID_JWT_AUDIENCE", "*", "wildcard_novaid_audience"),
        ("NOVAID_SIGNING_KEYS_JSON", "{}", "invalid_novaid_signing_key_registry"),
        (
            "NOVAID_ACTIVE_SIGNING_KEY_ID",
            "unknown",
            "invalid_novaid_signing_key_registry",
        ),
        ("NOVAID_TOKEN_ALGORITHM", "none", "unsupported_novaid_token_algorithm"),
        ("NOVAID_REDIS_URL", "", "required_novaid_redis_url_missing"),
    ],
)
def test_production_configuration_fails_closed(monkeypatch, name, value, message) -> None:
    for key, configured in BASE.items():
        monkeypatch.setenv(key, configured)
    monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError, match=message):
        validate_runtime_environment("production", "postgres")


def test_production_refuses_sqlite() -> None:
    with pytest.raises(RuntimeError, match="production_novaid_requires_postgres"):
        validate_runtime_environment("production", "sqlite")


def test_production_requires_rotation_registry(monkeypatch) -> None:
    for key, configured in BASE.items():
        monkeypatch.setenv(key, configured)
    monkeypatch.delenv("NOVAID_SIGNING_KEYS_JSON")
    monkeypatch.delenv("NOVAID_ACTIVE_SIGNING_KEY_ID")
    monkeypatch.setenv(
        "NOVAID_SIGNING_KEY",
        "legacy-single-key-is-no-longer-production-valid",
    )
    with pytest.raises(RuntimeError, match="missing_novaid_signing_key_registry"):
        validate_runtime_environment("production", "postgres")


def test_optional_redis_may_be_absent(monkeypatch) -> None:
    for key, configured in BASE.items():
        monkeypatch.setenv(key, configured)
    monkeypatch.setenv("NOVAID_REDIS_REQUIRED", "false")
    monkeypatch.delenv("NOVAID_REDIS_URL")
    validate_runtime_environment("production", "postgres")
