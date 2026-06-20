from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from nacl.signing import SigningKey, VerifyKey

from afritech.afriprogramming.persistence import (
    PlatformStore,
    _derive_signing_seed,
    _hash_payload,
    _stable_json,
    get_platform_store,
)


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class KeyBundle:
    key_id: str
    organization_id: str
    key_family: str
    key_version: int
    public_key: str
    status: str
    created_at: str
    rotated_at: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "organization_id": self.organization_id,
            "key_family": self.key_family,
            "key_version": self.key_version,
            "public_key": self.public_key,
            "status": self.status,
            "created_at": self.created_at,
            "rotated_at": self.rotated_at,
        }


class PKIService:
    """Deterministic org-scoped PKI and key-rotation helper."""

    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def current_key(self, *, organization_id: str, key_family: str = "audit") -> dict[str, Any]:
        return self.repository.current_signing_key(organization_id=organization_id, key_family=key_family)

    def list_keys(
        self,
        *,
        organization_id: str | None = None,
        key_family: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.repository.list_signing_keys(
            organization_id=organization_id,
            key_family=key_family,
            limit=limit,
        )

    def list_rotations(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.repository.list_key_rotations(organization_id=organization_id, limit=limit)

    def rotate(
        self,
        *,
        organization_id: str,
        key_family: str = "audit",
        rotated_by: str = "system",
        reason: str = "rotation",
    ) -> dict[str, Any]:
        return self.repository.rotate_signing_key(
            organization_id=organization_id,
            key_family=key_family,
            rotated_by=rotated_by,
            reason=reason,
        )

    def bundle(
        self,
        *,
        organization_id: str,
        key_family: str = "audit",
    ) -> dict[str, Any]:
        key = self.current_key(organization_id=organization_id, key_family=key_family)
        return {
            **key,
            "bundle_issued_at": _now(),
        }

    def sign(
        self,
        *,
        organization_id: str,
        payload: dict[str, Any],
        key_family: str = "audit",
    ) -> dict[str, Any]:
        key = self.current_key(organization_id=organization_id, key_family=key_family)
        signing_key = SigningKey(
            _derive_signing_seed(
                organization_id=organization_id,
                key_family=key_family,
                key_version=int(key["key_version"]),
            )
        )
        raw = _stable_json(payload).encode("utf-8")
        signature = signing_key.sign(raw).signature.hex()
        return {
            "key_id": key["key_id"],
            "key_version": int(key["key_version"]),
            "public_key": key["public_key"],
            "payload_hash": _hash_payload(payload),
            "signature": signature,
            "payload": payload,
        }

    def verify(self, *, public_key: str, payload: dict[str, Any], signature: str) -> bool:
        import json

        try:
            VerifyKey(bytes.fromhex(public_key)).verify(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
                bytes.fromhex(signature),
            )
            return True
        except Exception:
            return False


__all__ = ["KeyBundle", "PKIService"]
