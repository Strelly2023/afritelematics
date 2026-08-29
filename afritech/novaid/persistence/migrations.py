from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path
from typing import Any


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
    "0010_tenant_authorization.sql",
    "0011_device_attestation_authority.sql",
)

MIGRATION_DIRECTORY = Path(__file__).with_name("migrations")
MIGRATION_LOCK_ID = 7_314_920_021


def migration_checksum(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def apply_migrations(
    connection: Any,
    *,
    migration_directory: Path = MIGRATION_DIRECTORY,
) -> tuple[str, ...]:
    """Apply the canonical migration chain atomically under a PostgreSQL advisory lock."""
    paths = tuple(sorted(migration_directory.glob("*.sql")))
    revisions = tuple(path.name for path in paths)
    if migration_directory == MIGRATION_DIRECTORY and revisions != EXPECTED_REVISIONS:
        raise RuntimeError(f"novaid_migration_files_mismatch:{revisions!r}")

    try:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_ID,))
        connection.execute(
            "CREATE TABLE IF NOT EXISTS novaid_schema_migrations ("
            "revision text PRIMARY KEY,"
            "checksum text,"
            "applied_at timestamptz NOT NULL DEFAULT now()"
            ")"
        )
        connection.execute(
            "ALTER TABLE novaid_schema_migrations "
            "ADD COLUMN IF NOT EXISTS checksum text"
        )
        rows = connection.execute(
            "SELECT revision,checksum FROM novaid_schema_migrations"
        ).fetchall()
        applied = {
            str(_row_value(row, "revision", 0)): _row_value(row, "checksum", 1)
            for row in rows
        }

        for path in paths:
            revision = path.name
            checksum = migration_checksum(path)
            recorded_checksum = applied.get(revision)
            if recorded_checksum and str(recorded_checksum) != checksum:
                raise RuntimeError(f"novaid_migration_checksum_mismatch:{revision}")
            if revision in applied:
                if not recorded_checksum:
                    connection.execute(
                        "UPDATE novaid_schema_migrations SET checksum=%s "
                        "WHERE revision=%s",
                        (checksum, revision),
                    )
                continue

            connection.execute(path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO novaid_schema_migrations(revision,checksum) "
                "VALUES(%s,%s) ON CONFLICT(revision) DO UPDATE "
                "SET checksum=EXCLUDED.checksum",
                (revision, checksum),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return revisions


def verify_migration_revisions(connection) -> tuple[str, ...]:
    try:
        rows = connection.execute(
            "SELECT revision FROM novaid_schema_migrations ORDER BY revision"
        ).fetchall()
    except Exception as exc:
        raise RuntimeError("novaid_migration_ledger_missing") from exc
    actual = tuple(str(_row_value(row, "revision", 0)) for row in rows)
    if actual != EXPECTED_REVISIONS:
        raise RuntimeError(f"novaid_migration_revision_mismatch:{actual!r}")
    return actual


def _row_value(row: Any, key: str, index: int) -> Any:
    if isinstance(row, dict):
        return row[key]
    return row[index]


def main() -> int:
    """Apply and verify the migration ledger from the certified runtime image."""
    import psycopg

    dsn = os.environ.get("NOVAID_DATABASE_URL", "")
    if not dsn:
        raise RuntimeError("missing_novaid_postgres_url")
    with psycopg.connect(dsn) as connection:
        revisions = apply_migrations(connection)
        verified = verify_migration_revisions(connection)
    if revisions != verified:
        raise RuntimeError("novaid_migration_post_apply_verification_failed")
    print(f"NovaID migrations verified: {len(verified)} revisions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
