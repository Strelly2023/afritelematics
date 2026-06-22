from __future__ import annotations

import json
import os
import sqlite3
import re
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4


DEFAULT_ORGANIZATION_ID = "afritech-core"


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash_payload(payload: Any) -> str:
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _derive_signing_seed(*, organization_id: str, key_family: str, key_version: int) -> bytes:
    return sha256(f"{organization_id}:{key_family}:{key_version}".encode("utf-8")).digest()


def _default_db_path() -> Path:
    configured = os.environ.get("NOVAPROGRAMMING_CONTROL_DB")
    if configured:
        return Path(configured)
    return Path(__file__).with_name("novaprogramming_control_plane.sqlite3")


def _default_database_url() -> str | None:
    configured = os.environ.get("NOVAPROGRAMMING_DATABASE_URL")
    if configured:
        return configured
    legacy = os.environ.get("NOVAPROGRAMMING_CONTROL_DATABASE_URL")
    if legacy:
        return legacy
    return None


_POSTGRES_INSERT_REPLACE_TARGETS: dict[str, tuple[str, ...]] = {
    "verification_proofs": ("proof_id",),
    "deployment_receipts": ("receipt_id",),
    "replay_records": ("replay_id",),
    "dashboard_analytics_snapshots": (
        "organization_id",
        "source",
        "snapshot_type",
        "window_bucket",
        "snapshot_hash",
    ),
    "ai_decision_snapshots": (
        "organization_id",
        "source",
        "decision_type",
        "window_bucket",
        "snapshot_hash",
    ),
    "ai_action_snapshots": (
        "organization_id",
        "source",
        "action_type",
        "window_bucket",
        "snapshot_hash",
    ),
    "policy_definitions": ("organization_id", "policy_name", "version"),
    "certification_records": ("certification_id",),
    "retention_policies": ("retention_id",),
    "event_stream_topics": ("organization_id", "topic_name"),
    "zero_trust_policies": ("organization_id", "policy_name", "version"),
    "crypto_key_backends": ("organization_id", "key_family", "backend_name"),
    "stream_backends": ("organization_id", "backend_name"),
    "trust_regions": ("region_id",),
    "identity_bindings": ("organization_id", "user_id", "device_id"),
    "trust_graph_nodes": ("organization_id", "node_type", "label"),
    "trust_graph_edges": ("edge_id",),
}


class _PostgresCursorAdapter:
    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return list(self._cursor.fetchall())

    def __iter__(self):
        return iter(self._cursor)


class _PostgresConnectionAdapter:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, sql: str, params: Any = ()) -> _PostgresCursorAdapter:
        sql = _rewrite_sql_for_postgres(sql)
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        return _PostgresCursorAdapter(cursor)

    def executescript(self, script: str) -> None:
        for statement in _split_sql_script(script):
            if statement:
                self.execute(statement)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "_PostgresConnectionAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def _split_sql_script(script: str) -> list[str]:
    statements: list[str] = []
    for raw in script.split(";"):
        statement = raw.strip()
        if not statement:
            continue
        if statement.startswith("PRAGMA "):
            continue
        statements.append(statement + ";")
    return statements


def _rewrite_sql_for_postgres(sql: str) -> str:
    sql = sql.strip()
    if sql.startswith("PRAGMA "):
        return ""
    sql = sql.replace("?", "%s")
    if sql.upper().startswith("INSERT OR REPLACE INTO"):
        return _rewrite_insert_or_replace(sql)
    return sql


def _rewrite_insert_or_replace(sql: str) -> str:
    match = re.match(
        r"INSERT OR REPLACE INTO\s+([A-Za-z0-9_]+)\s*\((.+?)\)\s*VALUES\s*\((.+)\)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return sql
    table = match.group(1)
    columns = [column.strip() for column in match.group(2).split(",")]
    placeholders = match.group(3).strip()
    conflict_target = _POSTGRES_INSERT_REPLACE_TARGETS.get(table)
    if conflict_target is None:
        conflict_target = (columns[0],)
    update_columns = [column for column in columns if column not in conflict_target]
    if not update_columns:
        return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT ({', '.join(conflict_target)}) DO NOTHING"
    assignments = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
    return (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(conflict_target)}) DO UPDATE SET {assignments}"
    )


class PlatformStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.database_url = _default_database_url()
        self._use_postgres = bool(self.database_url and self.database_url.startswith(("postgres://", "postgresql://")))
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        if self._use_postgres:
            self.db_path = Path(":postgres:")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._use_postgres:
            import psycopg
            from psycopg.rows import dict_row

            connection = psycopg.connect(self.database_url, row_factory=dict_row)
            return _PostgresConnectionAdapter(connection)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        schema = """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS organizations (
            organization_id TEXT PRIMARY KEY,
            organization_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            target TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS verification_proofs (
            proof_id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            proof_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL,
            replayable INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deployment_requests (
            request_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            service TEXT NOT NULL,
            environment TEXT NOT NULL,
            image TEXT NOT NULL,
            rationale TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            requested_role TEXT NOT NULL,
            status TEXT NOT NULL,
            approved_by TEXT,
            approval_notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deployments (
            deployment_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            service TEXT NOT NULL,
            environment TEXT NOT NULL,
            image TEXT NOT NULL,
            status TEXT NOT NULL,
            approved INTEGER NOT NULL,
            deployed_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_chain_events (
            chain_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            target TEXT NOT NULL,
            status TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            audit_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deployment_receipts (
            receipt_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            deployment_id TEXT NOT NULL,
            request_id TEXT NOT NULL,
            proof_hash TEXT NOT NULL,
            audit_hash TEXT NOT NULL,
            receipt_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assurance_records (
            assurance_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            deployment_id TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            proof_coverage INTEGER NOT NULL,
            policy_compliance INTEGER NOT NULL,
            assurance_status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_scores (
            score_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            classification TEXT NOT NULL,
            breakdown_json TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            computed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_stream_events (
            stream_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS dashboard_analytics_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            source TEXT NOT NULL,
            snapshot_type TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            trust_health INTEGER NOT NULL,
            replay_health_score INTEGER NOT NULL,
            evidence_coverage INTEGER NOT NULL,
            exception_pressure INTEGER NOT NULL,
            alert_count INTEGER NOT NULL,
            active_drivers INTEGER NOT NULL,
            completed_rides INTEGER NOT NULL,
            total_rides INTEGER NOT NULL,
            guard_count INTEGER NOT NULL,
            replay_failures INTEGER NOT NULL,
            hash_chain_failures INTEGER NOT NULL,
            missing_traces INTEGER NOT NULL,
            receipts_count INTEGER NOT NULL,
            trace_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            window_bucket TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, source, snapshot_type, window_bucket, snapshot_hash)
        );
        CREATE TABLE IF NOT EXISTS ai_decision_snapshots (
            decision_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            source TEXT NOT NULL,
            decision_type TEXT NOT NULL,
            decision_lane TEXT NOT NULL,
            decision_action TEXT NOT NULL,
            decision_priority TEXT NOT NULL,
            decision_summary TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            trust_health INTEGER NOT NULL,
            replay_health_score INTEGER NOT NULL,
            evidence_coverage INTEGER NOT NULL,
            exception_pressure INTEGER NOT NULL,
            alert_count INTEGER NOT NULL,
            guard_count INTEGER NOT NULL,
            replay_failures INTEGER NOT NULL,
            hash_chain_failures INTEGER NOT NULL,
            missing_traces INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            confidence REAL NOT NULL,
            stability_index INTEGER NOT NULL,
            recommended_actions_json TEXT NOT NULL,
            watch_items_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            window_bucket TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, source, decision_type, window_bucket, snapshot_hash)
        );
        CREATE TABLE IF NOT EXISTS ai_action_snapshots (
            action_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            source TEXT NOT NULL,
            action_type TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            decision_lane TEXT NOT NULL,
            action_lane TEXT NOT NULL,
            action_mode TEXT NOT NULL,
            action_priority TEXT NOT NULL,
            action_summary TEXT NOT NULL,
            control_signal TEXT NOT NULL,
            safety_gate TEXT NOT NULL,
            automation_tier INTEGER NOT NULL,
            decision_quality_score INTEGER NOT NULL,
            evidence_alignment_score INTEGER NOT NULL,
            calibrated_confidence REAL NOT NULL,
            history_alignment_score INTEGER NOT NULL,
            quality_band TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            trust_health INTEGER NOT NULL,
            replay_health_score INTEGER NOT NULL,
            evidence_coverage INTEGER NOT NULL,
            exception_pressure INTEGER NOT NULL,
            alert_count INTEGER NOT NULL,
            guard_count INTEGER NOT NULL,
            replay_failures INTEGER NOT NULL,
            hash_chain_failures INTEGER NOT NULL,
            missing_traces INTEGER NOT NULL,
            stability_index INTEGER NOT NULL,
            recommended_actions_json TEXT NOT NULL,
            watch_items_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            window_bucket TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, source, action_type, window_bucket, snapshot_hash)
        );
        CREATE TABLE IF NOT EXISTS outcome_snapshots (
            outcome_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            source TEXT NOT NULL,
            outcome_type TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            action_id TEXT NOT NULL,
            outcome_status TEXT NOT NULL,
            outcome_band TEXT NOT NULL,
            learning_band TEXT NOT NULL,
            outcome_score INTEGER NOT NULL,
            trust_score INTEGER NOT NULL,
            trust_health INTEGER NOT NULL,
            replay_health_score INTEGER NOT NULL,
            evidence_coverage INTEGER NOT NULL,
            exception_pressure INTEGER NOT NULL,
            decision_quality_score INTEGER NOT NULL,
            evidence_alignment_score INTEGER NOT NULL,
            calibrated_confidence REAL NOT NULL,
            history_alignment_score INTEGER NOT NULL,
            execution_tier TEXT NOT NULL,
            execution_tier_ready INTEGER NOT NULL,
            measurement_summary TEXT NOT NULL,
            learning_actions_json TEXT NOT NULL,
            recalibration_notes_json TEXT NOT NULL,
            watch_items_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            window_bucket TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, source, outcome_type, window_bucket, snapshot_hash)
        );
        CREATE TABLE IF NOT EXISTS replay_records (
            replay_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            deployment_id TEXT NOT NULL,
            proof_id TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            audit_hash TEXT NOT NULL,
            replay_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usage_events (
            usage_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            amount INTEGER NOT NULL,
            context_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS billing_records (
            billing_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            plan TEXT NOT NULL,
            usage_total INTEGER NOT NULL,
            estimated_amount REAL NOT NULL,
            billing_enabled INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS policy_definitions (
            policy_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            version TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            rule_payload_json TEXT NOT NULL,
            active INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            policy_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, policy_name, version)
        );
        CREATE TABLE IF NOT EXISTS policy_decisions (
            decision_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            action TEXT NOT NULL,
            allowed INTEGER NOT NULL,
            reason TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            target TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS certification_records (
            certification_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            certification_type TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            assurance_status TEXT NOT NULL,
            audit_chain_hash TEXT NOT NULL,
            proof_count INTEGER NOT NULL,
            receipt_count INTEGER NOT NULL,
            certification_hash TEXT NOT NULL UNIQUE,
            signature TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assurance_runs (
            assurance_run_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            previous_trust_score INTEGER NOT NULL,
            drift INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            assurance_status TEXT NOT NULL,
            alert_level TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assurance_drift_events (
            drift_event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            assurance_run_id TEXT NOT NULL,
            previous_trust_score INTEGER NOT NULL,
            current_trust_score INTEGER NOT NULL,
            drift INTEGER NOT NULL,
            severity TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assurance_alerts (
            alert_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            assurance_run_id TEXT NOT NULL,
            alert_level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS retention_policies (
            retention_policy_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            record_type TEXT NOT NULL,
            retention_days INTEGER NOT NULL,
            legal_hold INTEGER NOT NULL,
            deletion_allowed INTEGER NOT NULL,
            policy_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, record_type)
        );
        CREATE TABLE IF NOT EXISTS assurance_reports (
            report_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            report_classification TEXT NOT NULL,
            report_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_exchange_events (
            trust_exchange_event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            external_organization_id TEXT NOT NULL,
            receipt_hash TEXT NOT NULL,
            proof_hash TEXT NOT NULL,
            audit_hash TEXT NOT NULL,
            certification_hash TEXT NOT NULL,
            valid INTEGER NOT NULL,
            details_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS key_registry (
            key_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            key_family TEXT NOT NULL,
            key_version INTEGER NOT NULL,
            public_key TEXT NOT NULL,
            status TEXT NOT NULL,
            rotated_from_key_id TEXT,
            reason TEXT,
            created_at TEXT NOT NULL,
            rotated_at TEXT NOT NULL,
            UNIQUE(organization_id, key_family, key_version)
        );
        CREATE TABLE IF NOT EXISTS key_rotation_events (
            rotation_event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            key_family TEXT NOT NULL,
            previous_key_id TEXT,
            next_key_id TEXT NOT NULL,
            rotated_by TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS signed_audit_chain_events (
            signed_event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            key_id TEXT NOT NULL,
            key_version INTEGER NOT NULL,
            previous_hash TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            audit_hash TEXT NOT NULL,
            signature TEXT NOT NULL,
            public_key TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS federation_nodes (
            node_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            jurisdiction TEXT NOT NULL,
            role TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            trust_level TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, peer_organization_id, node_id)
        );
        CREATE TABLE IF NOT EXISTS federation_claims (
            claim_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            claim_hash TEXT NOT NULL,
            proof_hash TEXT NOT NULL,
            audit_hash TEXT NOT NULL,
            receipt_hash TEXT NOT NULL,
            certification_hash TEXT NOT NULL,
            signature TEXT NOT NULL,
            public_key_id TEXT NOT NULL,
            valid INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS federation_events (
            federation_event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            details_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS event_stream_topics (
            topic_name TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            description TEXT NOT NULL,
            retention_days INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS event_stream_events (
            event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            partition_key TEXT NOT NULL,
            event_type TEXT NOT NULL,
            offset_number INTEGER NOT NULL,
            headers_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, topic_name, offset_number)
        );
        CREATE TABLE IF NOT EXISTS workflow_instances (
            workflow_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            workflow_name TEXT NOT NULL,
            state TEXT NOT NULL,
            definition_json TEXT NOT NULL,
            input_json TEXT NOT NULL,
            output_json TEXT NOT NULL,
            current_step TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workflow_steps (
            step_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            status TEXT NOT NULL,
            input_json TEXT NOT NULL,
            output_json TEXT NOT NULL,
            error TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS zero_trust_policies (
            policy_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            version TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            rule_payload_json TEXT NOT NULL,
            active INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            policy_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, policy_name, version)
        );
        CREATE TABLE IF NOT EXISTS zero_trust_decisions (
            decision_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            allowed INTEGER NOT NULL,
            reason TEXT NOT NULL,
            context_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS crypto_key_backends (
            backend_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            key_family TEXT NOT NULL,
            backend_name TEXT NOT NULL,
            provider_ref TEXT NOT NULL,
            key_arn TEXT,
            hardware_bound INTEGER NOT NULL,
            certificate_chain_json TEXT NOT NULL,
            attestation_json TEXT NOT NULL,
            active INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            rotated_at TEXT NOT NULL,
            UNIQUE(organization_id, key_family, backend_name)
        );
        CREATE TABLE IF NOT EXISTS certificate_chains (
            certificate_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            key_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            issuer TEXT NOT NULL,
            chain_json TEXT NOT NULL,
            chain_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_regions (
            region_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            region_name TEXT NOT NULL,
            country_code TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_region_links (
            link_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            source_region_id TEXT NOT NULL,
            target_region_id TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            trust_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS identity_bindings (
            binding_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            human_trust_score INTEGER NOT NULL,
            device_trust_score INTEGER NOT NULL,
            attestation_hash TEXT NOT NULL,
            signed_by_key_id TEXT NOT NULL,
            trust_level TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, user_id, device_id)
        );
        CREATE TABLE IF NOT EXISTS trust_graph_nodes (
            node_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            node_type TEXT NOT NULL,
            label TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(organization_id, node_type, label)
        );
        CREATE TABLE IF NOT EXISTS trust_graph_edges (
            edge_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS risk_predictions (
            prediction_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            horizon_days INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            confidence REAL NOT NULL,
            features_json TEXT NOT NULL,
            explanation_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_negotiations (
            negotiation_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            state TEXT NOT NULL,
            proposed_terms_json TEXT NOT NULL,
            counter_terms_json TEXT NOT NULL,
            trust_offer INTEGER NOT NULL,
            trust_floor INTEGER NOT NULL,
            signed_request_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trust_negotiation_events (
            negotiation_event_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            negotiation_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS signed_http_requests (
            request_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            peer_organization_id TEXT NOT NULL,
            method TEXT NOT NULL,
            url TEXT NOT NULL,
            headers_json TEXT NOT NULL,
            body_hash TEXT NOT NULL,
            signature TEXT NOT NULL,
            public_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            verified INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stream_backends (
            backend_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            backend_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            region TEXT NOT NULL,
            partitions INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(organization_id, backend_name)
        );
        """
        with self._connect() as conn:
            conn.executescript(schema)

    def _touch_organization(self, organization_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO organizations (organization_id, organization_name, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(organization_id) DO UPDATE SET organization_name=excluded.organization_name
                """,
                (organization_id, organization_id, _now()),
            )
            conn.commit()

    def _derive_key_record(
        self,
        *,
        organization_id: str,
        key_family: str,
        key_version: int,
    ) -> dict[str, Any]:
        from nacl.signing import SigningKey

        seed = _derive_signing_seed(
            organization_id=organization_id,
            key_family=key_family,
            key_version=key_version,
        )
        signing_key = SigningKey(seed)
        public_key = signing_key.verify_key.encode().hex()
        return {
            "key_id": f"{organization_id}.{key_family}.v{key_version}",
            "organization_id": organization_id,
            "key_family": key_family,
            "key_version": key_version,
            "public_key": public_key,
        }

    def _sign_with_key(
        self,
        *,
        organization_id: str,
        key_family: str,
        key_version: int,
        payload: dict[str, Any],
    ) -> tuple[str, str]:
        from nacl.signing import SigningKey

        seed = _derive_signing_seed(
            organization_id=organization_id,
            key_family=key_family,
            key_version=key_version,
        )
        signing_key = SigningKey(seed)
        message = _stable_json(payload).encode("utf-8")
        signature = signing_key.sign(message).signature.hex()
        public_key = signing_key.verify_key.encode().hex()
        return public_key, signature

    def _get_current_key_row(
        self,
        *,
        organization_id: str,
        key_family: str = "audit",
        create_if_missing: bool = True,
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM key_registry
                WHERE organization_id = ? AND key_family = ? AND status = 'active'
                ORDER BY key_version DESC
                LIMIT 1
                """,
                (organization_id, key_family),
            ).fetchone()
            if row is None and create_if_missing:
                key_row = self._derive_key_record(
                    organization_id=organization_id,
                    key_family=key_family,
                    key_version=1,
                )
                now = _now()
                conn.execute(
                    """
                    INSERT INTO key_registry (
                        key_id, organization_id, key_family, key_version,
                        public_key, status, rotated_from_key_id, reason,
                        created_at, rotated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key_row["key_id"],
                        organization_id,
                        key_family,
                        key_row["key_version"],
                        key_row["public_key"],
                        "active",
                        None,
                        "initial",
                        now,
                        now,
                    ),
                )
                conn.commit()
                key_row.update({"status": "active", "created_at": now, "rotated_at": now})
                return key_row
        if row is None:
            return None
        return {
            "key_id": row["key_id"],
            "organization_id": row["organization_id"],
            "key_family": row["key_family"],
            "key_version": row["key_version"],
            "public_key": row["public_key"],
            "status": row["status"],
            "rotated_from_key_id": row["rotated_from_key_id"],
            "reason": row["reason"],
            "created_at": row["created_at"],
            "rotated_at": row["rotated_at"],
        }

    def record_audit_event(
        self,
        *,
        organization_id: str,
        event_type: str,
        actor_user_id: str,
        actor_role: str,
        target: str,
        status: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        created_at = _now()
        payload_hash = _hash_payload(payload)
        previous_hash = self.get_last_audit_hash(organization_id=organization_id) or ""
        audit_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "event_type": event_type,
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "target": target,
                "status": status,
                "payload_hash": payload_hash,
                "previous_hash": previous_hash,
                "created_at": created_at,
            }
        )
        event = {
            "event_id": str(uuid4()),
            "organization_id": organization_id,
            "event_type": event_type,
            "actor_user_id": actor_user_id,
            "actor_role": actor_role,
            "target": target,
            "status": status,
            "payload": payload,
            "payload_hash": payload_hash,
            "previous_hash": previous_hash,
            "audit_hash": audit_hash,
            "created_at": created_at,
        }
        key_row = self._get_current_key_row(
            organization_id=organization_id,
            key_family="audit",
            create_if_missing=True,
        )
        if key_row is None:
            raise RuntimeError("audit signing key unavailable")
        signature_payload = {
            "organization_id": organization_id,
            "event_id": event["event_id"],
            "payload_hash": payload_hash,
            "previous_hash": previous_hash,
            "audit_hash": audit_hash,
            "key_id": key_row["key_id"],
            "key_version": int(key_row["key_version"]),
            "created_at": created_at,
        }
        public_key, signature = self._sign_with_key(
            organization_id=organization_id,
            key_family="audit",
            key_version=int(key_row["key_version"]),
            payload=signature_payload,
        )
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (
                    event_id, organization_id, event_type, actor_user_id,
                    actor_role, target, status, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    organization_id,
                    event_type,
                    actor_user_id,
                    actor_role,
                    target,
                    status,
                    json.dumps(payload, sort_keys=True),
                    created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO audit_chain_events (
                    chain_id, event_id, organization_id, event_type,
                    actor_user_id, actor_role, target, status,
                    previous_hash, payload_hash, audit_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    event["event_id"],
                    organization_id,
                    event_type,
                    actor_user_id,
                    actor_role,
                    target,
                    status,
                    previous_hash,
                    payload_hash,
                    audit_hash,
                    created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO signed_audit_chain_events (
                    signed_event_id, organization_id, event_id, key_id,
                    key_version, previous_hash, payload_hash, audit_hash,
                    signature, public_key, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    organization_id,
                    event["event_id"],
                    key_row["key_id"],
                    int(key_row["key_version"]),
                    previous_hash,
                    payload_hash,
                    audit_hash,
                    signature,
                    public_key,
                    created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO usage_events (
                    usage_id, organization_id, metric, amount, context_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    organization_id,
                    event_type,
                    1,
                    json.dumps(payload, sort_keys=True),
                    created_at,
                ),
            )
            conn.commit()
        return event

    def list_audit_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                audit_events.*,
                audit_chain_events.previous_hash AS chain_previous_hash,
                audit_chain_events.payload_hash AS chain_payload_hash,
                audit_chain_events.audit_hash AS chain_audit_hash
            FROM audit_events
            LEFT JOIN audit_chain_events
                ON audit_chain_events.event_id = audit_events.event_id
        """
        params: tuple[Any, ...] = ()
        if organization_id is not None:
            query += " WHERE audit_events.organization_id = ?"
            params = (organization_id,)
        query += " ORDER BY audit_events.created_at DESC LIMIT ?"
        params = params + (limit,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_audit_event(row) for row in rows]

    def get_last_audit_hash(self, *, organization_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT audit_hash
                FROM audit_chain_events
                WHERE organization_id = ?
                ORDER BY created_at DESC, chain_id DESC
                LIMIT 1
                """,
                (organization_id,),
            ).fetchone()
        if row is None:
            return None
        return str(row["audit_hash"])

    def verify_audit_chain(self, *, organization_id: str | None = None) -> bool:
        query = """
            SELECT organization_id, event_type, actor_user_id, actor_role,
                   target, status, previous_hash, payload_hash, audit_hash,
                   created_at
            FROM audit_chain_events
        """
        params: tuple[Any, ...] = ()
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params = (organization_id,)
        query += " ORDER BY created_at ASC, chain_id ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        previous_hash = ""
        for row in rows:
            payload = {
                "organization_id": row["organization_id"],
                "event_type": row["event_type"],
                "actor_user_id": row["actor_user_id"],
                "actor_role": row["actor_role"],
                "target": row["target"],
                "status": row["status"],
                "payload_hash": row["payload_hash"],
                "previous_hash": row["previous_hash"],
                "created_at": row["created_at"],
            }
            if row["previous_hash"] != previous_hash:
                return False
            if _hash_payload(payload) != row["audit_hash"]:
                return False
            previous_hash = str(row["audit_hash"])
        return True

    def store_proof(
        self,
        *,
        execution_id: str,
        organization_id: str,
        project_id: str,
        proof_hash: str,
        payload: dict[str, Any],
        status: str = "verified",
        replayable: bool = True,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        proof = {
            "proof_id": proof_hash,
            "execution_id": execution_id,
            "organization_id": organization_id,
            "project_id": project_id,
            "proof_hash": proof_hash,
            "payload": payload,
            "status": status,
            "replayable": replayable,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO verification_proofs (
                    proof_id, execution_id, organization_id, project_id,
                    proof_hash, payload_json, status, replayable, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proof["proof_id"],
                    execution_id,
                    organization_id,
                    project_id,
                    proof_hash,
                    json.dumps(payload, sort_keys=True),
                    status,
                    1 if replayable else 0,
                    proof["created_at"],
                ),
            )
            conn.commit()
        return proof

    def get_proof(
        self,
        *,
        execution_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM verification_proofs WHERE execution_id = ?"
        params: list[Any] = [execution_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_proof(row)

    def list_proofs(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM verification_proofs"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_proof(row) for row in rows]

    def latest_proof(self, *, organization_id: str | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM verification_proofs"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_proof(row)

    def request_deployment(
        self,
        *,
        organization_id: str,
        service: str,
        environment: str,
        image: str,
        rationale: str,
        requested_by: str,
        requested_role: str,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        request_id = f"drq-{uuid4().hex[:12]}"
        now = _now()
        record = {
            "request_id": request_id,
            "organization_id": organization_id,
            "service": service,
            "environment": environment,
            "image": image,
            "rationale": rationale,
            "requested_by": requested_by,
            "requested_role": requested_role,
            "status": "pending",
            "approved_by": None,
            "approval_notes": None,
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO deployment_requests (
                    request_id, organization_id, service, environment, image,
                    rationale, requested_by, requested_role, status,
                    approved_by, approval_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    organization_id,
                    service,
                    environment,
                    image,
                    rationale,
                    requested_by,
                    requested_role,
                    "pending",
                    None,
                    None,
                    now,
                    now,
                ),
            )
            conn.commit()
        return record

    def get_deployment_request(
        self,
        *,
        request_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM deployment_requests WHERE request_id = ?"
        params: list[Any] = [request_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_request(row)

    def approve_deployment_request(
        self,
        *,
        request_id: str,
        organization_id: str,
        approved_by: str,
        decision: str,
        notes: str = "",
    ) -> dict[str, Any]:
        request = self.get_deployment_request(
            request_id=request_id, organization_id=organization_id
        )
        if request is None:
            raise KeyError(request_id)
        status = "approved" if decision.lower() == "approved" else "rejected"
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE deployment_requests
                SET status = ?, approved_by = ?, approval_notes = ?, updated_at = ?
                WHERE request_id = ? AND organization_id = ?
                """,
                (status, approved_by, notes, _now(), request_id, organization_id),
            )
            conn.commit()
        request["status"] = status
        request["approved_by"] = approved_by
        request["approval_notes"] = notes
        request["updated_at"] = _now()
        return request

    def create_deployment_from_request(
        self,
        *,
        request_id: str,
        organization_id: str,
        deployed_by: str,
    ) -> dict[str, Any]:
        request = self.get_deployment_request(
            request_id=request_id, organization_id=organization_id
        )
        if request is None:
            raise KeyError(request_id)
        if request["status"] != "approved":
            raise PermissionError("deployment_not_approved")
        deployment_id = f"deploy-{uuid4().hex[:12]}"
        record = {
            "deployment_id": deployment_id,
            "request_id": request_id,
            "organization_id": organization_id,
            "service": request["service"],
            "environment": request["environment"],
            "image": request["image"],
            "status": "queued",
            "approved": True,
            "deployed_by": deployed_by,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO deployments (
                    deployment_id, request_id, organization_id, service,
                    environment, image, status, approved, deployed_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deployment_id,
                    request_id,
                    organization_id,
                    request["service"],
                    request["environment"],
                    request["image"],
                    "queued",
                    1,
                    deployed_by,
                    record["created_at"],
                ),
            )
            conn.execute(
                """
                UPDATE deployment_requests
                SET status = ?, updated_at = ?
                WHERE request_id = ? AND organization_id = ?
                """,
                ("deployed", _now(), request_id, organization_id),
            )
            conn.commit()
        return record

    def get_deployment(
        self,
        *,
        deployment_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM deployments WHERE deployment_id = ?"
        params: list[Any] = [deployment_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_deployment(row)

    def list_deployment_requests(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM deployment_requests"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_request(row) for row in rows]

    def list_deployments(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM deployments"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_deployment(row) for row in rows]

    def store_deployment_receipt(
        self,
        *,
        organization_id: str,
        deployment_id: str,
        request_id: str,
        proof_hash: str,
        audit_hash: str,
        status: str = "issued",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        receipt_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "deployment_id": deployment_id,
                "request_id": request_id,
                "proof_hash": proof_hash,
                "audit_hash": audit_hash,
                "status": status,
            }
        )
        record = {
            "receipt_id": receipt_hash,
            "organization_id": organization_id,
            "deployment_id": deployment_id,
            "request_id": request_id,
            "proof_hash": proof_hash,
            "audit_hash": audit_hash,
            "receipt_hash": receipt_hash,
            "status": status,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO deployment_receipts (
                    receipt_id, organization_id, deployment_id, request_id,
                    proof_hash, audit_hash, receipt_hash, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["receipt_id"],
                    organization_id,
                    deployment_id,
                    request_id,
                    proof_hash,
                    audit_hash,
                    receipt_hash,
                    status,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def get_deployment_receipt(
        self,
        *,
        deployment_id: str | None = None,
        receipt_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM deployment_receipts WHERE 1 = 1"
        params: list[Any] = []
        if deployment_id is not None:
            query += " AND deployment_id = ?"
            params.append(deployment_id)
        if receipt_id is not None:
            query += " AND receipt_id = ?"
            params.append(receipt_id)
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_deployment_receipt(row)

    def list_deployment_receipts(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM deployment_receipts"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_deployment_receipt(row) for row in rows]

    def store_assurance_record(
        self,
        *,
        organization_id: str,
        deployment_id: str,
        trust_score: int,
        risk_score: int,
        proof_coverage: int,
        policy_compliance: int,
        assurance_status: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "assurance_id": str(uuid4()),
            "organization_id": organization_id,
            "deployment_id": deployment_id,
            "trust_score": int(trust_score),
            "risk_score": int(risk_score),
            "proof_coverage": int(proof_coverage),
            "policy_compliance": int(policy_compliance),
            "assurance_status": assurance_status,
            "payload": payload,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assurance_records (
                    assurance_id, organization_id, deployment_id, trust_score,
                    risk_score, proof_coverage, policy_compliance,
                    assurance_status, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["assurance_id"],
                    organization_id,
                    deployment_id,
                    record["trust_score"],
                    record["risk_score"],
                    record["proof_coverage"],
                    record["policy_compliance"],
                    assurance_status,
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_assurance_records(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM assurance_records"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_assurance(row) for row in rows]

    def latest_assurance_record(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        records = self.list_assurance_records(organization_id=organization_id, limit=1)
        return records[0] if records else None

    def store_trust_score(
        self,
        *,
        organization_id: str,
        trust_score: int,
        classification: str,
        breakdown: dict[str, Any],
        findings: list[str],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "score_id": str(uuid4()),
            "organization_id": organization_id,
            "trust_score": int(trust_score),
            "classification": classification,
            "breakdown": breakdown,
            "findings": findings,
            "computed_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_scores (
                    score_id, organization_id, trust_score, classification,
                    breakdown_json, findings_json, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["score_id"],
                    organization_id,
                    record["trust_score"],
                    classification,
                    json.dumps(breakdown, sort_keys=True),
                    json.dumps(findings, sort_keys=True),
                    record["computed_at"],
                ),
            )
            conn.commit()
        return record

    def latest_trust_score(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM trust_scores"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY computed_at DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_trust_score(row)

    def list_trust_scores(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_scores"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY computed_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_trust_score(row) for row in rows]

    def publish_trust_stream_event(
        self,
        *,
        organization_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "stream_id": str(uuid4()),
            "organization_id": organization_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_stream_events (
                    stream_id, organization_id, event_type, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record["stream_id"],
                    organization_id,
                    event_type,
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_trust_stream_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_stream_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_trust_stream(row) for row in rows]

    def store_dashboard_analytics_snapshot(
        self,
        *,
        organization_id: str,
        source: str,
        snapshot_type: str,
        trust_score: int,
        trust_health: int,
        replay_health_score: int,
        evidence_coverage: int,
        exception_pressure: int,
        alert_count: int,
        active_drivers: int,
        completed_rides: int,
        total_rides: int,
        guard_count: int,
        replay_failures: int,
        hash_chain_failures: int,
        missing_traces: int,
        receipts_count: int,
        trace_count: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        created_at = _now()
        window_bucket = created_at[:16]
        snapshot_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "source": source,
                "snapshot_type": snapshot_type,
                "trust_score": int(trust_score),
                "trust_health": int(trust_health),
                "replay_health_score": int(replay_health_score),
                "evidence_coverage": int(evidence_coverage),
                "exception_pressure": int(exception_pressure),
                "alert_count": int(alert_count),
                "active_drivers": int(active_drivers),
                "completed_rides": int(completed_rides),
                "total_rides": int(total_rides),
                "guard_count": int(guard_count),
                "replay_failures": int(replay_failures),
                "hash_chain_failures": int(hash_chain_failures),
                "missing_traces": int(missing_traces),
                "receipts_count": int(receipts_count),
                "trace_count": int(trace_count),
                "payload": payload,
            }
        )
        record = {
            "snapshot_id": f"analytics-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "source": source,
            "snapshot_type": snapshot_type,
            "trust_score": int(trust_score),
            "trust_health": int(trust_health),
            "replay_health_score": int(replay_health_score),
            "evidence_coverage": int(evidence_coverage),
            "exception_pressure": int(exception_pressure),
            "alert_count": int(alert_count),
            "active_drivers": int(active_drivers),
            "completed_rides": int(completed_rides),
            "total_rides": int(total_rides),
            "guard_count": int(guard_count),
            "replay_failures": int(replay_failures),
            "hash_chain_failures": int(hash_chain_failures),
            "missing_traces": int(missing_traces),
            "receipts_count": int(receipts_count),
            "trace_count": int(trace_count),
            "payload": payload,
            "snapshot_hash": snapshot_hash,
            "window_bucket": window_bucket,
            "created_at": created_at,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO dashboard_analytics_snapshots (
                    snapshot_id, organization_id, source, snapshot_type,
                    trust_score, trust_health, replay_health_score,
                    evidence_coverage, exception_pressure, alert_count,
                    active_drivers, completed_rides, total_rides,
                    guard_count, replay_failures, hash_chain_failures,
                    missing_traces, receipts_count, trace_count,
                    payload_json, snapshot_hash, window_bucket, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["snapshot_id"],
                    organization_id,
                    source,
                    snapshot_type,
                    record["trust_score"],
                    record["trust_health"],
                    record["replay_health_score"],
                    record["evidence_coverage"],
                    record["exception_pressure"],
                    record["alert_count"],
                    record["active_drivers"],
                    record["completed_rides"],
                    record["total_rides"],
                    record["guard_count"],
                    record["replay_failures"],
                    record["hash_chain_failures"],
                    record["missing_traces"],
                    record["receipts_count"],
                    record["trace_count"],
                    json.dumps(payload, sort_keys=True),
                    snapshot_hash,
                    window_bucket,
                    created_at,
                ),
            )
            conn.commit()
        return record

    def list_dashboard_analytics_snapshots(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        snapshot_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM dashboard_analytics_snapshots"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if snapshot_type is not None:
            clauses.append("snapshot_type = ?")
            params.append(snapshot_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_dashboard_analytics_snapshot(row) for row in rows]

    def latest_dashboard_analytics_snapshot(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        snapshot_type: str | None = None,
    ) -> dict[str, Any] | None:
        snapshots = self.list_dashboard_analytics_snapshots(
            organization_id=organization_id,
            source=source,
            snapshot_type=snapshot_type,
            limit=1,
        )
        return snapshots[0] if snapshots else None

    def store_ai_decision_snapshot(
        self,
        *,
        organization_id: str,
        source: str,
        decision_type: str,
        decision_lane: str,
        decision_action: str,
        decision_priority: str,
        decision_summary: str,
        trust_score: int,
        trust_health: int,
        replay_health_score: int,
        evidence_coverage: int,
        exception_pressure: int,
        alert_count: int,
        guard_count: int,
        replay_failures: int,
        hash_chain_failures: int,
        missing_traces: int,
        risk_score: int,
        risk_level: str,
        confidence: float,
        stability_index: int,
        recommended_actions: list[str],
        watch_items: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        created_at = _now()
        window_bucket = created_at[:16]
        snapshot_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "source": source,
                "decision_type": decision_type,
                "decision_lane": decision_lane,
                "decision_action": decision_action,
                "decision_priority": decision_priority,
                "decision_summary": decision_summary,
                "trust_score": int(trust_score),
                "trust_health": int(trust_health),
                "replay_health_score": int(replay_health_score),
                "evidence_coverage": int(evidence_coverage),
                "exception_pressure": int(exception_pressure),
                "alert_count": int(alert_count),
                "guard_count": int(guard_count),
                "replay_failures": int(replay_failures),
                "hash_chain_failures": int(hash_chain_failures),
                "missing_traces": int(missing_traces),
                "risk_score": int(risk_score),
                "risk_level": risk_level,
                "confidence": float(confidence),
                "stability_index": int(stability_index),
                "recommended_actions": recommended_actions,
                "watch_items": watch_items,
                "payload": payload,
            }
        )
        record = {
            "decision_id": f"decision-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "source": source,
            "decision_type": decision_type,
            "decision_lane": decision_lane,
            "decision_action": decision_action,
            "decision_priority": decision_priority,
            "decision_summary": decision_summary,
            "trust_score": int(trust_score),
            "trust_health": int(trust_health),
            "replay_health_score": int(replay_health_score),
            "evidence_coverage": int(evidence_coverage),
            "exception_pressure": int(exception_pressure),
            "alert_count": int(alert_count),
            "guard_count": int(guard_count),
            "replay_failures": int(replay_failures),
            "hash_chain_failures": int(hash_chain_failures),
            "missing_traces": int(missing_traces),
            "risk_score": int(risk_score),
            "risk_level": risk_level,
            "confidence": float(confidence),
            "stability_index": int(stability_index),
            "recommended_actions": list(recommended_actions),
            "watch_items": list(watch_items),
            "payload": payload,
            "snapshot_hash": snapshot_hash,
            "window_bucket": window_bucket,
            "created_at": created_at,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ai_decision_snapshots (
                    decision_id, organization_id, source, decision_type,
                    decision_lane, decision_action, decision_priority, decision_summary,
                    trust_score, trust_health, replay_health_score, evidence_coverage,
                    exception_pressure, alert_count, guard_count, replay_failures,
                    hash_chain_failures, missing_traces, risk_score, risk_level,
                    confidence, stability_index, recommended_actions_json, watch_items_json,
                    payload_json, snapshot_hash, window_bucket, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["decision_id"],
                    organization_id,
                    source,
                    decision_type,
                    decision_lane,
                    decision_action,
                    decision_priority,
                    decision_summary,
                    record["trust_score"],
                    record["trust_health"],
                    record["replay_health_score"],
                    record["evidence_coverage"],
                    record["exception_pressure"],
                    record["alert_count"],
                    record["guard_count"],
                    record["replay_failures"],
                    record["hash_chain_failures"],
                    record["missing_traces"],
                    record["risk_score"],
                    risk_level,
                    record["confidence"],
                    record["stability_index"],
                    json.dumps(recommended_actions, sort_keys=True),
                    json.dumps(watch_items, sort_keys=True),
                    json.dumps(payload, sort_keys=True),
                    snapshot_hash,
                    window_bucket,
                    created_at,
                ),
            )
            conn.commit()
        return record

    def store_ai_action_snapshot(
        self,
        *,
        organization_id: str,
        source: str,
        action_type: str,
        decision_id: str,
        decision_lane: str,
        action_lane: str,
        action_mode: str,
        action_priority: str,
        action_summary: str,
        control_signal: str,
        safety_gate: str,
        automation_tier: int,
        decision_quality_score: int,
        evidence_alignment_score: int,
        calibrated_confidence: float,
        history_alignment_score: int,
        quality_band: str,
        trust_score: int,
        trust_health: int,
        replay_health_score: int,
        evidence_coverage: int,
        exception_pressure: int,
        alert_count: int,
        guard_count: int,
        replay_failures: int,
        hash_chain_failures: int,
        missing_traces: int,
        stability_index: int,
        recommended_actions: list[str],
        watch_items: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        created_at = _now()
        window_bucket = created_at[:16]
        snapshot_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "source": source,
                "action_type": action_type,
                "decision_id": decision_id,
                "decision_lane": decision_lane,
                "action_lane": action_lane,
                "action_mode": action_mode,
                "action_priority": action_priority,
                "action_summary": action_summary,
                "control_signal": control_signal,
                "safety_gate": safety_gate,
                "automation_tier": int(automation_tier),
                "decision_quality_score": int(decision_quality_score),
                "evidence_alignment_score": int(evidence_alignment_score),
                "calibrated_confidence": float(calibrated_confidence),
                "history_alignment_score": int(history_alignment_score),
                "quality_band": quality_band,
                "trust_score": int(trust_score),
                "trust_health": int(trust_health),
                "replay_health_score": int(replay_health_score),
                "evidence_coverage": int(evidence_coverage),
                "exception_pressure": int(exception_pressure),
                "alert_count": int(alert_count),
                "guard_count": int(guard_count),
                "replay_failures": int(replay_failures),
                "hash_chain_failures": int(hash_chain_failures),
                "missing_traces": int(missing_traces),
                "stability_index": int(stability_index),
                "recommended_actions": recommended_actions,
                "watch_items": watch_items,
                "payload": payload,
            }
        )
        record = {
            "action_id": f"action-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "source": source,
            "action_type": action_type,
            "decision_id": decision_id,
            "decision_lane": decision_lane,
            "action_lane": action_lane,
            "action_mode": action_mode,
            "action_priority": action_priority,
            "action_summary": action_summary,
            "control_signal": control_signal,
            "safety_gate": safety_gate,
            "automation_tier": int(automation_tier),
            "decision_quality_score": int(decision_quality_score),
            "evidence_alignment_score": int(evidence_alignment_score),
            "calibrated_confidence": float(calibrated_confidence),
            "history_alignment_score": int(history_alignment_score),
            "quality_band": quality_band,
            "trust_score": int(trust_score),
            "trust_health": int(trust_health),
            "replay_health_score": int(replay_health_score),
            "evidence_coverage": int(evidence_coverage),
            "exception_pressure": int(exception_pressure),
            "alert_count": int(alert_count),
            "guard_count": int(guard_count),
            "replay_failures": int(replay_failures),
            "hash_chain_failures": int(hash_chain_failures),
            "missing_traces": int(missing_traces),
            "stability_index": int(stability_index),
            "recommended_actions": list(recommended_actions),
            "watch_items": list(watch_items),
            "payload": payload,
            "snapshot_hash": snapshot_hash,
            "window_bucket": window_bucket,
            "created_at": created_at,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ai_action_snapshots (
                    action_id, organization_id, source, action_type,
                    decision_id, decision_lane, action_lane, action_mode,
                    action_priority, action_summary, control_signal, safety_gate,
                    automation_tier, decision_quality_score, evidence_alignment_score,
                    calibrated_confidence, history_alignment_score, quality_band,
                    trust_score, trust_health, replay_health_score, evidence_coverage,
                    exception_pressure, alert_count, guard_count, replay_failures,
                    hash_chain_failures, missing_traces, stability_index,
                    recommended_actions_json, watch_items_json, payload_json,
                    snapshot_hash, window_bucket, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["action_id"],
                    organization_id,
                    source,
                    action_type,
                    decision_id,
                    decision_lane,
                    action_lane,
                    action_mode,
                    action_priority,
                    action_summary,
                    control_signal,
                    safety_gate,
                    int(automation_tier),
                    int(decision_quality_score),
                    int(evidence_alignment_score),
                    float(calibrated_confidence),
                    int(history_alignment_score),
                    quality_band,
                    record["trust_score"],
                    record["trust_health"],
                    record["replay_health_score"],
                    record["evidence_coverage"],
                    record["exception_pressure"],
                    record["alert_count"],
                    record["guard_count"],
                    record["replay_failures"],
                    record["hash_chain_failures"],
                    record["missing_traces"],
                    record["stability_index"],
                    json.dumps(recommended_actions, sort_keys=True),
                    json.dumps(watch_items, sort_keys=True),
                    json.dumps(payload, sort_keys=True),
                    snapshot_hash,
                    window_bucket,
                    created_at,
                ),
            )
            conn.commit()
        return record

    def list_ai_decision_snapshots(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        decision_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM ai_decision_snapshots"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if decision_type is not None:
            clauses.append("decision_type = ?")
            params.append(decision_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_ai_decision_snapshot(row) for row in rows]

    def latest_ai_decision_snapshot(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        decision_type: str | None = None,
    ) -> dict[str, Any] | None:
        snapshots = self.list_ai_decision_snapshots(
            organization_id=organization_id,
            source=source,
            decision_type=decision_type,
            limit=1,
        )
        return snapshots[0] if snapshots else None

    def list_ai_action_snapshots(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        action_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM ai_action_snapshots"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if action_type is not None:
            clauses.append("action_type = ?")
            params.append(action_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_ai_action_snapshot(row) for row in rows]

    def latest_ai_action_snapshot(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        action_type: str | None = None,
    ) -> dict[str, Any] | None:
        snapshots = self.list_ai_action_snapshots(
            organization_id=organization_id,
            source=source,
            action_type=action_type,
            limit=1,
        )
        return snapshots[0] if snapshots else None

    def store_outcome_snapshot(
        self,
        *,
        organization_id: str,
        source: str,
        outcome_type: str,
        decision_id: str,
        action_id: str,
        outcome_status: str,
        outcome_band: str,
        learning_band: str,
        outcome_score: int,
        trust_score: int,
        trust_health: int,
        replay_health_score: int,
        evidence_coverage: int,
        exception_pressure: int,
        decision_quality_score: int,
        evidence_alignment_score: int,
        calibrated_confidence: float,
        history_alignment_score: int,
        execution_tier: str,
        execution_tier_ready: bool,
        measurement_summary: str,
        learning_actions: list[str],
        recalibration_notes: list[str],
        watch_items: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        created_at = _now()
        window_bucket = created_at[:16]
        snapshot_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "source": source,
                "outcome_type": outcome_type,
                "decision_id": decision_id,
                "action_id": action_id,
                "outcome_status": outcome_status,
                "outcome_band": outcome_band,
                "learning_band": learning_band,
                "outcome_score": int(outcome_score),
                "trust_score": int(trust_score),
                "trust_health": int(trust_health),
                "replay_health_score": int(replay_health_score),
                "evidence_coverage": int(evidence_coverage),
                "exception_pressure": int(exception_pressure),
                "decision_quality_score": int(decision_quality_score),
                "evidence_alignment_score": int(evidence_alignment_score),
                "calibrated_confidence": float(calibrated_confidence),
                "history_alignment_score": int(history_alignment_score),
                "execution_tier": execution_tier,
                "execution_tier_ready": bool(execution_tier_ready),
                "measurement_summary": measurement_summary,
                "learning_actions": learning_actions,
                "recalibration_notes": recalibration_notes,
                "watch_items": watch_items,
                "payload": payload,
            }
        )
        record = {
            "outcome_id": f"outcome-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "source": source,
            "outcome_type": outcome_type,
            "decision_id": decision_id,
            "action_id": action_id,
            "outcome_status": outcome_status,
            "outcome_band": outcome_band,
            "learning_band": learning_band,
            "outcome_score": int(outcome_score),
            "trust_score": int(trust_score),
            "trust_health": int(trust_health),
            "replay_health_score": int(replay_health_score),
            "evidence_coverage": int(evidence_coverage),
            "exception_pressure": int(exception_pressure),
            "decision_quality_score": int(decision_quality_score),
            "evidence_alignment_score": int(evidence_alignment_score),
            "calibrated_confidence": float(calibrated_confidence),
            "history_alignment_score": int(history_alignment_score),
            "execution_tier": execution_tier,
            "execution_tier_ready": bool(execution_tier_ready),
            "measurement_summary": measurement_summary,
            "learning_actions": list(learning_actions),
            "recalibration_notes": list(recalibration_notes),
            "watch_items": list(watch_items),
            "payload": payload,
            "snapshot_hash": snapshot_hash,
            "window_bucket": window_bucket,
            "created_at": created_at,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO outcome_snapshots (
                    outcome_id, organization_id, source, outcome_type,
                    decision_id, action_id, outcome_status, outcome_band,
                    learning_band, outcome_score, trust_score, trust_health,
                    replay_health_score, evidence_coverage, exception_pressure,
                    decision_quality_score, evidence_alignment_score,
                    calibrated_confidence, history_alignment_score,
                    execution_tier, execution_tier_ready, measurement_summary,
                    learning_actions_json, recalibration_notes_json,
                    watch_items_json, payload_json, snapshot_hash, window_bucket,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["outcome_id"],
                    organization_id,
                    source,
                    outcome_type,
                    decision_id,
                    action_id,
                    outcome_status,
                    outcome_band,
                    learning_band,
                    record["outcome_score"],
                    record["trust_score"],
                    record["trust_health"],
                    record["replay_health_score"],
                    record["evidence_coverage"],
                    record["exception_pressure"],
                    record["decision_quality_score"],
                    record["evidence_alignment_score"],
                    record["calibrated_confidence"],
                    record["history_alignment_score"],
                    execution_tier,
                    1 if execution_tier_ready else 0,
                    measurement_summary,
                    json.dumps(learning_actions, sort_keys=True),
                    json.dumps(recalibration_notes, sort_keys=True),
                    json.dumps(watch_items, sort_keys=True),
                    json.dumps(payload, sort_keys=True),
                    snapshot_hash,
                    window_bucket,
                    created_at,
                ),
            )
            conn.commit()
        return record

    def list_outcome_snapshots(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        outcome_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM outcome_snapshots"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if outcome_type is not None:
            clauses.append("outcome_type = ?")
            params.append(outcome_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_outcome_snapshot(row) for row in rows]

    def latest_outcome_snapshot(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = None,
        outcome_type: str | None = None,
    ) -> dict[str, Any] | None:
        snapshots = self.list_outcome_snapshots(
            organization_id=organization_id,
            source=source,
            outcome_type=outcome_type,
            limit=1,
        )
        return snapshots[0] if snapshots else None

    def store_replay_record(
        self,
        *,
        organization_id: str,
        deployment_id: str,
        proof_id: str,
        receipt_id: str,
        audit_hash: str,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        replay_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "deployment_id": deployment_id,
                "proof_id": proof_id,
                "receipt_id": receipt_id,
                "audit_hash": audit_hash,
            }
        )
        record = {
            "replay_id": replay_hash,
            "organization_id": organization_id,
            "deployment_id": deployment_id,
            "proof_id": proof_id,
            "receipt_id": receipt_id,
            "audit_hash": audit_hash,
            "replay_hash": replay_hash,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO replay_records (
                    replay_id, organization_id, deployment_id, proof_id,
                    receipt_id, audit_hash, replay_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["replay_id"],
                    organization_id,
                    deployment_id,
                    proof_id,
                    receipt_id,
                    audit_hash,
                    replay_hash,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def get_replay_record(
        self,
        *,
        replay_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM replay_records WHERE replay_id = ?"
        params: list[Any] = [replay_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_replay(row)

    def latest_replay_record(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM replay_records"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_replay(row)

    def list_replay_records(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM replay_records"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_replay(row) for row in rows]

    def list_usage_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM usage_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_usage(row) for row in rows]

    def track_usage(
        self,
        *,
        organization_id: str,
        metric: str,
        amount: int = 1,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "usage_id": str(uuid4()),
            "organization_id": organization_id,
            "metric": metric,
            "amount": int(amount),
            "context": context or {},
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_events (
                    usage_id, organization_id, metric, amount, context_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["usage_id"],
                    organization_id,
                    metric,
                    record["amount"],
                    json.dumps(record["context"], sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def count_usage(
        self,
        *,
        organization_id: str | None = None,
        metric: str | None = None,
    ) -> int:
        query = "SELECT COALESCE(SUM(amount), 0) AS total FROM usage_events WHERE 1 = 1"
        params: list[Any] = []
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        if metric is not None:
            query += " AND metric = ?"
            params.append(metric)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row["total"] if row is not None else 0)

    def store_billing_record(
        self,
        *,
        organization_id: str,
        plan: str,
        usage_total: int,
        estimated_amount: float,
        billing_enabled: bool,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "billing_id": str(uuid4()),
            "organization_id": organization_id,
            "plan": plan,
            "usage_total": int(usage_total),
            "estimated_amount": float(estimated_amount),
            "billing_enabled": billing_enabled,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO billing_records (
                    billing_id, organization_id, plan, usage_total,
                    estimated_amount, billing_enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["billing_id"],
                    organization_id,
                    plan,
                    record["usage_total"],
                    record["estimated_amount"],
                    1 if billing_enabled else 0,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def billing_summary(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        usage_total = self.count_usage(organization_id=organization_id)
        latest = self.latest_trust_score(organization_id=organization_id)
        estimated_amount = round(usage_total * 0.05, 2)
        summary = {
            "organization_id": organization_id or "all",
            "plan": "enterprise",
            "usage_total": usage_total,
            "estimated_amount": estimated_amount,
            "billing_enabled": False,
            "trust_score": latest["trust_score"] if latest else None,
            "classification": latest["classification"] if latest else None,
        }
        if organization_id is not None:
            self.store_billing_record(
                organization_id=organization_id,
                plan=summary["plan"],
                usage_total=usage_total,
                estimated_amount=estimated_amount,
                billing_enabled=False,
            )
        return summary

    def list_billing_records(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM billing_records"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_billing_record(row) for row in rows]

    def latest_billing_record(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        records = self.list_billing_records(organization_id=organization_id, limit=1)
        return records[0] if records else None

    def store_policy_definition(
        self,
        *,
        organization_id: str,
        policy_name: str,
        version: str,
        rule_type: str,
        rule_payload: dict[str, Any],
        active: bool,
        created_by: str,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        policy_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "policy_name": policy_name,
                "version": version,
                "rule_type": rule_type,
                "rule_payload": rule_payload,
                "active": active,
                "created_by": created_by,
            }
        )
        record = {
            "policy_id": f"policy-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "policy_name": policy_name,
            "version": version,
            "rule_type": rule_type,
            "rule_payload": rule_payload,
            "active": active,
            "created_by": created_by,
            "policy_hash": policy_hash,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO policy_definitions (
                    policy_id, organization_id, policy_name, version,
                    rule_type, rule_payload_json, active, created_by,
                    policy_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["policy_id"],
                    organization_id,
                    policy_name,
                    version,
                    rule_type,
                    json.dumps(rule_payload, sort_keys=True),
                    1 if active else 0,
                    created_by,
                    policy_hash,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_policy_definitions(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM policy_definitions"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_policy_definition(row) for row in rows]

    def get_policy_definition(
        self,
        *,
        policy_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM policy_definitions WHERE policy_id = ?"
        params: list[Any] = [policy_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_policy_definition(row)

    def store_policy_decision(
        self,
        *,
        organization_id: str,
        policy_id: str,
        action: str,
        allowed: bool,
        reason: str,
        actor_user_id: str,
        target: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "decision_id": f"decision-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "policy_id": policy_id,
            "action": action,
            "allowed": allowed,
            "reason": reason,
            "actor_user_id": actor_user_id,
            "target": target,
            "payload_hash": _hash_payload(payload),
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO policy_decisions (
                    decision_id, organization_id, policy_id, action,
                    allowed, reason, actor_user_id, target,
                    payload_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["decision_id"],
                    organization_id,
                    policy_id,
                    action,
                    1 if allowed else 0,
                    reason,
                    actor_user_id,
                    target,
                    record["payload_hash"],
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_policy_decisions(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM policy_decisions"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_policy_decision(row) for row in rows]

    def store_certification_record(
        self,
        *,
        organization_id: str,
        certification_type: str,
        trust_score: int,
        assurance_status: str,
        audit_chain_hash: str,
        proof_count: int,
        receipt_count: int,
        certification_hash: str,
        signature: str,
        public_key_id: str,
        issued_at: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        issued_at = issued_at or _now()
        record = {
            "certification_id": f"cert-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "certification_type": certification_type,
            "trust_score": int(trust_score),
            "assurance_status": assurance_status,
            "audit_chain_hash": audit_chain_hash,
            "proof_count": int(proof_count),
            "receipt_count": int(receipt_count),
            "certification_hash": certification_hash,
            "signature": signature,
            "public_key_id": public_key_id,
            "issued_at": issued_at,
            "payload": payload or {},
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO certification_records (
                    certification_id, organization_id, certification_type,
                    trust_score, assurance_status, audit_chain_hash,
                    proof_count, receipt_count, certification_hash,
                    signature, public_key_id, issued_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["certification_id"],
                    organization_id,
                    certification_type,
                    record["trust_score"],
                    assurance_status,
                    audit_chain_hash,
                    record["proof_count"],
                    record["receipt_count"],
                    certification_hash,
                    signature,
                    public_key_id,
                    issued_at,
                    json.dumps(record["payload"], sort_keys=True),
                ),
            )
            conn.commit()
        return record

    def list_certification_records(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM certification_records"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY issued_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_certification(row) for row in rows]

    def latest_certification_record(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        records = self.list_certification_records(organization_id=organization_id, limit=1)
        return records[0] if records else None

    def store_assurance_run(
        self,
        *,
        organization_id: str,
        trust_score: int,
        previous_trust_score: int,
        drift: int,
        risk_score: int,
        assurance_status: str,
        alert_level: str,
        findings: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "assurance_run_id": f"run-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "trust_score": int(trust_score),
            "previous_trust_score": int(previous_trust_score),
            "drift": int(drift),
            "risk_score": int(risk_score),
            "assurance_status": assurance_status,
            "alert_level": alert_level,
            "findings": findings,
            "payload": payload,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assurance_runs (
                    assurance_run_id, organization_id, trust_score,
                    previous_trust_score, drift, risk_score,
                    assurance_status, alert_level, findings_json,
                    payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["assurance_run_id"],
                    organization_id,
                    record["trust_score"],
                    record["previous_trust_score"],
                    record["drift"],
                    record["risk_score"],
                    assurance_status,
                    alert_level,
                    json.dumps(findings, sort_keys=True),
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_assurance_runs(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM assurance_runs"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_assurance_run(row) for row in rows]

    def latest_assurance_run(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        runs = self.list_assurance_runs(organization_id=organization_id, limit=1)
        return runs[0] if runs else None

    def store_assurance_drift_event(
        self,
        *,
        organization_id: str,
        assurance_run_id: str,
        previous_trust_score: int,
        current_trust_score: int,
        drift: int,
        severity: str,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "drift_event_id": f"drift-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "assurance_run_id": assurance_run_id,
            "previous_trust_score": int(previous_trust_score),
            "current_trust_score": int(current_trust_score),
            "drift": int(drift),
            "severity": severity,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assurance_drift_events (
                    drift_event_id, organization_id, assurance_run_id,
                    previous_trust_score, current_trust_score, drift,
                    severity, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["drift_event_id"],
                    organization_id,
                    assurance_run_id,
                    record["previous_trust_score"],
                    record["current_trust_score"],
                    record["drift"],
                    severity,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_assurance_drift_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM assurance_drift_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_assurance_drift(row) for row in rows]

    def store_assurance_alert(
        self,
        *,
        organization_id: str,
        assurance_run_id: str,
        alert_level: str,
        message: str,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "alert_id": f"alert-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "assurance_run_id": assurance_run_id,
            "alert_level": alert_level,
            "message": message,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assurance_alerts (
                    alert_id, organization_id, assurance_run_id,
                    alert_level, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["alert_id"],
                    organization_id,
                    assurance_run_id,
                    alert_level,
                    message,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_assurance_alerts(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM assurance_alerts"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_assurance_alert(row) for row in rows]

    def store_retention_policy(
        self,
        *,
        organization_id: str,
        record_type: str,
        retention_days: int,
        legal_hold: bool,
        deletion_allowed: bool,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        policy_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "record_type": record_type,
                "retention_days": retention_days,
                "legal_hold": legal_hold,
                "deletion_allowed": deletion_allowed,
            }
        )
        record = {
            "retention_policy_id": f"retention-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "record_type": record_type,
            "retention_days": int(retention_days),
            "legal_hold": legal_hold,
            "deletion_allowed": deletion_allowed,
            "policy_hash": policy_hash,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO retention_policies (
                    retention_policy_id, organization_id, record_type,
                    retention_days, legal_hold, deletion_allowed,
                    policy_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["retention_policy_id"],
                    organization_id,
                    record_type,
                    record["retention_days"],
                    1 if legal_hold else 0,
                    1 if deletion_allowed else 0,
                    policy_hash,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_retention_policies(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM retention_policies"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_retention_policy(row) for row in rows]

    def retention_check(self, *, organization_id: str | None = None) -> dict[str, Any]:
        defaults = {
            "audit": {"retention_days": 0, "legal_hold": True, "deletion_allowed": False},
            "proof": {"retention_days": 0, "legal_hold": True, "deletion_allowed": False},
            "receipt": {"retention_days": 0, "legal_hold": True, "deletion_allowed": False},
            "replay": {"retention_days": 0, "legal_hold": True, "deletion_allowed": False},
            "certification": {"retention_days": 0, "legal_hold": True, "deletion_allowed": False},
        }
        policies = self.list_retention_policies(organization_id=organization_id, limit=500)
        lookup = {policy["record_type"]: policy for policy in policies}
        check = {
            "organization_id": organization_id or "all",
            "records": {},
        }
        for record_type, defaults_payload in defaults.items():
            policy = lookup.get(record_type)
            if policy is None:
                policy = self.store_retention_policy(
                    organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
                    record_type=record_type,
                    retention_days=defaults_payload["retention_days"],
                    legal_hold=defaults_payload["legal_hold"],
                    deletion_allowed=defaults_payload["deletion_allowed"],
                )
            check["records"][record_type] = {
                "retention_days": policy["retention_days"],
                "legal_hold": policy["legal_hold"],
                "deletion_allowed": policy["deletion_allowed"],
                "policy_hash": policy["policy_hash"],
            }
        return check

    def store_assurance_report(
        self,
        *,
        organization_id: str,
        report_classification: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        report_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "report_classification": report_classification,
                "payload": payload,
            }
        )
        record = {
            "report_id": f"report-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "report_classification": report_classification,
            "report_hash": report_hash,
            "payload": payload,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assurance_reports (
                    report_id, organization_id, report_classification,
                    report_hash, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["report_id"],
                    organization_id,
                    report_classification,
                    report_hash,
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_assurance_reports(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM assurance_reports"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_assurance_report(row) for row in rows]

    def store_trust_exchange_event(
        self,
        *,
        organization_id: str,
        external_organization_id: str,
        receipt_hash: str,
        proof_hash: str,
        audit_hash: str,
        certification_hash: str,
        valid: bool,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "trust_exchange_event_id": f"tex-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "external_organization_id": external_organization_id,
            "receipt_hash": receipt_hash,
            "proof_hash": proof_hash,
            "audit_hash": audit_hash,
            "certification_hash": certification_hash,
            "valid": valid,
            "details": details,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_exchange_events (
                    trust_exchange_event_id, organization_id,
                    external_organization_id, receipt_hash, proof_hash,
                    audit_hash, certification_hash, valid, details_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["trust_exchange_event_id"],
                    organization_id,
                    external_organization_id,
                    receipt_hash,
                    proof_hash,
                    audit_hash,
                    certification_hash,
                    1 if valid else 0,
                    json.dumps(details, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_trust_exchange_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_exchange_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_trust_exchange_event(row) for row in rows]

    def list_signing_keys(
        self,
        *,
        organization_id: str | None = None,
        key_family: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM key_registry"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if key_family is not None:
            clauses.append("key_family = ?")
            params.append(key_family)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY key_version DESC, created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_signing_key(row) for row in rows]

    def current_signing_key(
        self,
        *,
        organization_id: str,
        key_family: str = "audit",
    ) -> dict[str, Any]:
        key = self._get_current_key_row(
            organization_id=organization_id,
            key_family=key_family,
            create_if_missing=True,
        )
        if key is None:
            raise KeyError("signing key unavailable")
        return key

    def rotate_signing_key(
        self,
        *,
        organization_id: str,
        key_family: str = "audit",
        rotated_by: str = "system",
        reason: str = "rotation",
    ) -> dict[str, Any]:
        current = self._get_current_key_row(
            organization_id=organization_id,
            key_family=key_family,
            create_if_missing=True,
        )
        if current is None:
            raise KeyError("signing key unavailable")
        next_version = int(current["key_version"]) + 1
        next_row = self._derive_key_record(
            organization_id=organization_id,
            key_family=key_family,
            key_version=next_version,
        )
        now = _now()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE key_registry
                SET status = ?, reason = ?, rotated_at = ?
                WHERE key_id = ? AND organization_id = ?
                """,
                ("rotated", reason, now, current["key_id"], organization_id),
            )
            conn.execute(
                """
                INSERT INTO key_registry (
                    key_id, organization_id, key_family, key_version,
                    public_key, status, rotated_from_key_id, reason,
                    created_at, rotated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_row["key_id"],
                    organization_id,
                    key_family,
                    next_version,
                    next_row["public_key"],
                    "active",
                    current["key_id"],
                    reason,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO key_rotation_events (
                    rotation_event_id, organization_id, key_family,
                    previous_key_id, next_key_id, rotated_by, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    organization_id,
                    key_family,
                    current["key_id"],
                    next_row["key_id"],
                    rotated_by,
                    reason,
                    now,
                ),
            )
            conn.commit()
        return {
            **next_row,
            "status": "active",
            "rotated_from_key_id": current["key_id"],
            "reason": reason,
            "created_at": now,
            "rotated_at": now,
        }

    def list_key_rotations(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM key_rotation_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_key_rotation(row) for row in rows]

    def list_signed_audit_chain_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM signed_audit_chain_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at ASC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_signed_audit(row) for row in rows]

    def verify_signed_audit_chain(self, *, organization_id: str | None = None) -> bool:
        events = self.list_signed_audit_chain_events(organization_id=organization_id, limit=5000)
        previous_hash = ""
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError

        for event in events:
            if event["previous_hash"] != previous_hash:
                return False
            payload = {
                "organization_id": event["organization_id"],
                "event_id": event["event_id"],
                "key_id": event["key_id"],
                "key_version": event["key_version"],
                "previous_hash": event["previous_hash"],
                "payload_hash": event["payload_hash"],
                "audit_hash": event["audit_hash"],
                "created_at": event["created_at"],
            }
            try:
                VerifyKey(bytes.fromhex(event["public_key"])).verify(
                    _stable_json(payload).encode("utf-8"),
                    bytes.fromhex(event["signature"]),
                )
            except (ValueError, BadSignatureError):
                return False
            previous_hash = event["audit_hash"]
        return True

    def store_federation_node(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        jurisdiction: str,
        role: str,
        public_key_id: str,
        endpoint: str,
        trust_level: str = "TRUSTED",
        status: str = "active",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "node_id": f"node-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "peer_organization_id": peer_organization_id,
            "jurisdiction": jurisdiction,
            "role": role,
            "public_key_id": public_key_id,
            "endpoint": endpoint,
            "trust_level": trust_level,
            "status": status,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO federation_nodes (
                    node_id, organization_id, peer_organization_id,
                    jurisdiction, role, public_key_id, endpoint,
                    trust_level, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["node_id"],
                    organization_id,
                    peer_organization_id,
                    jurisdiction,
                    role,
                    public_key_id,
                    endpoint,
                    trust_level,
                    status,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_federation_nodes(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM federation_nodes"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_federation_node(row) for row in rows]

    def store_federation_claim(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        claim_type: str,
        claim_hash: str,
        proof_hash: str,
        audit_hash: str,
        receipt_hash: str,
        certification_hash: str,
        signature: str,
        public_key_id: str,
        valid: bool,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "claim_id": f"claim-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "peer_organization_id": peer_organization_id,
            "claim_type": claim_type,
            "claim_hash": claim_hash,
            "proof_hash": proof_hash,
            "audit_hash": audit_hash,
            "receipt_hash": receipt_hash,
            "certification_hash": certification_hash,
            "signature": signature,
            "public_key_id": public_key_id,
            "valid": valid,
            "payload": payload,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO federation_claims (
                    claim_id, organization_id, peer_organization_id, claim_type,
                    claim_hash, proof_hash, audit_hash, receipt_hash,
                    certification_hash, signature, public_key_id, valid,
                    payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["claim_id"],
                    organization_id,
                    peer_organization_id,
                    claim_type,
                    claim_hash,
                    proof_hash,
                    audit_hash,
                    receipt_hash,
                    certification_hash,
                    signature,
                    public_key_id,
                    1 if valid else 0,
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_federation_claims(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM federation_claims"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_federation_claim(row) for row in rows]

    def store_federation_event(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        record = {
            "federation_event_id": f"fed-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "peer_organization_id": peer_organization_id,
            "event_type": event_type,
            "details": details,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO federation_events (
                    federation_event_id, organization_id, peer_organization_id,
                    event_type, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["federation_event_id"],
                    organization_id,
                    peer_organization_id,
                    event_type,
                    json.dumps(details, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_federation_events(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM federation_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_federation_event(row) for row in rows]

    def store_stream_topic(
        self,
        *,
        organization_id: str,
        topic_name: str,
        description: str = "",
        retention_days: int = 0,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "topic_name": topic_name,
            "organization_id": organization_id,
            "description": description,
            "retention_days": int(retention_days),
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO event_stream_topics (
                    topic_name, organization_id, description, retention_days, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    topic_name,
                    organization_id,
                    description,
                    int(retention_days),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_stream_topics(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM event_stream_topics"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_stream_topic(row) for row in rows]

    def publish_stream_event(
        self,
        *,
        organization_id: str,
        topic_name: str,
        event_type: str,
        payload: dict[str, Any],
        partition_key: str = "",
        headers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        with self._connect() as conn:
            topic_row = conn.execute(
                "SELECT topic_name FROM event_stream_topics WHERE topic_name = ? AND organization_id = ?",
                (topic_name, organization_id),
            ).fetchone()
            if topic_row is None:
                conn.execute(
                    """
                    INSERT INTO event_stream_topics (
                        topic_name, organization_id, description, retention_days, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (topic_name, organization_id, "", 0, _now()),
                )
            offset_row = conn.execute(
                """
                SELECT COALESCE(MAX(offset_number), 0) AS next_offset
                FROM event_stream_events
                WHERE organization_id = ? AND topic_name = ?
                """,
                (organization_id, topic_name),
            ).fetchone()
            offset = int(offset_row["next_offset"]) + 1
            record = {
                "event_id": f"evt-{uuid4().hex[:12]}",
                "organization_id": organization_id,
                "topic_name": topic_name,
                "partition_key": partition_key,
                "event_type": event_type,
                "offset_number": offset,
                "headers": headers or {},
                "payload": payload,
                "created_at": _now(),
            }
            conn.execute(
                """
                INSERT INTO event_stream_events (
                    event_id, organization_id, topic_name, partition_key,
                    event_type, offset_number, headers_json, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["event_id"],
                    organization_id,
                    topic_name,
                    partition_key,
                    event_type,
                    offset,
                    json.dumps(record["headers"], sort_keys=True),
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_stream_events(
        self,
        *,
        organization_id: str | None = None,
        topic_name: str | None = None,
        after_offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM event_stream_events WHERE offset_number > ?"
        params: list[Any] = [after_offset]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        if topic_name is not None:
            query += " AND topic_name = ?"
            params.append(topic_name)
        query += " ORDER BY offset_number ASC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_stream_event(row) for row in rows]

    def store_workflow_instance(
        self,
        *,
        organization_id: str,
        workflow_name: str,
        definition: dict[str, Any],
        input_payload: dict[str, Any],
        state: str = "running",
        current_step: str = "start",
        output_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "workflow_id": f"wf-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "workflow_name": workflow_name,
            "state": state,
            "definition": definition,
            "input": input_payload,
            "output": output_payload or {},
            "current_step": current_step,
            "created_at": _now(),
            "updated_at": _now(),
            "completed_at": "",
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_instances (
                    workflow_id, organization_id, workflow_name, state,
                    definition_json, input_json, output_json, current_step,
                    created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["workflow_id"],
                    organization_id,
                    workflow_name,
                    state,
                    json.dumps(definition, sort_keys=True),
                    json.dumps(input_payload, sort_keys=True),
                    json.dumps(record["output"], sort_keys=True),
                    current_step,
                    record["created_at"],
                    record["updated_at"],
                    record["completed_at"],
                ),
            )
            conn.commit()
        return record

    def update_workflow_instance(
        self,
        *,
        workflow_id: str,
        organization_id: str,
        state: str,
        current_step: str,
        output_payload: dict[str, Any] | None = None,
        completed: bool = False,
    ) -> dict[str, Any]:
        now = _now()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE workflow_instances
                SET state = ?, current_step = ?, output_json = ?, updated_at = ?, completed_at = ?
                WHERE workflow_id = ? AND organization_id = ?
                """,
                (
                    state,
                    current_step,
                    json.dumps(output_payload or {}, sort_keys=True),
                    now,
                    now if completed else "",
                    workflow_id,
                    organization_id,
                ),
            )
            conn.commit()
        instance = self.get_workflow_instance(workflow_id=workflow_id, organization_id=organization_id)
        if instance is None:
            raise KeyError(workflow_id)
        return instance

    def get_workflow_instance(
        self,
        *,
        workflow_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM workflow_instances WHERE workflow_id = ?"
        params: list[Any] = [workflow_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_workflow_instance(row)

    def list_workflow_instances(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM workflow_instances"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_workflow_instance(row) for row in rows]

    def store_workflow_step(
        self,
        *,
        workflow_id: str,
        organization_id: str,
        step_name: str,
        step_index: int,
        status: str,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        error: str = "",
    ) -> dict[str, Any]:
        record = {
            "step_id": f"step-{uuid4().hex[:12]}",
            "workflow_id": workflow_id,
            "organization_id": organization_id,
            "step_name": step_name,
            "step_index": int(step_index),
            "status": status,
            "input": input_payload or {},
            "output": output_payload or {},
            "error": error,
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_steps (
                    step_id, workflow_id, organization_id, step_name,
                    step_index, status, input_json, output_json, error,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["step_id"],
                    workflow_id,
                    organization_id,
                    step_name,
                    int(step_index),
                    status,
                    json.dumps(record["input"], sort_keys=True),
                    json.dumps(record["output"], sort_keys=True),
                    error,
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            conn.commit()
        return record

    def list_workflow_steps(
        self,
        *,
        organization_id: str | None = None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM workflow_steps WHERE 1 = 1"
        params: list[Any] = []
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        if workflow_id is not None:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        query += " ORDER BY step_index ASC, created_at ASC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_workflow_step(row) for row in rows]

    def store_zero_trust_policy(
        self,
        *,
        organization_id: str,
        policy_name: str,
        version: str,
        rule_type: str,
        rule_payload: dict[str, Any],
        active: bool,
        created_by: str,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        policy_hash = _hash_payload(
            {
                "organization_id": organization_id,
                "policy_name": policy_name,
                "version": version,
                "rule_type": rule_type,
                "rule_payload": rule_payload,
                "active": active,
                "created_by": created_by,
            }
        )
        record = {
            "policy_id": f"ztp-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "policy_name": policy_name,
            "version": version,
            "rule_type": rule_type,
            "rule_payload": rule_payload,
            "active": active,
            "created_by": created_by,
            "policy_hash": policy_hash,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO zero_trust_policies (
                    policy_id, organization_id, policy_name, version,
                    rule_type, rule_payload_json, active, created_by,
                    policy_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["policy_id"],
                    organization_id,
                    policy_name,
                    version,
                    rule_type,
                    json.dumps(rule_payload, sort_keys=True),
                    1 if active else 0,
                    created_by,
                    policy_hash,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_zero_trust_policies(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM zero_trust_policies"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_zero_trust_policy(row) for row in rows]

    def store_zero_trust_decision(
        self,
        *,
        organization_id: str,
        policy_id: str,
        subject: str,
        action: str,
        resource: str,
        allowed: bool,
        reason: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        record = {
            "decision_id": f"ztd-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "policy_id": policy_id,
            "subject": subject,
            "action": action,
            "resource": resource,
            "allowed": allowed,
            "reason": reason,
            "context_hash": _hash_payload(context),
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO zero_trust_decisions (
                    decision_id, organization_id, policy_id, subject, action,
                    resource, allowed, reason, context_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["decision_id"],
                    organization_id,
                    policy_id,
                    subject,
                    action,
                    resource,
                    1 if allowed else 0,
                    reason,
                    record["context_hash"],
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_zero_trust_decisions(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM zero_trust_decisions"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_zero_trust_decision(row) for row in rows]

    def latest_policy_definition(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        policies = self.list_policy_definitions(organization_id=organization_id, limit=1)
        return policies[0] if policies else None

    def latest_policy_decision(
        self,
        *,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        decisions = self.list_policy_decisions(organization_id=organization_id, limit=1)
        return decisions[0] if decisions else None

    def register_crypto_backend(
        self,
        *,
        organization_id: str,
        key_family: str,
        backend_name: str,
        provider_ref: str,
        key_arn: str | None = None,
        hardware_bound: bool = False,
        certificate_chain: list[dict[str, Any]] | None = None,
        attestation: dict[str, Any] | None = None,
        active: bool = True,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "backend_id": f"backend-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "key_family": key_family,
            "backend_name": backend_name,
            "provider_ref": provider_ref,
            "key_arn": key_arn,
            "hardware_bound": bool(hardware_bound),
            "certificate_chain": certificate_chain or [],
            "attestation": attestation or {},
            "active": active,
            "created_at": _now(),
            "rotated_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO crypto_key_backends (
                    backend_id, organization_id, key_family, backend_name,
                    provider_ref, key_arn, hardware_bound,
                    certificate_chain_json, attestation_json, active,
                    created_at, rotated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["backend_id"],
                    organization_id,
                    key_family,
                    backend_name,
                    provider_ref,
                    key_arn,
                    1 if hardware_bound else 0,
                    json.dumps(record["certificate_chain"], sort_keys=True),
                    json.dumps(record["attestation"], sort_keys=True),
                    1 if active else 0,
                    record["created_at"],
                    record["rotated_at"],
                ),
            )
            conn.commit()
        return record

    def list_crypto_backends(
        self,
        *,
        organization_id: str | None = None,
        key_family: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM crypto_key_backends"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if key_family is not None:
            clauses.append("key_family = ?")
            params.append(key_family)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY rotated_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        backends: list[dict[str, Any]] = []
        for row in rows:
            backends.append(
                {
                    "backend_id": row["backend_id"],
                    "organization_id": row["organization_id"],
                    "key_family": row["key_family"],
                    "backend_name": row["backend_name"],
                    "provider_ref": row["provider_ref"],
                    "key_arn": row["key_arn"],
                    "hardware_bound": bool(row["hardware_bound"]),
                    "certificate_chain": json.loads(row["certificate_chain_json"]),
                    "attestation": json.loads(row["attestation_json"]),
                    "active": bool(row["active"]),
                    "created_at": row["created_at"],
                    "rotated_at": row["rotated_at"],
                }
            )
        return backends

    def record_certificate_chain(
        self,
        *,
        organization_id: str,
        key_id: str,
        subject: str,
        issuer: str,
        chain: list[dict[str, Any]],
        status: str = "valid",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        chain_hash = _hash_payload(chain)
        record = {
            "certificate_id": f"cert-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "key_id": key_id,
            "subject": subject,
            "issuer": issuer,
            "chain": chain,
            "chain_hash": chain_hash,
            "status": status,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO certificate_chains (
                    certificate_id, organization_id, key_id, subject, issuer,
                    chain_json, chain_hash, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["certificate_id"],
                    organization_id,
                    key_id,
                    subject,
                    issuer,
                    json.dumps(chain, sort_keys=True),
                    chain_hash,
                    status,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_certificate_chains(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM certificate_chains"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "certificate_id": row["certificate_id"],
                "organization_id": row["organization_id"],
                "key_id": row["key_id"],
                "subject": row["subject"],
                "issuer": row["issuer"],
                "chain": json.loads(row["chain_json"]),
                "chain_hash": row["chain_hash"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def verify_certificate_chain(self, *, organization_id: str | None = None) -> bool:
        chains = self.list_certificate_chains(organization_id=organization_id, limit=1000)
        previous_subject = ""
        previous_hash = ""
        for item in chains:
            chain = item["chain"]
            if _hash_payload(chain) != item["chain_hash"]:
                return False
            for index, cert in enumerate(chain):
                if index == 0:
                    previous_subject = str(cert.get("issuer", ""))
                if index and str(cert.get("issuer", "")) != previous_subject:
                    return False
                previous_subject = str(cert.get("subject", ""))
            previous_hash = item["chain_hash"]
        return True

    def register_stream_backend(
        self,
        *,
        organization_id: str,
        backend_name: str,
        provider: str,
        region: str,
        partitions: int,
        status: str = "active",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "backend_id": f"stream-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "backend_name": backend_name,
            "provider": provider,
            "region": region,
            "partitions": int(partitions),
            "status": status,
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO stream_backends (
                    backend_id, organization_id, backend_name, provider, region,
                    partitions, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["backend_id"],
                    organization_id,
                    backend_name,
                    provider,
                    region,
                    record["partitions"],
                    status,
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            conn.commit()
        return record

    def list_stream_backends(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM stream_backends"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "backend_id": row["backend_id"],
                "organization_id": row["organization_id"],
                "backend_name": row["backend_name"],
                "provider": row["provider"],
                "region": row["region"],
                "partitions": int(row["partitions"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def register_trust_region(
        self,
        *,
        organization_id: str,
        region_name: str,
        country_code: str,
        provider: str,
        status: str = "active",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "region_id": f"region-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "region_name": region_name,
            "country_code": country_code,
            "provider": provider,
            "status": status,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trust_regions (
                    region_id, organization_id, region_name, country_code,
                    provider, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["region_id"],
                    organization_id,
                    region_name,
                    country_code,
                    provider,
                    status,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_trust_regions(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_regions"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def link_trust_regions(
        self,
        *,
        organization_id: str,
        source_region_id: str,
        target_region_id: str,
        latency_ms: int,
        trust_score: int,
        status: str = "active",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "link_id": f"link-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "source_region_id": source_region_id,
            "target_region_id": target_region_id,
            "latency_ms": int(latency_ms),
            "trust_score": int(trust_score),
            "status": status,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_region_links (
                    link_id, organization_id, source_region_id, target_region_id,
                    latency_ms, trust_score, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["link_id"],
                    organization_id,
                    source_region_id,
                    target_region_id,
                    record["latency_ms"],
                    record["trust_score"],
                    status,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_trust_region_links(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_region_links"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def bind_identity(
        self,
        *,
        organization_id: str,
        user_id: str,
        device_id: str,
        human_trust_score: int,
        device_trust_score: int,
        attestation_hash: str,
        signed_by_key_id: str,
        trust_level: str = "BOUND",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "binding_id": f"binding-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "user_id": user_id,
            "device_id": device_id,
            "human_trust_score": int(human_trust_score),
            "device_trust_score": int(device_trust_score),
            "attestation_hash": attestation_hash,
            "signed_by_key_id": signed_by_key_id,
            "trust_level": trust_level,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO identity_bindings (
                    binding_id, organization_id, user_id, device_id,
                    human_trust_score, device_trust_score, attestation_hash,
                    signed_by_key_id, trust_level, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["binding_id"],
                    organization_id,
                    user_id,
                    device_id,
                    record["human_trust_score"],
                    record["device_trust_score"],
                    attestation_hash,
                    signed_by_key_id,
                    trust_level,
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_identity_bindings(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM identity_bindings"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def store_graph_node(
        self,
        *,
        organization_id: str,
        node_type: str,
        label: str,
        trust_score: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "node_id": f"node-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "node_type": node_type,
            "label": label,
            "trust_score": int(trust_score),
            "metadata": metadata or {},
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trust_graph_nodes (
                    node_id, organization_id, node_type, label, trust_score,
                    metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["node_id"],
                    organization_id,
                    node_type,
                    label,
                    record["trust_score"],
                    json.dumps(record["metadata"], sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def store_graph_edge(
        self,
        *,
        organization_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_type: str,
        weight: float,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "edge_id": f"edge-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "edge_type": edge_type,
            "weight": float(weight),
            "metadata": metadata or {},
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_graph_edges (
                    edge_id, organization_id, source_node_id, target_node_id,
                    edge_type, weight, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["edge_id"],
                    organization_id,
                    source_node_id,
                    target_node_id,
                    edge_type,
                    record["weight"],
                    json.dumps(record["metadata"], sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_graph_nodes(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_graph_nodes"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "node_id": row["node_id"],
                "organization_id": row["organization_id"],
                "node_type": row["node_type"],
                "label": row["label"],
                "trust_score": int(row["trust_score"]),
                "metadata": json.loads(row["metadata_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_graph_edges(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_graph_edges"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "edge_id": row["edge_id"],
                "organization_id": row["organization_id"],
                "source_node_id": row["source_node_id"],
                "target_node_id": row["target_node_id"],
                "edge_type": row["edge_type"],
                "weight": float(row["weight"]),
                "metadata": json.loads(row["metadata_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def store_risk_prediction(
        self,
        *,
        organization_id: str,
        entity_type: str,
        entity_id: str,
        horizon_days: int,
        risk_score: int,
        confidence: float,
        features: dict[str, Any],
        explanation: list[str],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "prediction_id": f"risk-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "horizon_days": int(horizon_days),
            "risk_score": int(risk_score),
            "confidence": float(confidence),
            "features": features,
            "explanation": explanation,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO risk_predictions (
                    prediction_id, organization_id, entity_type, entity_id,
                    horizon_days, risk_score, confidence, features_json,
                    explanation_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["prediction_id"],
                    organization_id,
                    entity_type,
                    entity_id,
                    record["horizon_days"],
                    record["risk_score"],
                    record["confidence"],
                    json.dumps(features, sort_keys=True),
                    json.dumps(explanation, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_risk_predictions(
        self,
        *,
        organization_id: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM risk_predictions"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if entity_type is not None:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "prediction_id": row["prediction_id"],
                "organization_id": row["organization_id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "horizon_days": int(row["horizon_days"]),
                "risk_score": int(row["risk_score"]),
                "confidence": float(row["confidence"]),
                "features": json.loads(row["features_json"]),
                "explanation": json.loads(row["explanation_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def latest_risk_prediction(
        self,
        *,
        organization_id: str | None = None,
        entity_type: str | None = None,
    ) -> dict[str, Any] | None:
        predictions = self.list_risk_predictions(
            organization_id=organization_id,
            entity_type=entity_type,
            limit=1,
        )
        return predictions[0] if predictions else None

    def store_negotiation_session(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        proposed_terms: dict[str, Any],
        trust_offer: int,
        trust_floor: int,
        signed_request: dict[str, Any],
        state: str = "pending",
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "negotiation_id": f"neg-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "peer_organization_id": peer_organization_id,
            "state": state,
            "proposed_terms": proposed_terms,
            "counter_terms": {},
            "trust_offer": int(trust_offer),
            "trust_floor": int(trust_floor),
            "signed_request": signed_request,
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_negotiations (
                    negotiation_id, organization_id, peer_organization_id, state,
                    proposed_terms_json, counter_terms_json, trust_offer,
                    trust_floor, signed_request_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["negotiation_id"],
                    organization_id,
                    peer_organization_id,
                    state,
                    json.dumps(proposed_terms, sort_keys=True),
                    json.dumps({}, sort_keys=True),
                    record["trust_offer"],
                    record["trust_floor"],
                    json.dumps(signed_request, sort_keys=True),
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            conn.commit()
        return record

    def update_negotiation_session(
        self,
        *,
        negotiation_id: str,
        organization_id: str,
        state: str,
        counter_terms: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self.get_negotiation_session(
            negotiation_id=negotiation_id,
            organization_id=organization_id,
        )
        if session is None:
            raise KeyError(negotiation_id)
        counter_terms = counter_terms or {}
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE trust_negotiations
                SET state = ?, counter_terms_json = ?, updated_at = ?
                WHERE negotiation_id = ? AND organization_id = ?
                """,
                (
                    state,
                    json.dumps(counter_terms, sort_keys=True),
                    _now(),
                    negotiation_id,
                    organization_id,
                ),
            )
            conn.commit()
        session["state"] = state
        session["counter_terms"] = counter_terms
        session["updated_at"] = _now()
        return session

    def get_negotiation_session(
        self,
        *,
        negotiation_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM trust_negotiations WHERE negotiation_id = ?"
        params: list[Any] = [negotiation_id]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return {
            "negotiation_id": row["negotiation_id"],
            "organization_id": row["organization_id"],
            "peer_organization_id": row["peer_organization_id"],
            "state": row["state"],
            "proposed_terms": json.loads(row["proposed_terms_json"]),
            "counter_terms": json.loads(row["counter_terms_json"]),
            "trust_offer": int(row["trust_offer"]),
            "trust_floor": int(row["trust_floor"]),
            "signed_request": json.loads(row["signed_request_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_negotiation_sessions(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_negotiations"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            self.get_negotiation_session(
                negotiation_id=row["negotiation_id"],
                organization_id=row["organization_id"],
            )
            for row in rows
        ]

    def store_negotiation_event(
        self,
        *,
        organization_id: str,
        negotiation_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "negotiation_event_id": f"nevt-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "negotiation_id": negotiation_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trust_negotiation_events (
                    negotiation_event_id, organization_id, negotiation_id,
                    event_type, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["negotiation_event_id"],
                    organization_id,
                    negotiation_id,
                    event_type,
                    json.dumps(payload, sort_keys=True),
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list_negotiation_events(
        self,
        *,
        organization_id: str | None = None,
        negotiation_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_negotiation_events"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if negotiation_id is not None:
            clauses.append("negotiation_id = ?")
            params.append(negotiation_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at ASC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "negotiation_event_id": row["negotiation_event_id"],
                "organization_id": row["organization_id"],
                "negotiation_id": row["negotiation_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def store_signed_http_request(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        method: str,
        url: str,
        headers: dict[str, Any],
        body_hash: str,
        signature: str,
        public_key: str,
        verified: bool,
    ) -> dict[str, Any]:
        self._touch_organization(organization_id)
        record = {
            "request_id": f"req-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "peer_organization_id": peer_organization_id,
            "method": method.upper(),
            "url": url,
            "headers": headers,
            "body_hash": body_hash,
            "signature": signature,
            "public_key": public_key,
            "verified": bool(verified),
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signed_http_requests (
                    request_id, organization_id, peer_organization_id, method,
                    url, headers_json, body_hash, signature, public_key,
                    created_at, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["request_id"],
                    organization_id,
                    peer_organization_id,
                    record["method"],
                    url,
                    json.dumps(headers, sort_keys=True),
                    body_hash,
                    signature,
                    public_key,
                    record["created_at"],
                    1 if verified else 0,
                ),
            )
            conn.commit()
        return record

    def list_signed_http_requests(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM signed_http_requests"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "request_id": row["request_id"],
                "organization_id": row["organization_id"],
                "peer_organization_id": row["peer_organization_id"],
                "method": row["method"],
                "url": row["url"],
                "headers": json.loads(row["headers_json"]),
                "body_hash": row["body_hash"],
                "signature": row["signature"],
                "public_key": row["public_key"],
                "created_at": row["created_at"],
                "verified": bool(row["verified"]),
            }
            for row in rows
        ]

    def insights(self, *, organization_id: str | None = None) -> dict[str, Any]:
        query_filter = ""
        params: list[Any] = []
        if organization_id is not None:
            query_filter = " WHERE organization_id = ?"
            params = [organization_id]
        with self._connect() as conn:
            org_count = conn.execute("SELECT COUNT(*) FROM organizations" + query_filter, params).fetchone()[0]
            audit_count = conn.execute("SELECT COUNT(*) FROM audit_events" + query_filter, params).fetchone()[0]
            proof_count = conn.execute("SELECT COUNT(*) FROM verification_proofs" + query_filter, params).fetchone()[0]
            deployment_request_count = conn.execute("SELECT COUNT(*) FROM deployment_requests" + query_filter, params).fetchone()[0]
            deployment_count = conn.execute("SELECT COUNT(*) FROM deployments" + query_filter, params).fetchone()[0]
            receipt_count = conn.execute("SELECT COUNT(*) FROM deployment_receipts" + query_filter, params).fetchone()[0]
            assurance_count = conn.execute("SELECT COUNT(*) FROM assurance_records" + query_filter, params).fetchone()[0]
            trust_count = conn.execute("SELECT COUNT(*) FROM trust_scores" + query_filter, params).fetchone()[0]
            certification_count = conn.execute("SELECT COUNT(*) FROM certification_records" + query_filter, params).fetchone()[0]
            assurance_run_count = conn.execute("SELECT COUNT(*) FROM assurance_runs" + query_filter, params).fetchone()[0]
            policy_count = conn.execute("SELECT COUNT(*) FROM policy_definitions" + query_filter, params).fetchone()[0]
            decision_count = conn.execute("SELECT COUNT(*) FROM policy_decisions" + query_filter, params).fetchone()[0]
            key_count = conn.execute("SELECT COUNT(*) FROM key_registry" + query_filter, params).fetchone()[0]
            signed_audit_count = conn.execute("SELECT COUNT(*) FROM signed_audit_chain_events" + query_filter, params).fetchone()[0]
            federation_node_count = conn.execute("SELECT COUNT(*) FROM federation_nodes" + query_filter, params).fetchone()[0]
            federation_claim_count = conn.execute("SELECT COUNT(*) FROM federation_claims" + query_filter, params).fetchone()[0]
            federation_event_count = conn.execute("SELECT COUNT(*) FROM federation_events" + query_filter, params).fetchone()[0]
            stream_topic_count = conn.execute("SELECT COUNT(*) FROM event_stream_topics" + query_filter, params).fetchone()[0]
            stream_event_count = conn.execute("SELECT COUNT(*) FROM event_stream_events" + query_filter, params).fetchone()[0]
            analytics_snapshot_count = conn.execute(
                "SELECT COUNT(*) FROM dashboard_analytics_snapshots" + query_filter,
                params,
            ).fetchone()[0]
            ai_decision_snapshot_count = conn.execute(
                "SELECT COUNT(*) FROM ai_decision_snapshots" + query_filter,
                params,
            ).fetchone()[0]
            ai_action_snapshot_count = conn.execute(
                "SELECT COUNT(*) FROM ai_action_snapshots" + query_filter,
                params,
            ).fetchone()[0]
            workflow_count = conn.execute("SELECT COUNT(*) FROM workflow_instances" + query_filter, params).fetchone()[0]
            workflow_step_count = conn.execute("SELECT COUNT(*) FROM workflow_steps" + query_filter, params).fetchone()[0]
            zero_trust_policy_count = conn.execute("SELECT COUNT(*) FROM zero_trust_policies" + query_filter, params).fetchone()[0]
            zero_trust_decision_count = conn.execute("SELECT COUNT(*) FROM zero_trust_decisions" + query_filter, params).fetchone()[0]
            usage_total = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM usage_events" + query_filter, params).fetchone()[0]
            approved_request_count = conn.execute(
                "SELECT COUNT(*) FROM deployment_requests" + query_filter + (" AND status = 'approved'" if query_filter else " WHERE status = 'approved'"),
                params,
            ).fetchone()[0]
        audit_chain_valid = self.verify_audit_chain(organization_id=organization_id)
        signed_audit_chain_valid = self.verify_signed_audit_chain(organization_id=organization_id)
        latest_trust = self.latest_trust_score(organization_id=organization_id)
        trust_score = latest_trust["trust_score"] if latest_trust else None
        risk_score = max(
            0,
            100
            - (proof_count * 3 + deployment_count * 2 + approved_request_count + receipt_count * 2)
            - (0 if audit_chain_valid else 20),
        )
        return {
            "organization_id": organization_id or "all",
            "organizations": org_count,
            "audit_events": audit_count,
            "proofs": proof_count,
            "deployment_requests": deployment_request_count,
            "deployments": deployment_count,
            "deployment_receipts": receipt_count,
            "assurance_records": assurance_count,
            "assurance_runs": assurance_run_count,
            "trust_scores": trust_count,
            "certifications": certification_count,
            "policies": policy_count,
            "policy_decisions": decision_count,
            "signing_keys": key_count,
            "signed_audit_events": signed_audit_count,
            "federation_nodes": federation_node_count,
            "federation_claims": federation_claim_count,
            "federation_events": federation_event_count,
            "stream_topics": stream_topic_count,
            "stream_events": stream_event_count,
            "dashboard_analytics_snapshots": analytics_snapshot_count,
            "ai_decision_snapshots": ai_decision_snapshot_count,
            "ai_action_snapshots": ai_action_snapshot_count,
            "workflows": workflow_count,
            "workflow_steps": workflow_step_count,
            "zero_trust_policies": zero_trust_policy_count,
            "zero_trust_decisions": zero_trust_decision_count,
            "usage_total": int(usage_total),
            "approved_requests": approved_request_count,
            "audit_chain_valid": audit_chain_valid,
            "signed_audit_chain_valid": signed_audit_chain_valid,
            "trust_score": trust_score,
            "risk_score": risk_score,
            "status": "ok",
        }

    def metrics_snapshot(self, *, organization_id: str | None = None) -> dict[str, Any]:
        snapshot = self.insights(organization_id=organization_id)
        return {
            "organization_id": snapshot["organization_id"],
            "products_live": 5,
            "roles_supported": 4,
            "audit_events": snapshot["audit_events"],
            "proofs": snapshot["proofs"],
            "deployments": snapshot["deployments"],
            "deployment_requests": snapshot["deployment_requests"],
            "deployment_receipts": snapshot["deployment_receipts"],
            "dashboard_analytics_snapshots": snapshot["dashboard_analytics_snapshots"],
            "ai_decision_snapshots": snapshot["ai_decision_snapshots"],
            "ai_action_snapshots": snapshot["ai_action_snapshots"],
            "certifications": snapshot["certifications"],
            "trust_score": snapshot["trust_score"],
            "usage_total": snapshot["usage_total"],
            "stack": {
                "frameworks": ("Django", "FastAPI", "Spring"),
                "databases": ("PostgreSQL", "Redis", "Elasticsearch"),
                "cloud": ("AWS", "Azure", "GCP"),
                "devops": ("Docker", "Kubernetes", "Terraform"),
                "ci_cd": ("GitHub Actions", "GitLab CI"),
                "monitoring": ("Prometheus", "Grafana", "ELK"),
                "security": ("Keycloak", "Vault"),
            },
            "status": "ok",
        }

    @staticmethod
    def _row_to_audit_event(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "event_id": row["event_id"],
            "organization_id": row["organization_id"],
            "event_type": row["event_type"],
            "actor_user_id": row["actor_user_id"],
            "actor_role": row["actor_role"],
            "target": row["target"],
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
            "previous_hash": row["chain_previous_hash"],
            "payload_hash": row["chain_payload_hash"],
            "audit_hash": row["chain_audit_hash"],
        }

    @staticmethod
    def _row_to_proof(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "proof_id": row["proof_id"],
            "execution_id": row["execution_id"],
            "organization_id": row["organization_id"],
            "project_id": row["project_id"],
            "proof_hash": row["proof_hash"],
            "payload": json.loads(row["payload_json"]),
            "status": row["status"],
            "replayable": bool(row["replayable"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_request(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "request_id": row["request_id"],
            "organization_id": row["organization_id"],
            "service": row["service"],
            "environment": row["environment"],
            "image": row["image"],
            "rationale": row["rationale"],
            "requested_by": row["requested_by"],
            "requested_role": row["requested_role"],
            "status": row["status"],
            "approved_by": row["approved_by"],
            "approval_notes": row["approval_notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_deployment(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "deployment_id": row["deployment_id"],
            "request_id": row["request_id"],
            "organization_id": row["organization_id"],
            "service": row["service"],
            "environment": row["environment"],
            "image": row["image"],
            "status": row["status"],
            "approved": bool(row["approved"]),
            "deployed_by": row["deployed_by"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_deployment_receipt(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "receipt_id": row["receipt_id"],
            "organization_id": row["organization_id"],
            "deployment_id": row["deployment_id"],
            "request_id": row["request_id"],
            "proof_hash": row["proof_hash"],
            "audit_hash": row["audit_hash"],
            "receipt_hash": row["receipt_hash"],
            "status": row["status"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_assurance(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "assurance_id": row["assurance_id"],
            "organization_id": row["organization_id"],
            "deployment_id": row["deployment_id"],
            "trust_score": row["trust_score"],
            "risk_score": row["risk_score"],
            "proof_coverage": row["proof_coverage"],
            "policy_compliance": row["policy_compliance"],
            "assurance_status": row["assurance_status"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_trust_score(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "score_id": row["score_id"],
            "organization_id": row["organization_id"],
            "trust_score": row["trust_score"],
            "classification": row["classification"],
            "breakdown": json.loads(row["breakdown_json"]),
            "findings": json.loads(row["findings_json"]),
            "computed_at": row["computed_at"],
        }

    @staticmethod
    def _row_to_trust_stream(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "stream_id": row["stream_id"],
            "organization_id": row["organization_id"],
            "event_type": row["event_type"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_dashboard_analytics_snapshot(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "snapshot_id": row["snapshot_id"],
            "organization_id": row["organization_id"],
            "source": row["source"],
            "snapshot_type": row["snapshot_type"],
            "trust_score": int(row["trust_score"]),
            "trust_health": int(row["trust_health"]),
            "replay_health_score": int(row["replay_health_score"]),
            "evidence_coverage": int(row["evidence_coverage"]),
            "exception_pressure": int(row["exception_pressure"]),
            "alert_count": int(row["alert_count"]),
            "active_drivers": int(row["active_drivers"]),
            "completed_rides": int(row["completed_rides"]),
            "total_rides": int(row["total_rides"]),
            "guard_count": int(row["guard_count"]),
            "replay_failures": int(row["replay_failures"]),
            "hash_chain_failures": int(row["hash_chain_failures"]),
            "missing_traces": int(row["missing_traces"]),
            "receipts_count": int(row["receipts_count"]),
            "trace_count": int(row["trace_count"]),
            "payload": json.loads(row["payload_json"]),
            "snapshot_hash": row["snapshot_hash"],
            "window_bucket": row["window_bucket"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_ai_decision_snapshot(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "decision_id": row["decision_id"],
            "organization_id": row["organization_id"],
            "source": row["source"],
            "decision_type": row["decision_type"],
            "decision_lane": row["decision_lane"],
            "decision_action": row["decision_action"],
            "decision_priority": row["decision_priority"],
            "decision_summary": row["decision_summary"],
            "trust_score": int(row["trust_score"]),
            "trust_health": int(row["trust_health"]),
            "replay_health_score": int(row["replay_health_score"]),
            "evidence_coverage": int(row["evidence_coverage"]),
            "exception_pressure": int(row["exception_pressure"]),
            "alert_count": int(row["alert_count"]),
            "guard_count": int(row["guard_count"]),
            "replay_failures": int(row["replay_failures"]),
            "hash_chain_failures": int(row["hash_chain_failures"]),
            "missing_traces": int(row["missing_traces"]),
            "risk_score": int(row["risk_score"]),
            "risk_level": row["risk_level"],
            "confidence": float(row["confidence"]),
            "stability_index": int(row["stability_index"]),
            "recommended_actions": json.loads(row["recommended_actions_json"]),
            "watch_items": json.loads(row["watch_items_json"]),
            "payload": json.loads(row["payload_json"]),
            "snapshot_hash": row["snapshot_hash"],
            "window_bucket": row["window_bucket"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_ai_action_snapshot(row: sqlite3.Row) -> dict[str, Any]:
        payload = json.loads(row["payload_json"])
        action_payload = payload.get("action", {}) if isinstance(payload, dict) else {}
        return {
            "action_id": row["action_id"],
            "organization_id": row["organization_id"],
            "source": row["source"],
            "action_type": row["action_type"],
            "decision_id": row["decision_id"],
            "decision_lane": row["decision_lane"],
            "action_lane": row["action_lane"],
            "action_mode": row["action_mode"],
            "action_priority": row["action_priority"],
            "action_summary": row["action_summary"],
            "control_signal": row["control_signal"],
            "safety_gate": row["safety_gate"],
            "automation_tier": int(row["automation_tier"]),
            "decision_quality_score": int(row["decision_quality_score"]),
            "evidence_alignment_score": int(row["evidence_alignment_score"]),
            "calibrated_confidence": float(row["calibrated_confidence"]),
            "history_alignment_score": int(row["history_alignment_score"]),
            "quality_band": row["quality_band"],
            "execution_tier": action_payload.get("execution_tier"),
            "execution_tier_ready": bool(action_payload.get("execution_tier_ready", False)),
            "execution_tier_summary": action_payload.get("execution_tier_summary", ""),
            "execution_tier_controls": action_payload.get("execution_tier_controls", []),
            "trust_score": int(row["trust_score"]),
            "trust_health": int(row["trust_health"]),
            "replay_health_score": int(row["replay_health_score"]),
            "evidence_coverage": int(row["evidence_coverage"]),
            "exception_pressure": int(row["exception_pressure"]),
            "alert_count": int(row["alert_count"]),
            "guard_count": int(row["guard_count"]),
            "replay_failures": int(row["replay_failures"]),
            "hash_chain_failures": int(row["hash_chain_failures"]),
            "missing_traces": int(row["missing_traces"]),
            "stability_index": int(row["stability_index"]),
            "recommended_actions": json.loads(row["recommended_actions_json"]),
            "watch_items": json.loads(row["watch_items_json"]),
            "payload": payload,
            "snapshot_hash": row["snapshot_hash"],
            "window_bucket": row["window_bucket"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_outcome_snapshot(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "outcome_id": row["outcome_id"],
            "organization_id": row["organization_id"],
            "source": row["source"],
            "outcome_type": row["outcome_type"],
            "decision_id": row["decision_id"],
            "action_id": row["action_id"],
            "outcome_status": row["outcome_status"],
            "outcome_band": row["outcome_band"],
            "learning_band": row["learning_band"],
            "outcome_score": int(row["outcome_score"]),
            "trust_score": int(row["trust_score"]),
            "trust_health": int(row["trust_health"]),
            "replay_health_score": int(row["replay_health_score"]),
            "evidence_coverage": int(row["evidence_coverage"]),
            "exception_pressure": int(row["exception_pressure"]),
            "decision_quality_score": int(row["decision_quality_score"]),
            "evidence_alignment_score": int(row["evidence_alignment_score"]),
            "calibrated_confidence": float(row["calibrated_confidence"]),
            "history_alignment_score": int(row["history_alignment_score"]),
            "execution_tier": row["execution_tier"],
            "execution_tier_ready": bool(row["execution_tier_ready"]),
            "measurement_summary": row["measurement_summary"],
            "learning_actions": json.loads(row["learning_actions_json"]),
            "recalibration_notes": json.loads(row["recalibration_notes_json"]),
            "watch_items": json.loads(row["watch_items_json"]),
            "payload": json.loads(row["payload_json"]),
            "snapshot_hash": row["snapshot_hash"],
            "window_bucket": row["window_bucket"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_replay(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "replay_id": row["replay_id"],
            "organization_id": row["organization_id"],
            "deployment_id": row["deployment_id"],
            "proof_id": row["proof_id"],
            "receipt_id": row["receipt_id"],
            "audit_hash": row["audit_hash"],
            "replay_hash": row["replay_hash"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_usage(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "usage_id": row["usage_id"],
            "organization_id": row["organization_id"],
            "metric": row["metric"],
            "amount": row["amount"],
            "context": json.loads(row["context_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_organization(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "organization_id": row["organization_id"],
            "organization_name": row["organization_name"],
            "created_at": row["created_at"],
            "status": "active",
            "source": "store",
        }

    @staticmethod
    def _row_to_billing_record(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "billing_id": row["billing_id"],
            "organization_id": row["organization_id"],
            "plan": row["plan"],
            "usage_total": int(row["usage_total"]),
            "estimated_amount": float(row["estimated_amount"]),
            "billing_enabled": bool(row["billing_enabled"]),
            "created_at": row["created_at"],
            "status": "active" if row["billing_enabled"] else "preview",
        }

    def list_organizations(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM organizations"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_organization(row) for row in rows]

    def latest_organization(self, *, organization_id: str | None = None) -> dict[str, Any] | None:
        organizations = self.list_organizations(organization_id=organization_id, limit=1)
        return organizations[0] if organizations else None

    @staticmethod
    def _row_to_policy_definition(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "policy_id": row["policy_id"],
            "organization_id": row["organization_id"],
            "policy_name": row["policy_name"],
            "version": row["version"],
            "rule_type": row["rule_type"],
            "rule_payload": json.loads(row["rule_payload_json"]),
            "active": bool(row["active"]),
            "created_by": row["created_by"],
            "policy_hash": row["policy_hash"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_policy_decision(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "decision_id": row["decision_id"],
            "organization_id": row["organization_id"],
            "policy_id": row["policy_id"],
            "action": row["action"],
            "allowed": bool(row["allowed"]),
            "reason": row["reason"],
            "actor_user_id": row["actor_user_id"],
            "target": row["target"],
            "payload_hash": row["payload_hash"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_certification(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "certification_id": row["certification_id"],
            "organization_id": row["organization_id"],
            "certification_type": row["certification_type"],
            "trust_score": row["trust_score"],
            "assurance_status": row["assurance_status"],
            "audit_chain_hash": row["audit_chain_hash"],
            "proof_count": row["proof_count"],
            "receipt_count": row["receipt_count"],
            "certification_hash": row["certification_hash"],
            "signature": row["signature"],
            "public_key_id": row["public_key_id"],
            "issued_at": row["issued_at"],
            "payload": json.loads(row["payload_json"]),
        }

    @staticmethod
    def _row_to_assurance_run(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "assurance_run_id": row["assurance_run_id"],
            "organization_id": row["organization_id"],
            "trust_score": row["trust_score"],
            "previous_trust_score": row["previous_trust_score"],
            "drift": row["drift"],
            "risk_score": row["risk_score"],
            "assurance_status": row["assurance_status"],
            "alert_level": row["alert_level"],
            "findings": json.loads(row["findings_json"]),
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_assurance_drift(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "drift_event_id": row["drift_event_id"],
            "organization_id": row["organization_id"],
            "assurance_run_id": row["assurance_run_id"],
            "previous_trust_score": row["previous_trust_score"],
            "current_trust_score": row["current_trust_score"],
            "drift": row["drift"],
            "severity": row["severity"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_assurance_alert(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "alert_id": row["alert_id"],
            "organization_id": row["organization_id"],
            "assurance_run_id": row["assurance_run_id"],
            "alert_level": row["alert_level"],
            "message": row["message"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_retention_policy(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "retention_policy_id": row["retention_policy_id"],
            "organization_id": row["organization_id"],
            "record_type": row["record_type"],
            "retention_days": row["retention_days"],
            "legal_hold": bool(row["legal_hold"]),
            "deletion_allowed": bool(row["deletion_allowed"]),
            "policy_hash": row["policy_hash"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_assurance_report(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "report_id": row["report_id"],
            "organization_id": row["organization_id"],
            "report_classification": row["report_classification"],
            "report_hash": row["report_hash"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_trust_exchange_event(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "trust_exchange_event_id": row["trust_exchange_event_id"],
            "organization_id": row["organization_id"],
            "external_organization_id": row["external_organization_id"],
            "receipt_hash": row["receipt_hash"],
            "proof_hash": row["proof_hash"],
            "audit_hash": row["audit_hash"],
            "certification_hash": row["certification_hash"],
            "valid": bool(row["valid"]),
            "details": json.loads(row["details_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_signing_key(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "key_id": row["key_id"],
            "organization_id": row["organization_id"],
            "key_family": row["key_family"],
            "key_version": row["key_version"],
            "public_key": row["public_key"],
            "status": row["status"],
            "rotated_from_key_id": row["rotated_from_key_id"],
            "reason": row["reason"],
            "created_at": row["created_at"],
            "rotated_at": row["rotated_at"],
        }

    @staticmethod
    def _row_to_key_rotation(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "rotation_event_id": row["rotation_event_id"],
            "organization_id": row["organization_id"],
            "key_family": row["key_family"],
            "previous_key_id": row["previous_key_id"],
            "next_key_id": row["next_key_id"],
            "rotated_by": row["rotated_by"],
            "reason": row["reason"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_signed_audit(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "signed_event_id": row["signed_event_id"],
            "organization_id": row["organization_id"],
            "event_id": row["event_id"],
            "key_id": row["key_id"],
            "key_version": row["key_version"],
            "previous_hash": row["previous_hash"],
            "payload_hash": row["payload_hash"],
            "audit_hash": row["audit_hash"],
            "signature": row["signature"],
            "public_key": row["public_key"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_federation_node(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "node_id": row["node_id"],
            "organization_id": row["organization_id"],
            "peer_organization_id": row["peer_organization_id"],
            "jurisdiction": row["jurisdiction"],
            "role": row["role"],
            "public_key_id": row["public_key_id"],
            "endpoint": row["endpoint"],
            "trust_level": row["trust_level"],
            "status": row["status"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_federation_claim(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "claim_id": row["claim_id"],
            "organization_id": row["organization_id"],
            "peer_organization_id": row["peer_organization_id"],
            "claim_type": row["claim_type"],
            "claim_hash": row["claim_hash"],
            "proof_hash": row["proof_hash"],
            "audit_hash": row["audit_hash"],
            "receipt_hash": row["receipt_hash"],
            "certification_hash": row["certification_hash"],
            "signature": row["signature"],
            "public_key_id": row["public_key_id"],
            "valid": bool(row["valid"]),
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_federation_event(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "federation_event_id": row["federation_event_id"],
            "organization_id": row["organization_id"],
            "peer_organization_id": row["peer_organization_id"],
            "event_type": row["event_type"],
            "details": json.loads(row["details_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_stream_topic(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "topic_name": row["topic_name"],
            "organization_id": row["organization_id"],
            "description": row["description"],
            "retention_days": row["retention_days"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_stream_event(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "event_id": row["event_id"],
            "organization_id": row["organization_id"],
            "topic_name": row["topic_name"],
            "partition_key": row["partition_key"],
            "event_type": row["event_type"],
            "offset_number": row["offset_number"],
            "headers": json.loads(row["headers_json"]),
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_workflow_instance(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "workflow_id": row["workflow_id"],
            "organization_id": row["organization_id"],
            "workflow_name": row["workflow_name"],
            "state": row["state"],
            "definition": json.loads(row["definition_json"]),
            "input": json.loads(row["input_json"]),
            "output": json.loads(row["output_json"]),
            "current_step": row["current_step"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "completed_at": row["completed_at"],
        }

    @staticmethod
    def _row_to_workflow_step(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "step_id": row["step_id"],
            "workflow_id": row["workflow_id"],
            "organization_id": row["organization_id"],
            "step_name": row["step_name"],
            "step_index": row["step_index"],
            "status": row["status"],
            "input": json.loads(row["input_json"]),
            "output": json.loads(row["output_json"]),
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_zero_trust_policy(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "policy_id": row["policy_id"],
            "organization_id": row["organization_id"],
            "policy_name": row["policy_name"],
            "version": row["version"],
            "rule_type": row["rule_type"],
            "rule_payload": json.loads(row["rule_payload_json"]),
            "active": bool(row["active"]),
            "created_by": row["created_by"],
            "policy_hash": row["policy_hash"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_zero_trust_decision(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "decision_id": row["decision_id"],
            "organization_id": row["organization_id"],
            "policy_id": row["policy_id"],
            "subject": row["subject"],
            "action": row["action"],
            "resource": row["resource"],
            "allowed": bool(row["allowed"]),
            "reason": row["reason"],
            "context_hash": row["context_hash"],
            "created_at": row["created_at"],
        }


_DEFAULT_STORE: PlatformStore | None = None


def get_platform_store() -> PlatformStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = PlatformStore()
    return _DEFAULT_STORE


__all__ = ["DEFAULT_ORGANIZATION_ID", "PlatformStore", "get_platform_store"]
