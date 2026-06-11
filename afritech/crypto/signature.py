import base64
import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa


# =====================================================
# ✅ CONFIG — KEY LOCATION (ROBUST)
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
_GENERATED_KEYPAIR: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey] | None = None


def _get_key_path(filename: str) -> Path:
    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"KEY_NOT_FOUND: {path}")

    return path


def _env_key_bytes(value_name: str) -> bytes | None:
    value = os.environ.get(value_name, "").strip()
    if not value:
        return None
    return value.encode("utf-8")


def _env_key_path(value_name: str) -> Path | None:
    value = os.environ.get(value_name, "").strip()
    if not value:
        return None
    return Path(value).expanduser()


def _generated_keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    global _GENERATED_KEYPAIR
    if _GENERATED_KEYPAIR is None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        _GENERATED_KEYPAIR = (private_key, private_key.public_key())
    return _GENERATED_KEYPAIR


# =====================================================
# ✅ LOAD KEYS
# =====================================================

def load_private_key():
    """
    Loads RSA private key from environment, configured path, or ephemeral runtime key.
    """
    env_bytes = _env_key_bytes("AFRITECH_SIGNING_PRIVATE_KEY_PEM")
    if env_bytes is not None:
        return serialization.load_pem_private_key(env_bytes, password=None)

    env_path = _env_key_path("AFRITECH_SIGNING_PRIVATE_KEY_PATH")
    if env_path is not None and env_path.exists():
        with open(env_path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)

    repo_path = BASE_DIR / "private_key.pem"
    if repo_path.exists():
        with open(repo_path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)

    return _generated_keypair()[0]


def load_public_key():
    """
    Loads RSA public key from environment, configured path, or ephemeral runtime key.
    """
    env_bytes = _env_key_bytes("AFRITECH_SIGNING_PUBLIC_KEY_PEM")
    if env_bytes is not None:
        return serialization.load_pem_public_key(env_bytes)

    env_path = _env_key_path("AFRITECH_SIGNING_PUBLIC_KEY_PATH")
    if env_path is not None and env_path.exists():
        with open(env_path, "rb") as f:
            return serialization.load_pem_public_key(f.read())

    repo_path = BASE_DIR / "public_key.pem"
    if repo_path.exists():
        with open(repo_path, "rb") as f:
            return serialization.load_pem_public_key(f.read())

    return _generated_keypair()[1]


def current_public_key_pem() -> str:
    public_key = load_public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


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
