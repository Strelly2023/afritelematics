import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_keys(output_dir: str | None = None):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()
    target_dir = Path(output_dir or os.environ.get("AFRITECH_KEY_OUTPUT_DIR", ".")).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    private_path = target_dir / "private_key.pem"
    public_path = target_dir / "public_key.pem"

    # Save private key
    with open(private_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Save public key
    with open(public_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return {"private_key_path": str(private_path), "public_key_path": str(public_path)}
