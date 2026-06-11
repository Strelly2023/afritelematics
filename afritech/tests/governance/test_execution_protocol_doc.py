from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "docs/protocol/AFRITECH_EXECUTION_PROTOCOL.md"
SNAPSHOT = ROOT / "afritech/governance/authority_snapshots/cfa8657d95e4f6024d981bfb1f04db74defb95a24b3110cb82680faf56a9a6bc.json"
SCHEMA = ROOT / "afritech/verify/public_verifier_bundle.schema.json"
WRAPPER = ROOT / "scripts/run_public_verifier.sh"


def test_execution_protocol_spec_declares_authority_bound_verification_rules() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")

    for item in (
        "EXECUTION PROTOCOL SPECIFICATION",
        "EXTERNAL_VERIFICATION_PROTOCOL_SURFACE",
        "event_hash = H(event fields + previous_hash + authority_hash)",
        "replay_hash = H(reconstructed replay payload + authority_hash)",
        "receipt_hash = H(receipt payload + authority_hash)",
        "execution_fingerprint = H(replay_hash + receipt_hash + authority_hash)",
        "authority_snapshots",
        "Version Compatibility",
        "Ecosystem Integration Roles",
        "settlement adapter",
        "Smart Contract Boundary",
        "Protocol validity may not depend on contract execution.",
        "Public Verifier Tooling",
        "run_public_verifier.sh",
        "Independent Verification Procedure",
    ):
        assert item in text


def test_architecture_authority_snapshot_exists() -> None:
    assert SNAPSHOT.exists()


def test_public_verifier_schema_and_wrapper_exist() -> None:
    assert SCHEMA.exists()
    assert WRAPPER.exists()
