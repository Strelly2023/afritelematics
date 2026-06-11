# afritech/chain/types.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ChainReceipt:
    """
    Represents a normalized blockchain anchoring receipt.

    This model supports:
    - ✅ Live Sepolia / Mainnet transactions
    - ✅ Fallback simulation (runtime_safe_fallback)
    - ✅ Future multi-chain support
    - ✅ JSON serialization for API/CLI usage
    """

    # ✅ Core identity
    tx_hash: str
    network: str

    # ✅ Block metadata (optional for fallback)
    block_number: Optional[int] = None

    # ✅ Explorer reference
    explorer_url: Optional[str] = None

    # ✅ Status (live | runtime_safe_fallback | pending | failed)
    status: str = "unknown"

    # ✅ Optional chain metadata
    chain_id: Optional[int] = None
    chain_name: Optional[str] = None

    # ✅ Optional contract interaction (future smart contract mode)
    contract_address: Optional[str] = None
    method: Optional[str] = None

    # ✅ Optional payload reference
    proof_hash: Optional[str] = None

    # ✅ Authority + provenance
    authority: str = "runtime"
    source: str = "anchor_publisher"

    # ✅ Extendable metadata
    meta: Dict[str, Any] = field(default_factory=dict)

    # =========================
    # ✅ Utilities
    # =========================

    def is_live(self) -> bool:
        """Returns True if this is a real on-chain transaction."""
        return self.status == "live"

    def is_fallback(self) -> bool:
        """Returns True if this is a fallback/non-chain receipt."""
        return self.status == "runtime_safe_fallback"

    def canonical_dict(self) -> Dict[str, Any]:
        """
        Returns a stable JSON-safe representation.
        Ensures compatibility with:
        - FastAPI responses
        - CLI tools
        - verification pipeline
        """

        return {
            "status": self.status,
            "network": self.network,
            "chain_id": self.chain_id,
            "chain_name": self.chain_name,
            "tx_hash": self.tx_hash,
            "transaction_hash": self.tx_hash,
            "block_number": self.block_number,
            "explorer_url": self.explorer_url,
            "contract_address": self.contract_address,
            "method": self.method,
            "proof_hash": self.proof_hash,
            "authority": self.authority,
            "source": self.source,
            "meta": self.meta,
        }
