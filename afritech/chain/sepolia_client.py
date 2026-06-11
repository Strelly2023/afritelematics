# afritech/chain/sepolia_client.py

import os
from typing import Dict, Any, cast


# =========================
# ✅ ENV CONFIG
# =========================

RPC_URL = os.getenv("AFRITECH_CHAIN_RPC_URL_SEPOLIA")
PRIVATE_KEY = os.getenv("AFRITECH_CHAIN_PRIVATE_KEY")
ADDRESS = os.getenv("AFRITECH_CHAIN_ADDRESS")

CHAIN_ID = int(os.getenv("AFRITECH_CHAIN_ID", "11155111"))
GAS_PRICE_GWEI = float(os.getenv("AFRITECH_CHAIN_GAS_PRICE_GWEI", "2"))
TX_TIMEOUT = int(os.getenv("AFRITECH_CHAIN_TX_TIMEOUT", "60"))

ENABLE_PUBLISH = os.getenv("AFRITECH_CHAIN_ENABLE_PUBLISH", "false").lower() == "true"


def _load_web3() -> Any:
    try:
        from web3 import Web3
    except ModuleNotFoundError as exc:
        raise RuntimeError("web3 is required for live Sepolia anchoring") from exc
    return Web3


def _web3() -> Any:
    if not RPC_URL:
        raise RuntimeError("Missing AFRITECH_CHAIN_RPC_URL_SEPOLIA")
    Web3 = _load_web3()
    return Web3(Web3.HTTPProvider(RPC_URL))


def _raw_transaction(signed: Any) -> Any:
    return getattr(signed, "rawTransaction", getattr(signed, "raw_transaction", None))


# =========================
# ✅ VALIDATION
# =========================

def _validate_config(web3: Any) -> Any:
    """
    Validates environment and returns checksum address.
    Fully type-safe for Web3 + Pylance.
    """

    if not web3.is_connected():
        raise RuntimeError("Web3 not connected")

    if not PRIVATE_KEY:
        raise RuntimeError("Missing AFRITECH_CHAIN_PRIVATE_KEY")

    if not ADDRESS:
        raise RuntimeError("Missing AFRITECH_CHAIN_ADDRESS")

    Web3 = _load_web3()
    if not Web3.is_address(ADDRESS):
        raise ValueError("Invalid wallet address")

    return cast(Any, Web3.to_checksum_address(ADDRESS))


# =========================
# ✅ SEND TRANSACTION
# =========================

def send_proof_hash(proof_hash: str) -> Dict[str, Any]:
    """
    Publish proof hash on Ethereum Sepolia.

    ✅ Safe via ENABLE_PUBLISH flag
    ✅ Encodes proof_hash into tx.data
    ✅ Returns normalized dict
    """

    if not ENABLE_PUBLISH:
        raise RuntimeError("Chain publishing disabled (AFRITECH_CHAIN_ENABLE_PUBLISH=false)")

    web3 = _web3()
    address = _validate_config(web3)

    try:
        nonce = web3.eth.get_transaction_count(address)

        gas_price = web3.to_wei(GAS_PRICE_GWEI, "gwei")

        tx = {
            "nonce": nonce,
            "to": address,
            "value": 0,
            "gas": 21000,
            "gasPrice": gas_price,
            "data": proof_hash.encode("utf-8"),
            "chainId": CHAIN_ID,
        }

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        raw_tx = _raw_transaction(signed_tx)
        if raw_tx is None:
            raise RuntimeError("signed transaction did not expose raw transaction bytes")

        tx_hash_bytes = web3.eth.send_raw_transaction(raw_tx)

        receipt = web3.eth.wait_for_transaction_receipt(
            tx_hash_bytes,
            timeout=TX_TIMEOUT,
        )

        return {
            "status": "live",
            "tx_hash": tx_hash_bytes.hex(),
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to publish proof hash: {str(e)}")


# =========================
# ✅ FETCH RECEIPT
# =========================

def get_transaction_receipt(tx_hash: str) -> Dict[str, Any]:
    """
    Fetch transaction receipt from Sepolia.
    """

    web3 = _web3()
    _validate_config(web3)

    try:
        try:
            from hexbytes import HexBytes
        except ModuleNotFoundError as exc:
            raise RuntimeError("hexbytes is required for receipt lookup") from exc
        try:
            from web3.exceptions import TransactionNotFound
        except ModuleNotFoundError as exc:
            raise RuntimeError("web3 is required for receipt lookup") from exc

        tx_hash_bytes = HexBytes(tx_hash)

        receipt = web3.eth.get_transaction_receipt(tx_hash_bytes)

        return {
            "status": "confirmed",
            "tx_hash": tx_hash,
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
        }

    except TransactionNotFound:
        return {
            "status": "pending",
            "tx_hash": tx_hash,
        }


# =========================
# ✅ HEALTH CHECK
# =========================

def chain_health_check() -> Dict[str, Any]:
    """
    Basic RPC + chain connectivity check.
    Safe for dashboards/public API.
    """

    try:
        web3 = _web3()
        if not web3.is_connected():
            return {
                "status": "unavailable",
                "reason": "RPC not connected",
            }

        return {
            "status": "ok",
            "network": "sepolia",
            "latest_block": web3.eth.block_number,
        }

    except Exception as e:
        return {
            "status": "error",
            "reason": str(e),
        }
