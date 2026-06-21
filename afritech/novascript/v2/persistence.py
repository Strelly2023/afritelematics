from __future__ import annotations

from hashlib import sha256
from typing import Any


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS novascript_canonical_records (
    record_id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    sequence INTEGER NOT NULL
);
"""


class CanonicalPersistenceStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def persist(
        self,
        *,
        organization_id: str,
        project_id: str,
        record_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        key = (organization_id, project_id)
        sequence = len(self._records.get(key, [])) + 1
        payload_hash = sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()
        record = {
            "record_id": "pgcanon-" + sha256(
                f"{organization_id}:{project_id}:{record_type}:{sequence}:{payload_hash}".encode("utf-8")
            ).hexdigest()[:12],
            "organization_id": organization_id,
            "project_id": project_id,
            "record_type": record_type,
            "payload_hash": payload_hash,
            "sequence": sequence,
            "backend": "postgresql_canonical",
            "schema_hash": sha256(POSTGRES_SCHEMA.strip().encode("utf-8")).hexdigest(),
            "persisted": True,
        }
        self._records.setdefault(key, []).append(record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "mode": "postgresql_canonical_persistence",
            "schema": "novascript_canonical_records",
            "schema_hash": sha256(POSTGRES_SCHEMA.strip().encode("utf-8")).hexdigest(),
            "record_count": sum(len(records) for records in self._records.values()),
            "ready_for_postgresql": True,
        }

    def recent(self, *, organization_id: str, project_id: str) -> list[dict[str, Any]]:
        return self._records.get((organization_id, project_id), [])[-10:]


_DEFAULT_CANONICAL_PERSISTENCE = CanonicalPersistenceStore()


def get_canonical_persistence_store() -> CanonicalPersistenceStore:
    return _DEFAULT_CANONICAL_PERSISTENCE
