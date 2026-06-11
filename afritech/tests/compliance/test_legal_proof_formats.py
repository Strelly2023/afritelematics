from __future__ import annotations

import pytest

from afritech.compliance.legal_proof_formats import build_legal_proof_document
from afritech.partner_verification import build_partner_verification_packet


def _packet():
    return build_partner_verification_packet(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash="a" * 64,
        replay_hash="b" * 64,
        receipt_hash="c" * 64,
        authority_hash="d" * 64,
        execution_fingerprint="e" * 64,
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-legal-001",
    )


def test_legal_proof_document_is_deterministic() -> None:
    first = build_legal_proof_document(_packet(), legal_format="REGULATORY_AUDIT_V1")
    second = build_legal_proof_document(_packet(), legal_format="REGULATORY_AUDIT_V1")

    assert first == second
    assert first.legal_format == "REGULATORY_AUDIT_V1"
    assert len(first.document_hash) == 64


def test_legal_proof_document_requires_format() -> None:
    with pytest.raises(ValueError, match="legal_format"):
        build_legal_proof_document(_packet(), legal_format="")
