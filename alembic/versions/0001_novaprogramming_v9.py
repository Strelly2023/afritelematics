"""NovaProgramming V9 canonical trust platform schema.

Revision ID: 0001_novaprogramming_v9
Revises: None
Create Date: 2026-06-20 09:30:00.000000
"""

from __future__ import annotations

from alembic import op  # type: ignore

from afritech.afriprogramming.v9.schema import build_v9_postgres_schema_sql, build_v9_rls_sql


revision = "0001_novaprogramming_v9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(build_v9_postgres_schema_sql(partition_count=4))
    op.execute(build_v9_rls_sql())


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS assurance_scheduler_runs CASCADE;
        DROP TABLE IF EXISTS trace_spans CASCADE;
        DROP TABLE IF EXISTS key_revocation_events CASCADE;
        DROP TABLE IF EXISTS certificate_transparency_log CASCADE;
        DROP TABLE IF EXISTS trust_consensus_votes CASCADE;
        DROP TABLE IF EXISTS trust_consensus_rounds CASCADE;
        """
    )
