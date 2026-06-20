from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Iterable

from afritech.afriprogramming.persistence import PlatformStore


V9_PARTITIONED_TABLES: tuple[str, ...] = (
    "trust_consensus_rounds",
    "trust_consensus_votes",
    "certificate_transparency_log",
    "key_revocation_events",
    "trace_spans",
    "assurance_scheduler_runs",
)


V9_ROW_LEVEL_TABLES: tuple[str, ...] = (
    "trust_consensus_rounds",
    "trust_consensus_votes",
    "certificate_transparency_log",
    "key_revocation_events",
    "trace_spans",
    "assurance_scheduler_runs",
)


@dataclass(frozen=True)
class V9SchemaBundle:
    partition_count: int
    schema_sql: str
    rls_sql: str
    tables: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "partition_count": self.partition_count,
            "tables": self.tables,
            "schema_sql": self.schema_sql,
            "rls_sql": self.rls_sql,
        }


def _table_sql(
    table_name: str,
    partitioned: bool,
    columns: str,
    primary_key: str | None = None,
    unique_constraints: tuple[str, ...] = (),
) -> str:
    partition_clause = " PARTITION BY HASH (organization_id)" if partitioned else ""
    key_clauses = []
    if primary_key:
        key_clauses.append(f"PRIMARY KEY ({primary_key})")
    key_clauses.extend(f"UNIQUE ({constraint})" for constraint in unique_constraints)
    key_sql = ",\n            ".join(key_clauses)
    if key_sql:
        key_sql = ",\n            " + key_sql
    return dedent(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns}{key_sql}
        ){partition_clause};
        """
    ).strip()


def _partition_sql(table_name: str, partition_count: int) -> list[str]:
    statements: list[str] = []
    for remainder in range(partition_count):
        statements.append(
            dedent(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name}_p{remainder}
                PARTITION OF {table_name}
                FOR VALUES WITH (MODULUS {partition_count}, REMAINDER {remainder});
                """
            ).strip()
        )
    return statements


def build_v9_postgres_schema_sql(partition_count: int = 4) -> str:
    statements = [
        _table_sql(
            "trust_consensus_rounds",
            True,
            """
            round_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            proposal_hash TEXT NOT NULL,
            proposal_json JSONB NOT NULL,
            quorum_required INTEGER NOT NULL,
            yes_votes INTEGER NOT NULL,
            no_votes INTEGER NOT NULL,
            abstain_votes INTEGER NOT NULL,
            weighted_yes REAL NOT NULL,
            weighted_no REAL NOT NULL,
            decision TEXT NOT NULL,
            consensus_hash TEXT NOT NULL,
            region_count INTEGER NOT NULL,
            latency_ms INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            primary_key="organization_id, round_id",
            unique_constraints=("organization_id, consensus_hash",),
        ),
        _table_sql(
            "trust_consensus_votes",
            True,
            """
            vote_id TEXT NOT NULL,
            round_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            region_id TEXT NOT NULL,
            vote TEXT NOT NULL,
            weight REAL NOT NULL,
            signature TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            primary_key="organization_id, vote_id",
        ),
        _table_sql(
            "certificate_transparency_log",
            True,
            """
            log_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            certificate_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            issuer TEXT NOT NULL,
            certificate_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            signature TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            primary_key="organization_id, log_id",
            unique_constraints=("organization_id, certificate_hash", "organization_id, chain_hash"),
        ),
        _table_sql(
            "key_revocation_events",
            True,
            """
            revocation_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            key_id TEXT NOT NULL,
            key_family TEXT NOT NULL,
            key_version INTEGER NOT NULL,
            reason TEXT NOT NULL,
            revoked_by TEXT NOT NULL,
            status TEXT NOT NULL,
            certificate_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            primary_key="organization_id, revocation_id",
        ),
        _table_sql(
            "trace_spans",
            True,
            """
            span_id TEXT NOT NULL,
            trace_id TEXT NOT NULL,
            parent_span_id TEXT,
            organization_id TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            operation_name TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            status_code INTEGER NOT NULL,
            policy_decision_id TEXT,
            proof_hash TEXT,
            deployment_id TEXT,
            attributes_json JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            primary_key="organization_id, span_id",
        ),
        _table_sql(
            "assurance_scheduler_runs",
            True,
            """
            scheduler_run_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            scheduled_at TIMESTAMPTZ NOT NULL,
            executed_at TIMESTAMPTZ NOT NULL,
            status TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            drift INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            notes TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """,
            primary_key="organization_id, scheduler_run_id",
        ),
    ]
    statements.extend(_partition_sql("trust_consensus_rounds", partition_count))
    statements.extend(_partition_sql("trust_consensus_votes", partition_count))
    statements.extend(_partition_sql("certificate_transparency_log", partition_count))
    statements.extend(_partition_sql("key_revocation_events", partition_count))
    statements.extend(_partition_sql("trace_spans", partition_count))
    statements.extend(_partition_sql("assurance_scheduler_runs", partition_count))
    statements.extend(
        [
            "CREATE INDEX IF NOT EXISTS idx_v9_consensus_rounds_org_created ON trust_consensus_rounds (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_consensus_votes_round_created ON trust_consensus_votes (round_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_ct_log_org_created ON certificate_transparency_log (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_key_revocations_org_created ON key_revocation_events (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_trace_spans_org_created ON trace_spans (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_scheduler_runs_org_created ON assurance_scheduler_runs (organization_id, created_at DESC);",
        ]
    )
    return "\n".join(statements)


def build_v9_sqlite_schema_sql() -> str:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS trust_consensus_rounds (
            round_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            proposal_hash TEXT NOT NULL,
            proposal_json TEXT NOT NULL,
            quorum_required INTEGER NOT NULL,
            yes_votes INTEGER NOT NULL,
            no_votes INTEGER NOT NULL,
            abstain_votes INTEGER NOT NULL,
            weighted_yes REAL NOT NULL,
            weighted_no REAL NOT NULL,
            decision TEXT NOT NULL,
            consensus_hash TEXT NOT NULL,
            region_count INTEGER NOT NULL,
            latency_ms INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (organization_id, round_id),
            UNIQUE (organization_id, consensus_hash)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trust_consensus_votes (
            vote_id TEXT NOT NULL,
            round_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            region_id TEXT NOT NULL,
            vote TEXT NOT NULL,
            weight REAL NOT NULL,
            signature TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (organization_id, vote_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS certificate_transparency_log (
            log_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            certificate_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            issuer TEXT NOT NULL,
            certificate_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            signature TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (organization_id, log_id),
            UNIQUE (organization_id, certificate_hash),
            UNIQUE (organization_id, chain_hash)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS key_revocation_events (
            revocation_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            key_id TEXT NOT NULL,
            key_family TEXT NOT NULL,
            key_version INTEGER NOT NULL,
            reason TEXT NOT NULL,
            revoked_by TEXT NOT NULL,
            status TEXT NOT NULL,
            certificate_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (organization_id, revocation_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trace_spans (
            span_id TEXT NOT NULL,
            trace_id TEXT NOT NULL,
            parent_span_id TEXT,
            organization_id TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            operation_name TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            status_code INTEGER NOT NULL,
            policy_decision_id TEXT,
            proof_hash TEXT,
            deployment_id TEXT,
            attributes_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (organization_id, span_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS assurance_scheduler_runs (
            scheduler_run_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            executed_at TEXT NOT NULL,
            status TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            drift INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (organization_id, scheduler_run_id)
        );
        """,
    ]
    statements.extend(
        [
            "CREATE INDEX IF NOT EXISTS idx_v9_consensus_rounds_org_created ON trust_consensus_rounds (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_consensus_votes_round_created ON trust_consensus_votes (round_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_ct_log_org_created ON certificate_transparency_log (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_key_revocations_org_created ON key_revocation_events (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_trace_spans_org_created ON trace_spans (organization_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_v9_scheduler_runs_org_created ON assurance_scheduler_runs (organization_id, created_at DESC);",
        ]
    )
    return "\n".join(statements)


def build_v9_rls_sql(tables: Iterable[str] | None = None) -> str:
    selected = tuple(tables or V9_ROW_LEVEL_TABLES)
    statements: list[str] = []
    for table in selected:
        policy = f"{table}_organization_isolation"
        statements.append(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        statements.append(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        statements.append(f"DROP POLICY IF EXISTS {policy} ON {table};")
        statements.append(
            " ".join(
                [
                    f"CREATE POLICY {policy} ON {table}",
                    "USING (organization_id = current_setting('app.organization_id', true))",
                    "WITH CHECK (organization_id = current_setting('app.organization_id', true));",
                ]
            )
        )
    return "\n".join(statements)


def ensure_v9_schema(store: PlatformStore, partition_count: int = 4) -> dict[str, Any]:
    if getattr(store, "_use_postgres", False):
        schema_sql = build_v9_postgres_schema_sql(partition_count=partition_count)
        rls_sql = build_v9_rls_sql()
    else:
        schema_sql = build_v9_sqlite_schema_sql()
        rls_sql = ""
    with store._connect() as conn:  # noqa: SLF001 - repository boundary shim
        conn.executescript(schema_sql)
        if rls_sql:
            conn.executescript(rls_sql)
    return {
        "partition_count": partition_count,
        "tables": V9_PARTITIONED_TABLES,
        "schema_sql": schema_sql,
        "rls_sql": rls_sql,
    }


__all__ = [
    "V9_PARTITIONED_TABLES",
    "V9_ROW_LEVEL_TABLES",
    "V9SchemaBundle",
    "build_v9_postgres_schema_sql",
    "build_v9_sqlite_schema_sql",
    "build_v9_rls_sql",
    "ensure_v9_schema",
]
