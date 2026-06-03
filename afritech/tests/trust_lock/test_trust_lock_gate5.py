from __future__ import annotations

from afritech.ci.trust_lock_validator import validate
from afritech.replay_authority.engine.proof import run_replay_authority_proof
from afritech.trust_lock.engine import (
    build_dependency_graph,
    consume_audit_packet,
    simulate_removal,
)
from afritech.trust_lock.engine.proof import (
    REQUIRED_SCENARIOS,
    run_trust_lock_proof,
)


def test_trust_lock_proof_preserves_all_scenarios():
    report = run_trust_lock_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.verified is True


def test_trust_lock_validator_accepts_generated_reports():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_external_workflows_accept_replay_authority_packet():
    graph = build_dependency_graph()
    packet = _audit_packet()
    results = tuple(
        consume_audit_packet(dependency, packet)
        for dependency in graph.dependencies
    )

    assert all(result.accepted for result in results)
    assert {result.reason for result in results} == {
        "accepted_replay_authority_evidence"
    }


def test_removal_breaks_all_dependent_workflows():
    graph = build_dependency_graph()
    simulation = simulate_removal(graph, _audit_packet())

    assert simulation.baseline_trusted is True
    assert simulation.removal_breaks_workflows is True
    assert {
        result.reason for result in simulation.removed_results
    } == {"missing_replay_authority_packet"}


def test_replacement_without_replay_authority_breaks_trust():
    graph = build_dependency_graph()
    simulation = simulate_removal(graph, _audit_packet())

    assert simulation.replacement_breaks_trust is True
    assert {
        result.reason for result in simulation.replacement_results
    } == {"missing_required_evidence:replay_authority_hash"}


def _audit_packet():
    report = run_replay_authority_proof()
    scenario = next(
        item
        for item in report.scenarios
        if item.scenario == "conflicting_claims_resolution"
    )
    return scenario.audit_packet.canonical_dict()

