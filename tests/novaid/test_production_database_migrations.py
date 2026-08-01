import pytest

from afritech.novaid.persistence.migrations import (
    EXPECTED_REVISIONS,
    MIGRATION_DIRECTORY,
    migration_checksum,
)


def test_every_canonical_migration_is_ordered_and_checksummed() -> None:
    paths = tuple(sorted(MIGRATION_DIRECTORY.glob("*.sql")))

    assert tuple(path.name for path in paths) == EXPECTED_REVISIONS
    assert all(len(migration_checksum(path)) == 64 for path in paths)


def test_every_canonical_migration_records_its_revision() -> None:
    for revision in EXPECTED_REVISIONS:
        text = (MIGRATION_DIRECTORY / revision).read_text(encoding="utf-8")
        if revision == "0001_identity_core.sql":
            # The runner creates and records the ledger around the bootstrap revision.
            continue
        assert revision in text


def test_authorization_migration_uses_uuid_foreign_key_types() -> None:
    text = (MIGRATION_DIRECTORY / "0010_tenant_authorization.sql").read_text(
        encoding="utf-8"
    )

    assert "tenant_id TEXT" not in text
    assert "membership_id TEXT" not in text
    assert text.count("tenant_id UUID") == 5
    assert "membership_id UUID" in text


@pytest.mark.parametrize("statement", ("BEGIN;", "COMMIT;"))
def test_migrations_do_not_override_runner_transaction(statement: str) -> None:
    for path in MIGRATION_DIRECTORY.glob("*.sql"):
        lines = {
            line.strip().upper()
            for line in path.read_text(encoding="utf-8").splitlines()
        }
        assert statement not in lines, path.name
