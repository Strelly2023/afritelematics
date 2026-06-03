from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


DOC = (
    Path(__file__).resolve().parents[3]
    / "afritech/docs/operations/afriride_readiness_classification.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def yaml_blocks() -> list[dict[str, Any]]:
    text = read_doc()
    blocks = re.findall(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    payloads: list[dict[str, Any]] = []
    for block in blocks:
        payload = yaml.safe_load(block)
        assert isinstance(payload, dict)
        payloads.append(payload)
    return payloads


def status_payload() -> dict[str, Any]:
    for payload in yaml_blocks():
        if "afriride_status" in payload:
            return payload["afriride_status"]
    raise AssertionError("missing afriride_status block")


def test_readiness_classification_preserves_claim_boundary() -> None:
    status = status_payload()
    classification = status["classification"]

    assert classification["architecture_ready"] is True
    assert classification["pilot_ready"] == "partial"
    assert classification["product_ready"] is False
    assert classification["public_launch_ready"] is False


def test_architecture_evidence_is_complete_for_current_scope() -> None:
    architecture = status_payload()["architecture"]

    for key in (
        "deterministic_execution",
        "replay_integrity",
        "normalization_layer",
        "distributed_convergence",
        "network_determinism",
        "adversarial_resistance",
    ):
        assert architecture[key] == "complete"

    assert architecture["economic_model"] == "defined_and_validated"


def test_product_readiness_gaps_remain_explicit() -> None:
    product = status_payload()["product_readiness"]

    assert product["mobile_apps"] == "not_implemented"
    assert product["backend_integration"] == "partial"
    assert product["payments"] == "not_integrated"
    assert product["identity_kyc"] == "not_implemented"
    assert product["observability_ui"] == "not_implemented"
    assert product["app_distribution"] == "not_prepared"


def test_pilot_entry_and_exit_conditions_are_declared() -> None:
    payloads = yaml_blocks()
    entry = next(payload["pilot_entry_conditions"] for payload in payloads if "pilot_entry_conditions" in payload)
    exit_ = next(payload["pilot_exit_conditions"] for payload in payloads if "pilot_exit_conditions" in payload)

    for required in (
        "functional driver mobile app",
        "functional rider mobile app",
        "event ingestion API",
        "production-enforced normalization pipeline",
    ):
        assert required in entry["must_exist"]

    for proof in (
        "100% replay reconstruction of real trips",
        "zero divergence under real usage",
        "pilot traces are complete and invariant-safe",
    ):
        assert proof in exit_["must_prove"]


def test_required_before_product_ready_is_complete() -> None:
    payloads = yaml_blocks()
    required = next(
        payload["required_before_product_ready"]
        for payload in payloads
        if "required_before_product_ready" in payload
    )

    for section in (
        "mobile_layer",
        "backend_deployment",
        "payments",
        "identity_kyc",
        "support_operations",
        "observability",
        "pilot_evidence",
        "legal_compliance",
        "distribution",
    ):
        assert section in required
        assert required[section]


def test_readiness_doc_contains_non_claims() -> None:
    text = read_doc()

    for non_claim in (
        "product readiness",
        "public launch readiness",
        "regulatory approval",
        "payment provider readiness",
        "completed city pilot",
    ):
        assert non_claim in text
