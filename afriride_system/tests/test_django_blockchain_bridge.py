from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DJANGO_APP = ROOT / "afriride_system/django_app"

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))


def test_runtime_safe_fallback_is_a_successful_handled_anchor(monkeypatch):
    from blockchain import services

    def fake_publish_anchor(proof_hash: str):
        return {
            "status": "runtime_safe_fallback",
            "tx_hash": f"fallback-{proof_hash}",
            "proof_hash": proof_hash,
            "network": "papc-testnet",
        }

    monkeypatch.setattr(services, "publish_anchor", fake_publish_anchor)

    result = services.publish_proof_to_chain({"proof_hash": "test123"})

    assert result["success"] is True
    assert result["mode"] == "contract"
    assert result["anchor"]["status"] == "runtime_safe_fallback"
    assert result["anchor"]["tx_hash"] == "fallback-test123"


def test_missing_proof_hash_is_rejected():
    from blockchain.services import publish_proof_to_chain

    result = publish_proof_to_chain({"proof_hash": ""})

    assert result["success"] is False
    assert result["mode"] == "fallback"
    assert result["anchor"]["status"] == "rejected"
