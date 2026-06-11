from __future__ import annotations

import hashlib
import json
from typing import Any

from afritech.partner_verification import build_partner_verification_packet


class PartnerVerificationClient:
    def prepare_verify_request(
        self,
        *,
        tenant_id: str,
        region_id: str,
        trace_hash: str,
        replay_hash: str,
        receipt_hash: str,
        authority_hash: str | None = None,
        execution_fingerprint: str | None = None,
        publication_target: str,
        network: str = "external-ledger-testnet",
        publisher_id: str = "afritech-anchor-publisher",
        external_reference: str | None = None,
        expected_anchor_id: str | None = None,
        expected_commitment_hash: str | None = None,
        expected_publication_hash: str | None = None,
        expected_receipt_hash: str | None = None,
    ) -> dict[str, Any]:
        resolved_authority_hash = authority_hash or receipt_hash
        resolved_execution_fingerprint = execution_fingerprint or self._default_execution_fingerprint(
            trace_hash=trace_hash,
            replay_hash=replay_hash,
            receipt_hash=receipt_hash,
            authority_hash=resolved_authority_hash,
        )
        return {
            "tenant_id": tenant_id,
            "region_id": region_id,
            "trace_hash": trace_hash,
            "replay_hash": replay_hash,
            "receipt_hash": receipt_hash,
            "authority_hash": resolved_authority_hash,
            "execution_fingerprint": resolved_execution_fingerprint,
            "publication_target": publication_target,
            "network": network,
            "publisher_id": publisher_id,
            "external_reference": external_reference,
            "expected_anchor_id": expected_anchor_id,
            "expected_commitment_hash": expected_commitment_hash,
            "expected_publication_hash": expected_publication_hash,
            "expected_receipt_hash": expected_receipt_hash,
        }

    def verify_locally(self, payload: dict[str, Any]) -> dict[str, Any]:
        packet = build_partner_verification_packet(
            tenant_id=str(payload["tenant_id"]),
            region_id=str(payload["region_id"]),
            trace_hash=str(payload["trace_hash"]),
            replay_hash=str(payload["replay_hash"]),
            receipt_hash=str(payload["receipt_hash"]),
            authority_hash=str(payload["authority_hash"]),
            execution_fingerprint=str(payload["execution_fingerprint"]),
            publication_target=str(payload["publication_target"]),
            network=str(payload.get("network", "external-ledger-testnet")),
            publisher_id=str(payload.get("publisher_id", "afritech-anchor-publisher")),
            external_reference=payload.get("external_reference"),
            expected_anchor_id=payload.get("expected_anchor_id"),
            expected_commitment_hash=payload.get("expected_commitment_hash"),
            expected_publication_hash=payload.get("expected_publication_hash"),
            expected_receipt_hash=payload.get("expected_receipt_hash"),
        )
        return packet.canonical_dict()

    def decode_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = (
            "anchor_id",
            "publication_id",
            "verification_status",
            "trace_hash",
            "replay_hash",
            "receipt_hash",
            "authority_hash",
            "execution_fingerprint",
            "commitment_hash",
            "publication_hash",
            "authority_boundary",
        )
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError(f"partner verification response missing fields: {missing}")
        return payload

    @staticmethod
    def _default_execution_fingerprint(
        *,
        trace_hash: str,
        replay_hash: str,
        receipt_hash: str,
        authority_hash: str,
    ) -> str:
        encoded = json.dumps(
            {
                "trace_hash": trace_hash,
                "replay_hash": replay_hash,
                "receipt_hash": receipt_hash,
                "authority_hash": authority_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
