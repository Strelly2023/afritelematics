import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# =====================================================
# ✅ PUBLIC KEY REGISTRY (PRODUCTION-GRADE)
# =====================================================

PUBLIC_KEY_REGISTRY = {
    "afritech-key-01": {
        "path": "keys/afritech.pem",
        "algorithm": "rsa",
        "owner": "afritech-core",
        "status": "active",
        "created_at": "2026-01-01",
    },

    "partner-01": {
        "path": "keys/partner.pem",
        "algorithm": "rsa",
        "owner": "partner-system",
        "status": "active",
        "created_at": "2026-03-15",
    },

    # ✅ example rotated key
    "afritech-key-02": {
        "path": "keys/afritech_v2.pem",
        "algorithm": "rsa",
        "owner": "afritech-core",
        "status": "active",
        "created_at": "2026-05-01",
    },

    # ✅ deprecated key (still usable for validation)
    "legacy-key-01": {
        "path": "keys/legacy.pem",
        "algorithm": "rsa",
        "owner": "old-system",
        "status": "deprecated",
        "created_at": "2025-01-01",
    }
}


# =====================================================
# ✅ KEY RESOLUTION
# =====================================================

def get_public_key(key_id: str) -> Optional[str]:
    """
    Load public key content from registry.
    """

    try:
        key_info = PUBLIC_KEY_REGISTRY.get(key_id)

        if not key_info:
            logger.warning(f"[KEY_REGISTRY] Unknown key: {key_id}")
            return None

        if key_info.get("status") == "revoked":
            logger.error(f"[KEY_REGISTRY] Revoked key used: {key_id}")
            return None

        path = key_info.get("path")

        if not path or not os.path.exists(path):
            fallback = Path(__file__).resolve().parents[2] / "public_key.pem"
            if fallback.exists():
                return fallback.read_text(encoding="utf-8")
            logger.error(f"[KEY_REGISTRY] Key file missing: {path}")
            return None

        with open(path, "r") as f:
            return f.read()

    except Exception:
        logger.exception("[KEY_REGISTRY] Failed to load key")
        return None


# =====================================================
# ✅ VALIDATION
# =====================================================

def is_valid_key(key_id: str) -> bool:
    """
    Check if key exists and is usable.
    """
    key_info = PUBLIC_KEY_REGISTRY.get(key_id)

    if not key_info:
        return False

    if key_info.get("status") == "revoked":
        return False

    return True


# =====================================================
# ✅ LISTING (FOR DASHBOARD / ADMIN)
# =====================================================

def list_keys():
    """
    Return safe key metadata (no key material).
    """
    return [
        {
            "key_id": key_id,
            "owner": info.get("owner"),
            "status": info.get("status"),
            "algorithm": info.get("algorithm"),
            "created_at": info.get("created_at"),
        }
        for key_id, info in PUBLIC_KEY_REGISTRY.items()
    ]


# =====================================================
# ✅ ROTATION SUPPORT
# =====================================================

def get_active_keys(owner: str):
    """
    Return all active keys for a given system/client.
    """
    return [
        key_id
        for key_id, info in PUBLIC_KEY_REGISTRY.items()
        if info.get("owner") == owner and info.get("status") == "active"
    ]


# =====================================================
# ✅ DEBUG
# =====================================================

def debug_key_info(key_id: str):
    """
    Return full key info (admin/debug only).
    """
    return PUBLIC_KEY_REGISTRY.get(key_id)
