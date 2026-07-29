from __future__ import annotations

EXPECTED_REVISIONS = (
    "0001_identity_core.sql",
    "0002_novaid_runtime.sql",
    "0003_novaid_session_lifecycle.sql",
    "0004_novaid_webauthn.sql",
    "0005_novaid_webauthn_sessions_recovery.sql",
    "0006_novaid_webauthn_recovery_policy_distribution.sql",
    "0007_novaid_webauthn_distributed_runtime.sql",
    "0008_novaid_governed_audit_replay.sql",
    "0009_canonical_identity_profile.sql",
)


def verify_migration_revisions(connection) -> tuple[str, ...]:
    try:
        rows = connection.execute(
            "SELECT revision FROM novaid_schema_migrations ORDER BY revision"
        ).fetchall()
    except Exception as exc:
        raise RuntimeError("novaid_migration_ledger_missing") from exc
    actual = tuple(str(row["revision"]) for row in rows)
    if actual != EXPECTED_REVISIONS:
        raise RuntimeError(f"novaid_migration_revision_mismatch:{actual!r}")
    return actual
