# afritech/tests/replay/test_replay_valid.py

import json
import hashlib
import yaml

import pytest

from afritech.replay.verify import ReplayVerifier


# ============================================================
# MINIMAL CONSTITUTIONAL REQUEST (LOCAL)
# ============================================================

class ConstitutionalRequest:
    """
    Minimal test-compatible request object.

    Provides canonical_hash() required by ReplayVerifier.
    """

    def __init__(self, request_id: str):
        self.request_id = request_id

    def canonical_hash(self) -> str:
        payload = {
            "request_id": self.request_id
        }

        canonical = json.dumps(
            payload,
            sort_keys=True
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def valid_request():
    return ConstitutionalRequest(
        request_id="test-req-001"
    )


@pytest.fixture
def valid_transcript(tmp_path):

    path = tmp_path / "transcript.yaml"

    base = {
        "replay_environment": {
            "deterministic_mode": True
        },
        "execution_trace": [
            {
                "step": 1,
                "input_hash": "abc123",
                "output_hash": "def456",
            },
            {
                "step": 2,
                "input_hash": "def456",
                "output_hash": "ghi789",
            }
        ],
        "truthpacket": {
            "valid": True
        }
    }

    # ✅ canonical hash
    canonical = json.dumps(base, sort_keys=True)

    base["replay_hash"] = hashlib.sha256(
        canonical.encode()
    ).hexdigest()

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            base,
            f,
            sort_keys=True,
            allow_unicode=True,
        )

    return path


# ============================================================
# TEST
# ============================================================

def test_replay_valid(valid_request, valid_transcript):

    verifier = ReplayVerifier()

    verdict = verifier.verify(
        transcript_path=str(valid_transcript),
        request=valid_request,
    )

    assert verdict.status == "REPLAY_VALID"

    assert verdict.replay_hash is not None
    assert len(verdict.replay_hash) == 64

    assert verdict.failure_mode is None

    assert verdict.environment_match is True
    assert verdict.trace_match is True
    assert verdict.truthpacket_match is True

    assert verdict.violated_invariant is None
    assert verdict.divergence_location is None