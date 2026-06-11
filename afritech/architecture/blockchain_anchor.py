"""Real blockchain anchoring helpers for architecture proof publication."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import json
import os
from typing import Any
from urllib import request


@dataclass(frozen=True)
class ChainProfile:
    key: str
    chain_name: str
    network: str
    chain_id: int
    explorer_base_url: str
    rpc_env_var: str
    rollout_stage: str
    recommended_use: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "chain_name": self.chain_name,
            "network": self.network,
            "chain_id": self.chain_id,
            "explorer_base_url": self.explorer_base_url,
            "rpc_env_var": self.rpc_env_var,
            "rollout_stage": self.rollout_stage,
            "recommended_use": self.recommended_use,
        }


@dataclass(frozen=True)
class BlockchainAnchorPublication:
    anchor_id: str
    publication_id: str
    chain_name: str
    network: str
    chain_id: int
    contract_address: str
    transaction_hash: str
    block_number: int | None
    explorer_url: str
    status: str
    method: str | None = None
    proof_hash: str | None = None
    anchor_mode: str = "raw_transaction"
    meta: dict[str, Any] = field(default_factory=dict)
    authority_boundary: str = "blockchain_anchor_proves_publication_not_runtime_truth"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.blockchain_anchor_publication.v1",
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "chain_name": self.chain_name,
            "network": self.network,
            "chain_id": self.chain_id,
            "contract_address": self.contract_address,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "explorer_url": self.explorer_url,
            "status": self.status,
            "method": self.method,
            "proof_hash": self.proof_hash,
            "anchor_mode": self.anchor_mode,
            "meta": self.meta,
            "authority_boundary": self.authority_boundary,
        }


CHAIN_PROFILES = {
    "sepolia": ChainProfile(
        key="sepolia",
        chain_name="Ethereum Sepolia",
        network="sepolia",
        chain_id=11155111,
        explorer_base_url="https://sepolia.etherscan.io/tx/",
        rpc_env_var="AFRITECH_CHAIN_RPC_URL_SEPOLIA",
        rollout_stage="pilot",
        recommended_use="First live partner verification sessions and dry-run publications.",
    ),
    "mainnet": ChainProfile(
        key="mainnet",
        chain_name="Ethereum Mainnet",
        network="mainnet",
        chain_id=1,
        explorer_base_url="https://etherscan.io/tx/",
        rpc_env_var="AFRITECH_CHAIN_RPC_URL_MAINNET",
        rollout_stage="production",
        recommended_use="Post-pilot immutable publication once Sepolia evidence and runbooks are stable.",
    ),
}


class BlockchainAnchorStore:
    """Small in-memory store for latest blockchain anchor publications."""

    def __init__(self) -> None:
        self._publications: dict[str, BlockchainAnchorPublication] = {}

    def remember(self, publication: BlockchainAnchorPublication) -> None:
        self._publications[publication.anchor_id] = publication

    def load(self, anchor_id: str) -> BlockchainAnchorPublication:
        if anchor_id not in self._publications:
            raise KeyError(anchor_id)
        return self._publications[anchor_id]

    def latest(self) -> BlockchainAnchorPublication | None:
        if not self._publications:
            return None
        return next(reversed(self._publications.values()))


def list_chain_profiles() -> tuple[ChainProfile, ...]:
    return tuple(CHAIN_PROFILES.values())


def get_chain_profile(profile_name: str) -> ChainProfile:
    try:
        return CHAIN_PROFILES[profile_name.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported chain profile: {profile_name}") from exc


def build_chain_promotion_plan() -> dict[str, Any]:
    default_profile = os.getenv("AFRITECH_CHAIN_PROFILE", "sepolia").strip().lower() or "sepolia"
    return {
        "default_profile": default_profile,
        "promotion_path": [
            {
                "stage": 1,
                "profile": "sepolia",
                "goal": "prove transaction publication, partner CLI validation, and dashboard readiness on testnet",
            },
            {
                "stage": 2,
                "profile": "mainnet",
                "goal": "promote immutable publication once Sepolia verification sessions and operational controls pass",
            },
        ],
        "profiles": [profile.canonical_dict() for profile in list_chain_profiles()],
        "authority_boundary": "chain promotion changes publication venue only; replay and governed execution remain truth authority",
    }


def resolve_chain_rpc_url(profile: ChainProfile, rpc_url: str | None = None) -> str:
    if rpc_url and rpc_url.strip():
        return rpc_url.strip()
    env_value = os.getenv(profile.rpc_env_var) or os.getenv("AFRITECH_CHAIN_RPC_URL")
    if env_value and env_value.strip():
        return env_value.strip()
    raise ValueError(
        f"rpc_url required for profile '{profile.key}'; provide rpc_url or set {profile.rpc_env_var}"
    )


def _rpc_call(rpc_url: str, method: str, params: list[Any]) -> Any:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        sort_keys=True,
    ).encode("utf-8")
    req = request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("error"):
        raise RuntimeError(str(body["error"]))
    return body.get("result")


def publish_architecture_anchor_to_evm(
    *,
    anchor_id: str,
    publication_id: str,
    rpc_url: str,
    signed_tx_hex: str,
    chain_name: str = "Ethereum Compatible Chain",
    network: str = "sepolia",
    chain_id: int = 11155111,
    contract_address: str = "0x0000000000000000000000000000000000000000",
    explorer_base_url: str = "https://sepolia.etherscan.io/tx/",
) -> BlockchainAnchorPublication:
    if not rpc_url.strip():
        raise ValueError("rpc_url required")
    if not signed_tx_hex.strip():
        raise ValueError("signed_tx_hex required")
    tx_hash = str(_rpc_call(rpc_url, "eth_sendRawTransaction", [signed_tx_hex]))
    receipt = _rpc_call(rpc_url, "eth_getTransactionReceipt", [tx_hash])
    block_number = None
    status = "PENDING_CHAIN_CONFIRMATION"
    if isinstance(receipt, dict):
        block_hex = receipt.get("blockNumber")
        if isinstance(block_hex, str) and block_hex.startswith("0x"):
            block_number = int(block_hex, 16)
        status_hex = receipt.get("status")
        if status_hex == "0x1":
            status = "CONFIRMED"
        elif status_hex == "0x0":
            status = "FAILED"
    return BlockchainAnchorPublication(
        anchor_id=anchor_id,
        publication_id=publication_id,
        chain_name=chain_name,
        network=network,
        chain_id=chain_id,
        contract_address=contract_address,
        transaction_hash=tx_hash,
        block_number=block_number,
        explorer_url=f"{explorer_base_url}{tx_hash.removeprefix('0x')}",
        status=status,
    )


def publish_architecture_anchor_with_profile(
    *,
    anchor_id: str,
    publication_id: str,
    signed_tx_hex: str,
    profile_name: str = "sepolia",
    rpc_url: str | None = None,
    contract_address: str = "0x0000000000000000000000000000000000000000",
    chain_name: str | None = None,
    network: str | None = None,
    chain_id: int | None = None,
    explorer_base_url: str | None = None,
) -> BlockchainAnchorPublication:
    profile = get_chain_profile(profile_name)
    effective_rpc_url = resolve_chain_rpc_url(profile, rpc_url)
    return publish_architecture_anchor_to_evm(
        anchor_id=anchor_id,
        publication_id=publication_id,
        rpc_url=effective_rpc_url,
        signed_tx_hex=signed_tx_hex,
        chain_name=chain_name or profile.chain_name,
        network=network or profile.network,
        chain_id=chain_id or profile.chain_id,
        contract_address=contract_address,
        explorer_base_url=explorer_base_url or profile.explorer_base_url,
    )


def publish_architecture_anchor_contract_with_profile(
    *,
    anchor_id: str,
    publication_id: str,
    proof_hash: str,
    profile_name: str = "sepolia",
) -> BlockchainAnchorPublication:
    """Publish an architecture proof via the ArchitectureAnchor smart contract.

    This function is live-mode capable, but still fail-closed into the chain
    publisher's runtime-safe fallback when chain dependencies or env vars are
    unavailable. Importing this module never requires Web3.
    """

    from afritech.chain.anchor_publisher import publish_anchor

    profile = get_chain_profile(profile_name)
    receipt = publish_anchor(proof_hash, profile_name=profile.key)
    payload = receipt.canonical_dict()
    tx_hash = str(payload.get("tx_hash") or f"fallback-{proof_hash[:16]}")
    explorer_url = payload.get("explorer_url") or ""
    if not explorer_url and tx_hash.startswith("0x"):
        explorer_url = f"{profile.explorer_base_url}{tx_hash.removeprefix('0x')}"
    return BlockchainAnchorPublication(
        anchor_id=anchor_id,
        publication_id=publication_id,
        chain_name=str(payload.get("chain_name") or profile.chain_name),
        network=str(payload.get("network") or profile.network),
        chain_id=int(payload["chain_id"]) if payload.get("chain_id") is not None else profile.chain_id,
        contract_address=str(payload.get("contract_address") or os.getenv("AFRITECH_CHAIN_CONTRACT_ADDRESS", "")),
        transaction_hash=tx_hash,
        block_number=payload.get("block_number"),
        explorer_url=str(explorer_url),
        status=str(payload.get("status") or "runtime_safe_fallback"),
        method=payload.get("method") or "anchorProof",
        proof_hash=str(payload.get("proof_hash") or proof_hash),
        anchor_mode="smart_contract",
        meta=dict(payload.get("meta") or {}),
    )


__all__ = [
    "ChainProfile",
    "build_chain_promotion_plan",
    "BlockchainAnchorPublication",
    "BlockchainAnchorStore",
    "get_chain_profile",
    "list_chain_profiles",
    "publish_architecture_anchor_to_evm",
    "publish_architecture_anchor_contract_with_profile",
    "publish_architecture_anchor_with_profile",
    "resolve_chain_rpc_url",
]
