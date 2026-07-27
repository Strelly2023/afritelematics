from pathlib import Path


MIGRATION = (
    Path(__file__).parents[2]
    / "afritech"
    / "novaid"
    / "persistence"
    / "migrations"
    / "0009_canonical_identity_profile.sql"
)


def test_canonical_identity_migration_is_idempotent_by_contract() -> None:
    text = MIGRATION.read_text(encoding="utf-8")

    assert text.count("ADD COLUMN IF NOT EXISTS") == 10
    assert text.count("DO $$") == 3
    assert text.count(
        "conrelid = 'novaid_identities'::regclass"
    ) == 3
    assert text.count("CREATE INDEX IF NOT EXISTS") == 3

    for constraint in (
        "ck_novaid_identity_type",
        "ck_novaid_verification_status",
        "ck_novaid_assurance_level",
    ):
        assert constraint in text


def test_canonical_identity_migration_has_no_unguarded_constraints() -> None:
    text = MIGRATION.read_text(encoding="utf-8")

    constraint_section = text[
        text.index("DO $$"):
        text.index("CREATE INDEX IF NOT EXISTS")
    ]

    assert "IF NOT EXISTS (" in constraint_section
    assert constraint_section.count("ADD CONSTRAINT") == 3
