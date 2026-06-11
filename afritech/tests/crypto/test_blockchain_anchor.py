from __future__ import annotations

from afritech.architecture.blockchain_anchor import (
    build_chain_promotion_plan,
    get_chain_profile,
    publish_architecture_anchor_contract_with_profile,
    publish_architecture_anchor_to_evm,
    publish_architecture_anchor_with_profile,
)


def test_publish_architecture_anchor_to_evm_uses_rpc_and_returns_confirmed(monkeypatch) -> None:
    calls: list[tuple[str, list[object]]] = []

    def fake_rpc(url: str, method: str, params: list[object]) -> object:
        calls.append((method, params))
        if method == "eth_sendRawTransaction":
            return "0xabc123"
        if method == "eth_getTransactionReceipt":
            return {"blockNumber": "0x10", "status": "0x1"}
        raise AssertionError(method)

    monkeypatch.setattr("afritech.architecture.blockchain_anchor._rpc_call", fake_rpc)

    receipt = publish_architecture_anchor_to_evm(
        anchor_id="anchor-1",
        publication_id="publish-1",
        rpc_url="https://rpc.example",
        signed_tx_hex="0xsigned",
    )

    assert calls[0][0] == "eth_sendRawTransaction"
    assert calls[1][0] == "eth_getTransactionReceipt"
    assert receipt.transaction_hash == "0xabc123"
    assert receipt.block_number == 16
    assert receipt.status == "CONFIRMED"


def test_publish_architecture_anchor_with_profile_uses_profile_defaults(monkeypatch) -> None:
    monkeypatch.setenv("AFRITECH_CHAIN_RPC_URL_SEPOLIA", "https://rpc.sepolia.example")

    captured: dict[str, object] = {}

    def fake_publish(**kwargs: object):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        "afritech.architecture.blockchain_anchor.publish_architecture_anchor_to_evm",
        fake_publish,
    )

    publish_architecture_anchor_with_profile(
        anchor_id="anchor-1",
        publication_id="publish-1",
        signed_tx_hex="0xsigned",
        profile_name="sepolia",
    )

    assert captured["rpc_url"] == "https://rpc.sepolia.example"
    assert captured["network"] == "sepolia"
    assert captured["chain_id"] == 11155111


def test_chain_promotion_plan_lists_sepolia_and_mainnet() -> None:
    plan = build_chain_promotion_plan()

    assert plan["promotion_path"][0]["profile"] == "sepolia"
    assert plan["promotion_path"][1]["profile"] == "mainnet"
    assert get_chain_profile("mainnet").chain_id == 1


def test_contract_anchor_publication_falls_back_without_live_env(monkeypatch) -> None:
    monkeypatch.delenv("AFRITECH_CHAIN_ENABLE_PUBLISH", raising=False)

    receipt = publish_architecture_anchor_contract_with_profile(
        anchor_id="anchor-1",
        publication_id="publish-1",
        proof_hash="a" * 64,
        profile_name="sepolia",
    )

    payload = receipt.canonical_dict()
    assert payload["anchor_mode"] == "smart_contract"
    assert payload["method"] == "anchorProof"
    assert payload["status"] == "runtime_safe_fallback"
    assert payload["proof_hash"] == "a" * 64
