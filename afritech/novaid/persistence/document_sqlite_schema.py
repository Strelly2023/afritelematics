from __future__ import annotations

import sqlite3
from collections.abc import Iterable


DOCUMENT_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS novaid_identity_documents (
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    issuing_country TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    document_number_reference TEXT,
    issued_at TEXT,
    expires_at TEXT,
    verified_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL,
    document_payload_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    PRIMARY KEY (tenant_id, document_id),

    CHECK (length(trim(tenant_id)) > 0),
    CHECK (length(trim(document_id)) > 0),
    CHECK (length(trim(identity_id)) > 0),
    CHECK (length(trim(document_type)) > 0),
    CHECK (length(trim(issuing_country)) = 2),
    CHECK (length(trim(verification_status)) > 0),
    CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS
idx_novaid_identity_documents_identity
ON novaid_identity_documents (
    tenant_id,
    identity_id,
    created_at,
    document_id
);

CREATE INDEX IF NOT EXISTS
idx_novaid_identity_documents_status
ON novaid_identity_documents (
    tenant_id,
    verification_status,
    updated_at
);

CREATE TABLE IF NOT EXISTS novaid_document_captures (
    tenant_id TEXT NOT NULL,
    capture_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    capture_reference TEXT NOT NULL,
    capture_side TEXT NOT NULL,
    media_type TEXT NOT NULL,
    checksum TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    capture_order INTEGER NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    PRIMARY KEY (tenant_id, capture_id),

    FOREIGN KEY (tenant_id, document_id)
        REFERENCES novaid_identity_documents (
            tenant_id,
            document_id
        )
        ON DELETE CASCADE,

    CHECK (length(trim(capture_reference)) > 0),
    CHECK (length(trim(checksum)) > 0),
    CHECK (capture_order >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS
idx_novaid_document_capture_order
ON novaid_document_captures (
    tenant_id,
    document_id,
    capture_order
);

CREATE INDEX IF NOT EXISTS
idx_novaid_document_captures_document
ON novaid_document_captures (
    tenant_id,
    document_id,
    captured_at
);

CREATE TABLE IF NOT EXISTS
novaid_identity_verifications (
    tenant_id TEXT NOT NULL,
    verification_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    correlation_id TEXT,
    request_id TEXT,
    actor_identity_id TEXT,
    document_type TEXT NOT NULL,
    purpose TEXT NOT NULL,
    decision TEXT NOT NULL,
    assurance_level TEXT NOT NULL,
    combined_score REAL NOT NULL,
    policy_version TEXT NOT NULL,
    document_version INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    verified_at TEXT NOT NULL,
    expires_at TEXT,
    reason_codes_json TEXT NOT NULL,
    verification_payload_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    PRIMARY KEY (tenant_id, verification_id),

    FOREIGN KEY (tenant_id, document_id)
        REFERENCES novaid_identity_documents (
            tenant_id,
            document_id
        )
        ON DELETE RESTRICT,

    CHECK (length(trim(workflow_id)) > 0),
    CHECK (combined_score >= 0.0),
    CHECK (combined_score <= 1.0),
    CHECK (document_version >= 1),
    CHECK (attempt_number >= 1)
);

CREATE UNIQUE INDEX IF NOT EXISTS
idx_novaid_identity_verification_workflow
ON novaid_identity_verifications (
    tenant_id,
    workflow_id,
    verification_id
);

CREATE INDEX IF NOT EXISTS
idx_novaid_identity_verification_document
ON novaid_identity_verifications (
    tenant_id,
    document_id,
    verified_at,
    verification_id
);

CREATE INDEX IF NOT EXISTS
idx_novaid_identity_verification_identity
ON novaid_identity_verifications (
    tenant_id,
    identity_id,
    verified_at,
    verification_id
);

CREATE TABLE IF NOT EXISTS
novaid_identity_verification_evidence_refs (
    tenant_id TEXT NOT NULL,
    verification_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    evidence_version INTEGER NOT NULL,
    collected_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    PRIMARY KEY (
        tenant_id,
        verification_id,
        evidence_type
    ),

    FOREIGN KEY (tenant_id, verification_id)
        REFERENCES novaid_identity_verifications (
            tenant_id,
            verification_id
        )
        ON DELETE CASCADE,

    CHECK (length(trim(evidence_type)) > 0),
    CHECK (length(trim(evidence_id)) > 0),
    CHECK (evidence_version >= 1)
);

CREATE UNIQUE INDEX IF NOT EXISTS
idx_novaid_identity_verification_evidence_id
ON novaid_identity_verification_evidence_refs (
    tenant_id,
    verification_id,
    evidence_id
);

CREATE TABLE IF NOT EXISTS
novaid_document_persistence_events (
    tenant_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    actor_identity_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    PRIMARY KEY (tenant_id, event_id),

    CHECK (length(trim(event_type)) > 0),
    CHECK (length(trim(aggregate_type)) > 0),
    CHECK (length(trim(aggregate_id)) > 0),
    CHECK (aggregate_version >= 1),
    CHECK (length(trim(actor_identity_id)) > 0),
    CHECK (length(trim(correlation_id)) > 0),
    CHECK (length(trim(request_id)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS
idx_novaid_document_persistence_event_version
ON novaid_document_persistence_events (
    tenant_id,
    aggregate_type,
    aggregate_id,
    aggregate_version
);

CREATE INDEX IF NOT EXISTS
idx_novaid_document_persistence_event_correlation
ON novaid_document_persistence_events (
    tenant_id,
    correlation_id,
    occurred_at,
    event_id
);
"""


EXPECTED_DOCUMENT_TABLES = frozenset(
    {
        "novaid_identity_documents",
        "novaid_document_captures",
        "novaid_identity_verifications",
        "novaid_identity_verification_evidence_refs",
        "novaid_document_persistence_events",
    }
)


FORBIDDEN_DOCUMENT_SCHEMA_TERMS = frozenset(
    {
        "raw_image",
        "image_bytes",
        "document_bytes",
        "raw_document",
        "raw_selfie",
        "selfie_bytes",
        "raw_video",
        "video_bytes",
        "raw_mrz",
        "mrz_text",
        "barcode_payload",
        "raw_barcode",
        "nfc_dump",
        "raw_nfc",
        "provider_payload",
        "provider_response",
        "face_embedding",
        "embedding",
        "embeddings",
        "biometric_template",
        "template_bytes",
        "api_key",
        "provider_secret",
        "private_key",
        "access_token",
        "refresh_token",
        "password",
    }
)


def initialize_document_sqlite_schema(
    connection: sqlite3.Connection,
) -> None:
    if not isinstance(connection, sqlite3.Connection):
        raise TypeError(
            "SQLITE_CONNECTION_REQUIRED"
        )

    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(DOCUMENT_SQLITE_SCHEMA)


def list_document_tables(
    connection: sqlite3.Connection,
) -> tuple[str, ...]:
    rows: Iterable[tuple[str]] = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name LIKE 'novaid_%'
        ORDER BY name
        """
    )

    return tuple(
        row[0]
        for row in rows
    )


__all__ = [
    "DOCUMENT_SQLITE_SCHEMA",
    "EXPECTED_DOCUMENT_TABLES",
    "FORBIDDEN_DOCUMENT_SCHEMA_TERMS",
    "initialize_document_sqlite_schema",
    "list_document_tables",
]
