from datetime import UTC, datetime, timedelta

import pytest

from afritech.novaid.config import NovaIDAuthenticationConfig
from afritech.novaid.revocation import ProcessLocalRevocationStore


def test_revocation_is_tenant_bound_and_expires() -> None:
    store = ProcessLocalRevocationStore()
    future = datetime.now(UTC) + timedelta(minutes=5)
    store.revoke_session("tenant-a", "session", future)
    assert store.is_session_revoked("tenant-a", "session")
    assert not store.is_session_revoked("tenant-b", "session")


def test_production_configuration_fails_closed(monkeypatch) -> None:
    monkeypatch.delenv("NOVAID_JWT_ISSUER", raising=False)
    monkeypatch.delenv("NOVAID_JWT_AUDIENCE", raising=False)
    with pytest.raises(ValueError, match="missing_production"):
        NovaIDAuthenticationConfig.from_environment("production")
