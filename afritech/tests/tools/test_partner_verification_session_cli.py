from __future__ import annotations

from afritech.tools.partner_verification_session_cli import build_partner_session_report


def test_build_partner_session_report_fetches_public_surfaces(monkeypatch) -> None:
    def fake_load_json(url: str) -> dict[str, object]:
        if url.endswith("/public/architecture/proof"):
            return {
                "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
                "proof": {
                    "proof_id": "proof-1",
                    "proof_hash": "hash-1",
                    "anchor_commitment": {"anchor_id": "anchor-1", "commitment_hash": "commit-1"},
                    "publication_envelope": {
                        "publication_id": "publish-1",
                        "publication_hash": "pub-hash-1",
                    },
                    "public_chain_receipt": {
                        "chain_receipt_id": "chain-1",
                        "network": "sepolia",
                        "transaction_hash": "0xabc123",
                    },
                    "verification_packet": {"anchor_id": "anchor-1", "verification_status": "VERIFIED"},
                    "registry_entry": {"entry_id": "registry-1"},
                    "authority_boundary": "proof-boundary",
                },
            }
        if url.endswith("/public/architecture/chain/anchor-1"):
            return {
                "classification": "CONTROLLED_PUBLIC_CHAIN_RECEIPT",
                "status": "READY",
                "chain_receipt": {
                    "network": "sepolia",
                    "transaction_hash": "0xabc123",
                },
            }
        if url.endswith("/public/trust/dashboard"):
            return {
                "classification": "PUBLIC_TRUST_DASHBOARD",
                "status": "READY",
                "headline": "AfriTech public trust dashboard",
                "integrity": {"proof_id": "proof-1"},
                "chain": {"live_publication": {"status": "CONFIRMED"}},
                "distribution": {
                    "verifier_cli": "afritech-verify",
                    "partner_session_cli": "afritech-verify-session",
                },
                "surfaces": [{"label": "Architecture proof", "path": "/public/architecture/proof"}],
            }
        if url.endswith("/public/demo/system-integrity"):
            return {
                "classification": "PARTNER_LIVE_SYSTEM_INTEGRITY_DEMO",
                "demo_readiness": "PARTNER_READY",
                "walkthrough": [{"step": 1}],
                "proof": {"proof_id": "proof-1"},
            }
        raise AssertionError(url)

    monkeypatch.setattr(
        "afritech.tools.partner_verification_session_cli._load_json",
        fake_load_json,
    )
    monkeypatch.setattr(
        "afritech.sdk.external_verifier.ExternalVerifierClient.verify_architecture_proof_locally",
        lambda self, payload: {
            "proof_id": "proof-1",
            "verification_status": "VERIFIED",
            "anchor_id": "anchor-1",
            "chain_receipt_matches": True,
            "authority_boundary": "proof-boundary",
        },
    )

    report = build_partner_session_report(
        base_url="https://trust.example.com",
        partner="Launch Partner",
        expect_network="sepolia",
        notes="session complete",
    )

    assert report["outcome"] == "PASSED"
    assert report["dashboard"]["verifier_cli"] == "afritech-verify"
    assert report["next_step"] == "promote_to_mainnet"
