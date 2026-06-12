# afritech/chain/contracts/deployment_config.py

import os
import re
from typing import Dict, Any, Optional


ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
PLACEHOLDER_CONTRACT_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x1234567890abcdef1234567890abcdef12345678",
}


# =========================
# ✅ DEFAULT PROFILES
# =========================

DEFAULT_DEPLOYMENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "sepolia": {
        "chain_name": "Ethereum Sepolia",
        "network": "sepolia",
        "chain_id": 11155111,
        "rpc_env": "AFRITECH_CHAIN_RPC_URL_SEPOLIA",
        "explorer_base_url": "https://sepolia.etherscan.io/tx/",
        "contract_env": "AFRITECH_CHAIN_CONTRACT_ADDRESS",
        "gas_price_gwei": 2,
        "timeout": 60,
        "rollout_stage": "pilot",
    },
    "mainnet": {
        "chain_name": "Ethereum Mainnet",
        "network": "mainnet",
        "chain_id": 1,
        "rpc_env": "AFRITECH_CHAIN_RPC_URL_MAINNET",
        "explorer_base_url": "https://etherscan.io/tx/",
        "contract_env": "AFRITECH_CHAIN_CONTRACT_ADDRESS",
        "gas_price_gwei": 10,
        "timeout": 120,
        "rollout_stage": "production",
    },
}


# =========================
# ✅ ACTIVE PROFILE RESOLVER
# =========================

def get_active_profile_name() -> str:
    """
    Determines which chain profile to use.

    Priority:
    1. AFRITECH_CHAIN_MODE
    2. fallback → sepolia
    """

    mode = os.getenv("AFRITECH_CHAIN_MODE", "sepolia").lower()

    if mode not in DEFAULT_DEPLOYMENT_PROFILES:
        return "sepolia"

    return mode


# =========================
# ✅ LOAD PROFILE
# =========================

def get_deployment_profile(profile_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns merged deployment profile:
    - default profile values
    - overridden by environment variables
    """

    name = profile_name or get_active_profile_name()

    if name not in DEFAULT_DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown deployment profile: {name}")

    base = DEFAULT_DEPLOYMENT_PROFILES[name]

    rpc_url = os.getenv(base["rpc_env"])
    contract_address = os.getenv(base["contract_env"])

    profile = {
        "profile": name,
        "chain_name": base["chain_name"],
        "network": base["network"],
        "chain_id": base["chain_id"],
        "rpc_url": rpc_url,
        "contract_address": contract_address,
        "explorer_base_url": base["explorer_base_url"],
        "gas_price_gwei": float(os.getenv("AFRITECH_CHAIN_GAS_PRICE_GWEI", base["gas_price_gwei"])),
        "timeout": int(os.getenv("AFRITECH_CHAIN_TX_TIMEOUT", base["timeout"])),
        "rollout_stage": base["rollout_stage"],
        "enabled": os.getenv("AFRITECH_CHAIN_ENABLE_PUBLISH", "false").lower() == "true",
    }

    return profile


# =========================
# ✅ VALIDATION
# =========================

def validate_deployment_profile(profile: Dict[str, Any]) -> None:
    """
    Strict validation before sending transactions.
    """

    if not profile["enabled"]:
        raise RuntimeError("Chain publishing disabled")

    if not profile["rpc_url"]:
        raise RuntimeError("Missing RPC URL")

    if not profile["contract_address"]:
        raise RuntimeError("Missing contract address")

    contract_address = str(profile["contract_address"])
    if not ETH_ADDRESS_RE.match(contract_address):
        raise RuntimeError("Invalid contract address")

    if contract_address.lower() in PLACEHOLDER_CONTRACT_ADDRESSES:
        raise RuntimeError(
            "AFRITECH_CHAIN_CONTRACT_ADDRESS must be a deployed ArchitectureAnchor "
            "address on the selected network, not a placeholder"
        )

    if not profile["chain_id"]:
        raise RuntimeError("Invalid chain ID")


# =========================
# ✅ PUBLIC SYSTEM SNAPSHOT
# =========================

def get_chain_config_snapshot() -> Dict[str, Any]:
    """
    Used for:
    - dashboard
    - CLI
    - proof metadata
    """

    profile = get_deployment_profile()

    return {
        "network": profile["network"],
        "chain_name": profile["chain_name"],
        "chain_id": profile["chain_id"],
        "enabled": profile["enabled"],
        "rpc_configured": bool(profile["rpc_url"]),
        "contract_configured": bool(profile["contract_address"]),
        "contract_placeholder": str(profile.get("contract_address") or "").lower()
        in PLACEHOLDER_CONTRACT_ADDRESSES,
        "wallet_configured": bool(
            os.getenv("AFRITECH_CHAIN_ADDRESS")
            or os.getenv("AFRITECH_CHAIN_ADDRESS_CHECKSUM")
        ),
        "private_key_configured": bool(
            os.getenv("AFRITECH_CHAIN_PRIVATE_KEY")
            or os.getenv("AFRITECH_CHAIN_PRIVATE_KEY_PATH")
        ),
        "rollout_stage": profile["rollout_stage"],
    }


# =========================
# ✅ EXPLORER URL BUILDER
# =========================

def build_explorer_url(tx_hash: str, profile_name: Optional[str] = None) -> Optional[str]:
    profile = get_deployment_profile(profile_name)

    base = profile.get("explorer_base_url")

    if not base or not tx_hash:
        return None

    return f"{base}{tx_hash}"


# =========================
# ✅ CHAIN ENABLE CHECK
# =========================

def is_chain_enabled() -> bool:
    profile = get_deployment_profile()
    return bool(profile["enabled"])


# =========================
# ✅ SAFE PROFILE LOADER
# =========================

def safe_get_profile() -> Dict[str, Any]:
    """
    Never raises → safe for API/dashboard usage
    """

    try:
        profile = get_deployment_profile()
        return profile
    except Exception as e:
        return {
            "network": "papc-testnet",
            "enabled": False,
            "error": str(e),
        }
