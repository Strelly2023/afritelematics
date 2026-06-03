from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.trace_api import TraceStoreAPI, build_trace_router


# ============================================================
# TEST SETUP UTILITIES
# ============================================================

def create_trace_file(
    trace_dir: Path,
    name: str,
    payload: dict,
) -> Path:
    """Create a trace file in a tmp directory."""
    trace_path = trace_dir / f"{name}.json"
    trace_path.write_text(json.dumps(payload), encoding="utf-8")
    return trace_path


def build_test_client(trace_dir: Path) -> TestClient:
    """Create an isolated FastAPI client with custom trace store."""
    store = TraceStoreAPI(trace_dir=trace_dir)

    # ✅ Isolated test app (critical)
    test_app = FastAPI()
    test_app.include_router(build_trace_router(store=store))

    return TestClient(test_app)


# ============================================================
# TEST: LIST TRACES
# ============================================================

def test_list_traces_empty(tmp_path: Path):
    client = build_test_client(tmp_path)

    response = client.get("/v1/traces")

    assert response.status_code == 200
    data = response.json()

    assert "traces" in data
    assert data["traces"] == []


def test_list_traces_with_files(tmp_path: Path):
    create_trace_file(tmp_path, "trace_a", {})
    create_trace_file(tmp_path, "trace_b", {})

    client = build_test_client(tmp_path)

    response = client.get("/v1/traces")

    assert response.status_code == 200
    data = response.json()

    assert sorted(data["traces"]) == ["trace_a.json", "trace_b.json"]


# ============================================================
# TEST: GET TRACE
# ============================================================

def test_get_trace_success(tmp_path: Path):
    payload = {"events": [], "execution_states": []}
    create_trace_file(tmp_path, "sample", payload)

    client = build_test_client(tmp_path)

    response = client.get("/v1/traces/sample")

    assert response.status_code == 200
    assert response.json() == payload


def test_get_trace_not_found(tmp_path: Path):
    client = build_test_client(tmp_path)

    response = client.get("/v1/traces/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "trace not found"


def test_get_trace_invalid_format(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("not-json", encoding="utf-8")

    client = build_test_client(tmp_path)

    response = client.get("/v1/traces/bad")

    assert response.status_code == 400


def test_get_trace_non_object(tmp_path: Path):
    path = tmp_path / "array.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    client = build_test_client(tmp_path)

    response = client.get("/v1/traces/array")

    assert response.status_code == 400
    assert "trace must be a JSON object" in response.json()["detail"]


# ============================================================
# TEST: TRACE ID SAFETY
# ============================================================

# ✅ IMPORTANT:
# "." CANNOT be tested because FastAPI normalizes:
# /traces/. → /traces → list endpoint (200)
# So we exclude it from validation tests.

@pytest.mark.parametrize("bad_id", ["../hack", "a/b", "a\\b", ".."])
def test_trace_id_validation(tmp_path: Path, bad_id: str):
    client = build_test_client(tmp_path)

    response = client.get(f"/v1/traces/{bad_id}")

    # Some inputs hit router (404), others hit validation (400)
    assert response.status_code in (400, 404)


# ============================================================
# TEST: REPLAY INSPECTION
# ============================================================

def test_replay_ready_trace(tmp_path: Path):
    payload = {
        "events": [],
        "normalized_events": [],
        "execution_states": [],
        "witnesses": [],
        "hash": None,
    }

    create_trace_file(tmp_path, "trace_ready", payload)

    client = build_test_client(tmp_path)

    response = client.post("/v1/traces/trace_ready/replay")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ready"
    assert data["missing"] == []
    assert "computed_hash" in data
    assert data["hash_matches"] is False


def test_replay_incomplete_trace(tmp_path: Path):
    payload = {
        "events": [],
        "execution_states": [],
    }

    create_trace_file(tmp_path, "trace_partial", payload)

    client = build_test_client(tmp_path)

    response = client.post("/v1/traces/trace_partial/replay")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "incomplete"
    assert "normalized_events" in data["missing"]
    assert "witnesses" in data["missing"]


def test_replay_trace_not_found(tmp_path: Path):
    client = build_test_client(tmp_path)

    response = client.post("/v1/traces/missing/replay")

    assert response.status_code == 404


# ============================================================
# TEST: HASH CONSISTENCY
# ============================================================

def test_hash_match_detection(tmp_path: Path, monkeypatch):
    expected_hash = "fixed_hash"

    monkeypatch.setattr(
        "afritech.api.trace_api.stable_hash",
        lambda _: expected_hash,
    )

    payload = {
        "events": [],
        "normalized_events": [],
        "execution_states": [],
        "witnesses": [],
        "hash": expected_hash,
    }

    create_trace_file(tmp_path, "trace_hash", payload)

    client = build_test_client(tmp_path)

    response = client.post("/v1/traces/trace_hash/replay")

    assert response.status_code == 200
    data = response.json()

    assert data["hash_matches"] is True
    assert data["computed_hash"] == expected_hash


# ============================================================
# TEST: FILE FILTERING
# ============================================================

def test_ignores_non_json_files(tmp_path: Path):
    (tmp_path / "note.txt").write_text("ignore me", encoding="utf-8")
    create_trace_file(tmp_path, "valid", {})

    client = build_test_client(tmp_path)

    response = client.get("/v1/traces")

    assert response.status_code == 200
    traces = response.json()["traces"]

    assert traces == ["valid.json"]