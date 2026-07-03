from __future__ import annotations

from pathlib import Path

from afritech.architecture.anchor_indexer import (
    AnchorEventSubscriber,
    AnchorIndexStore,
    InMemoryAnchorIndexBackend,
    get_chain_profile,
)
from afritech.chain.anchor_batch_queue import AnchorBatchQueue
from afritech.chain.anchor_publisher import publish_anchor, publish_anchor_batch_v2
from afritech.chain.contracts.architecture_anchor_v2_abi import ARCHITECTURE_ANCHOR_V2_ABI
from afritech.chain.contracts.contract_client import (
    _anchor_id_to_bytes32,
    _bytes32_to_context,
    _context_to_bytes32,
)
from afritech.chain.contracts.deployment_config import get_chain_config_snapshot


def test_architecture_anchor_v2_contract_keeps_v1_separate_and_adds_batching() -> None:
    source = Path("afritech/contracts/ArchitectureAnchorV2.sol").read_text(encoding="utf-8")
    v1_source = Path("afritech/contracts/ArchitectureAnchor.sol").read_text(encoding="utf-8")

    assert "contract ArchitectureAnchorV2" in source
    assert "mapping(bytes32 => AnchorRecord) private anchors;" in source
    assert "mapping(bytes32 => bool) private proofUsed;" in source
    assert "function anchorBatch(" in source
    assert "bytes32 context" in source
    assert "bool enforceUniqueProof" in source
    assert "revert EmptyBatch()" in source
    assert "revert ArrayLengthMismatch()" in source
    assert "contract ArchitectureAnchor {" in v1_source
    assert "mapping(string => AnchorRecord) private anchors;" in v1_source


def test_architecture_anchor_v2_abi_exposes_single_batch_verify_and_read() -> None:
    functions = {
        item["name"]: item
        for item in ARCHITECTURE_ANCHOR_V2_ABI
        if item.get("type") == "function"
    }
    event = next(
        item
        for item in ARCHITECTURE_ANCHOR_V2_ABI
        if item.get("type") == "event" and item.get("name") == "ProofAnchored"
    )

    assert list(functions["anchorProof"]["inputs"][0].values()) == [
        "bytes32",
        "anchorId",
        "bytes32",
    ]
    assert functions["anchorBatch"]["inputs"][0]["type"] == "bytes32[]"
    assert functions["anchorBatch"]["inputs"][2]["name"] == "contexts"
    assert functions["verifyAnchor"]["inputs"][0]["type"] == "bytes32"
    assert functions["getAnchor"]["outputs"][3]["name"] == "context"
    assert [input_["type"] for input_ in event["inputs"]] == [
        "bytes32",
        "bytes32",
        "address",
        "uint256",
        "bytes32",
    ]


def test_v2_bytes32_conversion_is_deterministic_and_context_safe() -> None:
    first = _anchor_id_to_bytes32("ride-001")
    second = _anchor_id_to_bytes32("ride-001")
    different = _anchor_id_to_bytes32("ride-002")
    context = _context_to_bytes32("RIDE")

    assert len(first) == 32
    assert first == second
    assert first != different
    assert len(context) == 32
    assert _bytes32_to_context(context) == "RIDE"


def test_publish_anchor_v2_falls_back_without_live_env(monkeypatch) -> None:
    monkeypatch.setenv("AFRITECH_CHAIN_ANCHOR_VERSION", "v2")
    monkeypatch.delenv("AFRITECH_CHAIN_ENABLE_PUBLISH", raising=False)

    receipt = publish_anchor("a" * 64, anchor_id="ride-001", context="RIDE")
    payload = receipt.canonical_dict()

    assert payload["status"] == "runtime_safe_fallback"
    assert payload["meta"]["anchor_version"] == "v2"
    assert payload["meta"]["anchor_id"] == "ride-001"
    assert payload["meta"]["context"] == "RIDE"


def test_anchor_batch_queue_flushes_v2_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_publish(anchors, *, profile_name=None, require_live=False):
        captured["anchors"] = anchors
        captured["profile_name"] = profile_name
        captured["require_live"] = require_live
        return publish_anchor_batch_v2(anchors)

    monkeypatch.setattr("afritech.chain.anchor_batch_queue.publish_anchor_batch_v2", fake_publish)

    queue = AnchorBatchQueue(max_batch_size=2)
    assert queue.enqueue("ride-001", "a" * 64, "RIDE") == 1
    assert queue.enqueue("payment-001", "b" * 64, "PAYMENT") == 2
    receipt = queue.flush(profile_name="sepolia")

    assert receipt is not None
    assert queue.pending_count() == 0
    assert captured["profile_name"] == "sepolia"
    assert captured["anchors"] == [
        {"anchor_id": "ride-001", "proof_hash": "a" * 64, "context": "RIDE"},
        {"anchor_id": "payment-001", "proof_hash": "b" * 64, "context": "PAYMENT"},
    ]


def test_chain_snapshot_reports_v2_contract_configuration(monkeypatch) -> None:
    monkeypatch.setenv("AFRITECH_CHAIN_CONTRACT_ADDRESS_V2", "0x1111111111111111111111111111111111111111")

    snapshot = get_chain_config_snapshot()

    assert snapshot["contract_v2_configured"] is True


def test_indexer_normalizes_v2_event_with_context() -> None:
    store = AnchorIndexStore(InMemoryAnchorIndexBackend())
    subscriber = AnchorEventSubscriber(store)
    profile = get_chain_profile("sepolia")
    event = {
        "args": {
            "anchorId": bytes.fromhex("11" * 32),
            "proofHash": bytes.fromhex("aa" * 32),
            "publisher": "0x2222222222222222222222222222222222222222",
            "timestamp": 123,
            "context": _context_to_bytes32("RIDE"),
        },
        "transactionHash": bytes.fromhex("bb" * 32),
        "blockNumber": 99,
    }

    entry = subscriber._build_entry_from_event(
        profile,
        event,
        version="v2",
        contract_address="0x3333333333333333333333333333333333333333",
    )

    assert entry.anchor_id == "1111111111111111111111111111111111111111111111111111111111111111"
    assert entry.proof_hash == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert entry.contract_address == "0x3333333333333333333333333333333333333333"
    assert entry.meta["contract_version"] == "v2"
    assert entry.meta["context"] == "RIDE"
