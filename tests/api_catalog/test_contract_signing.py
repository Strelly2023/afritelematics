from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from afritech.api_catalog.signing import _decode_private_key, get_signing_backend, verify_signed_publication
from afritech.api_catalog.registry import get_api_catalog


def test_signed_publication_verifies_and_tampering_fails() -> None:
    publication = get_api_catalog().publication("novapay")
    assert verify_signed_publication(publication) is True
    tampered = dict(publication)
    tampered["openapi_hash"] = "sha256:tampered"
    assert verify_signed_publication(tampered) is False


def test_wrong_public_key_fails() -> None:
    publication = get_api_catalog().publication("novapay")
    wrong_private = Ed25519PrivateKey.generate()
    tampered_signature = dict(publication["signature"])
    tampered_signature["public_key"] = base64.b64encode(wrong_private.public_key().public_bytes_raw()).decode("ascii")
    assert get_signing_backend().verify({key: value for key, value in publication.items() if key != "signature"}, tampered_signature) is False


def test_invalid_private_key_rejected() -> None:
    with pytest.raises(ValueError):
        _decode_private_key(base64.b64encode(b"short").decode("ascii"))


def test_production_without_signing_key_fails_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVATECH_ENVIRONMENT", "production")
    monkeypatch.delenv("NOVATECH_API_CONTRACT_SIGNING_PRIVATE_KEY_B64", raising=False)
    get_signing_backend.cache_clear()  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError):
        get_signing_backend()
    monkeypatch.setenv("NOVATECH_ENVIRONMENT", "development")
    get_signing_backend.cache_clear()  # type: ignore[attr-defined]
