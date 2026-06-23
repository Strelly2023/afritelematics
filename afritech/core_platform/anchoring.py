"""Chain-of-trust anchoring metadata for NovaTrust packets."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import request

from afritech.core_platform.signing import canonical_bytes, sign_packet


@dataclass(frozen=True)
class TrustAnchor:
    anchor_id: str
    method: str
    network: str
    payload_hash: str
    signature_hash: str
    status: str

    def canonical(self) -> dict[str, str]:
        return {
            "anchor_id": self.anchor_id,
            "method": self.method,
            "network": self.network,
            "payload_hash": self.payload_hash,
            "signature_hash": self.signature_hash,
            "status": self.status,
        }


@dataclass(frozen=True)
class OptionalBlockchainAnchor:
    status: str
    provider: str
    payload_hash: str
    anchor_id: str | None
    transaction_id: str | None
    network: str | None
    message: str

    def canonical(self) -> dict[str, str | None]:
        return {
            "status": self.status,
            "provider": self.provider,
            "payload_hash": self.payload_hash,
            "anchor_id": self.anchor_id,
            "transaction_id": self.transaction_id,
            "network": self.network,
            "message": self.message,
        }


def anchor_packet(packet: Mapping[str, Any], *, network: str = "novatrust-local-anchor") -> TrustAnchor:
    signature = sign_packet(packet)
    payload_hash = hashlib.sha256(canonical_bytes(packet)).hexdigest()
    signature_hash = hashlib.sha256(signature.signature.encode("ascii")).hexdigest()
    anchor_id = hashlib.sha256(f"{network}:{payload_hash}:{signature_hash}".encode("utf-8")).hexdigest()
    return TrustAnchor(
        anchor_id=f"anchor_{anchor_id[:24]}",
        method="deterministic_timestamp_anchor",
        network=network,
        payload_hash=payload_hash,
        signature_hash=signature_hash,
        status="anchored",
    )


def build_optional_blockchain_anchor(
    packet: Mapping[str, Any],
    *,
    publisher: Any | None = None,
) -> OptionalBlockchainAnchor:
    """Return optional external anchor metadata without making it mandatory.

    If `NOVATRUST_BLOCKCHAIN_ANCHOR_URL` is not configured, the function returns
    a disabled adapter status. When configured, it posts the payload hash to the
    provider and expects JSON metadata back. Tests can pass `publisher` to avoid
    network access and exercise the adapter contract deterministically.
    """

    payload_hash = hashlib.sha256(canonical_bytes(packet)).hexdigest()
    provider = os.environ.get("NOVATRUST_BLOCKCHAIN_ANCHOR_PROVIDER", "disabled")
    endpoint = os.environ.get("NOVATRUST_BLOCKCHAIN_ANCHOR_URL")
    if publisher is None and not endpoint:
        return OptionalBlockchainAnchor(
            status="disabled",
            provider=provider,
            payload_hash=payload_hash,
            anchor_id=None,
            transaction_id=None,
            network=None,
            message="optional blockchain anchoring is not configured",
        )

    payload = {
        "payload_hash": payload_hash,
        "method": "novatrust_optional_blockchain_anchor",
    }
    if publisher is not None:
        published = publisher(payload)
    else:
        assert endpoint is not None
        req = request.Request(
            endpoint,
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=20) as response:
            published = json.loads(response.read().decode("utf-8"))
    if not isinstance(published, Mapping):
        raise ValueError("blockchain anchor provider must return a JSON object")
    return OptionalBlockchainAnchor(
        status=str(published.get("status", "published")),
        provider=str(published.get("provider", provider or "external")),
        payload_hash=payload_hash,
        anchor_id=str(published["anchor_id"]) if published.get("anchor_id") else None,
        transaction_id=str(published["transaction_id"]) if published.get("transaction_id") else None,
        network=str(published["network"]) if published.get("network") else None,
        message=str(published.get("message", "optional external anchor metadata returned")),
    )
