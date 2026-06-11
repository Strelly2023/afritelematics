from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TRUST_SPEC = ROOT / "docs/standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md"
CPPT_SPEC = ROOT / "docs/standards/AFRICPPT_PROTOCOL_SPEC.md"


def test_trust_protocol_spec_declares_dependency_surfaces() -> None:
    text = TRUST_SPEC.read_text(encoding="utf-8")

    for item in (
        "conformance profile",
        "dependent system declaration",
        "GET /v1/trust/standards/profile",
        "POST /v1/trust/dependents/register",
        "GET /v1/trust/dependents",
        "dependent systems consume verification, not truth authority",
    ):
        assert item in text


def test_africppt_spec_declares_dependency_declaration_flow() -> None:
    text = CPPT_SPEC.read_text(encoding="utf-8")

    for item in (
        "Dependency Declaration Flow",
        "conformance profile",
        "dependent system declaration",
        "GET /v1/trust/standards/profile",
        "POST /v1/trust/dependents/register",
        "GET /v1/trust/dependents",
    ):
        assert item in text
