from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from afritech.agents.environment_runtime import (
    AdmissionDecision,
    AgentApproval,
    AgentDecisionStore,
    AgentProposal,
    AgentRuntimeViolation,
    DecisionTransitionPolicy,
    EnvironmentAgentPolicy,
    build_environment_agent_runtime,
    build_environment_agent_runtime_from_env,
    generate_proposal_id,
)


ALLOWED_ACTIONS = frozenset({"recommend_capacity", "recommend_dispatch"})


class StubAgent:
    agent_id = "capacity-agent"

    def __init__(self, output: dict[str, object]) -> None:
        self.output = output

    def propose(self, context):
        return {**self.output, "payload": {"observed_load": context["load"]}}


def _proposal(*, environment: str, risk: str = "low", confidence: float = 0.9) -> AgentProposal:
    return AgentProposal(
        proposal_id="proposal-001",
        environment=environment,
        agent_id="capacity-agent",
        action="recommend_capacity",
        rationale="Observed demand exceeds configured capacity.",
        confidence=confidence,
        risk=risk,
        payload={"replicas": 3},
        created_at="2026-07-03T00:00:00+00:00",
    )


def _proposal_hash(proposal: AgentProposal) -> str:
    encoded = json.dumps(
        proposal.canonical(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _decision_hash(
    *,
    proposal_id: str,
    environment: str,
    status: str,
    executable: bool,
    reason: str,
    policy_version: str,
    proposal_hash: str,
    approval: AgentApproval | None = None,
) -> str:
    encoded = json.dumps(
        {
            "proposal_id": proposal_id,
            "environment": environment,
            "status": status,
            "executable": executable,
            "reason": reason,
            "policy_version": policy_version,
            "proposal_hash": proposal_hash,
            "approval": approval.canonical() if approval else None,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_staging_auto_admits_only_low_risk_high_confidence_proposals() -> None:
    policy = EnvironmentAgentPolicy(
        environment="staging",
        allowed_actions=ALLOWED_ACTIONS,
        minimum_confidence=0.7,
    )

    decision = policy.evaluate(_proposal(environment="staging"))

    assert decision.status == "admitted"
    assert decision.executable is True
    assert decision.reason == "staging_low_risk_auto_admission"


def test_production_requires_explicit_approval_before_admission() -> None:
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
        minimum_confidence=0.85,
    )
    proposal = _proposal(environment="production")

    pending = policy.evaluate(proposal)
    admitted = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="operator-001",
            approval_ref="change-approval-001",
        ),
    )

    assert pending.status == "review_required"
    assert pending.executable is False
    assert pending.reason == "production_approval_required"
    assert admitted.status == "admitted"
    assert admitted.executable is True
    assert admitted.reason == "production_approval_validated"


def test_high_risk_and_unknown_actions_are_never_executable() -> None:
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )

    high_risk = policy.evaluate(_proposal(environment="production", risk="high"))
    unknown = policy.evaluate(
        AgentProposal(
            **{
                **_proposal(environment="production").__dict__,
                "action": "mutate_production_state",
            }
        )
    )

    assert (high_risk.status, high_risk.executable) == ("rejected", False)
    assert high_risk.reason == "risk_exceeds_environment_policy"
    assert (unknown.status, unknown.executable) == ("rejected", False)
    assert unknown.reason == "action_not_allowed"


def test_cross_environment_proposals_and_state_writes_are_rejected(tmp_path: Path) -> None:
    production_policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    staging_proposal = _proposal(environment="staging")

    with pytest.raises(AgentRuntimeViolation, match="cross_environment"):
        production_policy.evaluate(staging_proposal)

    staging_policy = EnvironmentAgentPolicy(
        environment="staging",
        allowed_actions=ALLOWED_ACTIONS,
    )
    decision = staging_policy.evaluate(staging_proposal)
    production_store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    with pytest.raises(AgentRuntimeViolation, match="cross_environment"):
        production_store.save(staging_proposal, decision)


def test_decision_ledger_survives_rebuild_and_is_hash_chained(tmp_path: Path) -> None:
    state_path = tmp_path / "staging.sqlite3"
    policy = EnvironmentAgentPolicy(
        environment="staging",
        allowed_actions=ALLOWED_ACTIONS,
    )
    first_store = AgentDecisionStore(state_path, environment="staging")
    first = _proposal(environment="staging")
    first_store.save(first, policy.evaluate(first))

    second = AgentProposal(
        **{
            **first.__dict__,
            "proposal_id": "proposal-002",
            "payload": {"replicas": 4},
        }
    )
    rebuilt_store = AgentDecisionStore(state_path, environment="staging")
    rebuilt_store.save(second, policy.evaluate(second))

    records = rebuilt_store.decisions()
    assert len(records) == 2
    assert records[0]["previous_record_hash"] == "GENESIS"
    assert records[1]["previous_record_hash"] == records[0]["record_hash"]


def test_repeated_identical_proposal_and_decision_is_idempotent(
    tmp_path: Path,
) -> None:
    store = AgentDecisionStore(
        tmp_path / "staging.sqlite3",
        environment="staging",
    )
    policy = EnvironmentAgentPolicy(
        environment="staging",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="staging")
    decision = policy.evaluate(proposal)

    first_record_hash = store.save(proposal, decision)
    repeated_record_hash = store.save(proposal, decision)

    assert repeated_record_hash == first_record_hash
    assert len(store.decisions()) == 1


def test_production_approval_appends_new_decision(
    tmp_path: Path,
) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production")
    pending = policy.evaluate(proposal)
    store.save(proposal, pending)

    approved = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-001",
        ),
    )

    store.save(proposal, approved)

    records = store.decisions_for_proposal(proposal.proposal_id)
    assert len(records) == 2
    assert records[0]["decision"]["status"] == "review_required"
    assert records[0]["decision"]["executable"] is False
    assert records[1]["decision"]["status"] == "admitted"
    assert records[1]["decision"]["executable"] is True
    assert records[1]["previous_record_hash"] == records[0]["record_hash"]


def test_terminal_decision_cannot_be_replaced_by_another_decision(
    tmp_path: Path,
) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production")
    admitted = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-001",
        ),
    )
    store.save(proposal, admitted)

    pending = policy.evaluate(proposal)
    with pytest.raises(
        AgentRuntimeViolation,
        match="invalid_decision_transition",
    ):
        store.save(proposal, pending)


def test_transition_policy_is_configurable_and_environment_scoped() -> None:
    transition_policy = DecisionTransitionPolicy(
        environment="production",
        allowed_states=frozenset(
            {
                "review_required",
                "investigation_required",
                "admitted",
                "rejected",
            }
        ),
        transitions={
            "review_required": frozenset({"investigation_required"}),
            "investigation_required": frozenset({"admitted", "rejected"}),
            "admitted": frozenset(),
            "rejected": frozenset(),
        },
    )

    transition_policy.validate(
        {
            "environment": "production",
            "status": "review_required",
        },
        {
            "environment": "production",
            "status": "investigation_required",
            "executable": False,
        },
    )

    with pytest.raises(
        AgentRuntimeViolation,
        match="cross_environment_decision_transition",
    ):
        transition_policy.validate(
            {
                "environment": "staging",
                "status": "review_required",
            },
            {
                "environment": "production",
                "status": "investigation_required",
            },
        )


def test_transition_policy_rejects_unknown_states() -> None:
    with pytest.raises(
        AgentRuntimeViolation,
        match=r"transition_state_not_registered.*investigation_required",
    ):
        DecisionTransitionPolicy(
            environment="production",
            allowed_states=frozenset({"review_required", "admitted", "rejected"}),
            transitions={
                "review_required": frozenset({"investigation_required"}),
                "admitted": frozenset(),
                "rejected": frozenset(),
            },
        )


def test_transition_policy_rejects_unknown_states_without_allowed_states() -> None:
    with pytest.raises(
        AgentRuntimeViolation,
        match=r"transition_state_not_registered.*admited",
    ):
        DecisionTransitionPolicy(
            environment="production",
            transitions={
                "review_required": frozenset({"admited"}),
            },
        )


def test_registered_custom_workflow_is_valid() -> None:
    transition_policy = DecisionTransitionPolicy(
        environment="production",
        allowed_states=frozenset(
            {
                "review_required",
                "investigation_required",
                "admitted",
                "rejected",
            }
        ),
        transitions={
            "review_required": frozenset({"investigation_required"}),
            "investigation_required": frozenset({"admitted"}),
            "admitted": frozenset(),
            "rejected": frozenset(),
        },
    )

    transition_policy.validate(
        {
            "environment": "production",
            "status": "review_required",
        },
        {
            "environment": "production",
            "status": "investigation_required",
        },
    )


def test_admitted_decision_is_terminal(tmp_path: Path) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production")
    first_admitted = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-001",
        ),
    )
    store.save(proposal, first_admitted)

    second_admitted = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops-2",
            approval_ref="chg-002",
        ),
    )

    with pytest.raises(AgentRuntimeViolation, match="invalid_decision_transition"):
        store.save(proposal, second_admitted)


def test_legacy_single_decision_schema_migrates_to_decision_history(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy-production.sqlite3"
    proposal = _proposal(environment="production")
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    pending = policy.evaluate(proposal)
    proposal_json = json.dumps(
        proposal.canonical(),
        sort_keys=True,
        separators=(",", ":"),
    )
    decision_json = json.dumps(
        pending.canonical(),
        indent=2,
    )
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE agent_proposals (
                proposal_id TEXT PRIMARY KEY,
                environment TEXT NOT NULL,
                proposal_json TEXT NOT NULL,
                proposal_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE agent_decisions (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL UNIQUE,
                environment TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                previous_record_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL UNIQUE
            );
            """
        )
        connection.execute(
            """
            INSERT INTO agent_proposals
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                proposal.proposal_id,
                proposal.environment,
                proposal_json,
                pending.proposal_hash,
                proposal.created_at,
            ),
        )
        connection.execute(
            """
            INSERT INTO agent_decisions (
                proposal_id, environment, decision_json,
                previous_record_hash, record_hash
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                proposal.proposal_id,
                proposal.environment,
                decision_json,
                "GENESIS",
                "legacy-record-hash",
            ),
        )

    migrated = AgentDecisionStore(path, environment="production")
    approved = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-legacy-001",
        ),
    )
    migrated.save(proposal, approved)

    records = migrated.decisions_for_proposal(proposal.proposal_id)
    assert [record["decision"]["status"] for record in records] == [
        "review_required",
        "admitted",
    ]


def test_failed_legacy_migration_rolls_back_without_losing_ledger(
    tmp_path: Path,
) -> None:
    path = tmp_path / "broken-legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE agent_proposals (
                proposal_id TEXT PRIMARY KEY,
                environment TEXT NOT NULL,
                proposal_json TEXT NOT NULL,
                proposal_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE agent_decisions (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL UNIQUE,
                environment TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                previous_record_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL UNIQUE
            );
            INSERT INTO agent_decisions (
                proposal_id, environment, decision_json,
                previous_record_hash, record_hash
            ) VALUES (
                'proposal-broken', 'production', '{}',
                'GENESIS', 'legacy-broken-record'
            );
            """
        )

    with pytest.raises(
        AgentRuntimeViolation,
        match="legacy_decision_migration_failed:missing_hash",
    ):
        AgentDecisionStore(path, environment="production")

    with sqlite3.connect(path) as connection:
        table_names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        count = connection.execute(
            "SELECT COUNT(*) FROM agent_decisions"
        ).fetchone()[0]
    assert "agent_decisions" in table_names
    assert "agent_decisions_legacy" not in table_names
    assert count == 1


def test_full_production_workflow_persists_review_and_admission(
    tmp_path: Path,
) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production")

    review = policy.evaluate(proposal)
    store.save(proposal, review)

    approved = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-001",
        ),
    )
    store.save(proposal, approved)

    history = store.decisions_for_proposal(proposal.proposal_id)

    assert [entry["decision"]["status"] for entry in history] == [
        "review_required",
        "admitted",
    ]
    assert history[1]["decision"]["executable"] is True


def test_proposal_history_queries_only_requested_proposal(
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = AgentDecisionStore(
        tmp_path / "staging.sqlite3",
        environment="staging",
    )
    policy = EnvironmentAgentPolicy(
        environment="staging",
        allowed_actions=ALLOWED_ACTIONS,
    )
    target = _proposal(environment="staging")
    other = AgentProposal(
        **{
            **target.__dict__,
            "proposal_id": "proposal-other",
        }
    )
    store.save(target, policy.evaluate(target))
    store.save(other, policy.evaluate(other))
    monkeypatch.setattr(
        store,
        "decisions",
        lambda: (_ for _ in ()).throw(AssertionError("full scan")),
    )

    records = store.decisions_for_proposal(target.proposal_id)

    assert len(records) == 1
    assert records[0]["proposal_id"] == target.proposal_id


def test_deterministic_proposal_id_supports_retry_idempotency() -> None:
    payload = {
        "environment": "production",
        "agent_id": "capacity-agent",
        "action": "recommend_capacity",
        "confidence": 0.91,
    }

    first = generate_proposal_id(
        payload,
        deterministic=True,
        namespace="production:capacity-agent",
    )
    second = generate_proposal_id(
        dict(reversed(tuple(payload.items()))),
        deterministic=True,
        namespace="production:capacity-agent",
    )
    staging = generate_proposal_id(
        payload,
        deterministic=True,
        namespace="staging:capacity-agent",
    )

    assert first == second
    assert first != staging
    assert first.startswith("agent-proposal-")
    assert generate_proposal_id(payload) != generate_proposal_id(payload)


def test_rejected_decision_cannot_transition_to_admitted(tmp_path: Path) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production", risk="high")
    rejected = policy.evaluate(proposal)
    store.save(proposal, rejected)

    proposal_hash = _proposal_hash(proposal)
    approval = AgentApproval(
        approved_by="ops",
        approval_ref="chg-002",
    )
    admitted = AdmissionDecision(
        proposal_id=proposal.proposal_id,
        environment="production",
        status="admitted",
        executable=True,
        reason="production_approval_validated",
        policy_version=policy.policy_version,
        proposal_hash=proposal_hash,
        decision_hash=_decision_hash(
            proposal_id=proposal.proposal_id,
            environment="production",
            status="admitted",
            executable=True,
            reason="production_approval_validated",
            policy_version=policy.policy_version,
            proposal_hash=proposal_hash,
            approval=approval,
        ),
        approval=approval,
    )

    with pytest.raises(AgentRuntimeViolation, match="invalid_decision_transition"):
        store.save(proposal, admitted)


def test_store_rejects_tampered_current_proposal_hash(tmp_path: Path) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production")
    pending = policy.evaluate(proposal)
    store.save(proposal, pending)

    tampered = AdmissionDecision(
        proposal_id=proposal.proposal_id,
        environment="production",
        status="admitted",
        executable=True,
        reason="production_approval_validated",
        policy_version=policy.policy_version,
        proposal_hash="tampered-proposal-hash",
        decision_hash="tampered-decision-hash",
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-003",
        ),
    )

    with pytest.raises(AgentRuntimeViolation, match="proposal hash mismatch"):
        store.save(proposal, tampered)


def test_store_rejects_corrupted_previous_proposal_chain(tmp_path: Path) -> None:
    store = AgentDecisionStore(
        tmp_path / "production.sqlite3",
        environment="production",
    )
    policy = EnvironmentAgentPolicy(
        environment="production",
        allowed_actions=ALLOWED_ACTIONS,
    )
    proposal = _proposal(environment="production")
    pending = policy.evaluate(proposal)
    store.save(proposal, pending)

    with sqlite3.connect(store.path) as connection:
        connection.execute(
            """
            UPDATE agent_decisions
            SET decision_json = ?
            WHERE proposal_id = ? AND sequence = 1
            """,
            (
                json.dumps(
                    {
                        **pending.canonical(),
                        "proposal_hash": "corrupted-previous-proposal-hash",
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                proposal.proposal_id,
            ),
        )
        connection.commit()

    approved = policy.evaluate(
        proposal,
        approval=AgentApproval(
            approved_by="ops",
            approval_ref="chg-004",
        ),
    )

    with pytest.raises(AgentRuntimeViolation, match="proposal_chain_mismatch"):
        store.save(proposal, approved)


def test_decisions_table_uses_environment_proposal_sequence_index(
    tmp_path: Path,
) -> None:
    store = AgentDecisionStore(
        tmp_path / "staging.sqlite3",
        environment="staging",
    )

    with sqlite3.connect(store.path) as connection:
        index_names = {
            str(row[1])
            for row in connection.execute("PRAGMA index_list(agent_decisions)")
        }

    assert "agent_decisions_env_proposal_sequence" in index_names
    assert "agent_decisions_proposal_sequence" not in index_names


def test_runtime_contains_agent_nondeterminism_and_persists_admission(tmp_path: Path) -> None:
    runtime = build_environment_agent_runtime(
        environment="staging",
        state_path=tmp_path / "agents.sqlite3",
        allowed_actions=ALLOWED_ACTIONS,
        minimum_confidence=0.7,
    )
    runtime.clock = lambda: datetime(2026, 7, 3, tzinfo=UTC)
    agent = StubAgent(
        {
            "proposal_id": "proposal-runtime-001",
            "action": "recommend_capacity",
            "rationale": "Load is above the staging threshold.",
            "confidence": 0.91,
            "risk": "low",
        }
    )

    decision = runtime.run(agent, {"load": 0.92})

    assert decision.status == "admitted"
    assert runtime.store.decisions()[0]["decision"]["decision_hash"] == decision.decision_hash


def test_environment_factory_requires_explicit_isolated_configuration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("AFRITECH_RUNTIME_ENVIRONMENT", raising=False)
    monkeypatch.delenv("AFRITECH_AGENT_STATE_PATH", raising=False)
    with pytest.raises(AgentRuntimeViolation, match="required"):
        build_environment_agent_runtime_from_env(allowed_actions=ALLOWED_ACTIONS)

    state_path = tmp_path / "production.sqlite3"
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("AFRITECH_AGENT_STATE_PATH", str(state_path))
    monkeypatch.setenv("AFRITECH_AGENT_MINIMUM_CONFIDENCE", "0.9")
    runtime = build_environment_agent_runtime_from_env(
        allowed_actions=ALLOWED_ACTIONS
    )

    assert runtime.environment == "production"
    assert runtime.policy.minimum_confidence == 0.9
    assert runtime.store.path == state_path
