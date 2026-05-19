from __future__ import annotations

from afritech.demo import proof


def test_proof_module_runs_and_prints_claim_snapshot(capsys) -> None:
    exit_code = proof.run()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "=== AFRITECH CONTINUITY PROOF ===" in output
    assert "Scenario: AfriRide Mobility Disruption" in output
    assert "CLAIM -> EVIDENCE SNAPSHOT" in output
    assert "SUMMARY:" in output
    assert "No claim is made for global deployment readiness" in output


def test_proof_module_can_emit_machine_readable_payload(capsys) -> None:
    exit_code = proof.run(json_output=True)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"continuity": "pass"' in output
    assert '"replay": "pass"' in output
    assert '"identity": "stable"' in output
    assert '"conflicts": "deterministic"' in output
    assert '"claims_valid": true' in output
