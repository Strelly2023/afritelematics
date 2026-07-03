"""Smart-contract client for ArchitectureAnchor live publication.

The module is intentionally import-safe when Web3 or live chain environment
variables are absent. Live dependencies are loaded only when a chain function is
called, so local tests and API startup can keep using deterministic fallbacks.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, cast

from afritech.chain.contracts.architecture_anchor_abi import ARCHITECTURE_ANCHOR_ABI
from afritech.chain.contracts.architecture_anchor_v2_abi import ARCHITECTURE_ANCHOR_V2_ABI
from afritech.chain.contracts.deployment_config import (
    get_deployment_profile,
    validate_deployment_profile,
)


def _load_web3() -> Any:
    try:
        from web3 import Web3
    except ModuleNotFoundError as exc:
        raise RuntimeError("web3 is required for live contract anchoring") from exc
    return Web3


def _normalise_proof_hash(proof_hash: str) -> bytes:
    value = proof_hash.removeprefix("0x")
    if len(value) != 64:
        raise ValueError("proof_hash must be a 32-byte hex string")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError("proof_hash must be hex encoded") from exc


def _bytes32_hex(value: bytes) -> str:
    return f"0x{value.hex()}"


def _anchor_id_to_bytes32(anchor_id: str) -> bytes:
    if not anchor_id or not anchor_id.strip():
        raise ValueError("anchor_id is required")
    Web3 = _load_web3()
    return bytes(Web3.keccak(text=anchor_id.strip()))


def _context_to_bytes32(context: str) -> bytes:
    value = (context or "GENERAL").strip().upper()
    if not value:
        value = "GENERAL"
    if value.startswith("0x"):
        raw = bytes.fromhex(value.removeprefix("0x"))
        if len(raw) != 32:
            raise ValueError("context hex value must be 32 bytes")
        return raw
    encoded = value.encode("utf-8")
    if len(encoded) > 32:
        raise ValueError("context must be 32 bytes or fewer when utf-8 encoded")
    return encoded.ljust(32, b"\x00")


def _bytes32_to_context(value: Any) -> str:
    if value is None:
        return ""
    raw = value if isinstance(value, (bytes, bytearray)) else bytes.fromhex(str(value).removeprefix("0x"))
    return bytes(raw).rstrip(b"\x00").decode("utf-8", errors="replace")


def _raw_transaction(signed: Any) -> Any:
    return getattr(signed, "rawTransaction", getattr(signed, "raw_transaction", None))


def _web3(profile: dict[str, Any]) -> Any:
    Web3 = _load_web3()
    return Web3(Web3.HTTPProvider(str(profile["rpc_url"])))


def _address(web3: Any) -> Any:
    address = os.getenv("AFRITECH_CHAIN_ADDRESS") or os.getenv("AFRITECH_CHAIN_ADDRESS_CHECKSUM")
    if not address:
        raise RuntimeError("Missing AFRITECH_CHAIN_ADDRESS")
    Web3 = _load_web3()
    if not Web3.is_address(address):
        raise ValueError("Invalid AFRITECH_CHAIN_ADDRESS")
    return cast(Any, Web3.to_checksum_address(address))


def _contract(web3: Any, profile: dict[str, Any]) -> Any:
    Web3 = _load_web3()
    contract_address = str(profile["contract_address"])
    if not Web3.is_address(contract_address):
        raise ValueError("Invalid AFRITECH_CHAIN_CONTRACT_ADDRESS")
    return web3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=ARCHITECTURE_ANCHOR_ABI,
    )


def _v2_contract(web3: Any, profile: dict[str, Any]) -> Any:
    Web3 = _load_web3()
    contract_address = str(profile.get("contract_address_v2") or "")
    if not Web3.is_address(contract_address):
        raise ValueError("Invalid AFRITECH_CHAIN_CONTRACT_ADDRESS_V2")
    return web3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=ARCHITECTURE_ANCHOR_V2_ABI,
    )


def _validate_v2_profile(profile: dict[str, Any]) -> None:
    validate_deployment_profile(profile)
    Web3 = _load_web3()
    contract_address = str(profile.get("contract_address_v2") or "")
    if not contract_address:
        raise RuntimeError("Missing AFRITECH_CHAIN_CONTRACT_ADDRESS_V2")
    if not Web3.is_address(contract_address):
        raise RuntimeError("Invalid AFRITECH_CHAIN_CONTRACT_ADDRESS_V2")


def _private_key() -> str:
    private_key = os.getenv("AFRITECH_CHAIN_PRIVATE_KEY")
    if private_key and private_key.strip():
        return private_key.strip()

    private_key_path = os.getenv("AFRITECH_CHAIN_PRIVATE_KEY_PATH")
    if private_key_path and private_key_path.strip():
        try:
            return open(private_key_path.strip(), encoding="utf-8").read().strip()
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read AFRITECH_CHAIN_PRIVATE_KEY_PATH: {exc}"
            ) from exc

    raise RuntimeError("Missing AFRITECH_CHAIN_PRIVATE_KEY")


def anchor_proof_on_chain(
    anchor_id: str,
    proof_hash: str,
    *,
    profile_name: str | None = None,
) -> Dict[str, Any]:
    """Submit an architecture proof hash to ArchitectureAnchor.anchorProof."""

    profile = get_deployment_profile(profile_name)
    validate_deployment_profile(profile)
    proof_hash_bytes = _normalise_proof_hash(proof_hash)
    web3 = _web3(profile)
    if not web3.is_connected():
        raise RuntimeError("Web3 not connected")

    account = _address(web3)
    contract = _contract(web3, profile)
    private_key = _private_key()
    nonce = web3.eth.get_transaction_count(account)
    gas_price = web3.to_wei(float(profile["gas_price_gwei"]), "gwei")

    tx = contract.functions.anchorProof(anchor_id, proof_hash_bytes).build_transaction(
        {
            "chainId": int(profile["chain_id"]),
            "from": account,
            "nonce": nonce,
            "gas": int(os.getenv("AFRITECH_CHAIN_GAS_LIMIT", "200000")),
            "gasPrice": gas_price,
        }
    )

    signed = web3.eth.account.sign_transaction(tx, private_key)
    raw_tx = _raw_transaction(signed)
    if raw_tx is None:
        raise RuntimeError("signed transaction did not expose raw transaction bytes")

    tx_hash_bytes = web3.eth.send_raw_transaction(raw_tx)
    receipt = web3.eth.wait_for_transaction_receipt(
        tx_hash_bytes,
        timeout=int(profile["timeout"]),
    )
    decoded = _decode_proof_anchored_event(receipt, profile_name=profile_name)
    tx_hash = tx_hash_bytes.hex()
    if not tx_hash.startswith("0x"):
        tx_hash = f"0x{tx_hash}"

    return {
        "status": "live",
        "tx_hash": tx_hash,
        "block_number": receipt["blockNumber"],
        "contract_address": profile["contract_address"],
        "anchor_id": anchor_id,
        "proof_hash": proof_hash.removeprefix("0x"),
        "network": profile["network"],
        "chain_id": profile["chain_id"],
        "chain_name": profile["chain_name"],
        "explorer_url": f"{profile['explorer_base_url']}{tx_hash.removeprefix('0x')}",
        "method": "anchorProof",
        "event": decoded,
    }


def anchor_proof_v2_on_chain(
    anchor_id: str,
    proof_hash: str,
    *,
    context: str = "GENERAL",
    enforce_unique_proof: bool = True,
    profile_name: str | None = None,
) -> Dict[str, Any]:
    """Submit a proof hash to ArchitectureAnchorV2.anchorProof."""

    profile = get_deployment_profile(profile_name)
    _validate_v2_profile(profile)
    proof_hash_bytes = _normalise_proof_hash(proof_hash)
    anchor_id_bytes = _anchor_id_to_bytes32(anchor_id)
    context_bytes = _context_to_bytes32(context)
    web3 = _web3(profile)
    if not web3.is_connected():
        raise RuntimeError("Web3 not connected")

    account = _address(web3)
    contract = _v2_contract(web3, profile)
    private_key = _private_key()
    nonce = web3.eth.get_transaction_count(account)
    gas_price = web3.to_wei(float(profile["gas_price_gwei"]), "gwei")

    tx = contract.functions.anchorProof(
        anchor_id_bytes,
        proof_hash_bytes,
        context_bytes,
        enforce_unique_proof,
    ).build_transaction(
        {
            "chainId": int(profile["chain_id"]),
            "from": account,
            "nonce": nonce,
            "gas": int(os.getenv("AFRITECH_CHAIN_V2_GAS_LIMIT", "260000")),
            "gasPrice": gas_price,
        }
    )

    signed = web3.eth.account.sign_transaction(tx, private_key)
    raw_tx = _raw_transaction(signed)
    if raw_tx is None:
        raise RuntimeError("signed transaction did not expose raw transaction bytes")

    tx_hash_bytes = web3.eth.send_raw_transaction(raw_tx)
    receipt = web3.eth.wait_for_transaction_receipt(
        tx_hash_bytes,
        timeout=int(profile["timeout"]),
    )
    decoded = _decode_proof_anchored_v2_event(receipt, profile_name=profile_name)
    tx_hash = tx_hash_bytes.hex()
    if not tx_hash.startswith("0x"):
        tx_hash = f"0x{tx_hash}"

    return {
        "status": "live",
        "tx_hash": tx_hash,
        "block_number": receipt["blockNumber"],
        "contract_address": profile["contract_address_v2"],
        "anchor_id": anchor_id,
        "anchor_id_bytes32": _bytes32_hex(anchor_id_bytes),
        "proof_hash": proof_hash.removeprefix("0x"),
        "context": context,
        "context_bytes32": _bytes32_hex(context_bytes),
        "network": profile["network"],
        "chain_id": profile["chain_id"],
        "chain_name": profile["chain_name"],
        "explorer_url": f"{profile['explorer_base_url']}{tx_hash.removeprefix('0x')}",
        "method": "anchorProofV2",
        "event": decoded,
    }


def anchor_batch_v2_on_chain(
    anchors: list[dict[str, str]],
    *,
    enforce_unique_proof: bool = True,
    profile_name: str | None = None,
) -> Dict[str, Any]:
    """Submit a bounded batch to ArchitectureAnchorV2.anchorBatch."""

    if not anchors:
        raise ValueError("anchors batch is empty")
    max_batch = int(os.getenv("AFRITECH_CHAIN_V2_MAX_BATCH_SIZE", "50"))
    if len(anchors) > max_batch:
        raise ValueError(f"anchors batch exceeds max size {max_batch}")

    profile = get_deployment_profile(profile_name)
    _validate_v2_profile(profile)
    anchor_ids = [_anchor_id_to_bytes32(item["anchor_id"]) for item in anchors]
    proof_hashes = [_normalise_proof_hash(item["proof_hash"]) for item in anchors]
    contexts = [_context_to_bytes32(item.get("context", "GENERAL")) for item in anchors]
    web3 = _web3(profile)
    if not web3.is_connected():
        raise RuntimeError("Web3 not connected")

    account = _address(web3)
    contract = _v2_contract(web3, profile)
    private_key = _private_key()
    nonce = web3.eth.get_transaction_count(account)
    gas_price = web3.to_wei(float(profile["gas_price_gwei"]), "gwei")
    gas_limit = int(os.getenv("AFRITECH_CHAIN_V2_BATCH_GAS_LIMIT", str(200000 + len(anchors) * 90000)))

    tx = contract.functions.anchorBatch(
        anchor_ids,
        proof_hashes,
        contexts,
        enforce_unique_proof,
    ).build_transaction(
        {
            "chainId": int(profile["chain_id"]),
            "from": account,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
        }
    )

    signed = web3.eth.account.sign_transaction(tx, private_key)
    raw_tx = _raw_transaction(signed)
    if raw_tx is None:
        raise RuntimeError("signed transaction did not expose raw transaction bytes")

    tx_hash_bytes = web3.eth.send_raw_transaction(raw_tx)
    receipt = web3.eth.wait_for_transaction_receipt(
        tx_hash_bytes,
        timeout=int(profile["timeout"]),
    )
    tx_hash = tx_hash_bytes.hex()
    if not tx_hash.startswith("0x"):
        tx_hash = f"0x{tx_hash}"

    return {
        "status": "live",
        "tx_hash": tx_hash,
        "block_number": receipt["blockNumber"],
        "contract_address": profile["contract_address_v2"],
        "batch_size": len(anchors),
        "anchors": [
            {
                "anchor_id": item["anchor_id"],
                "anchor_id_bytes32": _bytes32_hex(anchor_ids[index]),
                "proof_hash": item["proof_hash"].removeprefix("0x"),
                "context": item.get("context", "GENERAL"),
                "context_bytes32": _bytes32_hex(contexts[index]),
            }
            for index, item in enumerate(anchors)
        ],
        "network": profile["network"],
        "chain_id": profile["chain_id"],
        "chain_name": profile["chain_name"],
        "explorer_url": f"{profile['explorer_base_url']}{tx_hash.removeprefix('0x')}",
        "method": "anchorBatchV2",
    }


def _decode_proof_anchored_event(
    receipt: Any,
    *,
    profile_name: str | None = None,
) -> Optional[Dict[str, Any]]:
    """Decode the first ProofAnchored event from a transaction receipt."""

    try:
        profile = get_deployment_profile(profile_name)
        web3 = _web3(profile)
        contract = _contract(web3, profile)
        events = contract.events.ProofAnchored().process_receipt(receipt)
        if not events:
            return None
        event = events[0]["args"]
        proof_hash = event.get("proofHash")
        return {
            "anchor_id": event.get("anchorId"),
            "proof_hash": proof_hash.hex() if hasattr(proof_hash, "hex") else str(proof_hash),
            "publisher": event.get("publisher"),
            "timestamp": int(event.get("timestamp")),
        }
    except Exception:
        return None


def _decode_proof_anchored_v2_event(
    receipt: Any,
    *,
    profile_name: str | None = None,
) -> Optional[Dict[str, Any]]:
    """Decode the first ArchitectureAnchorV2 ProofAnchored event."""

    try:
        profile = get_deployment_profile(profile_name)
        web3 = _web3(profile)
        contract = _v2_contract(web3, profile)
        events = contract.events.ProofAnchored().process_receipt(receipt)
        if not events:
            return None
        event = events[0]["args"]
        proof_hash = event.get("proofHash")
        anchor_id = event.get("anchorId")
        context = event.get("context")
        return {
            "anchor_id": _hex_value(anchor_id),
            "proof_hash": proof_hash.hex() if hasattr(proof_hash, "hex") else str(proof_hash),
            "publisher": event.get("publisher"),
            "timestamp": int(event.get("timestamp")),
            "context": _bytes32_to_context(context),
            "context_bytes32": _hex_value(context),
            "version": "v2",
        }
    except Exception:
        return None


def verify_anchor_on_chain(
    anchor_id: str,
    proof_hash: str,
    *,
    profile_name: str | None = None,
) -> bool:
    """Call verifyAnchor(anchorId, expectedProofHash) on the configured contract."""

    try:
        profile = get_deployment_profile(profile_name)
        validate_deployment_profile(profile)
        contract = _contract(_web3(profile), profile)
        return bool(contract.functions.verifyAnchor(anchor_id, _normalise_proof_hash(proof_hash)).call())
    except Exception:
        return False


def verify_anchor_v2_on_chain(
    anchor_id: str,
    proof_hash: str,
    *,
    profile_name: str | None = None,
) -> bool:
    """Call ArchitectureAnchorV2.verifyAnchor(bytes32,bytes32)."""

    try:
        profile = get_deployment_profile(profile_name)
        _validate_v2_profile(profile)
        contract = _v2_contract(_web3(profile), profile)
        return bool(
            contract.functions.verifyAnchor(
                _anchor_id_to_bytes32(anchor_id),
                _normalise_proof_hash(proof_hash),
            ).call()
        )
    except Exception:
        return False


def get_anchor(anchor_id: str, *, profile_name: str | None = None) -> Dict[str, Any]:
    """Fetch an anchor record from the configured contract."""

    try:
        profile = get_deployment_profile(profile_name)
        validate_deployment_profile(profile)
        contract = _contract(_web3(profile), profile)
        proof_hash, publisher, timestamp = contract.functions.getAnchor(anchor_id).call()
        return {
            "status": "found",
            "anchor_id": anchor_id,
            "proof_hash": proof_hash.hex() if hasattr(proof_hash, "hex") else str(proof_hash),
            "publisher": publisher,
            "timestamp": int(timestamp),
            "network": profile["network"],
            "contract_address": profile["contract_address"],
        }
    except Exception as exc:
        return {"status": "not_found", "anchor_id": anchor_id, "error": str(exc)}


def get_anchor_v2(anchor_id: str, *, profile_name: str | None = None) -> Dict[str, Any]:
    """Fetch an ArchitectureAnchorV2 record."""

    try:
        profile = get_deployment_profile(profile_name)
        _validate_v2_profile(profile)
        contract = _v2_contract(_web3(profile), profile)
        proof_hash, publisher, timestamp, context = contract.functions.getAnchor(
            _anchor_id_to_bytes32(anchor_id)
        ).call()
        return {
            "status": "found",
            "anchor_id": anchor_id,
            "anchor_id_bytes32": _bytes32_hex(_anchor_id_to_bytes32(anchor_id)),
            "proof_hash": proof_hash.hex() if hasattr(proof_hash, "hex") else str(proof_hash),
            "publisher": publisher,
            "timestamp": int(timestamp),
            "context": _bytes32_to_context(context),
            "context_bytes32": _hex_value(context),
            "network": profile["network"],
            "contract_address": profile["contract_address_v2"],
            "version": "v2",
        }
    except Exception as exc:
        return {"status": "not_found", "anchor_id": anchor_id, "error": str(exc)}


def chain_health(*, profile_name: str | None = None) -> Dict[str, Any]:
    """Check RPC and contract configuration without sending a transaction."""

    try:
        profile = get_deployment_profile(profile_name)
        validate_deployment_profile(profile)
        web3 = _web3(profile)
        if not web3.is_connected():
            return {"status": "unavailable", "network": profile["network"]}
        return {
            "status": "ok",
            "network": profile["network"],
            "chain_id": profile["chain_id"],
            "latest_block": web3.eth.block_number,
            "contract": profile["contract_address"],
            "contract_v2": profile.get("contract_address_v2"),
        }
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}
