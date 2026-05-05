import pytest

from afritech.replay.transcript import (
    ReplayTranscriptGenerator,
    ConstitutionalRequest
)


@pytest.fixture
def valid_request():
    return ConstitutionalRequest(
        payload={
            "constitutional_request": {
                "request_id": "test-req-001",
                "epoch_id": "constitution-epoch-0001",
                "authority_profile": "CONSTITUTIONAL_RESEARCH_AGENT",
                "domain": "research",
                "risk_class": "low",
                "permissible_operations": [
                    "research_synthesis",
                    "citation_analysis",
                    "non_mutating_inference",
                ],
                "prohibited_operations": [
                    "state_mutation",
                    "external_action",
                    "system_command",
                    "environment_interaction",
                    "registry_modification",
                    "epoch_advancement",
                    "authority_delegation",
                ],
                "required_attestations": [],
                "replay_requirements": {
                    "deterministic": True,
                    "witnesses_required": 0,
                },
                "determinism_scope": {
                    "assumes_single_runtime": True,
                    "excludes_federation_variance": True,
                },
                "output_constraints": {
                    "citation_required": True,
                    "max_claims": 10,
                    "epistemic_confidence_required": True,
                    "causal_trace_required": True,
                },
            }
        }
    )


@pytest.fixture
def transcript_path(tmp_path):
    return tmp_path / "transcript.yaml"


@pytest.fixture
def valid_transcript(valid_request, transcript_path):
    generator = ReplayTranscriptGenerator()
    generator.generate(
        request=valid_request,
        output_path=str(transcript_path),
    )
    return transcript_path