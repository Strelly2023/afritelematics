import base64
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


# =====================================================
# ✅ CONFIG — KEY LOCATION (ROBUST)
# =====================================================

# Assumes:
# project_root/
#   private_key.pem
#   public_key.pem
#   afritech/

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _get_key_path(filename: str) -> Path:
    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"KEY_NOT_FOUND: {path}")

    return path


# =====================================================
# ✅ LOAD KEYS
# =====================================================

def load_private_key():
    """
    Loads RSA private key from project root.
    """
    path = _get_key_path("private_key.pem")

    with open(path, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None,
        )


def load_public_key():
    """
    Loads RSA public key from project root.
    """
    path = _get_key_path("public_key.pem")

    with open(path, "rb") as f:
        return serialization.load_pem_public_key(
            f.read(),
        )


# =====================================================
# ✅ SIGN DATA
# =====================================================

def sign_data(data: str) -> str:
    """
    Signs input string using RSA + SHA256.

    Returns:
        Base64 encoded signature
    """

    if not isinstance(data, str):
        raise ValueError("DATA_MUST_BE_STRING")

    private_key = load_private_key()

    signature = private_key.sign(
        data.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode("utf-8")


# =====================================================
# ✅ VERIFY SIGNATURE
# =====================================================

def verify_signature(data: str, signature: str) -> bool:
    """
    Verifies RSA signature.

    Returns:
        True if valid, False otherwise
    """

    if not data or not signature:
        return False

    try:
        public_key = load_public_key()

        public_key.verify(
            base64.b64decode(signature),
            data.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        return True

    except Exception:
        # ✅ fail-safe (never crash verifier)
        return False
