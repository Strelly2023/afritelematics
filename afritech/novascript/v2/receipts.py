from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class GovernanceReceipt:
    receipt_id: str
    organization_id: str
    project_id: str
    prompt_hash: str
    output_hash: str
    trust_score: int
    status: str
    created_at: str
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
            "created_at": self.created_at,
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
        output_hash = sha256(str(sorted(output.items())).encode("utf-8")).hexdigest()
        receipt_id = f"rcpt-{uuid4().hex[:12]}"
        signature = sha256(f"{receipt_id}:{prompt_hash}:{output_hash}:{trust_score}:{status}".encode("utf-8")).hexdigest()
        receipt = GovernanceReceipt(
            receipt_id=receipt_id,
            organization_id=organization_id,
            project_id=project_id,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            trust_score=trust_score,
            status=status,
            created_at=datetime.now(timezone.utc).isoformat(),
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


_DEFAULT_RECEIPT_STORE = GovernanceReceiptStore()


def get_governance_receipt_store() -> GovernanceReceiptStore:
    return _DEFAULT_RECEIPT_STORE
