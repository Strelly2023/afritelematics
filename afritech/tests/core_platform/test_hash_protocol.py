from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.core_platform.cryptographic_consensus import _hash, build_signed_message
from afritech.core_platform.hash_domains import HASH_DOMAINS, PROTOCOL_HASH_VERSION, SIGNED_MESSAGE_PREFIX


ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "tests/fixtures/crypto_corpus/hash_corpus.json"


def _load_corpus() -> dict[str, object]:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def test_hash_protocol_version_and_prefix_are_locked() -> None:
    corpus = _load_corpus()
    protocol = corpus["protocol"]

    assert protocol["hash_version"] == PROTOCOL_HASH_VERSION
    assert protocol["signed_message_prefix"] == SIGNED_MESSAGE_PREFIX


def test_golden_hash_corpus_matches_protocol_outputs() -> None:
    corpus = _load_corpus()
    for case in corpus["cases"]:
        domain = case["domain"]
        payload = case["payload"]
        expected_hash = case["hash"]
        expected_message = case["signed_message"]

        computed_hash = _hash(payload, domain=domain)
        computed_message = (
            build_signed_message(payload)
            if case.get("use_payload_domain")
            else build_signed_message(payload, domain=domain)
        )

        assert computed_hash == expected_hash, case["name"]
        assert computed_message == expected_message, case["name"]


def test_signed_message_uses_declared_domain_when_present() -> None:
    payload = {"domain": HASH_DOMAINS["PROOF_RECEIPT"], "text": "domain-bound"}

    expected_hash = _hash(payload, domain=HASH_DOMAINS["PROOF_RECEIPT"])

    assert build_signed_message(payload) == (
        f"{SIGNED_MESSAGE_PREFIX}::{HASH_DOMAINS['PROOF_RECEIPT']}::{expected_hash}"
    )


def test_signed_message_rejects_mismatched_declared_domain() -> None:
    payload = {"domain": HASH_DOMAINS["PROOF_RECEIPT"], "text": "domain-bound"}

    with pytest.raises(ValueError, match="domain_mismatch"):
        build_signed_message(payload, domain=HASH_DOMAINS["SIGNED_PAYLOAD"])


def test_signed_message_rejects_empty_declared_domain() -> None:
    payload = {"domain": "", "text": "domain-bound"}

    with pytest.raises(ValueError, match="invalid_declared_hash_domain_empty"):
        build_signed_message(payload)


def test_signed_message_rejects_empty_domain_before_conflict() -> None:
    payload = {
        "domain": "",
        "signature": {"domain": HASH_DOMAINS["PROOF_RECEIPT"]},
        "text": "domain-bound",
    }

    with pytest.raises(ValueError, match="invalid_declared_hash_domain_empty"):
        build_signed_message(payload)


def test_signed_message_rejects_conflicting_declared_domains() -> None:
    payload = {
        "domain": HASH_DOMAINS["PROOF_RECEIPT"],
        "signature": {"domain": HASH_DOMAINS["SIGNED_PAYLOAD"]},
        "text": "domain-bound",
    }

    with pytest.raises(ValueError, match="conflicting_declared_hash_domain"):
        build_signed_message(payload)


def test_signed_message_rejects_non_string_domain() -> None:
    payload = {"domain": 123, "text": "domain-bound"}

    with pytest.raises(ValueError, match="invalid_declared_hash_domain"):
        build_signed_message(payload)


def test_unicode_nfc_and_nfd_remain_distinct() -> None:
    nfc = {"text": "é"}
    nfd = {"text": "e\u0301"}

    assert _hash(nfc, domain=HASH_DOMAINS["PROOF_RECEIPT"]) != _hash(
        nfd,
        domain=HASH_DOMAINS["PROOF_RECEIPT"],
    )
