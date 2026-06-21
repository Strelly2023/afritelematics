from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True)
class GovernanceReceipt:
    receipt_id: str
    organization_id: str
    project_id: str
    prompt_hash: str
    output_hash: str
    trust_score: int
    status: str
    sequence: int
    signature: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "prompt_hash": self.prompt_hash,
            "output_hash": self.output_hash,
            "trust_score": self.trust_score,
            "status": self.status,
            "sequence": self.sequence,
            "signature": self.signature,
        }


class GovernanceReceiptStore:
    def __init__(self) -> None:
        self._records: list[GovernanceReceipt] = []

    def issue(
        self,
        *,
        organization_id: str,
        project_id: str,
        prompt: str,
        output: dict[str, Any],
        trust_score: int,
        status: str,
    ) -> GovernanceReceipt:
        prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
        output_hash = sha256(json.dumps(output, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        sequence = 1 + len(
            [
                record
                for record in self._records
                if record.organization_id == organization_id and record.project_id == project_id
            ]
        )
        receipt_id = "rcpt-" + sha256(
            f"{organization_id}:{project_id}:{sequence}:{prompt_hash}:{output_hash}".encode("utf-8")
        ).hexdigest()[:12]
        signature = sha256(
            f"{receipt_id}:{prompt_hash}:{output_hash}:{trust_score}:{status}:{sequence}".encode("utf-8")
        ).hexdigest()
        receipt = GovernanceReceipt(
            receipt_id=receipt_id,
            organization_id=organization_id,
            project_id=project_id,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            trust_score=trust_score,
            status=status,
            sequence=sequence,
            signature=signature,
        )
        self._records.append(receipt)
        return receipt

    def recent(self, *, organization_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        items = [
            record.canonical_dict()
            for record in self._records
            if record.organization_id == organization_id and (project_id is None or record.project_id == project_id)
        ]
        return items[-10:]

    def find(self, receipt_id: str) -> dict[str, Any] | None:
        for record in self._records:
            if record.receipt_id == receipt_id:
                return record.canonical_dict()
        return None

    def trust_analytics(self, *, organization_id: str, project_id: str | None = None) -> dict[str, Any]:
        history = self.recent(organization_id=organization_id, project_id=project_id)
        scores = [int(item["trust_score"]) for item in history]
        latest = scores[-1] if scores else None
        previous = scores[-2] if len(scores) > 1 else latest
        delta = 0 if latest is None or previous is None else latest - previous
        if delta > 0:
            trend = "improving"
        elif delta < 0:
            trend = "declining"
        else:
            trend = "stable"
        return {
            "organization_id": organization_id,
            "project_id": project_id,
            "history": history,
            "trend": {
                "latest_trust_score": latest,
                "previous_trust_score": previous,
                "delta": delta,
                "direction": trend,
                "sample_count": len(scores),
                "average_trust_score": round(sum(scores) / len(scores), 2) if scores else None,
            },
        }

    def verify(self, receipt: dict[str, Any]) -> dict[str, Any]:
        required = {
            "receipt_id",
            "organization_id",
            "project_id",
            "prompt_hash",
            "output_hash",
            "trust_score",
            "status",
            "sequence",
            "signature",
        }
        missing = sorted(required - set(receipt))
        if missing:
            return {"verified": False, "reason": "missing_fields", "missing": missing}
        expected = sha256(
            (
                f"{receipt['receipt_id']}:{receipt['prompt_hash']}:{receipt['output_hash']}:"
                f"{receipt['trust_score']}:{receipt['status']}:{receipt['sequence']}"
            ).encode("utf-8")
        ).hexdigest()
        return {
            "verified": expected == receipt.get("signature"),
            "reason": "signature_match" if expected == receipt.get("signature") else "signature_mismatch",
            "receipt_id": receipt.get("receipt_id"),
            "expected_signature": expected,
        }


_DEFAULT_RECEIPT_STORE = GovernanceReceiptStore()


def get_governance_receipt_store() -> GovernanceReceiptStore:
    return _DEFAULT_RECEIPT_STORE
