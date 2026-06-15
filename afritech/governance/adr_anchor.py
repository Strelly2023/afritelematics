"""Governed ADR hashing and on-chain anchoring helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from afritech.architecture.anchor_indexer import remember_publication
from afritech.architecture.blockchain_anchor import (
    BlockchainAnchorPublication,
    get_chain_profile,
    publish_architecture_anchor_contract_with_profile,
)


ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = ROOT / "afritech/governance/adr"


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_yaml_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ModuleNotFoundError:
        return {"raw_text": text}
    try:
        payload = yaml.safe_load(text)
    except Exception:
        payload = {"raw_text": text}
    return payload if isinstance(payload, dict) else {"raw_text": text}


def resolve_adr_path(adr_id: str) -> Path:
    candidates = sorted(ADR_DIR.glob(f"{adr_id}*.yaml"))
    if not candidates:
        raise FileNotFoundError(f"ADR artifact not found: {adr_id}")
    return candidates[0]


def hash_adr_artifact(adr_id: str) -> dict[str, Any]:
    path = resolve_adr_path(adr_id)
    text = path.read_text(encoding="utf-8")
    payload = _load_yaml_payload(path)
    title = str(payload.get("title") or adr_id)
    status = str(payload.get("status") or "unknown")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    metadata_hash = _canonical_hash({k: payload.get(k) for k in ("id", "title", "status", "decision")})
    return {
        "classification": "ADR_HASH_RECORD",
        "status": "READY",
        "adr_id": adr_id,
        "title": title,
        "state": status,
        "path": str(path.relative_to(ROOT)),
        "content_hash": content_hash,
        "metadata_hash": metadata_hash,
        "authority_boundary": "adr_hash_is_public_reference_only",
    }


@dataclass(frozen=True)
class AdrAnchorRecord:
    adr_id: str
    title: str
    state: str
    path: str
    content_hash: str
    anchor_id: str
    publication_id: str
    network: str
    chain_id: int | None
    contract_address: str | None
    transaction_hash: str | None
    block_number: int | None
    explorer_url: str | None
    status: str
    anchor_mode: str
    authority_boundary: str = "adr_hash_publication_is_read_only"
    meta: dict[str, Any] = field(default_factory=dict)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.adr_anchor_record.v1",
            "adr_id": self.adr_id,
            "title": self.title,
            "state": self.state,
            "path": self.path,
            "content_hash": self.content_hash,
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "network": self.network,
            "chain_id": self.chain_id,
            "contract_address": self.contract_address,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "explorer_url": self.explorer_url,
            "status": self.status,
            "anchor_mode": self.anchor_mode,
            "authority_boundary": self.authority_boundary,
            "meta": self.meta,
        }


def build_adr_anchor_preview(adr_id: str) -> dict[str, Any]:
    record = hash_adr_artifact(adr_id)
    return {
        "classification": "ADR_HASH_PREVIEW",
        "status": "READY",
        "adr_id": adr_id,
        "title": record["title"],
        "state": record["state"],
        "path": record["path"],
        "content_hash": record["content_hash"],
        "authority_boundary": record["authority_boundary"],
    }


def build_adr_contract_link_packet(
    adr_id: str,
    *,
    profile_name: str = "sepolia",
) -> dict[str, Any]:
    record = hash_adr_artifact(adr_id)
    profile = get_chain_profile(profile_name)
    anchor_id = f"adr-{adr_id.lower()}"
    content_hash = str(record["content_hash"])
    proof_hash_bytes32 = f"0x{content_hash}"
    publication_id = f"{anchor_id}:{content_hash[:12]}"
    contract_address = None
    try:
        import os

        contract_address = os.getenv("AFRITECH_CHAIN_CONTRACT_ADDRESS") or None
    except Exception:
        contract_address = None

    return {
        "classification": "ADR_CONTRACT_LINK_PACKET",
        "status": "READY",
        "adr": record,
        "anchor_id": anchor_id,
        "publication_id": publication_id,
        "profile": profile.key,
        "network": profile.network,
        "chain_id": profile.chain_id,
        "contract_name": "ArchitectureAnchor",
        "contract_address": contract_address,
        "contract_method": "anchorProof",
        "contract_signature": "anchorProof(string,bytes32)",
        "contract_arguments": {
            "anchorId": anchor_id,
            "proofHash": proof_hash_bytes32,
        },
        "verification_call": {
            "method": "verifyAnchor",
            "signature": "verifyAnchor(string,bytes32)",
            "arguments": {
                "anchorId": anchor_id,
                "expectedProofHash": proof_hash_bytes32,
            },
        },
        "event_signature": "ProofAnchored(string,bytes32,address,uint256)",
        "explorer_base_url": profile.explorer_base_url,
        "authority_boundary": "adr_contract_link_is_public_reference_only",
    }


def anchor_adr_to_chain(
    adr_id: str,
    *,
    profile_name: str = "sepolia",
    require_live: bool = False,
) -> AdrAnchorRecord:
    record = hash_adr_artifact(adr_id)
    anchor_id = f"adr-{adr_id.lower()}"
    publication_id = f"{anchor_id}:{record['content_hash'][:12]}"
    publication: BlockchainAnchorPublication = publish_architecture_anchor_contract_with_profile(
        anchor_id=anchor_id,
        publication_id=publication_id,
        proof_hash=record["content_hash"],
        profile_name=profile_name,
        require_live=require_live,
    )
    remember_publication(publication, source="governance.adr_anchor")
    payload = publication.canonical_dict()
    return AdrAnchorRecord(
        adr_id=adr_id,
        title=str(record["title"]),
        state=str(record["state"]),
        path=str(record["path"]),
        content_hash=str(record["content_hash"]),
        anchor_id=anchor_id,
        publication_id=publication_id,
        network=str(payload.get("network") or profile_name),
        chain_id=int(payload["chain_id"]) if payload.get("chain_id") is not None else None,
        contract_address=str(payload.get("contract_address") or "") or None,
        transaction_hash=str(payload.get("transaction_hash") or "") or None,
        block_number=payload.get("block_number"),
        explorer_url=str(payload.get("explorer_url") or "") or None,
        status=str(payload.get("status") or "unknown"),
        anchor_mode=str(payload.get("anchor_mode") or "smart_contract"),
        meta={"publication": payload, "hash": record},
    )


__all__ = [
    "AdrAnchorRecord",
    "anchor_adr_to_chain",
    "build_adr_anchor_preview",
    "build_adr_contract_link_packet",
    "hash_adr_artifact",
    "resolve_adr_path",
]
