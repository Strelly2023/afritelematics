from __future__ import annotations

from afritech.extensions.afriprog.evidence.evidence_generator import EvidenceGenerator
from afritech.extensions.afriprog.git_agent.git_client import (
    GitClient,
    GitClientError,
    GitSnapshot,
)
from afritech.extensions.afriprog.git_agent.pr_generator import (
    PullRequestProposalGenerator,
)
from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.task_planner.task_types import RiskLevel, TaskType


def _task() -> Task:
    return Task(
        task_id="TASK-0001",
        task_type=TaskType.MISSING_ELEMENT.value,
        description="Investigate missing implementation element.",
        target_files=("afritech/extensions/afriprog/example.py",),
        risk_level=RiskLevel.LOW.value,
        requires_write=False,
        source_tests=(),
    )


def test_git_client_rejects_mutating_command():
    client = GitClient(root=".")

    try:
        client._run(["git", "commit"])  # noqa: SLF001
    except GitClientError as exc:
        assert "unsupported git command" in str(exc)
    else:
        raise AssertionError("mutating git command was accepted")


def test_git_client_snapshot_is_evidence_ready():
    snapshot = GitClient(root=".").snapshot()

    data = snapshot.canonical_dict()

    assert "branch" in data
    assert "dirty" in data
    assert isinstance(data["changed_files"], list)


def test_pull_request_proposal_is_metadata_only():
    task = _task()
    evidence = EvidenceGenerator().from_task(task)
    snapshot = GitSnapshot(
        branch="main",
        status_short=(" M afritech/extensions/afriprog/orchestrator.py",),
        changed_files=("afritech/extensions/afriprog/orchestrator.py",),
        head_sha="abc123",
    )

    proposal = PullRequestProposalGenerator().build(
        task=task,
        evidence=(evidence,),
        snapshot=snapshot,
    )

    data = proposal.canonical_dict()

    assert data["branch_name"] == "codex/afriprog-task-0001"
    assert data["git_mutation_enabled"] is False
    assert data["evidence_ids"] == [evidence.evidence_id]
    assert len(data["proposal_hash"]) == 64
