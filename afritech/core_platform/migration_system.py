"""Alembic-style migration runner for NovaTech core platform SQL migrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path
    sql: str

    def canonical(self) -> dict[str, str]:
        return {"version": self.version, "path": str(self.path), "sql": self.sql}


def list_migrations() -> list[Migration]:
    migrations: list[Migration] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        migrations.append(Migration(version=path.stem, path=path, sql=path.read_text(encoding="utf-8")))
    return migrations


def build_migration_plan(applied_versions: set[str] | None = None) -> dict[str, object]:
    applied_versions = applied_versions or set()
    migrations = list_migrations()
    pending = [migration for migration in migrations if migration.version not in applied_versions]
    return {
        "migration_system": "novatech_core_sql_migrations",
        "style": "alembic_compatible_linear_sql",
        "migrations": [migration.canonical() for migration in migrations],
        "pending": [migration.version for migration in pending],
    }


def apply_migrations(dsn: str) -> dict[str, object]:
    import psycopg

    applied: list[str] = []
    with psycopg.connect(dsn) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS novatech_core_schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        rows = conn.execute("SELECT version FROM novatech_core_schema_migrations").fetchall()
        existing = {str(row[0]) for row in rows}
        for migration in list_migrations():
            if migration.version in existing:
                continue
            conn.execute(migration.sql)
            conn.execute(
                "INSERT INTO novatech_core_schema_migrations(version) VALUES (%s)",
                (migration.version,),
            )
            applied.append(migration.version)
    return {"applied": applied, "count": len(applied)}
