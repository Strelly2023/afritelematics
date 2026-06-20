from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from afritech.afriprogramming.assurance.pki import PKIService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store
from afritech.afriprogramming.v9.schema import ensure_v9_schema


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _stable_json(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash(payload: dict[str, Any]) -> str:
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TransparencyEntry:
    log_id: str
    organization_id: str
    certificate_id: str
    subject: str
    issuer: str
    certificate_hash: str
    chain_hash: str
    previous_hash: str
    status: str
    public_key_id: str
    signature: str
    created_at: str


class CertificateTransparencyLogService:
    """Append-only certificate transparency log with deterministic chain hashing."""

    def __init__(self, repository: PlatformStore | None = None, pki_service: PKIService | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.pki = pki_service or PKIService(self.repository)
        ensure_v9_schema(self.repository)

    def append(
        self,
        *,
        organization_id: str,
        subject: str,
        issuer: str,
        key_family: str = "audit",
        status: str = "active",
        certificate_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        certificate_payload = certificate_payload or {
            "organization_id": organization_id,
            "subject": subject,
            "issuer": issuer,
            "key_family": key_family,
            "status": status,
        }
        signed = self.pki.sign(
            organization_id=organization_id,
            payload=certificate_payload,
            key_family=key_family,
        )
        previous = self.latest(organization_id=organization_id)
        previous_hash = previous["chain_hash"] if previous else ""
        certificate_hash = signed["payload_hash"]
        chain_hash = _hash(
            {
                "organization_id": organization_id,
                "subject": subject,
                "issuer": issuer,
                "certificate_hash": certificate_hash,
                "previous_hash": previous_hash,
                "status": status,
            }
        )
        record = {
            "log_id": f"ct-{uuid4().hex[:12]}",
            "organization_id": organization_id,
            "certificate_id": signed["key_id"],
            "subject": subject,
            "issuer": issuer,
            "certificate_hash": certificate_hash,
            "chain_hash": chain_hash,
            "previous_hash": previous_hash,
            "status": status,
            "public_key_id": signed["key_id"],
            "signature": signed["signature"],
            "created_at": _now(),
        }
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            conn.execute(
                """
                INSERT INTO certificate_transparency_log (
                    log_id, organization_id, certificate_id, subject, issuer,
                    certificate_hash, chain_hash, previous_hash, status,
                    public_key_id, signature, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["log_id"],
                    organization_id,
                    record["certificate_id"],
                    subject,
                    issuer,
                    certificate_hash,
                    chain_hash,
                    previous_hash,
                    status,
                    record["public_key_id"],
                    record["signature"],
                    record["created_at"],
                ),
            )
            conn.commit()
        return record

    def list(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM certificate_transparency_log"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "log_id": row["log_id"],
                "organization_id": row["organization_id"],
                "certificate_id": row["certificate_id"],
                "subject": row["subject"],
                "issuer": row["issuer"],
                "certificate_hash": row["certificate_hash"],
                "chain_hash": row["chain_hash"],
                "previous_hash": row["previous_hash"],
                "status": row["status"],
                "public_key_id": row["public_key_id"],
                "signature": row["signature"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def latest(self, organization_id: str | None = None) -> dict[str, Any] | None:
        records = self.list(organization_id=organization_id, limit=1)
        return records[0] if records else None

    def verify(self, organization_id: str | None = None) -> dict[str, Any]:
        entries = self.list(organization_id=organization_id, limit=5000)
        previous_hash = ""
        for entry in reversed(entries):
            payload = {
                "organization_id": entry["organization_id"],
                "subject": entry["subject"],
                "issuer": entry["issuer"],
                "certificate_hash": entry["certificate_hash"],
                "previous_hash": entry["previous_hash"],
                "status": entry["status"],
            }
            if entry["previous_hash"] != previous_hash:
                return {"valid": False, "reason": "chain break", "chain_hash": entry["chain_hash"]}
            if _hash(payload) != entry["chain_hash"]:
                return {"valid": False, "reason": "chain hash mismatch", "chain_hash": entry["chain_hash"]}
            previous_hash = entry["chain_hash"]
        return {"valid": True, "chain_hash": previous_hash}


class KeyRevocationAuthority:
    """Deterministic key revocation authority backed by the platform store."""

    def __init__(self, repository: PlatformStore | None = None, pki_service: PKIService | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.pki = pki_service or PKIService(self.repository)
        ensure_v9_schema(self.repository)

    def revoke(
        self,
        *,
        organization_id: str,
        key_id: str,
        reason: str,
        revoked_by: str = "system",
    ) -> dict[str, Any]:
        current = next(
            (
                key
                for key in self.pki.list_keys(organization_id=organization_id, limit=1000)
                if key["key_id"] == key_id
            ),
            None,
        )
        if current is None:
            raise KeyError(key_id)
        certificate_hash = _hash(
            {
                "organization_id": organization_id,
                "key_id": key_id,
                "reason": reason,
                "revoked_by": revoked_by,
                "key_family": current["key_family"],
                "key_version": current["key_version"],
            }
        )
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            conn.execute(
                """
                UPDATE key_registry
                SET status = ?, reason = ?, rotated_at = ?
                WHERE key_id = ? AND organization_id = ?
                """,
                ("revoked", reason, _now(), key_id, organization_id),
            )
            conn.execute(
                """
                INSERT INTO key_revocation_events (
                    revocation_id, organization_id, key_id, key_family,
                    key_version, reason, revoked_by, status, certificate_hash,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"rev-{uuid4().hex[:12]}",
                    organization_id,
                    key_id,
                    current["key_family"],
                    int(current["key_version"]),
                    reason,
                    revoked_by,
                    "revoked",
                    certificate_hash,
                    _now(),
                ),
            )
            conn.commit()
        return {
            "organization_id": organization_id,
            "key_id": key_id,
            "key_family": current["key_family"],
            "key_version": int(current["key_version"]),
            "reason": reason,
            "revoked_by": revoked_by,
            "status": "revoked",
            "certificate_hash": certificate_hash,
        }

    def revocations(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM key_revocation_events"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "revocation_id": row["revocation_id"],
                "organization_id": row["organization_id"],
                "key_id": row["key_id"],
                "key_family": row["key_family"],
                "key_version": row["key_version"],
                "reason": row["reason"],
                "revoked_by": row["revoked_by"],
                "status": row["status"],
                "certificate_hash": row["certificate_hash"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


__all__ = [
    "CertificateTransparencyLogService",
    "KeyRevocationAuthority",
]
