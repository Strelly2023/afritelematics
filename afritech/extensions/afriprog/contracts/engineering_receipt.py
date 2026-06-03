from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord
from afritech.extensions.afriprog.task_planner.task_model import Task


class EngineeringReceiptError(Exception):
    """Raised when an AfriProg engineering receipt is invalid."""


@dataclass(frozen=True)
class EngineeringReceipt:
    """
    Canonical AfriProg engineering receipt.

    The receipt binds a task to evidence without granting authority to merge,
    deploy, certify, or mutate runtime state.
    """

    receipt_id: str
    task: Task
    evidence: tuple[EvidenceRecord, ...]
    status: str = "proposal_only"

    def __post_init__(self) -> None:
        if not self.receipt_id.strip():
            raise EngineeringReceiptError("receipt_id must not be empty")

        if self.status not in {"proposal_only", "validated", "failed"}:
            raise EngineeringReceiptError(f"unsupported receipt status: {self.status}")

    @property
    def receipt_hash(self) -> str:
        material = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def canonical_payload(self) -> dict[str, Any]:
        ordered_evidence = tuple(
            sorted(self.evidence, key=lambda item: item.evidence_id)
        )

        return {
            "receipt_id": self.receipt_id,
            "task": self.task.canonical_dict(),
            "evidence": [
                record.canonical_dict()
                for record in ordered_evidence
            ],
            "status": self.status,
            "authority": "proposal_only",
            "merge_authority": False,
            "runtime_authority": False,
            "proof_authority": False,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            **self.canonical_payload(),
            "receipt_hash": self.receipt_hash,
        }


def build_engineering_receipt(
    *,
    task: Task,
    evidence: Iterable[EvidenceRecord],
    receipt_id: str | None = None,
    status: str = "proposal_only",
) -> EngineeringReceipt:
    evidence_tuple = tuple(evidence)
    stable_id = receipt_id or _receipt_id(task, evidence_tuple)

    return EngineeringReceipt(
        receipt_id=stable_id,
        task=task,
        evidence=evidence_tuple,
        status=status,
    )


def _receipt_id(task: Task, evidence: tuple[EvidenceRecord, ...]) -> str:
    material = json.dumps(
        {
            "task_id": task.task_id,
            "evidence_ids": sorted(record.evidence_id for record in evidence),
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16].upper()
    return f"AFRIPROG-RECEIPT-{digest}"


__all__ = [
    "EngineeringReceipt",
    "EngineeringReceiptError",
    "build_engineering_receipt",
]
