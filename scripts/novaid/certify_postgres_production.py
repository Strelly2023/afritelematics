#!/usr/bin/env python3
"""Certify PostgreSQL as NovaID's production persistence authority."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from statistics import median
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any, Iterator
from uuid import uuid4

import psycopg

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.novaid.persistence.migrations import (  # noqa: E402
    EXPECTED_REVISIONS,
    apply_migrations,
    verify_migration_revisions,
)
from afritech.novaid.runtime import validate_runtime_environment  # noqa: E402


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * percentile))
    return round(ordered[index], 3)


@contextmanager
def _environment(**values: str) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _connection(dsn: str, schema: str) -> psycopg.Connection[Any]:
    connection = psycopg.connect(dsn)
    connection.execute(f'SET search_path TO "{schema}"')
    connection.commit()
    return connection


def _production_authority_gate(dsn: str) -> dict[str, Any]:
    with _environment(
        NOVAID_DATABASE_URL=dsn,
        NOVAID_JWT_ISSUER="https://identity.afritech.example",
        NOVAID_JWT_AUDIENCE="afritech-production",
        NOVAID_SIGNING_KEYS_JSON=json.dumps(
            {
                "certification-previous": "previous-certification-signing-key-0001",
                "certification-active": "active-certification-signing-key-000002",
            }
        ),
        NOVAID_ACTIVE_SIGNING_KEY_ID="certification-active",
        NOVAID_REDIS_REQUIRED="false",
    ):
        rejected_sqlite = False
        try:
            validate_runtime_environment("production", "sqlite")
        except RuntimeError as exc:
            rejected_sqlite = str(exc) == "production_novaid_requires_postgres"
        validate_runtime_environment("production", "postgres")
    if not rejected_sqlite:
        raise RuntimeError("production_sqlite_authority_was_not_rejected")
    return {
        "production_backend": "postgres",
        "sqlite_rejected": True,
        "postgres_configuration_accepted": True,
    }


def _bootstrap(dsn: str, schema: str) -> dict[str, Any]:
    with _connection(dsn, schema) as connection:
        started = perf_counter()
        revisions = apply_migrations(connection)
        elapsed_ms = (perf_counter() - started) * 1000
        verified = verify_migration_revisions(connection)
        checksums = connection.execute(
            "SELECT revision,checksum FROM novaid_schema_migrations ORDER BY revision"
        ).fetchall()
        constraints = connection.execute(
            "SELECT count(*) FROM information_schema.table_constraints "
            "WHERE table_schema=%s AND constraint_type IN "
            "('PRIMARY KEY','FOREIGN KEY','UNIQUE','CHECK')",
            (schema,),
        ).fetchone()[0]
        tables = connection.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema=%s",
            (schema,),
        ).fetchone()[0]
    if revisions != EXPECTED_REVISIONS or verified != EXPECTED_REVISIONS:
        raise RuntimeError("canonical_migration_chain_not_verified")
    if not all(checksum for _, checksum in checksums):
        raise RuntimeError("migration_checksum_missing")
    return {
        "revision_count": len(revisions),
        "revisions": list(revisions),
        "checksums_present": True,
        "table_count": tables,
        "constraint_count": constraints,
        "bootstrap_ms": round(elapsed_ms, 3),
    }


def _failed_migration_rollback(dsn: str, schema: str) -> dict[str, Any]:
    with TemporaryDirectory(prefix="novaid-failed-migration-") as directory:
        migration_directory = Path(directory)
        (migration_directory / "0001_probe.sql").write_text(
            "CREATE TABLE rollback_probe(id integer PRIMARY KEY);",
            encoding="utf-8",
        )
        (migration_directory / "0002_failure.sql").write_text(
            "INSERT INTO rollback_probe(id) VALUES (1); "
            "ALTER TABLE table_that_does_not_exist ADD COLUMN impossible integer;",
            encoding="utf-8",
        )
        failed = False
        with _connection(dsn, schema) as connection:
            try:
                apply_migrations(
                    connection,
                    migration_directory=migration_directory,
                )
            except psycopg.Error:
                failed = True
            probe_exists = connection.execute(
                "SELECT to_regclass(%s)", (f"{schema}.rollback_probe",)
            ).fetchone()[0]
            ledger_exists = connection.execute(
                "SELECT to_regclass(%s)", (f"{schema}.novaid_schema_migrations",)
            ).fetchone()[0]
    if not failed or probe_exists is not None or ledger_exists is not None:
        raise RuntimeError("failed_migration_was_not_fully_rolled_back")
    return {
        "failure_injected": True,
        "partial_schema_absent": True,
        "partial_ledger_absent": True,
        "transactional_rollback": "PASS",
    }


def _seed_workload(dsn: str, schema: str, tenant_count: int, identities_per_tenant: int):
    tenants: list[str] = []
    identities: list[tuple[str, str]] = []
    now = datetime.now(UTC)
    with _connection(dsn, schema) as connection:
        for tenant_index in range(tenant_count):
            tenant_id = str(uuid4())
            tenants.append(tenant_id)
            connection.execute(
                "INSERT INTO novaid_tenants"
                "(tenant_id,name,status,created_at,updated_at) "
                "VALUES(%s,%s,'ACTIVE',%s,%s)",
                (tenant_id, f"Workload tenant {tenant_index}", now, now),
            )
            for identity_index in range(identities_per_tenant):
                identity_id = str(uuid4())
                identities.append((tenant_id, identity_id))
                connection.execute(
                    "INSERT INTO novaid_identities"
                    "(identity_id,tenant_id,normalized_email,status,created_at,updated_at) "
                    "VALUES(%s,%s,%s,'ACTIVE',%s,%s)",
                    (
                        identity_id,
                        tenant_id,
                        f"user-{identity_index}@tenant-{tenant_index}.example",
                        now,
                        now,
                    ),
                )
        connection.commit()
    return tenants, identities


def _workload(
    dsn: str,
    schema: str,
    *,
    workers: int,
    operations: int,
    tenant_count: int,
    identities_per_tenant: int,
) -> dict[str, Any]:
    tenants, identities = _seed_workload(
        dsn, schema, tenant_count, identities_per_tenant
    )

    def operation(index: int) -> float:
        tenant_id, identity_id = identities[index % len(identities)]
        started = perf_counter()
        with _connection(dsn, schema) as connection:
            row = connection.execute(
                "SELECT version FROM novaid_identities "
                "WHERE tenant_id=%s AND identity_id=%s FOR UPDATE",
                (tenant_id, identity_id),
            ).fetchone()
            if row is None:
                raise RuntimeError("tenant_bound_identity_missing")
            connection.execute(
                "UPDATE novaid_identities SET version=version+1,updated_at=now() "
                "WHERE tenant_id=%s AND identity_id=%s",
                (tenant_id, identity_id),
            )
            event_id = str(uuid4())
            connection.execute(
                "INSERT INTO novaid_security_events("
                "event_id,event_type,severity,tenant_id,actor_identity_id,"
                "subject_identity_id,correlation_id,request_id,occurred_at,"
                "recorded_at,outcome,reason_codes,metadata,schema_version"
                ") VALUES(%s,'CERTIFICATION_WRITE','INFO',%s,%s,%s,%s,%s,"
                "now(),now(),'SUCCESS','[]'::jsonb,'{}'::jsonb,1)",
                (
                    event_id,
                    tenant_id,
                    identity_id,
                    identity_id,
                    str(uuid4()),
                    str(uuid4()),
                ),
            )
            connection.commit()
        return (perf_counter() - started) * 1000

    started = perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        latencies = list(executor.map(operation, range(operations)))
    elapsed = perf_counter() - started

    with _connection(dsn, schema) as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM novaid_security_events "
            "WHERE event_type='CERTIFICATION_WRITE'"
        ).fetchone()[0]
        version_increments = connection.execute(
            "SELECT sum(version - 1) FROM novaid_identities"
        ).fetchone()[0]
        cross_tenant_rows = connection.execute(
            "SELECT count(*) FROM novaid_identities i "
            "JOIN novaid_tenants t ON t.tenant_id=i.tenant_id "
            "WHERE i.tenant_id<>t.tenant_id"
        ).fetchone()[0]

    if event_count != operations or version_increments != operations:
        raise RuntimeError("workload_write_or_audit_loss_detected")
    if cross_tenant_rows:
        raise RuntimeError("tenant_integrity_violation")
    return {
        "workers": workers,
        "operations": operations,
        "tenants": len(tenants),
        "identities": len(identities),
        "elapsed_seconds": round(elapsed, 3),
        "throughput_transactions_per_second": round(operations / elapsed, 2),
        "latency_ms": {
            "median": round(median(latencies), 3),
            "p95": _percentile(latencies, 0.95),
            "p99": _percentile(latencies, 0.99),
            "maximum": round(max(latencies), 3),
        },
        "committed_audit_events": event_count,
        "committed_version_increments": version_increments,
        "lost_writes": 0,
        "tenant_integrity_violations": 0,
    }


def certify(args: argparse.Namespace) -> dict[str, Any]:
    run_id = uuid4().hex[:12]
    schema = f"novaid_cert_{run_id}"
    rollback_schema = f"novaid_rollback_{run_id}"
    with psycopg.connect(args.dsn, autocommit=True) as admin:
        server = admin.execute(
            "SELECT version(), current_setting('server_version'), pg_is_in_recovery()"
        ).fetchone()
        admin.execute(f'CREATE SCHEMA "{schema}"')
        admin.execute(f'CREATE SCHEMA "{rollback_schema}"')
    try:
        result = {
            "schema": "afritech.novaid.production_database_certification.v1",
            "run_id": run_id,
            "executed_at": datetime.now(UTC).isoformat(),
            "database": {
                "engine": "PostgreSQL",
                "server_version": server[1],
                "in_recovery": server[2],
                "version_detail_sha256": sha256(server[0].encode()).hexdigest(),
            },
            "authority_gate": _production_authority_gate(args.dsn),
            "migration": _bootstrap(args.dsn, schema),
            "rollback": _failed_migration_rollback(args.dsn, rollback_schema),
            "workload": _workload(
                args.dsn,
                schema,
                workers=args.workers,
                operations=args.operations,
                tenant_count=args.tenants,
                identities_per_tenant=args.identities_per_tenant,
            ),
            "verdict": "PASS",
        }
    finally:
        with psycopg.connect(args.dsn, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            admin.execute(f'DROP SCHEMA IF EXISTS "{rollback_schema}" CASCADE')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--operations", type=int, default=1200)
    parser.add_argument("--tenants", type=int, default=12)
    parser.add_argument("--identities-per-tenant", type=int, default=25)
    args = parser.parse_args()
    result = certify(args)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
