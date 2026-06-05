from __future__ import annotations

import time
import os
from typing import Dict, Any

from afritech.distributed.crypto import NodeIdentity

# ✅ Replay protection window (seconds)
MAX_CLOCK_SKEW = 30


# =========================================================
# ✅ HANDSHAKE CREATION
# =========================================================

def create_handshake(identity: NodeIdentity) -> Dict[str, Any]:
    """
    Create a signed handshake payload.

    Structure:
    {
        node_id: str (public key hex)
        timestamp: int
        nonce: str (hex)
        signature: str (hex)
    }
    """

    if not isinstance(identity, NodeIdentity):
        raise TypeError("identity must be NodeIdentity")

    timestamp = int(time.time())

    # ✅ strong randomness
    nonce_bytes = os.urandom(16)
    nonce = nonce_bytes.hex()

    node_id = identity.get_public_key_hex()

    # ✅ canonical payload (deterministic)
    payload = f"{node_id}:{timestamp}:{nonce}".encode()

    # ✅ sign payload
    signature = identity.sign(payload).hex()

    return {
        "node_id": node_id,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature,
    }


# =========================================================
# ✅ HANDSHAKE VERIFICATION
# =========================================================

def verify_handshake(handshake: Dict[str, Any]) -> bool:
    """
    Verify a peer handshake.

    Checks:
    - structure validity
    - timestamp freshness (anti-replay)
    - signature correctness (crypto identity)
    """

    if not isinstance(handshake, dict):
        return False

    try:
        node_id = handshake.get("node_id")
        timestamp = handshake.get("timestamp")
        nonce = handshake.get("nonce")
        signature_hex = handshake.get("signature")

        # ✅ Basic structure validation
        if not isinstance(node_id, str):
            return False

        if not isinstance(timestamp, int):
            return False

        if not isinstance(nonce, str):
            return False

        if not isinstance(signature_hex, str):
            return False

        # ✅ Replay protection (time window)
        now = int(time.time())
        if abs(now - timestamp) > MAX_CLOCK_SKEW:
            return False

        # ✅ Decode signature
        try:
            signature = bytes.fromhex(signature_hex)
        except Exception:
            return False

        # ✅ Recreate signed payload
        payload = f"{node_id}:{timestamp}:{nonce}".encode()

        # ✅ Verify cryptographic identity
        if not NodeIdentity.verify_hex(node_id, signature, payload):
            return False

        return True

    except Exception:
        return False
