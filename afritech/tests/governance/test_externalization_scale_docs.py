from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ARCH_DOC = ROOT / "docs/architecture/AFRIRIDE_EXTERNALIZATION_AND_SCALE_ARCHITECTURE.md"
WHITEPAPER = ROOT / "docs/whitepaper/AFRIRIDE_PARTNER_ARCHITECTURE_WHITEPAPER.md"
UI_SOURCE = ROOT / "dashboard/src/App.jsx"


def test_externalization_architecture_doc_covers_dashboard_scale_and_anchoring() -> None:
    text = ARCH_DOC.read_text(encoding="utf-8")

    for item in (
        "REPLAY_BACKED_OPERATOR_AND_PARTNER_SURFACE",
        "dashboard = projection(replay(trace_events))",
        "Multi-Region Support",
        "Multi-Tenant Support",
        "Cryptographic Anchoring",
        "trace_hash + replay_hash + receipt_hash -> commitment_hash",
        "public multi-tenant launch complete",
    ):
        assert item in text


def test_partner_whitepaper_preserves_replay_truth_boundary() -> None:
    text = WHITEPAPER.read_text(encoding="utf-8")

    for item in (
        "PARTNER AND INVESTOR TECHNICAL WHITEPAPER",
        "This whitepaper is an isolated communication surface.",
        "trace records authority",
        "replay reconstructs truth",
        "multi-region convergence design",
        "cryptographic anchor commitments",
        "The anchor is evidence of export integrity. It is not a replacement for replay.",
    ):
        assert item in text


def test_operator_dashboard_exposes_externalization_and_scale_surfaces() -> None:
    text = UI_SOURCE.read_text(encoding="utf-8")

    for item in (
        "Replay-Backed Externalization Layer",
        "Multi-Region Topology",
        "Multi-Tenant Isolation",
        "External Anchor Commitments",
        "Partner Proof Surface",
        "Replay-backed operator dashboard",
        "public ledger test anchor",
    ):
        assert item in text
