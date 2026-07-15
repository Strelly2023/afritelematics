from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT


def _headers(*, subject_id: str, role: str, tenant_id: str = "tenant-novaride", organization_id: str = "org-novaride") -> dict[str, str]:
    token = JWT.create_token(
        subject_id,
        role=role,
        organization_id=organization_id,
        tenant_id=tenant_id,
        workspace_id="workspace-runtime",
        roles=(role,),
        permissions=(
            "novaride.runtime.read",
            "novaride.replay.create",
            "novaride.replay.review",
            "novaride.replay.validate",
            "novaride.replay.execute",
            "novaride.replay.approve",
            "novaride.replay.promote",
        ),
        region="australia-southeast",
    )
    return {"Authorization": f"Bearer {token}"}


def test_operator_replay_api_requires_authentication() -> None:
    client = TestClient(app)
    assert client.post("/v1/operator/replay/plans", json={"mode": "correlation_id", "scope": {"correlation_id": "corr_api"}, "reason": "test"}).status_code == 401


def test_operator_replay_api_promotes_only_after_quorum_approval() -> None:
    client = TestClient(app)

    creator_headers = _headers(subject_id="creator-1", role="PLATFORM_ADMIN")
    ops_headers = _headers(subject_id="ops-1", role="OPERATIONS_TEAM")
    qa_headers = _headers(subject_id="qa-1", role="QA_ENGINEER")
    promoter_headers = _headers(subject_id="promoter-1", role="PLATFORM_ADMIN")

    client.post("/v1/rider/fares/quote", headers=creator_headers, json={"service_type": "economy", "currency": "AUD"})
    plan = client.post(
        "/v1/operator/replay/plans",
        headers={**creator_headers, "Idempotency-Key": "replay-plan-1"},
        json={"mode": "correlation_id", "scope": {"correlation_id": "corr_api"}, "reason": "test replay"},
    )
    assert plan.status_code == 201
    replay_id = plan.json()["replay_id"]

    executed = client.post(f"/v1/operator/replay/{replay_id}/execute", headers=creator_headers)
    assert executed.status_code == 200
    assert executed.json()["validate_only"] is False

    blocked = client.post(f"/v1/operator/replay/{replay_id}/promote", headers=promoter_headers)
    assert blocked.status_code == 422 or blocked.status_code == 403

    first_vote = client.post(
        f"/v1/operator/replay/{replay_id}/approve-promotion",
        headers=ops_headers,
        params={"approval_reference": "approval-1"},
    )
    assert first_vote.status_code == 200
    assert first_vote.json()["status"] == "APPROVAL_REQUIRED"

    second_vote = client.post(
        f"/v1/operator/replay/{replay_id}/approve-promotion",
        headers=qa_headers,
        params={"approval_reference": "approval-2"},
    )
    assert second_vote.status_code == 200
    assert second_vote.json()["status"] == "APPROVED"

    promoted = client.post(f"/v1/operator/replay/{replay_id}/promote", headers=promoter_headers)
    assert promoted.status_code == 200
    assert promoted.json()["state"] == "PROMOTED"
