from __future__ import annotations

from afritech.api_catalog.envelopes import EvidenceRefs, ResponseMeta, error_envelope, success_envelope


def test_success_envelope_shape() -> None:
    envelope = success_envelope(
        {"ok": True},
        meta=ResponseMeta(request_id="req", trace_id="trace", contract_version="2026.07.0", organization_id="org"),
        evidence=EvidenceRefs(replay_id="replay", receipt_id="receipt"),
    )
    assert envelope["data"]["ok"] is True
    assert envelope["meta"]["request_id"] == "req"
    assert envelope["evidence"]["replay_id"] == "replay"
    assert envelope["errors"] == []


def test_error_envelope_shape() -> None:
    envelope = error_envelope(code="DENIED", message="Denied", trace_id="trace")
    assert envelope["data"] is None
    assert envelope["errors"][0]["code"] == "DENIED"
    assert envelope["errors"][0]["retryable"] is False
