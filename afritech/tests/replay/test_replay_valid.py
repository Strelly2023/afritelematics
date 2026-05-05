from afritech.replay.verify import ReplayVerifier


def test_replay_valid(valid_request, valid_transcript):
    verifier = ReplayVerifier()
    verdict = verifier.verify(
        transcript_path=str(valid_transcript),
        request=valid_request,
    )

    assert verdict.status == "REPLAY_VALID"
    assert verdict.replay_hash is not None
    assert verdict.failure_mode is None
    assert verdict.environment_match is True
    assert verdict.trace_match is True
    assert verdict.truthpacket_match is True