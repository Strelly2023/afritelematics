"""Cross-chain light client and merkle commitment helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from afritech.core_platform.cryptographic_consensus import _canonicalize_seal, _hash


@dataclass(frozen=True)
class LightClientState:
    """Minimal anchor state for light-client style verification."""

    chain_id: str
    block_height: int
    state_root: str
    validator_set_hash: str
    block_hash: str | None = None
    trusted_height: int | None = None
    timestamp: str | None = None

    def canonical(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chain_id": str(self.chain_id).strip(),
            "block_height": int(self.block_height),
            "state_root": str(self.state_root).strip(),
            "validator_set_hash": str(self.validator_set_hash).strip(),
        }
        if self.block_hash is not None:
            payload["block_hash"] = str(self.block_hash).strip()
        if self.trusted_height is not None:
            payload["trusted_height"] = int(self.trusted_height)
        if self.timestamp is not None:
            payload["timestamp"] = str(self.timestamp).strip()
        return _canonicalize_seal(payload)


def _state_payload(state: Mapping[str, Any] | LightClientState) -> dict[str, Any]:
    if isinstance(state, LightClientState):
        payload = state.canonical()
    elif hasattr(state, "canonical"):
        payload = _canonicalize_seal(state.canonical())  # type: ignore[arg-type]
    elif isinstance(state, Mapping):
        payload = _canonicalize_seal(dict(state))
    else:  # pragma: no cover - defensive
        raise ValueError("light_client_state_required")

    required = ("chain_id", "block_height", "state_root", "validator_set_hash")
    for field in required:
        if field not in payload or payload[field] in (None, ""):
            raise ValueError(f"missing_light_client_state_field:{field}")
    return payload


def _hash_leaf(leaf: Any) -> str:
    return _hash(leaf, domain="cross_chain_merkle_leaf")


def _hash_parent(left: str, right: str) -> str:
    return _hash({"left": left, "right": right}, domain="cross_chain_merkle_parent")


def _dedupe_sorted(values: Sequence[str]) -> list[str]:
    normalized = sorted({str(value).strip() for value in values if str(value).strip()})
    return normalized


def build_merkle_root(leaves: Sequence[Any]) -> str:
    leaf_hashes = [_hash_leaf(leaf) for leaf in leaves]
    if not leaf_hashes:
        return _hash({"leaves": []}, domain="cross_chain_merkle_root")
    level = leaf_hashes
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else level[index]
            next_level.append(_hash_parent(left, right))
        level = next_level
    return level[0]


def build_merkle_proof(leaves: Sequence[Any], index: int) -> dict[str, Any]:
    if index < 0 or index >= len(leaves):
        raise IndexError("merkle_proof_index_out_of_range")

    leaf_hashes = [_hash_leaf(leaf) for leaf in leaves]
    current_index = index
    path: list[dict[str, str]] = []
    level = leaf_hashes[:]

    while len(level) > 1:
        sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
        if sibling_index >= len(level):
            sibling_index = current_index
        sibling_hash = level[sibling_index]
        path.append(
            {
                "position": "right" if current_index % 2 == 0 else "left",
                "hash": sibling_hash,
            }
        )

        next_level: list[str] = []
        for idx in range(0, len(level), 2):
            left = level[idx]
            right = level[idx + 1] if idx + 1 < len(level) else level[idx]
            next_level.append(_hash_parent(left, right))
        level = next_level
        current_index //= 2

    root = level[0]
    leaf = leaves[index]
    return {
        "index": index,
        "leaf": leaf,
        "leaf_hash": leaf_hashes[index],
        "path": path,
        "root": root,
        "leaf_count": len(leaves),
    }


def verify_merkle_proof(leaf: Any, proof: Mapping[str, Any], root: str) -> bool:
    if not isinstance(proof, Mapping) or not proof:
        return False

    current = _hash_leaf(leaf)
    leaf_hash = str(proof.get("leaf_hash", "")).strip()
    if leaf_hash and leaf_hash != current:
        return False

    for step in proof.get("path", []):
        if not isinstance(step, Mapping):
            return False
        position = str(step.get("position", "")).strip().lower()
        sibling_hash = str(step.get("hash", "")).strip()
        if not sibling_hash or position not in {"left", "right"}:
            return False
        if position == "left":
            current = _hash_parent(sibling_hash, current)
        else:
            current = _hash_parent(current, sibling_hash)
    return current == str(root).strip()


def build_cross_chain_bridge(
    zk_bundle: Mapping[str, Any],
    light_client_state: Mapping[str, Any] | LightClientState,
    *,
    receipt_batch: Sequence[Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(zk_bundle, Mapping) or not zk_bundle:
        raise ValueError("zk_bundle_required")

    receipt_commitment = str(zk_bundle.get("commitment", "")).strip()
    if not receipt_commitment:
        raise ValueError("zk_commitment_required")

    state_payload = _state_payload(light_client_state)
    receipts = _dedupe_sorted(
        [
            receipt_commitment,
            *(
                str(item.get("commitment", "")).strip()
                if isinstance(item, Mapping)
                else str(item).strip()
                for item in (receipt_batch or [])
            ),
        ]
    )
    if receipt_commitment not in receipts:
        receipts.append(receipt_commitment)
        receipts = _dedupe_sorted(receipts)

    receipt_root = build_merkle_root(receipts)
    receipt_proof = build_merkle_proof(receipts, receipts.index(receipt_commitment))
    state_hash = _hash(state_payload, domain="cross_chain_light_client_state")

    bridge_payload = {
        "type": "cross_chain_bridge",
        "version": "1.0",
        "scheme": "novatrust-light-client-v1",
        "zk_commitment": receipt_commitment,
        "receipt_root": receipt_root,
        "receipt_proof": receipt_proof,
        "light_client_state": state_payload,
        "light_client_state_hash": state_hash,
        "receipt_batch_size": len(receipts),
    }
    bridge_hash = _hash(bridge_payload, domain="cross_chain_bridge")
    bridge_payload["bridge_hash"] = bridge_hash
    bridge_payload["bridge_id"] = f"bridge-{bridge_hash[:16]}"
    return bridge_payload


def verify_cross_chain_bridge(
    bridge: Mapping[str, Any],
    *,
    expected_commitment: str | None = None,
    expected_light_client_state: Mapping[str, Any] | LightClientState | None = None,
) -> dict[str, Any]:
    if not isinstance(bridge, Mapping) or not bridge:
        return {"valid": False, "reason": "cross_chain_bridge_required"}

    scheme = str(bridge.get("scheme", "")).strip()
    zk_commitment = str(bridge.get("zk_commitment", "")).strip()
    receipt_root = str(bridge.get("receipt_root", "")).strip()
    bridge_hash = str(bridge.get("bridge_hash", "")).strip()
    receipt_proof = bridge.get("receipt_proof")
    state_payload = bridge.get("light_client_state")
    state_hash = str(bridge.get("light_client_state_hash", "")).strip()

    if scheme != "novatrust-light-client-v1":
        return {"valid": False, "reason": "cross_chain_bridge_scheme_invalid"}
    if not zk_commitment or not receipt_root or not bridge_hash:
        return {"valid": False, "reason": "cross_chain_bridge_incomplete"}
    if not isinstance(receipt_proof, Mapping):
        return {"valid": False, "reason": "cross_chain_receipt_proof_missing"}
    if not isinstance(state_payload, Mapping):
        return {"valid": False, "reason": "cross_chain_light_client_state_missing"}

    canonical_state = _state_payload(state_payload)
    expected_state_hash = _hash(canonical_state, domain="cross_chain_light_client_state")
    if state_hash != expected_state_hash:
        return {"valid": False, "reason": "cross_chain_light_client_state_hash_mismatch"}

    if expected_light_client_state is not None:
        expected_state = _state_payload(expected_light_client_state)
        if expected_state != canonical_state:
            return {"valid": False, "reason": "cross_chain_light_client_state_mismatch"}

    payload_without_hash = {
        key: value
        for key, value in bridge.items()
        if key not in {"bridge_hash", "bridge_id"}
    }
    expected_bridge_hash = _hash(payload_without_hash, domain="cross_chain_bridge")
    if bridge_hash != expected_bridge_hash:
        return {"valid": False, "reason": "cross_chain_bridge_hash_mismatch"}

    if expected_commitment is not None and str(expected_commitment).strip() != zk_commitment:
        return {"valid": False, "reason": "cross_chain_commitment_mismatch"}

    proof_commitment = str(receipt_proof.get("leaf", "")).strip()
    if proof_commitment and proof_commitment != zk_commitment:
        return {"valid": False, "reason": "cross_chain_proof_leaf_mismatch"}
    if not verify_merkle_proof(zk_commitment, receipt_proof, receipt_root):
        return {"valid": False, "reason": "cross_chain_merkle_proof_invalid"}

    return {
        "valid": True,
        "reason": "cross_chain_bridge_verified",
        "bridge_hash": bridge_hash,
        "receipt_root": receipt_root,
        "zk_commitment": zk_commitment,
        "light_client_state_hash": expected_state_hash,
    }


__all__ = [
    "LightClientState",
    "build_cross_chain_bridge",
    "build_merkle_proof",
    "build_merkle_root",
    "verify_cross_chain_bridge",
    "verify_merkle_proof",
]
