from afritech.replay.verify import ReplayVerifier


def test_invalid_transcript_schema(valid_request, transcript_path):
    transcript_path.write_text(
        "invalid: true",
        encoding="utf-8",
    )

    verifier = ReplayVerifier()
    verdict = verifier.verify(
        transcript_path=str(transcript_path),
        request=valid_request,
    )

    assert verdict.status == "REPLAY_INVALID"
    assert verdict.failure_mode == "invalid_transcript_schema"