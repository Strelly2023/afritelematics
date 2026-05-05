import yaml
from afritech.replay.verify import ReplayVerifier


def test_trace_divergence(valid_request, valid_transcript):
    with open(valid_transcript, "r", encoding="utf-8") as f:
        transcript = yaml.safe_load(f)

    transcript["execution_trace"].append({
        "step": "illegal_extra_step",
        "input_hash": "x",
        "output_hash": "y",
    })

    with open(valid_transcript, "w", encoding="utf-8") as f:
        yaml.safe_dump(transcript, f)

    verifier = ReplayVerifier()
    verdict = verifier.verify(
        transcript_path=str(valid_transcript),
        request=valid_request,
    )

    assert verdict.status == "REPLAY_INVALID"
    assert verdict.failure_mode == "trace_divergence"