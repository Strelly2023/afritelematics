from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from afritech.extensions.afriprog.code_executor.diff_model import Diff
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord
from afritech.extensions.afriprog.git_agent.git_client import GitSnapshot
from afritech.extensions.afriprog.task_planner.task_model import Task


class PullRequestProposalError(Exception):
    """Raised when a pull request proposal cannot be constructed."""


@dataclass(frozen=True)
class PullRequestProposal:
    """
    Deterministic pull request proposal.

    This is metadata only. It never creates a branch, commit, push, or PR.
    """

    title: str
    body: str
    branch_name: str
    labels: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    proposal_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "body": self.body,
            "branch_name": self.branch_name,
            "labels": list(self.labels),
            "evidence_ids": list(self.evidence_ids),
            "proposal_hash": self.proposal_hash,
            "mode": "PROPOSAL_ONLY",
            "git_mutation_enabled": False,
        }


class PullRequestProposalGenerator:
    """
    Create review-ready PR metadata from AfriProg evidence.

    The output is useful for humans or a future approved git surface, but this
    generator does not perform git or network actions.
    """

    DEFAULT_LABELS = ("afriprog", "proposal-only", "ga-elite")

    def build(
        self,
        *,
        task: Task,
        patch: Patch | None = None,
        diff: Diff | None = None,
        evidence: Iterable[EvidenceRecord] = (),
        snapshot: GitSnapshot | None = None,
    ) -> PullRequestProposal:
        evidence_ids = tuple(
            sorted(record.evidence_id for record in evidence)
        )

        title = f"AfriProg: {task.description}"
        branch_name = _branch_name(task.task_id)
        body = _build_body(
            task=task,
            patch=patch,
            diff=diff,
            evidence_ids=evidence_ids,
            snapshot=snapshot,
        )

        material = {
            "title": title,
            "body": body,
            "branch_name": branch_name,
            "labels": self.DEFAULT_LABELS,
            "evidence_ids": evidence_ids,
        }

        proposal_hash = hashlib.sha256(
            json.dumps(
                material,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return PullRequestProposal(
            title=title,
            body=body,
            branch_name=branch_name,
            labels=self.DEFAULT_LABELS,
            evidence_ids=evidence_ids,
            proposal_hash=proposal_hash,
        )


def _branch_name(task_id: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "-"
        for character in task_id
    ).strip("-")

    if not normalized:
        raise PullRequestProposalError("task_id cannot form a branch name")

    return f"codex/afriprog-{normalized}"


def _build_body(
    *,
    task: Task,
    patch: Patch | None,
    diff: Diff | None,
    evidence_ids: tuple[str, ...],
    snapshot: GitSnapshot | None,
) -> str:
    lines = [
        "## AfriProg Proposal",
        "",
        f"- Task: {task.task_id}",
        f"- Risk: {task.risk_level}",
        "- Write permitted: False",
        f"- Patch proposed: {patch is not None}",
        f"- Diff proposed: {diff is not None}",
        "",
        "## Evidence",
    ]

    if evidence_ids:
        lines.extend(f"- {evidence_id}" for evidence_id in evidence_ids)
    else:
        lines.append("- none")

    if snapshot is not None:
        lines.extend(
            [
                "",
                "## Git Snapshot",
                f"- Branch: {snapshot.branch}",
                f"- Dirty: {snapshot.dirty}",
                f"- HEAD: {snapshot.head_sha}",
            ]
        )

    lines.extend(
        [
            "",
            "## Constitutional Boundary",
            "This proposal is metadata only and performs no git mutation.",
        ]
    )

    return "\n".join(lines)
