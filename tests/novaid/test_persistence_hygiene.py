from uuid import UUID

from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork


class RecordingConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, statement: str, parameters: tuple[object, ...] = ()):
        self.calls.append((statement, parameters))
        return self


def test_postgres_policy_history_preserves_reason_and_uses_uuid() -> None:
    connection = RecordingConnection()
    uow = object.__new__(PostgresNovaIdUnitOfWork)
    uow.connection = connection

    uow.replace_tenant_webauthn_policy(
        "tenant-1",
        {
            "enabled": True,
            "passkeys_enabled": True,
            "passwordless_enabled": True,
            "phishing_resistant_step_up_required": True,
            "user_verification": "required",
            "attestation": "direct",
            "maximum_credentials": 5,
            "recovery_codes_enabled": True,
            "recovery_code_count": 10,
            "recovery_code_expiry_days": 30,
            "recovery_approval_count": 2,
            "recovery_requires_new_authenticator": True,
            "step_up_seconds": 300,
        },
        updated_by="admin-1",
        reason="SECURITY_BASELINE_UPDATE",
        version=2,
        updated_at="2026-07-29T00:00:00+00:00",
    )

    history_parameters = connection.calls[-1][1]
    UUID(str(history_parameters[0]))
    assert history_parameters[5] == "SECURITY_BASELINE_UPDATE"
